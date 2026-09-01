import re
import threading
from collections import Counter
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from core.state import FinancialState, DocumentInput, ExtractionResult
from prompts.index import FINANCIAL_EXTRACTION_PROMPT
from graph.ocr_worker import run_ocr_single
import dateutil.parser
import unicodedata
from difflib import SequenceMatcher

llm_lock = threading.Lock()
# llm = ChatOllama(model="llama3.1:8b", temperature=0)

llm = ChatOllama(
    model="llama3.1:8b", #
    base_url="http://192.168.100.56:11434",
    temperature=0
)

_DATE_LINE_RE = re.compile(r"^\s*\d{1,4}[./-]\d{1,2}[./-]\d{1,4}")


def merge_continuation_lines(lines_text: list[str]) -> list[str]:
    """Merge OCR rows that don't start with a date into the previous transaction row.

    Multi-line transaction descriptions (e.g. 'date + desc' / 'Plătitor: ...' /
    'debit credit balance' as three separate detected lines) otherwise end up as
    three disconnected rows, and the LLM can lose the link between a transaction
    and its balance. Any row lacking a leading date is treated as a continuation
    of the previous row and appended to it.

    IMPORTANT: continuation lines are joined with '\\n', not ' | '. Using the same
    ' | ' separator for both within-row columns and between-row merges collapses
    a multi-row table (e.g. an invoice's two-column FURNIZOR / CLIENT layout) into
    a single flat blob, destroying the row alignment that tells the LLM which
    value in the left column pairs with which value in the right column on the
    SAME original row. Keeping '\\n' preserves that boundary: within a row, columns
    stay joined by ' | '; between rows (including merged continuations), a newline
    marks a new original visual line.
    """
    merged: list[str] = []
    for line in lines_text:
        if _DATE_LINE_RE.match(line) or not merged:
            merged.append(line)
        else:
            merged[-1] = f"{merged[-1]}\n{line}"
    return merged



def _build_company_context(company_name: Optional[str], company_cif: Optional[str]) -> str:
    """Build a context block about the main company, injected into the prompt."""
    if not company_name and not company_cif:
        return ""
    parts = []
    if company_name:
        parts.append(f"name \"{company_name}\"")
    if company_cif:
        parts.append(f"CIF \"{company_cif}\"")
    identity = " and ".join(parts)
    return (
        f"\nContext: the reports in this pipeline are generated for the company with {identity}. "
        f"This may help you recognize which party (supplier or client) it corresponds to on this "
        f"document, especially if the OCR text is noisy. Do not use this to decide income/expense "
        f"direction yourself — see the rules below.\n"
    )


