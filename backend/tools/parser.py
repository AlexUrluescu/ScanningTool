# tools/parser.py
"""Document parsing utilities — converts PDF/images to base64 for the vision model."""
import base64
import io
from PIL import Image
import pypdfium2 as pdfium



def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Convert a PIL Image to a base64 string."""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def parse_pdf_to_images(file_bytes: bytes) -> list[str]:
    """Convert each page of a PDF to a base64-encoded PNG image.

    Uses pypdfium2 (already installed as a pdfplumber dependency)
    to render PDF pages as images.
    """

    pdf = pdfium.PdfDocument(file_bytes)
    images_b64 = []

    for page_index in range(len(pdf)):
        page = pdf[page_index]

        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil()
        images_b64.append(image_to_base64(pil_image, "PNG"))

    pdf.close()
    return images_b64


def parse_image_to_base64(file_bytes: bytes) -> list[str]:
    """Convert an uploaded image file to a base64 string."""
    image = Image.open(io.BytesIO(file_bytes))

    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    return [image_to_base64(image, "PNG")]


def parse_document_to_images(file_bytes: bytes, content_type: str) -> list[str]:
    """Parse a document into a list of base64-encoded images.

    Args:
        file_bytes: Raw bytes of the uploaded file
        content_type: MIME type of the file

    Returns:
        List of base64-encoded image strings (one per page for PDFs)

    Raises:
        ValueError: If the file type is not supported
    """
    if content_type == "application/pdf":
        return parse_pdf_to_images(file_bytes)
    elif content_type in ("image/png", "image/jpeg", "image/jpg", "image/webp"):
        return parse_image_to_base64(file_bytes)
    else:
        raise ValueError(
            f"Unsupported file type: {content_type}. "
            "Supported types: PDF, PNG, JPG, WEBP"
        )
