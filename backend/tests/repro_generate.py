import os
from backend.app import create_app
from backend.config.config import Config
from backend.database.db import db_session
from backend.models import User, UploadedDocument, Flashcard
from backend.nlp.generator import generate_flashcards_from_doc

class TestConfig(Config):
    TESTING = True
    DATABASE_URL = 'sqlite:///./backend/tests/repro_generate.db'
    UPLOAD_FOLDER = './backend/tests/test_gen_uploads'

app = create_app(TestConfig)
with app.app_context():
    db_session.query(Flashcard).delete()
    db_session.query(UploadedDocument).delete()
    db_session.query(User).delete()
    db_session.commit()

    user = User(email='repro@example.com', password_hash='pass')
    db_session.add(user)
    db_session.commit()

    doc = UploadedDocument(user_id=user.id, filename='demo.txt', file_path='/tmp/demo.txt', file_type='txt', file_size=500, status='completed')
    db_session.add(doc)
    db_session.commit()
    doc_id = doc.id

os.makedirs('./backend/tests/test_gen_uploads/extracted', exist_ok=True)
with open(f'./backend/tests/test_gen_uploads/extracted/{doc_id}.txt', 'w', encoding='utf-8') as f:
    f.write('Photosynthesis is the process plants use to convert sunlight into chemical energy. Chlorophyll absorbs light in the leaves of plants. Plants release oxygen as a byproduct of photosynthesis.')

with app.app_context():
    cards = generate_flashcards_from_doc(doc_id, num_cards=5)
    print('cards', len(cards))
    for c in cards:
        print(c)
