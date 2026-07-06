# core/models.py
from pydantic import BaseModel, Field
from typing import Optional


class LineItem(BaseModel):
    """A single line item on an invoice/receipt."""
    description: str = Field(default="", description="Item description")
    quantity: Optional[float] = Field(default=None, description="Quantity of the item")
    unit_price: Optional[float] = Field(default=None, description="Price per unit")
    amount: Optional[float] = Field(default=None, description="Total amount for this line item")


class InvoiceData(BaseModel):
    """Structured data extracted from an invoice or receipt."""
    vendor_name: str = Field(default="", description="Company or seller name")
    vendor_address: str = Field(default="", description="Seller's address")
    invoice_number: str = Field(default="", description="Invoice or receipt number")
    date: str = Field(default="", description="Invoice/receipt date")
    due_date: str = Field(default="", description="Payment due date")
    subtotal: Optional[float] = Field(default=None, description="Pre-tax amount")
    tax: Optional[float] = Field(default=None, description="Tax amount")
    total: Optional[float] = Field(default=None, description="Total amount due")
    currency: str = Field(default="", description="Currency code (e.g. USD, EUR, RON)")
    items: list[LineItem] = Field(default_factory=list, description="Line items")
    payment_method: str = Field(default="", description="Payment method if present")
    notes: str = Field(default="", description="Additional notes")
