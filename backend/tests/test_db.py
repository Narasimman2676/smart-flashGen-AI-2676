import os
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Set environment variable to test database before importing config/db
test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_flashcards.db"))
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

from backend.config.config import Config
from backend.database.db import Base, init_db, close_db_session
from backend.models import User, UploadedDocument, Keyword, Topic, Flashcard, QuizHistory, LearningProgress


class TestDatabaseModels(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Double check the test database file is removed before starting
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            
        # Initialize test engine and session
        cls.engine = create_engine(Config.DATABASE_URL, connect_args={"check_same_thread": False})
        cls.Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=cls.engine))
        
        # Override the Base query property to use our test session
        Base.query = cls.Session.query_property()
        
        # Create all tables
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        # Drop all tables and clean up the test file
        Base.metadata.drop_all(bind=cls.engine)
        cls.Session.remove()
        cls.engine.dispose()
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

    def setUp(self):
        # Clear database and start fresh for each test
        self.session = self.Session()
        # Bind transaction
        self.trans = self.engine.connect().begin()

    def tearDown(self):
        # Roll back and close the session to prevent leaks
        self.session.close()
        self.trans.rollback()
        self.Session.remove()

    def test_database_creation_and_models(self):
        """Test table creation, data seeding, relationships, and cascade deletions."""
        
        # Record initial counts
        init_users = self.session.query(User).count()
        init_topics = self.session.query(Topic).count()
        init_docs = self.session.query(UploadedDocument).count()
        init_keywords = self.session.query(Keyword).count()
        init_cards = self.session.query(Flashcard).count()
        init_quizzes = self.session.query(QuizHistory).count()
        init_progress = self.session.query(LearningProgress).count()

        # 1. Create a User
        user = User(
            email="test_user@example.com",
            password_hash="pbkdf2:sha256:260000$hashedpassword"
        )
        self.session.add(user)
        self.session.commit()
        
        # Verify User was saved
        queried_user = self.session.query(User).filter_by(email="test_user@example.com").first()
        self.assertIsNotNone(queried_user)
        self.assertEqual(queried_user.email, "test_user@example.com")
        self.assertIsNotNone(queried_user.created_at)

        # 2. Create a Topic
        topic = Topic(
            name="Computer Science",
            description="Basics of computers and data structures",
            user_id=queried_user.id
        )
        self.session.add(topic)
        self.session.commit()

        queried_topic = self.session.query(Topic).filter_by(name="Computer Science").first()
        self.assertIsNotNone(queried_topic)
        self.assertEqual(queried_topic.user_id, queried_user.id)

        # 3. Create a Document
        document = UploadedDocument(
            user_id=queried_user.id,
            filename="lecture1.pdf",
            file_path="/uploads/lecture1.pdf",
            file_type="pdf",
            file_size=1024 * 50,  # 50 KB
            status="completed"
        )
        self.session.add(document)
        self.session.commit()

        queried_doc = self.session.query(UploadedDocument).filter_by(filename="lecture1.pdf").first()
        self.assertIsNotNone(queried_doc)
        self.assertEqual(queried_doc.user_id, queried_user.id)

        # 4. Create a Keyword linked to the Document
        keyword = Keyword(
            word="Algorithm",
            importance_score=0.95,
            document_id=queried_doc.id
        )
        self.session.add(keyword)
        self.session.commit()

        queried_keyword = self.session.query(Keyword).filter_by(word="Algorithm").first()
        self.assertIsNotNone(queried_keyword)
        self.assertEqual(queried_keyword.document_id, queried_doc.id)
        # Relationship traversal
        self.assertEqual(queried_doc.keywords[0].word, "Algorithm")

        # 5. Create a Flashcard linked to the User, Document, and Topic
        flashcard = Flashcard(
            user_id=queried_user.id,
            document_id=queried_doc.id,
            topic_id=queried_topic.id,
            question="What is an Algorithm?",
            answer="A set of step-by-step instructions for solving a problem.",
            difficulty="easy",
            is_favorite=True
        )
        self.session.add(flashcard)
        self.session.commit()

        queried_flashcard = self.session.query(Flashcard).filter_by(question="What is an Algorithm?").first()
        self.assertIsNotNone(queried_flashcard)
        self.assertEqual(queried_flashcard.user_id, queried_user.id)
        self.assertEqual(queried_flashcard.document_id, queried_doc.id)
        self.assertEqual(queried_flashcard.topic_id, queried_topic.id)
        self.assertTrue(queried_flashcard.is_favorite)

        # 6. Create QuizHistory
        quiz_history = QuizHistory(
            user_id=queried_user.id,
            topic_id=queried_topic.id,
            total_questions=10,
            correct_answers=8,
            score=80.0,
            incorrect_questions_json='[{"question": "What is an Algorithm?", "given_answer": "A dance move"}]'
        )
        self.session.add(quiz_history)
        self.session.commit()

        queried_quiz = self.session.query(QuizHistory).filter_by(user_id=queried_user.id).first()
        self.assertIsNotNone(queried_quiz)
        self.assertEqual(queried_quiz.score, 80.0)
        self.assertIn("dance move", queried_quiz.incorrect_questions_json)

        # 7. Create LearningProgress
        progress = LearningProgress(
            user_id=queried_user.id,
            topic_id=queried_topic.id,
            flashcards_viewed=5,
            mastery_level=50.0
        )
        self.session.add(progress)
        self.session.commit()

        queried_progress = self.session.query(LearningProgress).filter_by(user_id=queried_user.id).first()
        self.assertIsNotNone(queried_progress)
        self.assertEqual(queried_progress.mastery_level, 50.0)

        # Walk User relationships to ensure everything is connected
        self.assertEqual(len(queried_user.documents), 1)
        self.assertEqual(len(queried_user.topics), 1)
        self.assertEqual(len(queried_user.flashcards), 1)
        self.assertEqual(len(queried_user.quiz_histories), 1)
        self.assertEqual(len(queried_user.learning_progresses), 1)

        # 8. Test Cascade Deletion: Deleting the User should delete all cascading children
        self.session.delete(queried_user)
        self.session.commit()

        # Verify all associated data has been deleted due to CASCADE
        self.assertEqual(self.session.query(User).count(), init_users)
        self.assertEqual(self.session.query(Topic).count(), init_topics)
        self.assertEqual(self.session.query(UploadedDocument).count(), init_docs)
        self.assertEqual(self.session.query(Keyword).count(), init_keywords)
        self.assertEqual(self.session.query(Flashcard).count(), init_cards)
        self.assertEqual(self.session.query(QuizHistory).count(), init_quizzes)
        self.assertEqual(self.session.query(LearningProgress).count(), init_progress)


if __name__ == '__main__':
    unittest.main()
