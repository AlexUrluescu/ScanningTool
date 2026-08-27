FINANCIAL_EXTRACTION_PROMPT = """You are a highly precise data extraction AI. You are given text extracted from a fiscal receipt (e.g., gas station receipt, parking ticket, or other business trip expense).

Your task: Extract the core expense details from the text and return them in a structured JSON format.

CRITICAL INSTRUCTIONS:

1. Extract EXACTLY ONE expense per document, representing the document's final total (the amount actually paid).
   Do NOT extract individual items (e.g., "10 Liters Diesel", "Snacks") as separate expenses.

2. Extracted Fields:
   - expense_description: A short description of the expense based on the vendor or main item (e.g., "Gasoline - OMV", "Parking", "Diesel - Petrom").
   - invoice_number_date: The receipt/invoice number and the date (e.g., "Bon fiscal 12345 / 15.07.2026").
   - expense_amount: The total final amount paid (as a positive float).
   - currency: The currency of the transaction (e.g., "RON", "EUR", "USD"). Look for signs like "LEI", "RON", "€" in the total.
   - payment_method: How the expense was paid (e.g., "Card", "Cash"). Look for terms like "CARD", "NUMERAR", "CASH".

3. Formatting: Remove commas/spaces from numbers so they parse as floats (e.g. 1,234.56 -> 1234.56).

Text to process:
{text}
"""