def _run_extraction_on_text(text: str, doc_index: int, company_name: Optional[str], company_cif: Optional[str]) -> list:
    """Run LLM structured extraction on OCR text. Returns list of Transaction objects."""
    company_context = _build_company_context(company_name, company_cif)
    prompt = FINANCIAL_EXTRACTION_PROMPT.format(text=text, company_context=company_context)
    message = HumanMessage(content=prompt)

    # print(f"\\n--- [DEBUG-LLM] PROMPT SENT TO QWEN (Doc {doc_index + 1}) ---")
    # print(prompt[:200] + "...") # trunchiat
    # print("------------------------------------------------------\\n")

    import json
    
    try:
        # with llm_lock:
            # Folosim format="json" ca să forțăm Ollama să nu pună texte conversaționale
        response = llm.bind(format="json").invoke([message])
        
        raw_text = response.content.strip()
        # print(f"\\n--- [DEBUG-LLM] RAW JSON FROM QWEN (Doc {doc_index + 1}) ---")
        # print(raw_text[:200] + "...") # trunchiat
        # print("------------------------------------------------------\\n")

        # Eliminăm posibilele block-uri markdown ```json
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        data = json.loads(raw_text)
        from core.state import Transaction
        
        # Parsare robustă (Qwen câteodată dă un obiect direct în loc de listă de obiecte)
        if "transactions" in data and isinstance(data["transactions"], list):
            txs_data = data["transactions"]
        elif isinstance(data, list):
            txs_data = data
        elif isinstance(data, dict) and ("date" in data or "source_type" in data):
            txs_data = [data]
        else:
            print(f"[LLM] Error: Unexpected JSON structure: {raw_text[:150]}")
            return []

        # Validare prin Pydantic
        transactions = []
        valid_categories = {'Income', 'Rent', 'Utilities', 'Salaries', 'Food', 'Transport', 'Subscriptions', 'Taxes', 'Transfer', 'Fee', 'Other'}
        
        for t_data in txs_data:
            # Plase de siguranță (fallback-uri) dacă Qwen uită câmpuri obligatorii sau pune null
            if not t_data.get("description"):
                t_data["description"] = t_data.get("supplier_name") or t_data.get("client_name") or "Unknown"
            
            # Asigurăm că categoria e fix din lista permisă de Pydantic
            cat = t_data.get("category")
            if not cat or cat not in valid_categories:
                t_data["category"] = "Other"
                
            if not t_data.get("date"):
                t_data["date"] = "1970-01-01"
            
            try:
                transactions.append(Transaction(**t_data))
            except Exception as val_e:
                print(f"[LLM] Validation error for a transaction: {val_e}")

        # --- Post-procesare: corectează greșelile frecvente ale LLM-ului ---
        for tx in transactions:
            if tx.source_type != "INVOICE":
                continue

            # Fix 1: Qwen pune uneori suma în credit/debit în loc de total_amount.
            # Mutăm valoarea în total_amount și golim credit/debit (conform promptului).
            if tx.total_amount is None:
                if tx.credit is not None:
                    print(f"  [Post-fix] Moved credit={tx.credit} → total_amount (was None)")
                    tx.total_amount = tx.credit
                    tx.credit = None
                elif tx.debit is not None:
                    print(f"  [Post-fix] Moved debit={tx.debit} → total_amount (was None)")
                    tx.total_amount = tx.debit
                    tx.debit = None

            # Fix 2: Qwen uneori nu extrage supplier/client deloc (ex: factura DIGI).
            # Dacă description conține un nume de firmă și nu e compania noastră,
            # Dacă description conține un nume de firmă și nu e compania noastră,
            # îl setăm ca supplier_name (cel mai frecvent caz: factura de la un furnizor).
            if not tx.supplier_name and not tx.client_name and tx.description:
                # Dacă description arată ca un nume de firmă, folosim-o ca supplier
                tx.supplier_name = tx.description
                print(f"  [Post-fix] Set supplier_name from description: {tx.supplier_name!r}")
            
            # Fix 3: Extragere deterministă a CIF-urilor lipsă cu Regex direct din textul OCR.
            if not tx.supplier_cif or not tx.client_cif:
                import re
                # Căutăm toate secvențele care arată a CIF/CUI în text
                found_cifs = re.findall(r"(?:CIF|CUI|C\.I\.F\.)[^\w]*([A-Za-z]*\s*\d{6,10})", text, flags=re.IGNORECASE)
                if found_cifs:
                    # Curățăm CIF-urile găsite
                    clean_cifs = [_normalize_cif(c) for c in found_cifs if _normalize_cif(c)]
                    # Deduplicăm păstrând ordinea
                    seen = set()
                    unique_cifs = [x for x in clean_cifs if not (x in seen or seen.add(x))]
                    
                    if len(unique_cifs) >= 1:
                        # Dacă e primul CIF găsit și ne lipsește furnizorul
                        if not tx.supplier_cif and tx.supplier_name:
                            tx.supplier_cif = unique_cifs[0]
                            print(f"  [Post-fix] Extracted supplier_cif via regex: {tx.supplier_cif}")
                    
                    if len(unique_cifs) >= 2:
                        # Al doilea CIF este, de obicei, al clientului
                        if not tx.client_cif:
                            tx.client_cif = unique_cifs[1]
                            print(f"  [Post-fix] Extracted client_cif via regex: {tx.client_cif}")

        if transactions:
            print(f"[LLM] Extracted {len(transactions)} transactions from document {doc_index + 1}")
            for i, tx in enumerate(transactions):
                print(f"  [LLM-TX-{i}] desc={tx.description!r}, source={tx.source_type}")
                print(f"    supplier: name={tx.supplier_name!r}, cif={tx.supplier_cif!r}")
                print(f"    client:   name={tx.client_name!r}, cif={tx.client_cif!r}")
                print(f"    total_amount={tx.total_amount}, debit={tx.debit}, credit={tx.credit}")
            return transactions
        else:
            print(f"[LLM] No valid transactions found in document {doc_index + 1}")
            return []

    except json.JSONDecodeError as e:
        print(f"[LLM] Invalid JSON returned: {e}")
        return []
    except Exception as e:
        print(f"[LLM] Error extracting transactions: {e}")
        return []


