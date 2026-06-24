import random
import json
from sqlalchemy import func
from backend.database.db import db_session
from backend.models.flashcard import Flashcard
from backend.models.quiz_history import QuizHistory
from backend.models.learning_progress import LearningProgress
from backend.models.keyword import Keyword

def generate_quiz_questions(user_id, topic_id=None, document_id=None, num_questions=10):
    """Retrieve random flashcards and generate multiple choice distractors for each."""
    # 1. Query candidate flashcards
    query = db_session.query(Flashcard).filter(Flashcard.user_id == user_id)
    if topic_id:
        query = query.filter(Flashcard.topic_id == topic_id)
    if document_id:
        query = query.filter(Flashcard.document_id == document_id)
        
    flashcards = query.all()
    if not flashcards:
        return {"error": "No flashcards found for this topic/document. Generate some first!"}, 400

    # Determine quiz size
    quiz_size = min(len(flashcards), num_questions)
    quiz_cards = random.sample(flashcards, quiz_size)

    # 2. Get pool of other answers to use as distractors
    all_answers_pool = [c.answer.strip() for c in flashcards]
    
    # If the pool is too small, pull other answers belonging to this user
    if len(set(all_answers_pool)) < 4:
        user_cards = db_session.query(Flashcard).filter(Flashcard.user_id == user_id).all()
        all_answers_pool.extend([c.answer.strip() for c in user_cards])
        
    # If pool is still too small, pull keywords as fallback distractors
    if len(set(all_answers_pool)) < 4:
        user_kws = db_session.query(Keyword).join(Keyword.document).filter(Keyword.document.has(user_id=user_id)).all()
        all_answers_pool.extend([kw.word for kw in user_kws])
        
    # Ultimate backup fillers to guarantee 4 options
    backup_fillers = ["Not applicable", "None of the above", "Detail not specified", "Alternative context"]
    all_answers_pool.extend(backup_fillers)
    
    # Deduplicate pool and normalize
    distractor_pool = list(set([ans.lower() for ans in all_answers_pool if ans]))

    quiz_questions = []
    
    # 3. Compile MCQ options for each selected flashcard
    for card in quiz_cards:
        correct_answer = card.answer.strip()
        
        # Select 3 distractors
        card_distractors = []
        possible_distractors = [ans for ans in distractor_pool if ans != correct_answer.lower()]
        
        if len(possible_distractors) >= 3:
            selected_distractors = random.sample(possible_distractors, 3)
            # Find the original case versions from all_answers_pool
            for dist in selected_distractors:
                orig_case = next((ans for ans in all_answers_pool if ans.lower() == dist), dist)
                card_distractors.append(orig_case)
        else:
            # Fallback filler distractors
            fillers = [f for f in backup_fillers if f.lower() != correct_answer.lower()]
            card_distractors = fillers[:3]
            
        # Shuffle correct answer + distractors
        options = [correct_answer] + card_distractors
        # Ensure we have exactly 4 unique options (or fallback if some are duplicate)
        options = list(dict.fromkeys(options))[:4]
        while len(options) < 4:
            filler = random.choice(backup_fillers)
            if filler not in options:
                options.append(filler)
                
        random.shuffle(options)
        
        quiz_questions.append({
            "flashcard_id": card.id,
            "question": card.question,
            "options": options
        })
        
    return {"questions": quiz_questions}, 200

def evaluate_quiz_submission(user_id, topic_id, user_answers):
    """Grade quiz answers, save history, and update topic learning progress."""
    if not user_answers:
        return {"error": "No answers provided."}, 400

    correct_count = 0
    total_count = len(user_answers)
    incorrect_questions = []
    evaluation_details = []

    # 1. Grade each question
    for ans in user_answers:
        flashcard_id = ans.get("flashcard_id")
        selected_option = ans.get("selected_option", "").strip()

        card = db_session.get(Flashcard, flashcard_id)
        if not card or card.user_id != user_id:
            continue  # Skip invalid or unauthorized flashcard checks
            
        correct_ans = card.answer.strip()
        is_correct = selected_option.lower() == correct_ans.lower()
        
        if is_correct:
            correct_count += 1
        else:
            incorrect_questions.append({
                "question": card.question,
                "correct_answer": correct_ans,
                "given_answer": selected_option
            })
            
        evaluation_details.append({
            "flashcard_id": card.id,
            "question": card.question,
            "selected_option": selected_option,
            "correct_answer": correct_ans,
            "is_correct": is_correct
        })

    if total_count == 0:
        return {"error": "Could not validate any submitted answers."}, 400

    score_percentage = round((correct_count / total_count) * 100.0, 2)

    try:
        # 2. Record in QuizHistory
        history = QuizHistory(
            user_id=user_id,
            topic_id=topic_id,
            total_questions=total_count,
            correct_answers=correct_count,
            score=score_percentage,
            incorrect_questions_json=json.dumps(incorrect_questions)
        )
        db_session.add(history)
        db_session.commit()  # Commit first to generate history ID and include it in average calculation
        
        # 3. Update LearningProgress for this Topic (if topic is provided)
        progress_info = None
        if topic_id:
            progress = db_session.query(LearningProgress).filter_by(user_id=user_id, topic_id=topic_id).first()
            if not progress:
                progress = LearningProgress(
                    user_id=user_id,
                    topic_id=topic_id,
                    flashcards_viewed=0,
                    mastery_level=0.0
                )
                db_session.add(progress)
                
            progress.flashcards_viewed += total_count
            
            # Calculate new mastery level: average score of all quizzes taken on this topic
            avg_score = db_session.query(func.avg(QuizHistory.score)).filter_by(user_id=user_id, topic_id=topic_id).scalar()
            progress.mastery_level = round(float(avg_score), 2) if avg_score is not None else score_percentage
            
            db_session.commit()
            
            progress_info = {
                "flashcards_viewed": progress.flashcards_viewed,
                "mastery_level": progress.mastery_level
            }

        return {
            "score": score_percentage,
            "correct_answers": correct_count,
            "total_questions": total_count,
            "quiz_history_id": history.id,
            "evaluation": evaluation_details,
            "progress": progress_info
        }, 200
        
    except Exception as e:
        db_session.rollback()
        return {"error": f"Failed to submit quiz score: {str(e)}"}, 500
