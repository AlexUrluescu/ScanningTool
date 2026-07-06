EXTRACTION_PROMPT = """You are an expert document data extractor. Look at the provided invoice/receipt image(s) carefully and extract all relevant information.

Extract the following fields and return them as a valid JSON object. If a field is not found in the document, use null for numbers and empty string "" for text fields.

Return ONLY a valid JSON object with these exact keys:
{{
  "vendor_name": "Company or seller name",
  "vendor_address": "Seller's full address",
  "invoice_number": "Invoice or receipt number",
  "date": "Invoice date in YYYY-MM-DD format if possible",
  "due_date": "Payment due date in YYYY-MM-DD format if possible",
  "subtotal": 0.00,
  "tax": 0.00,
  "total": 0.00,
  "currency": "Currency code like USD, EUR, RON",
  "items": [
    {{
      "description": "Item description",
      "quantity": 1,
      "unit_price": 0.00,
      "amount": 0.00
    }}
  ],
  "payment_method": "Payment method if mentioned",
  "notes": "Any additional notes or comments"
}}

IMPORTANT: Return ONLY the JSON object. No explanations, no markdown, no code blocks. Just pure JSON."""


CLASSIFICATION_PROMPT = """You are a document classification expert. Look at the provided document image(s) carefully and determine the type of document.

Return ONLY a valid JSON object with these exact keys:
{{
  "type": "INVOICE" | "RECEIPT" | "CV" | "OTHER"
}}

IMPORTANT: Return ONLY the JSON object. No explanations, no markdown, no code blocks. Just pure JSON."""

CV_EXTRACTION_PROMPT = """You are an expert CV data extractor. Look at the provided CV image(s) carefully and extract all relevant information.

Extract the following fields and return them as a valid JSON object. If a field is not found in the document, use null for numbers and empty string "" for text fields.

Return ONLY a valid JSON object with these exact keys:
{{
  "name": "Candidate's full name",
  "email": "Candidate's email address",
  "phone": "Candidate's phone number",
  "location": "Candidate's location",
  "education": [
    {{
      "institution": "University/School name",
      "degree": "Degree obtained",
      "years": "Years attended"
    }}
  ],
  "experience": [
    {{
      "company": "Company name",
      "role": "Job title",
      "years": "Years worked",
      "description": "Brief description of responsibilities"
    }}
  ],
  "skills": ["List of skills"],
  "languages": ["List of languages"]
}}

IMPORTANT: Return ONLY the JSON object. No explanations, no markdown, no code blocks. Just pure JSON."""