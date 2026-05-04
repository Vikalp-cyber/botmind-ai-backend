import logging
from io import BytesIO
import pdfplumber
from bs4 import BeautifulSoup
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

def extract_text_from_pdf(data: bytes) -> str:
    """
    Extracts text from a PDF byte stream.
    Validates PDF header and handles corrupted files gracefully.
    """
    # 1. Validate PDF Header (%PDF-)
    if not data.startswith(b"%PDF-"):
        logger.warning("File rejection: Missing %PDF- header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format: Not a valid PDF (missing %PDF- header)."
        )

    try:
        with pdfplumber.open(BytesIO(data)) as pdf:
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            extracted_text = "\n\n".join(text_parts).strip()
            
            if not extracted_text:
                logger.info("PDF extraction: No text found (might be an image-only PDF)")
                # Fallback to pypdf or just return empty if OCR is not available
                return ""
                
            return extracted_text

    except Exception as e:
        logger.error(f"Failed to parse PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse PDF: The file might be corrupted or encrypted. Error: {str(e)}"
        )

def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ").split())
