import os
import pytest
from io import BytesIO
import fitz  # PyMuPDF
import docx
from backend.app import create_app
from backend.config.config import Config
from backend.database.db import db_session
from backend.models import User, UploadedDocument, TokenBlocklist

# Separate database and upload folders for testing isolation
test_upload_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_upload.db"))
test_db_url = f"sqlite:///{test_upload_db}"
test_upload_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_uploads"))

class TestConfig(Config):
    TESTING = True
    DATABASE_URL = test_db_url
    UPLOAD_FOLDER = test_upload_folder
    JWT_SECRET_KEY = "test_jwt_secret_must_be_over_32_characters_long_for_security"
    SECRET_KEY = "test_secret_must_be_over_32_characters_long_for_security"

@pytest.fixture(scope="module")
def app():
    # Remove files if exist
    if os.path.exists(test_upload_db):
        try:
            os.remove(test_upload_db)
        except PermissionError:
            pass

    app = create_app(TestConfig)
    
    yield app

    # Teardown database
    db_session.remove()
    from backend.database.db import engine
    engine.dispose()
    
    if os.path.exists(test_upload_db):
        try:
            os.remove(test_upload_db)
        except PermissionError:
            pass
            
    # Clean up test uploads directory
    if os.path.exists(test_upload_folder):
        import shutil
        shutil.rmtree(test_upload_folder, ignore_errors=True)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    """Fixture to register a user and return authorization headers."""
    client.post('/signup', json={
        "email": "uploader@example.com",
        "password": "password123"
    })
    login_resp = client.post('/login', json={
        "email": "uploader@example.com",
        "password": "password123"
    })
    token = login_resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(autouse=True)
def clean_db_and_files(app):
    # Clear tables and delete files
    with app.app_context():
        db_session.query(UploadedDocument).delete()
        db_session.query(TokenBlocklist).delete()
        db_session.query(User).delete()
        db_session.commit()
        
    if os.path.exists(test_upload_folder):
        import shutil
        shutil.rmtree(test_upload_folder, ignore_errors=True)
    os.makedirs(test_upload_folder, exist_ok=True)
    os.makedirs(os.path.join(test_upload_folder, "original"), exist_ok=True)
    os.makedirs(os.path.join(test_upload_folder, "extracted"), exist_ok=True)
    
    yield

def test_upload_unauthorized(client):
    """Test uploading a file without auth headers fails."""
    data = {'file': (BytesIO(b"simple text"), 'test.txt')}
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 401

def test_upload_no_file(client, auth_headers):
    """Test uploading request missing the file key."""
    response = client.post('/upload', headers=auth_headers, data={}, content_type='multipart/form-data')
    assert response.status_code == 400
    assert "No file part" in response.get_json()["error"]

def test_upload_invalid_extension(client, auth_headers):
    """Test uploading file with unsupported extension."""
    data = {'file': (BytesIO(b"console.log('malicious')"), 'script.js')}
    response = client.post('/upload', headers=auth_headers, data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert "Invalid file type" in response.get_json()["error"]

def test_upload_txt_success(client, auth_headers):
    """Test uploading and parsing a valid TXT file."""
    text_content = "This is a simple TXT file content for testing the document parser pipeline."
    data = {
        'file': (BytesIO(text_content.encode('utf-8')), 'test.txt')
    }
    response = client.post('/upload', headers=auth_headers, data=data, content_type='multipart/form-data')
    assert response.status_code == 201
    
    res_data = response.get_json()
    assert "document" in res_data
    doc_info = res_data["document"]
    assert doc_info["filename"] == "test.txt"
    assert doc_info["file_type"] == "txt"
    assert doc_info["status"] == "completed"
    
    # Check DB record
    doc_id = doc_info["id"]
    db_doc = db_session.get(UploadedDocument, doc_id)
    assert db_doc is not None
    assert db_doc.status == 'completed'
    
    # Verify original file exists
    assert os.path.exists(db_doc.file_path)
    
    # Verify extracted text file exists and matches original input
    extracted_text_path = os.path.join(test_upload_folder, "extracted", f"{doc_id}.txt")
    assert os.path.exists(extracted_text_path)
    with open(extracted_text_path, 'r', encoding='utf-8') as f:
        saved_text = f.read()
    assert saved_text.strip() == text_content

def test_upload_pdf_success(client, auth_headers):
    """Test uploading and parsing a valid PDF file."""
    # Create valid PDF in memory
    pdf_doc = fitz.open()
    page = pdf_doc.new_page()
    test_text = "This is some test text inside a dynamically generated PDF document."
    page.insert_text((50, 50), test_text)
    pdf_bytes = pdf_doc.write()
    pdf_doc.close()
    
    data = {
        'file': (BytesIO(pdf_bytes), 'test.pdf')
    }
    response = client.post('/upload', headers=auth_headers, data=data, content_type='multipart/form-data')
    assert response.status_code == 201
    
    res_data = response.get_json()
    doc_info = res_data["document"]
    assert doc_info["file_type"] == "pdf"
    
    # Verify extracted text
    doc_id = doc_info["id"]
    extracted_text_path = os.path.join(test_upload_folder, "extracted", f"{doc_id}.txt")
    assert os.path.exists(extracted_text_path)
    with open(extracted_text_path, 'r', encoding='utf-8') as f:
        saved_text = f.read()
    assert test_text in saved_text

def test_upload_docx_success(client, auth_headers):
    """Test uploading and parsing a valid DOCX file."""
    # Create valid DOCX in memory
    doc = docx.Document()
    test_text = "This is some text inside a dynamically generated DOCX document."
    doc.add_paragraph(test_text)
    docx_io = BytesIO()
    doc.save(docx_io)
    docx_bytes = docx_io.getvalue()
    
    data = {
        'file': (BytesIO(docx_bytes), 'test.docx')
    }
    response = client.post('/upload', headers=auth_headers, data=data, content_type='multipart/form-data')
    assert response.status_code == 201
    
    res_data = response.get_json()
    doc_info = res_data["document"]
    assert doc_info["file_type"] == "docx"
    
    # Verify extracted text
    doc_id = doc_info["id"]
    extracted_text_path = os.path.join(test_upload_folder, "extracted", f"{doc_id}.txt")
    assert os.path.exists(extracted_text_path)
    with open(extracted_text_path, 'r', encoding='utf-8') as f:
        saved_text = f.read()
    assert test_text in saved_text
