from typing import TypedDict, Optional, Literal
from pydantic import BaseModel, Field

CategoryType = Literal[
    "Income", "Rent", "Utilities", "Salaries", "Food",
    "Transport", "Subscriptions", "Taxes", "Transfer", "Fee", "Other"
]


class Transaction(BaseModel):
    date: str
    description: str
    debit: Optional[float] = None
    credit: Optional[float] = None
    balance: Optional[float] = None
    category: CategoryType
    source_type: Literal["STATEMENT", "INVOICE"] = Field(
        description="'STATEMENT' if from a bank statement, 'INVOICE' if from an invoice or receipt"
    )
    matched_invoice: bool = False

    # NOU: pentru facturi, LLM extrage doar datele brute — nu decide venit/cheltuială
    total_amount: Optional[float] = None
    supplier_name: Optional[str] = None
    supplier_cif: Optional[str] = None
    client_name: Optional[str] = None
    client_cif: Optional[str] = None
    direction_resolved: bool = False  # True doar dacă am putut stabili cu certitudine direcția


class ExtractionResult(BaseModel):
    transactions: list[Transaction]


class FinancialState(TypedDict):
    documents: list[str]
    extracted_texts: list[str]
    extracted_transactions: list[Transaction]
    current_doc_index: int
    report: str
    # NOU: identitatea companiei pentru care se generează raportul (configurabil de utilizator)
    company_cif: Optional[str]
    company_name: Optional[str]