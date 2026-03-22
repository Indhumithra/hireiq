import os
import re
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file) -> tuple:
    """Save uploaded file and return (saved_path, original_filename, file_type)."""
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'bin'
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, unique_filename)
    file.save(save_path)
    return save_path, original_filename, ext


def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract raw text from PDF, DOCX, or TXT file."""
    try:
        if file_type == 'pdf':
            text = _extract_from_pdf(file_path)
        elif file_type in ('docx', 'doc'):
            text = _extract_from_docx(file_path)
        elif file_type == 'txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        else:
            text = ''
        # Always sanitize the extracted text
        return _sanitize_text(text)
    except Exception as e:
        current_app.logger.error(f"Error extracting text from {file_path}: {e}")
    return ''


def _extract_from_pdf(file_path: str) -> str:
    """Extract text from PDF. Tries pdfplumber first, then PyPDF2, validates quality."""
    text = ''

    # Attempt 1: pdfplumber
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        text = '\n'.join(text_parts)
    except Exception:
        pass

    # If pdfplumber gave garbled/empty text, try PyPDF2
    if not _is_good_text(text):
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text2 = '\n'.join(
                    page.extract_text() or '' for page in reader.pages
                )
            # Use whichever extraction is better quality
            if _is_good_text(text2) or _text_quality_score(text2) > _text_quality_score(text):
                text = text2
        except Exception:
            pass

    # Fallback: maybe it's a raw text file with .pdf extension
    if not _is_good_text(text):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if len(content.strip()) > 10 and _is_good_text(content):
                    text = content
        except Exception:
            pass

    return text


def _is_good_text(text: str) -> bool:
    """Check if extracted text is readable (not garbled/binary)."""
    if not text or len(text.strip()) < 20:
        return False
    return _text_quality_score(text) >= 0.70


def _text_quality_score(text: str) -> float:
    """Score how 'readable' text is. Returns 0.0 to 1.0.
    Readable text has mostly printable ASCII + common unicode characters."""
    if not text:
        return 0.0
    # Count characters that are normal readable text
    readable = sum(
        1 for c in text
        if c.isalnum() or c.isspace() or c in '.,;:!?@#$%&*()-_+=\'"/<>[]{}|\\~`'
    )
    return readable / len(text)


def _sanitize_text(text: str) -> str:
    """Remove non-printable and garbled characters from extracted text."""
    if not text:
        return ''
    # Remove control characters (except newline, tab, carriage return)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    # Replace sequences of unusual unicode with a space
    text = re.sub(r'[^\x20-\x7E\xA0-\xFF\n\t\r]', ' ', text)
    # Collapse multiple spaces
    text = re.sub(r' {3,}', '  ', text)
    return text.strip()


def _extract_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        # Also extract from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        paragraphs.append(cell.text.strip())
        return '\n'.join(paragraphs)
    except Exception:
        return ''


def delete_file(file_path: str) -> bool:
    """Delete a file safely."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    return False
