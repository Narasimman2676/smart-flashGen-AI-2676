import React, { useEffect, useState } from 'react';
import API from '../services/api';

const Quiz = () => {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadQuiz = async () => {
    try {
      setLoading(true);
      const res = await API.post('/quiz', { num_questions: 10 });
      setQuestions(res.data.questions || []);
      setAnswers({});
      setResult(null);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuiz();
  }, []);

  const submitQuiz = async () => {
    const payload = Object.entries(answers).map(([flashcardId, selectedOption]) => ({
      flashcard_id: Number(flashcardId),
      selected_option: selectedOption,
    }));

    try {
      const res = await API.post('/quiz/submit', { answers: payload });
      setResult(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ maxWidth: '900px', margin: '100px auto 40px', padding: '0 20px' }}>
      <div className="glass-panel" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h1 style={{ fontSize: '1.9rem', marginBottom: '6px' }}>Take a Quiz</h1>
            <p style={{ color: 'hsl(var(--text-secondary))', margin: 0 }}>Answer the generated multiple-choice questions and check your progress.</p>
          </div>
          <button onClick={loadQuiz} className="btn-primary">New Quiz</button>
        </div>

        {loading ? (
          <p style={{ marginTop: '20px' }}>Loading questions...</p>
        ) : questions.length === 0 ? (
          <p style={{ marginTop: '20px' }}>No quiz questions available yet. Generate some flashcards first.</p>
        ) : (
          <>
            <div style={{ display: 'grid', gap: '16px', marginTop: '24px' }}>
              {questions.map((q, index) => (
                <div key={q.flashcard_id} className="glass-panel" style={{ padding: '16px' }}>
                  <h3 style={{ fontSize: '1rem', marginBottom: '10px' }}>{index + 1}. {q.question}</h3>
                  <div style={{ display: 'grid', gap: '8px' }}>
                    {q.options.map((option) => (
                      <label key={option} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <input
                          type="radio"
                          name={`q-${q.flashcard_id}`}
                          checked={answers[q.flashcard_id] === option}
                          onChange={() => setAnswers((prev) => ({ ...prev, [q.flashcard_id]: option }))}
                        />
                        <span>{option}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <button onClick={submitQuiz} className="btn-primary" style={{ marginTop: '20px' }}>Submit Quiz</button>
          </>
        )}

        {result && (
          <div className="glass-panel" style={{ padding: '16px', marginTop: '20px' }}>
            <h3 style={{ marginBottom: '8px' }}>Results</h3>
            <p>Score: {result.score}%</p>
            <p>Correct Answers: {result.correct_answers} / {result.total_questions}</p>
            {result.progress && (
              <p>Mastery Level: {result.progress.mastery_level}%</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Quiz;
