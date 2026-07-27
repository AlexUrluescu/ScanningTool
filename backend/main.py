# main.py
"""FastAPI server for the document extraction API."""
from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import traceback
from graph.builder import create_graph
from tools.parser import parse_document_to_images

app = FastAPI(
    title="Document Scanner API",
    description="Upload invoices/receipts and extract structured data using AI vision",
    version="1.0.0"
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

MAX_FILE_SIZE = 10 * 1024 * 1024

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "document-scanner"}


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


@app.post("/api/extract")
async def extract_document(file: UploadFile = File(...)):


    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Supported: PDF, PNG, JPG, WEBP"
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB"
        )

    try:
        document_images = parse_document_to_images(file_bytes, file.content_type)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to process document: {str(e)}"
        )

    if not document_images:
        raise HTTPException(
            status_code=422,
            detail="Could not extract any images from the document."
        )

    try:
        result = graph.invoke({
            "messages": [],
            "document_images": document_images,
            "extracted_data": None
        })
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"AI extraction failed: {str(e)}"
        )

    extracted_data = result.get("extracted_data", {})
    document_type = result.get("document_type", "UNKNOWN")

    return {
        "success": True,
        "document_type": document_type,
        "data": extracted_data,
        "pages_processed": len(document_images),
        "filename": file.filename
    }