import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename
from backend.database.db import db_session
from backend.models.document import UploadedDocument
from backend.utils.document_parser import extract_text

def allowed_file(filename):
    """Check if the uploaded file has a permitted extension."""
    allowed_exts = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'docx', 'txt'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

def handle_upload(user_id, file):
    """Process document upload, database recording, and text parsing."""
    if not file or file.filename == '':
        return {"error": "No file selected for upload."}, 400

    allowed_exts = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'docx', 'txt'})
    if not allowed_file(file.filename):
        return {"error": f"Invalid file type. Allowed types are: {', '.join(allowed_exts)}"}, 400

    original_filename = secure_filename(file.filename)
    file_ext = original_filename.rsplit('.', 1)[1].lower()
    
    # Generate a unique filename using UUID to prevent collisions on disk
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
    
    # Ensure upload target directories exist
    upload_folder = current_app.config['UPLOAD_FOLDER']
    original_dir = os.path.join(upload_folder, "original")
    extracted_dir = os.path.join(upload_folder, "extracted")
    os.makedirs(original_dir, exist_ok=True)
    os.makedirs(extracted_dir, exist_ok=True)

    original_file_path = os.path.join(original_dir, unique_filename)
    
    try:
        # 1. Save original file temporarily to get details (like size)
        file.save(original_file_path)
        file_size = os.path.getsize(original_file_path)
    except Exception as e:
        return {"error": f"Failed to save file: {str(e)}"}, 500

    # 2. Register document in database in 'processing' status
    db_doc = UploadedDocument(
        user_id=user_id,
        filename=original_filename,
        file_path=original_file_path,
        file_type=file_ext,
        file_size=file_size,
        status='processing'
    )
    
    try:
        db_session.add(db_doc)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        if os.path.exists(original_file_path):
            os.remove(original_file_path)
        return {"error": f"Database error registering document: {str(e)}"}, 500

    # 3. Parse and extract text content
    try:
        extracted_text = extract_text(original_file_path, file_ext)
        
        # Save extracted text to disk companion file
        extracted_filename = f"{db_doc.id}.txt"
        extracted_file_path = os.path.join(extracted_dir, extracted_filename)
        
        with open(extracted_file_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
            
        # 4. Update status to completed and point to extracted file path
        db_doc.status = 'completed'
        db_doc.file_path = original_file_path  # Point to the original uploaded file
        db_session.commit()
        
        return {
            "message": "Document uploaded and parsed successfully.",
            "document": {
                "id": db_doc.id,
                "filename": db_doc.filename,
                "file_type": db_doc.file_type,
                "file_size": db_doc.file_size,
                "status": db_doc.status,
                "created_at": db_doc.created_at.isoformat()
            }
        }, 201
        
    except Exception as e:
        # Mark record as failed
        db_doc.status = 'failed'
        db_session.commit()
        
        # Clean up files if parse failed to prevent junk build-up (optional, but keep original for logs if status is failed)
        # We'll keep the record in DB as failed so user knows it failed, but we can return the error.
        return {"error": f"Failed to parse document: {str(e)}"}, 422
