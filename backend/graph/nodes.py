"""LangGraph nodes for the financial report pipeline."""
import base64
import io
import re
import threading
from collections import Counter
from typing import Optional
from PIL import Image
from paddleocr import PaddleOCR
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from core.state import FinancialState, DocumentInput, ExtractionResult
from prompts.index import FINANCIAL_EXTRACTION_PROMPT

ocr = PaddleOCR(lang="en")
_ocr_lock = threading.Lock() 
llm = ChatOllama(model="qwen2.5:7b", temperature=0)

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


def _run_ocr_on_image(img_b64: str, doc_index: int, total_docs: int) -> str:
    """Run PaddleOCR on a single base64-encoded image and return structured text.
    
    This is the core OCR logic extracted from extract_ocr, untouched.
    """
    img_bytes = base64.b64decode(img_b64)
    image = Image.open(io.BytesIO(img_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")

    import numpy as np
    img_array = np.array(image)
    img_array = img_array[:, :, ::-1]

    with _ocr_lock:
        result = ocr.ocr(img_array)

    items = [] 

    if result and result[0]:
        res = result[0]

        if isinstance(res, dict):
            texts = res.get("rec_texts", [])
            polys = res.get("rec_polys") or res.get("dt_polys") or []
            for text, poly in zip(texts, polys):
                xs = [pt[0] for pt in poly]
                ys = [pt[1] for pt in poly]
                items.append((sum(ys) / len(ys), sum(xs) / len(xs), text))
        else:
            for box, (text, conf) in res:
                y_center = sum(pt[1] for pt in box) / 4.0
                x_center = sum(pt[0] for pt in box) / 4.0
                items.append((y_center, x_center, text))

    items.sort(key=lambda x: x[0])
    rows = []
    current_row = []
    current_y = None

    for y, x, text in items:
        if current_y is None:
            current_y = y
            current_row.append((x, text))
        elif abs(y - current_y) < 15:
            current_row.append((x, text))
            current_y = (current_y * len(current_row) + y) / (len(current_row) + 1)
        else:
            rows.append(current_row)
            current_row = [(x, text)]
            current_y = y

    if current_row:
        rows.append(current_row)

    lines_text = []
    for row in rows:
        row.sort(key=lambda item: item[0])
        lines_text.append(" | ".join(item[1] for item in row))

    lines_text = merge_continuation_lines(lines_text)

    page_text = "\n".join(lines_text)
    doc_label = f"--- Document {doc_index + 1} / {total_docs} ---"
    full_text = f"{doc_label}\n{page_text}"

    print(f"[OCR] Processed document {doc_index + 1}/{total_docs} — {len(lines_text)} rows reconstructed")
    return full_text


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
    """Run LLM structured extraction on OCR text. Returns list of Transaction objects.
    
    This is the core extraction logic from extract_transactions, untouched.
    """
    company_context = _build_company_context(company_name, company_cif)
    prompt = FINANCIAL_EXTRACTION_PROMPT.format(text=text, company_context=company_context)
    message = HumanMessage(content=prompt)

    structured_llm = llm.with_structured_output(ExtractionResult)

    try:
        response = structured_llm.invoke([message])
        if response and response.transactions:
            print(f"[LLM] Extracted {len(response.transactions)} transactions from document {doc_index + 1}")
            return list(response.transactions)
        else:
            print(f"[LLM] No transactions found in document {doc_index + 1}")
            return []
    except Exception as e:
        print(f"[LLM] Error extracting transactions: {e}")
        return []


def process_document(state: DocumentInput) -> dict:
    """Process a single document: OCR → LLM extraction.
    
    This node is called IN PARALLEL via Send() for each document.
    It receives a DocumentInput (single doc), not the full FinancialState.
    Returns partial state updates that get merged via operator.add reducers.
    """
    doc_b64 = state["doc_b64"]
    doc_index = state["doc_index"]
    total_docs = state["total_docs"]
    company_name = state.get("company_name")
    company_cif = state.get("company_cif")

    print(f"\n[DEBUG-START] processing doc_index={doc_index+1}/{total_docs}, base64_len={len(doc_b64)}")

    extracted_text = _run_ocr_on_image(doc_b64, doc_index, total_docs)
    
    print(f"[DEBUG-OCR] doc_index={doc_index+1}/{total_docs} OCR length: {len(extracted_text)} chars")
    print(f"[DEBUG-OCR-PREVIEW] doc_index={doc_index+1}/{total_docs}: {repr(extracted_text[:150])}...")

    transactions = _run_extraction_on_text(extracted_text, doc_index, company_name, company_cif)

    print(f"[DEBUG-LLM] doc_index={doc_index+1}/{total_docs} extracted {len(transactions)} txs")
    for i, t in enumerate(transactions):
        print(f"  tx {i}: date={t.date} desc={t.description} debit={t.debit} credit={t.credit} total={t.total_amount}")

    print(f"[DEBUG-END] finished doc_index={doc_index+1}/{total_docs}\n")

    return {
        "extracted_texts": [extracted_text],
        "extracted_transactions": transactions,
    }


import dateutil.parser
import unicodedata
from difflib import SequenceMatcher


def parse_date(date_str: str):
    try:
        return dateutil.parser.parse(date_str, fuzzy=True)
    except Exception:
        from datetime import datetime
        return datetime.min


def _normalize_cif(cif: Optional[str]) -> Optional[str]:
    """Normalizează un CIF pentru comparație (fără 'RO', fără spații, uppercase).

    OCR-ul poate introduce inconsistențe (spații, litere lipsă), dar cel puțin
    prefixul 'RO' și spațiile sunt un caz sigur de normalizat fără riscul de a
    masca o eroare de citire.
    """
    if not cif:
        return None
    c = cif.upper().replace(" ", "").strip()
    return c[2:] if c.startswith("RO") else c


_LEGAL_SUFFIXES = (
    "SRL", "SA", "PFA", "II", "IF", "SCS", "SCA", "SNC",
)


def _normalize_name(name: Optional[str]) -> Optional[str]:
    """Normalizează numele unei companii pentru comparație fuzzy.

    Elimină diacritice, punctuație, sufixe legale (S.R.L., S.A. etc.) și
    spații redundante. Scopul e ca 'Nexus Digital S.R.L.' și 'NEXUS DIGITAL
    SRL' (citite diferit de OCR pe cele două facturi) să ajungă la aceeași
    formă normalizată.
    """
    if not name:
        return None
    
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.upper()
    n = re.sub(r"[^A-Z0-9\s]", " ", n)
    tokens = [t for t in n.split() if t and t not in _LEGAL_SUFFIXES]
    return " ".join(tokens) if tokens else None


def _names_match(a: Optional[str], b: Optional[str], threshold: float = 0.87) -> bool:
    """Compară două nume normalizate prin similaritate fuzzy (nu doar egalitate exactă),
    ca să tolereze mici erori de OCR (o literă citită greșit etc.)."""
    if not a or not b:
        return False
    if a == b:
        return True
    return SequenceMatcher(None, a, b).ratio() >= threshold


def resolve_invoice_directions(
    transactions: list, company_cif: Optional[str], company_name: Optional[str]
) -> tuple[list, Optional[str], Optional[str], bool]:
    """Decide determinist debit vs. credit pentru fiecare factură, pe baza CIF-ului
    ȘI/SAU numelui companiei principale — NU pe baza unei presupuneri făcute de LLM.

    LLM-ul (vezi prompt) NU mai stabilește direcția facturii; extrage doar datele
    brute (total_amount, supplier_cif/name, client_cif/name). Direcția e calculată
    aici, determinist.

    Ordine de comparație per factură (pentru fiecare parte — furnizor și client):
      1. CIF exact (normalizat) — semnalul cel mai de încredere.
      2. Nume normalizat + comparație fuzzy — fallback pentru cazul în care CIF-ul
         lipsește din OCR sau a fost citit greșit (cifre confundate), dar numele
         companiei tot poate fi recunoscut.

    Identificarea companiei principale:
      1. Dacă `company_cif` sau `company_name` sunt furnizate explicit în state,
         se folosesc direct (CIF are prioritate dacă ambele sunt date).
      2. Altfel, se detectează automat compania principală ca fiind identitatea
         (CIF sau nume normalizat) care apare cel mai des ca furnizor SAU client
         peste toate facturile. Necesită minim 2 apariții ca să nu fie o ghicire
         din întâmplare pe un singur document.
      3. Dacă direcția tot nu poate fi determinată nici pe CIF, nici pe nume,
         tranzacția rămâne needetectată și e semnalată pentru verificare manuală
         — nu se ghicește niciodată.

    Returns:
        (transactions, resolved_cif, resolved_name, was_auto_detected)
    """
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

    for t in invoice_txs:
        if t.total_amount is None:

            t.direction_resolved = False
            continue

        supplier_cif = _normalize_cif(t.supplier_cif)
        client_cif = _normalize_cif(t.client_cif)
        supplier_name = _normalize_name(t.supplier_name)
        client_name = _normalize_name(t.client_name)

        is_supplier = (resolved_cif and supplier_cif == resolved_cif) or \
                      (resolved_name and _names_match(supplier_name, resolved_name))
        is_client = (resolved_cif and client_cif == resolved_cif) or \
                    (resolved_name and _names_match(client_name, resolved_name))

        if is_supplier and not is_client:
     
            t.credit = t.total_amount
            t.debit = None
            t.direction_resolved = True
        elif is_client and not is_supplier:
          
            t.debit = t.total_amount
            t.credit = None
            t.direction_resolved = True
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

    # NOU: mesaj despre compania principală folosită pentru rezolvarea direcției
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