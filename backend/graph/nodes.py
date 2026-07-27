import json
import re
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from core.state import State
from prompts.index import ONBOARDING_EXTRACTION_PROMPT, CLASSIFICATION_PROMPT
import re as _re

llm = ChatOllama(model="qwen2.5vl:7b", temperature=0)


ONBOARDING_FIELDS = {
    "firstName": "",
    "lastName": "",
    "email": "",
    "phone": "",
    "cnp": "",
    "birthDate": "",
    "address": "",
    "city": "",
    "postalCode": "",
    "jobTitle": "",
    "department": "",
    "startDate": "",
    "iban": "",
    "emergencyContactName": "",
    "emergencyContactPhone": "",
}


def classify_document(state: State) -> dict:
    """Classify the uploaded document (ID card, CV, contract, or other)."""
    document_images = state.get("document_images", [])

    content = [{"type": "text", "text": CLASSIFICATION_PROMPT}]

    for img_b64 in document_images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
        })

    message = HumanMessage(content=content)
    response = llm.invoke([message])
    extracted = _parse_llm_json(response.content)

    return {
        "document_type": extracted.get("type", "UNKNOWN"),
        "messages": state.get("messages", [])
    }


def extract_onboarding_data(state: State) -> dict:
    """Extract onboarding form fields from any document type."""
    document_images = state.get("document_images", [])

    if not document_images:
        return {
            "extracted_data": {**ONBOARDING_FIELDS, "error": "No images could be extracted from the document."},
            "messages": state.get("messages", [])
        }

    content = [{"type": "text", "text": ONBOARDING_EXTRACTION_PROMPT}]

    for img_b64 in document_images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
        })

    message = HumanMessage(content=content)
    response = llm.invoke([message])
    extracted = _parse_llm_json(response.content)

    return {
        "extracted_data": extracted,
        "messages": state.get("messages", [])
    }


def validate_output(state: State) -> dict:
    """Validate and normalise extracted onboarding data."""
    data = state.get("extracted_data", {})

    if data is None:
        data = {}

    for key, default_val in ONBOARDING_FIELDS.items():
        if key not in data or data[key] is None:
            data[key] = default_val
        else:
            data[key] = str(data[key]).strip()

    cnp = data.get("cnp", "")
    if cnp and (len(cnp) != 13 or not cnp.isdigit()):
        match = re.search(r"\d{13}", cnp)
        data["cnp"] = match.group() if match else ""

    for date_key in ("birthDate", "startDate"):
        date_val = data.get(date_key, "")
        if date_val:
            data[date_key] = _normalise_date(date_val)

    return {
        "extracted_data": data,
        "messages": state.get("messages", [])
    }


def _normalise_date(value: str) -> str:
    """Try to parse various date formats into YYYY-MM-DD."""

    if _re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value

    m = _re.match(r"^(\d{1,2})[./](\d{1,2})[./](\d{4})$", value)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"

    m = _re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})$", value)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    return value


def _parse_llm_json(content: str) -> dict:
    """Try multiple strategies to parse JSON from LLM output."""

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    brace_match = re.search(r"\{.*\}", content, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    return {
        "error": "Failed to parse LLM response as JSON",
        "raw_response": content[:500],
        **ONBOARDING_FIELDS,
    }