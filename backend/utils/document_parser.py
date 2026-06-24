import os
import fitz  # PyMuPDF
import pdfplumber
import docx

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file using PyMuPDF with fallback to pdfplumber."""
    text = ""
    try:
        # Try PyMuPDF first (fast and robust)
        doc = fitz.open(file_path)
        for page in doc:
            page_text = page.get_text()
            if page_text:
                text += page_text + "\n"
        doc.close()
    except Exception as e:
        # Fallback to pdfplumber
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as inner_e:
            raise IOError(f"Failed to parse PDF using PyMuPDF and pdfplumber: {str(inner_e)}") from e
            
    if not text.strip():
        # Double check with pdfplumber if PyMuPDF returned nothing (e.g. empty or complex layout)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            pass
            
    return text

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file using python-docx."""
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)
    except Exception as e:
        raise IOError(f"Failed to parse DOCX: {str(e)}") from e

def extract_text_from_txt(file_path):
    """Extract text from a raw TXT file, trying common encodings."""
    encodings = ['utf-8', 'latin-1', 'cp1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise IOError("Failed to parse TXT: Unknown encoding. File must be saved in UTF-8 or compatible encoding.")

def extract_text(file_path, file_type):
    """Route text extraction based on file extension/type."""
    file_type = file_type.lower().strip('.')
    
    if file_type == 'pdf':
        text = extract_text_from_pdf(file_path)
    elif file_type == 'docx':
        text = extract_text_from_docx(file_path)
    elif file_type == 'txt':
        text = extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
        
    return text