def process_document(state: DocumentInput) -> dict:
    """Process a single document: OCR (in separate process) → LLM extraction.

    This node is called IN PARALLEL via Send() for each document.
    OCR runs in an isolated process (via ProcessPoolExecutor) which has
    its own PaddleOCR instance — no shared memory, no corrupted results.
    LLM calls still run in threads (Ollama queues them internally).
    """
    doc_b64 = state["doc_b64"]
    doc_index = state["doc_index"]
    total_docs = state["total_docs"]
    company_name = state.get("company_name")
    company_cif = state.get("company_cif")


    extracted_text = run_ocr_single(doc_b64, doc_index, total_docs)
    
    print(f"\\n{'='*60}\\n[OCR-FULL-TEXT] doc_index={doc_index+1}/{total_docs}\\n{extracted_text}\\n{'='*60}\\n")

    transactions = _run_extraction_on_text(extracted_text, doc_index, company_name, company_cif)

    return {
        "extracted_texts": [extracted_text],
        "extracted_transactions": transactions,
    }


def parse_date(date_str: str):
    try:
        return dateutil.parser.parse(date_str, fuzzy=True)
    except Exception:
        from datetime import datetime
        return datetime.min


def _normalize_cif(cif: Optional[str]) -> Optional[str]:
    """Normalizează un CIF pentru comparație (fără 'RO', fără spații, uppercase)."""
    if not cif:
        return None
    c = cif.upper().replace(" ", "").strip()
    return c[2:] if c.startswith("RO") else c


_LEGAL_SUFFIXES = (
    "SRL", "SA", "PFA", "II", "IF", "SCS", "SCA", "SNC",
)


def _normalize_name(name: Optional[str]) -> Optional[str]:
    """Normalizează numele unei companii pentru comparație fuzzy."""
    if not name:
        return None

    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.upper()
    n = re.sub(r"[^A-Z0-9\s]", " ", n)
    tokens = [t for t in n.split() if t and t not in _LEGAL_SUFFIXES]
    return " ".join(tokens) if tokens else None


def _names_match(a: Optional[str], b: Optional[str], threshold: float = 0.87) -> bool:
    """Compară două nume normalizate prin similaritate fuzzy."""
    if not a or not b:
        return False
    if a == b:
        return True
    return SequenceMatcher(None, a, b).ratio() >= threshold


def _cifs_match(a: Optional[str], b: Optional[str], threshold: float = 0.85) -> bool:
    """Compară două CIF-uri normalizate prin similaritate fuzzy pentru a ignora erorile OCR minore."""
    if not a or not b:
        return False
    if a == b:
        return True
    return SequenceMatcher(None, a, b).ratio() >= threshold


