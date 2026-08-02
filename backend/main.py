from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import traceback
from graph.builder import create_graph
from tools.parser import parse_document_to_images

app = FastAPI(
    title="Financial Report AI",
    description="Upload bank statements, invoices, and receipts to generate financial reports using AI",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = create_graph()

SUPPORTED_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "financial-report-ai"}


@app.get("/api/graph")
async def get_graph_image():
    """Returns the LangGraph architecture as a PNG image."""
    try:
        img_bytes = graph.get_graph().draw_mermaid_png()
        return Response(content=img_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate graph image: {str(e)}"
        )


@app.post("/api/report")
async def generate_financial_report(files: List[UploadFile] = File(...)):
    """Upload one or more financial documents and generate a report.

    Accepts multiple PDF, PNG, JPG, or WEBP files.
    Each file is OCR'd, then all texts are sent to the LLM
    to generate a comprehensive financial report.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    # Parse all uploaded files into base64 images
    all_document_images: list[str] = []
    filenames: list[str] = []

    for file in files:
        if file.content_type not in SUPPORTED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type} ({file.filename}). "
                       f"Supported: PDF, PNG, JPG, WEBP"
            )

        file_bytes = await file.read()

        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB"
            )

        try:
            images = parse_document_to_images(file_bytes, file.content_type)
            all_document_images.extend(images)
            filenames.append(file.filename)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to process '{file.filename}': {str(e)}"
            )

    if not all_document_images:
        raise HTTPException(
            status_code=422,
            detail="Could not extract any images from the uploaded documents."
        )

    print(f"[API] Processing {len(files)} file(s), {len(all_document_images)} page(s) total")

    # Invoke the LangGraph pipeline
    try:
        result = graph.invoke({
            "documents": all_document_images,
            "extracted_texts": [],
            "current_doc_index": 0,
            "report": "",
            "company_name": "Nexus Digital",
            "company_cif": "RO38492011",
        })
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )

    return {
        "success": True,
        "report": result.get("report", ""),
        "pages_processed": len(all_document_images),
        "files": filenames,
        "extracted_texts": result.get("extracted_texts", []),
    }