
"""LangGraph nodes for the invoice extraction pipeline."""
import json
import re
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from core.state import State
from prompts.index import EXTRACTION_PROMPT, CLASSIFICATION_PROMPT, CV_EXTRACTION_PROMPT

llm = ChatOllama(model="qwen2.5vl:7b", temperature=0)

def extract_invoice_data(state: State) -> dict:
    """Extract structured invoice data from document images using the vision model."""
    document_images = state.get("document_images", [])

    if not document_images:
        return {
            "extracted_data": {
                "error": "No images could be extracted from the document.",
                "vendor_name": "",
                "vendor_address": "",
                "invoice_number": "",
                "date": "",
                "due_date": "",
                "subtotal": None,
                "tax": None,
                "total": None,
                "currency": "",
                "items": [],
                "payment_method": "",
                "notes": ""
            },
            "messages": state.get("messages", [])
        }

    content = [{"type": "text", "text": EXTRACTION_PROMPT}]

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


def extract_cv_data(state: State) -> dict:
    """Extract structured CV data from document images using the vision model."""
    document_images = state.get("document_images", [])

    if not document_images:
        return {
            "extracted_data": {
                "error": "No images could be extracted from the document."
            }
        }

    content = [{"type": "text", "text": CV_EXTRACTION_PROMPT}]

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
    """Validate and clean up the extracted data."""
    data = state.get("extracted_data", {})

    if data is None:
        data = {}

    doc_type = state.get("document_type", "UNKNOWN")

    if doc_type == "CV":
        defaults = {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "education": [],
            "experience": [],
            "skills": [],
            "languages": []
        }
        for key, default_val in defaults.items():
            if key not in data:
                data[key] = default_val
    else:
        defaults = {
            "vendor_name": "",
            "vendor_address": "",
            "invoice_number": "",
            "date": "",
            "due_date": "",
            "subtotal": None,
            "tax": None,
            "total": None,
            "currency": "",
            "items": [],
            "payment_method": "",
            "notes": ""
        }

        for key, default_val in defaults.items():
            if key not in data:
                data[key] = default_val

        if isinstance(data.get("items"), list):
            cleaned_items = []
            for item in data["items"]:
                if isinstance(item, dict):
                    cleaned_items.append({
                        "description": item.get("description", ""),
                        "quantity": item.get("quantity"),
                        "unit_price": item.get("unit_price"),
                        "amount": item.get("amount")
                    })
            data["items"] = cleaned_items

    return {
        "extracted_data": data,
        "messages": state.get("messages", [])
    }


async def classify_document(state: State) -> dict:
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
        "vendor_name": "",
        "vendor_address": "",
        "invoice_number": "",
        "date": "",
        "due_date": "",
        "subtotal": None,
        "tax": None,
        "total": None,
        "currency": "",
        "items": [],
        "payment_method": "",
        "notes": ""
    }