def resolve_invoice_directions(
    transactions: list, company_cif: Optional[str], company_name: Optional[str]
) -> tuple[list, Optional[str], Optional[str], bool]:
    """Decide determinist debit vs. credit pentru fiecare factură, pe baza CIF-ului
    ȘI/SAU numelui companiei principale — NU pe baza unei presupuneri făcute de LLM."""
    invoice_txs = [t for t in transactions if t.source_type == "INVOICE"]
    resolved_cif = _normalize_cif(company_cif)
    resolved_name = _normalize_name(company_name)
    auto_detected = False

    if not resolved_cif and not resolved_name:
        cif_counter = Counter()
        name_counter = Counter()
        for t in invoice_txs:
            for cif in (_normalize_cif(t.supplier_cif), _normalize_cif(t.client_cif)):
                if cif:
                    cif_counter[cif] += 1
            for nm in (_normalize_name(t.supplier_name), _normalize_name(t.client_name)):
                if nm:
                    name_counter[nm] += 1

        if cif_counter:
            top_cif, count = cif_counter.most_common(1)[0]
            if count >= 2:
                resolved_cif = top_cif
                auto_detected = True

        if not resolved_cif and name_counter:
            top_name, count = name_counter.most_common(1)[0]
            if count >= 2:
                resolved_name = top_name
                auto_detected = True

    print(f"\n[Resolve] resolved_cif={resolved_cif!r}, resolved_name={resolved_name!r}")
    print(f"[Resolve] Total invoices to resolve: {len(invoice_txs)}")

    for t in invoice_txs:
        print(f"\n[Resolve] --- Invoice: {t.description!r} ---")
        print(f"  total_amount={t.total_amount}, debit={t.debit}, credit={t.credit}")
        print(f"  supplier: name={t.supplier_name!r} cif={t.supplier_cif!r}")
        print(f"  client:   name={t.client_name!r} cif={t.client_cif!r}")

        if t.total_amount is None:
            print(f"  → SKIP: total_amount is None")
            t.direction_resolved = False
            continue

        supplier_cif = _normalize_cif(t.supplier_cif)
        client_cif = _normalize_cif(t.client_cif)
        supplier_name = _normalize_name(t.supplier_name)
        client_name = _normalize_name(t.client_name)

        print(f"  normalized: supplier_cif={supplier_cif!r}, client_cif={client_cif!r}")
        print(f"  normalized: supplier_name={supplier_name!r}, client_name={client_name!r}")

        is_supplier = (resolved_cif and _cifs_match(supplier_cif, resolved_cif)) or \
                      (resolved_name and _names_match(supplier_name, resolved_name))
        is_client = (resolved_cif and _cifs_match(client_cif, resolved_cif)) or \
                    (resolved_name and _names_match(client_name, resolved_name))

        print(f"  is_supplier={is_supplier}, is_client={is_client}")

        if is_supplier and not is_client:
            t.credit = t.total_amount
            t.debit = None
            t.direction_resolved = True
        elif is_client and not is_supplier:
            t.debit = t.total_amount
            t.credit = None
            t.direction_resolved = True
        else:
            # Fallback prin excludere: dacă nu am găsit CIF/nume direct, încercăm
            # să deducem din faptul că cealaltă parte este clar diferită de noi.
            # Ex: DIGI ROMANIA S.A. e evident furnizor extern → noi suntem clientul → debit.
            supplier_is_other = (
                (resolved_cif and supplier_cif and not _cifs_match(supplier_cif, resolved_cif)) or
                (resolved_name and supplier_name and not _names_match(supplier_name, resolved_name))
            )
            client_is_other = (
                (resolved_cif and client_cif and not _cifs_match(client_cif, resolved_cif)) or
                (resolved_name and client_name and not _names_match(client_name, resolved_name))
            )

            # Avem CIF/nume furnizor populat și el NU e compania noastră → noi suntem clientul
            if supplier_is_other and supplier_cif and not client_cif and not client_name:
                # Factura emisă de altcineva, câmpul client e gol → presupunem că noi suntem clientul
                t.debit = t.total_amount
                t.credit = None
                t.direction_resolved = True
                t.direction_fallback = True
                print(f"[Resolve] Fallback debit (supplier={t.supplier_name}, our company not in client field)")
            elif supplier_is_other and client_is_other:
                # Ambele entități sunt diferite de compania noastră — cu adevărat neclasificabilă
                t.debit = None
                t.credit = None
                t.direction_resolved = False
            elif supplier_is_other:
                # Furnizorul e altcineva → suntem clientul → cheltuială
                t.debit = t.total_amount
                t.credit = None
                t.direction_resolved = True
                t.direction_fallback = True
                print(f"[Resolve] Fallback debit by exclusion (supplier={t.supplier_name})")
            elif client_is_other:
                # Clientul e altcineva → suntem furnizorul → venit
                t.credit = t.total_amount
                t.debit = None
                t.direction_resolved = True
                t.direction_fallback = True
                print(f"[Resolve] Fallback credit by exclusion (client={t.client_name})")
            else:
                t.debit = None
                t.credit = None
                t.direction_resolved = False

    return transactions, resolved_cif, resolved_name, auto_detected


