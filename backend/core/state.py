from typing import TypedDict, Optional, Literal, Annotated
import operator
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
    total_amount: Optional[float] = None
    supplier_name: Optional[str] = None
    supplier_cif: Optional[str] = None
    client_name: Optional[str] = None
    client_cif: Optional[str] = None
    direction_resolved: bool = False
    direction_fallback: bool = False 



class ExtractionResult(BaseModel):
    transactions: list[Transaction]


class DocumentInput(TypedDict):
    """Input for a single parallel document processing branch.
    Each Send() creates one of these."""
    doc_b64: str
    doc_index: int
    total_docs: int
    company_cif: Optional[str]
    company_name: Optional[str]


class FinancialState(TypedDict):
    documents: list[str]

    extracted_texts: Annotated[list[str], operator.add]
    extracted_transactions: Annotated[list, operator.add]
    current_doc_index: int
    report: str

    company_cif: Optional[str]
    company_name: Optional[str]