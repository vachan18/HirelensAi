"""PDF parsing utility using pypdf."""
from pypdf import PdfReader
import io


def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from an uploaded PDF file object."""
    try:
        if isinstance(pdf_file, bytes):
            reader = PdfReader(io.BytesIO(pdf_file))
        else:
            reader = PdfReader(io.BytesIO(pdf_file.read()))

        text_parts = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted)

        full_text = "\n\n".join(text_parts)
        return full_text.strip() if full_text else "Could not extract text from PDF."
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"