def generate_report(state: FinancialState) -> dict:
    """Calculate totals, deduplicate invoices, reconcile, and generate final markdown report deterministically."""
    txs = state.get("extracted_transactions", [])
    documents_count = len(state.get("documents", []))
    company_cif = state.get("company_cif")
    company_name = state.get("company_name")

    if not txs:
        return {"report": "No transactions could be extracted from the uploaded documents."}

    txs, resolved_cif, resolved_name, auto_detected = resolve_invoice_directions(
        txs, company_cif, company_name
    )

    txs.sort(key=lambda t: parse_date(t.date))

    bank_txs = [t for t in txs if t.source_type == "STATEMENT"]
    invoice_txs = [t for t in txs if t.source_type == "INVOICE"]
    unresolved_invoices = [t for t in invoice_txs if not t.direction_resolved]

    for inv in invoice_txs:
        if not inv.direction_resolved:
            continue

        inv_amt = inv.debit or inv.credit or 0.0
        inv_date = parse_date(inv.date)

        for bank in bank_txs:
            bank_amt = bank.debit or bank.credit or 0.0
            bank_date = parse_date(bank.date)

            amount_match = abs(inv_amt - bank_amt) < 0.01
            direction_match = (inv.debit is not None and bank.debit is not None) or \
                               (inv.credit is not None and bank.credit is not None)
            date_match = abs((inv_date - bank_date).days) <= 7

            if amount_match and direction_match and date_match:
                inv.matched_invoice = True
                break

    total_income = sum(t.credit or 0.0 for t in bank_txs) + \
        sum(t.credit or 0.0 for t in invoice_txs if t.direction_resolved and not t.matched_invoice)
    total_expenses = sum(t.debit or 0.0 for t in bank_txs) + \
        sum(t.debit or 0.0 for t in invoice_txs if t.direction_resolved and not t.matched_invoice)
    net_balance = total_income - total_expenses

    categories = {}
    for t in bank_txs:
        if t.debit:
            categories[t.category] = categories.get(t.category, 0.0) + t.debit
    for t in invoice_txs:
        if t.direction_resolved and t.debit and not t.matched_invoice:
            categories[t.category] = categories.get(t.category, 0.0) + t.debit

    sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    reconciliation_msg = ""
    valid_balances = [t for t in bank_txs if t.balance is not None]
    if len(valid_balances) >= 1:
        first_tx = valid_balances[0]

        opening_balance = first_tx.balance - (first_tx.credit or 0.0) + (first_tx.debit or 0.0)
        final_balance = valid_balances[-1].balance

        computed_net_bank = sum(t.credit or 0.0 for t in bank_txs) - sum(t.debit or 0.0 for t in bank_txs)
        reported_net_bank = final_balance - opening_balance

        if abs(computed_net_bank - reported_net_bank) > 0.01:
            reconciliation_msg = (
                f"> [!WARNING]\n> **Discrepancy detected in Bank Statements**: "
                f"Computed net change is {computed_net_bank:.2f}, but reported balances "
                f"(derived opening {opening_balance:.2f} → closing {final_balance:.2f}) "
                f"show {reported_net_bank:.2f}. Manual verification required."
            )
        else:
            reconciliation_msg = (
                "> [!TIP]\n> **Reconciliation successful**: Computed net change matches "
                "reported bank balances perfectly."
            )
    elif bank_txs:
        reconciliation_msg = (
            "> [!WARNING]\n> **Reconciliation skipped**: no bank statement row had a "
            "`balance` value extracted, so the total could not be verified."
        )

    company_msg = ""
    if resolved_cif or resolved_name:
        source = "detectat automat (recurent în facturi)" if auto_detected else "configurat explicit"
        identity = f"CIF `{resolved_cif}`" if resolved_cif else f"nume `{resolved_name}`"
        company_msg += f"> [!NOTE]\n> **Companie principală**: {identity} ({source}).\n"
    if unresolved_invoices:
        company_msg += (
            f"> [!WARNING]\n> **{len(unresolved_invoices)} factură(i) neclasificată(e)**: "
            f"nu s-a putut identifica CIF-ul companiei principale pe niciuna dintre părți "
            f"(furnizor/client). Nu au fost incluse în Total Income/Expenses — necesită "
            f"verificare manuală.\n"
        )

    lines = [
        "### Summary",
        f"- **Documents processed**: {documents_count}",
        f"- **Total Transactions**: {len(txs)}",
        f"- **Total Income**: {total_income:.2f}",
        f"- **Total Expenses**: {total_expenses:.2f}",
        f"- **Net Balance**: **{net_balance:.2f}**",
        ""
    ]

    if company_msg:
        lines.extend([company_msg, ""])

    if reconciliation_msg:
        lines.extend([reconciliation_msg, ""])

    lines.extend([
        "### Transactions",
        "| Date | Description | Source | Debit | Credit | Balance |",
        "|---|---|---|---|---|---|"
    ])

    for t in txs:
        deb = f"{t.debit:.2f}" if t.debit is not None else "-"
        cre = f"{t.credit:.2f}" if t.credit is not None else "-"
        bal = f"{t.balance:.2f}" if t.balance is not None else "-"
        desc = t.description.replace("|", "-")

        source = t.source_type
        if t.matched_invoice:
            source += " ✅ *(Matched)*"
        elif t.source_type == "INVOICE" and t.direction_resolved and t.direction_fallback:
            source += " 🔶 *(Inferred)*"
        elif t.source_type == "INVOICE" and not t.direction_resolved:
            source += " ⚠️ *(Unclassified)*"

        lines.append(f"| {t.date} | {desc} | {source} | {deb} | {cre} | {bal} |")

    if sorted_categories:
        lines.extend(["", "### Expenses by Category", "| Category | Amount |", "|---|---|"])
        for cat, amt in sorted_categories:
            lines.append(f"| {cat} | {amt:.2f} |")

    report = "\n".join(lines)
    print(f"[Report] Generated deterministically ({len(report)} chars)")

    return {"report": report}