CLASSIFICATION_PROMPT = """You are a document classification expert. Look at the provided document image(s) carefully and determine the type of document.

Possible types:
- ID_CARD: National ID card (carte de identitate / buletin), passport, or driving license
- CV: Curriculum vitae or resume
- CONTRACT: Employment contract or job offer letter
- OTHER: Any other document type

Return ONLY a valid JSON object with this exact key:
{{
  "type": "ID_CARD" | "CV" | "CONTRACT" | "OTHER"
}}

IMPORTANT: Return ONLY the JSON object. No explanations, no markdown, no code blocks. Just pure JSON."""


ONBOARDING_EXTRACTION_PROMPT = """You are an expert data extractor for employee onboarding. You are given one or more images of a document (ID card, CV, employment contract, or similar).

Your task: extract as many of the following onboarding fields as possible from the document. If a field cannot be found, use an empty string "".

Return ONLY a valid JSON object with these exact keys:
{{
  "firstName": "Person's first name (prenume)",
  "lastName": "Person's last name (nume de familie)",
  "email": "Email address",
  "phone": "Phone number",
  "cnp": "CNP (Romanian personal numeric code, 13 digits)",
  "birthDate": "Date of birth in YYYY-MM-DD format",
  "address": "Full street address",
  "city": "City / locality",
  "postalCode": "Postal code",
  "jobTitle": "Job title / position",
  "department": "Department",
  "startDate": "Employment start date in YYYY-MM-DD format",
  "iban": "IBAN bank account number",
  "emergencyContactName": "Emergency contact full name",
  "emergencyContactPhone": "Emergency contact phone number"
}}

Guidelines:
- For ID cards (carte de identitate): extract firstName, lastName, cnp, birthDate, address, city. The CNP is a 13-digit number. The birth date can also be derived from the first 7 digits of the CNP (format: SAAMMZZ).
- For CVs: extract firstName, lastName, email, phone, address, city, jobTitle (most recent or desired role).
- For employment contracts: extract firstName, lastName, jobTitle, department, startDate, iban, and any other available fields.
- Always try to extract as many fields as possible regardless of document type.
- For Romanian names, "Prenume" = firstName, "Nume" / "Nume de familie" = lastName.
- If the document is in Romanian, translate field values only where it makes sense (e.g., keep names, addresses as-is).

IMPORTANT: Return ONLY the JSON object. No explanations, no markdown, no code blocks. Just pure JSON."""