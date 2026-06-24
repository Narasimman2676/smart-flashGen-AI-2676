import React, { useEffect, useState } from 'react';
import API from '../services/api';

const Analytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setLoading(true);
        const res = await API.get('/analytics');
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, []);

  return (
    <div style={{ maxWidth: '1100px', margin: '100px auto 40px', padding: '0 20px' }}>
      <div className="glass-panel" style={{ padding: '28px' }}>
        <h1 style={{ fontSize: '1.9rem', marginBottom: '6px' }}>Study Analytics</h1>
        <p style={{ color: 'hsl(var(--text-secondary))', marginBottom: '20px' }}>Track your study progress, quiz performance, and weak areas.</p>

        {loading ? (
          <p>Loading analytics...</p>
        ) : !data ? (
          <p>No analytics available yet.</p>
        ) : (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
              {[
                { label: 'Uploaded Documents', value: data.statistics?.total_documents ?? 0 },
                { label: 'Flashcards', value: data.statistics?.total_flashcards ?? 0 },
                { label: 'Quiz Count', value: data.statistics?.total_quizzes ?? 0 },
                { label: 'Accuracy', value: `${data.statistics?.average_accuracy ?? 0}%` },
              ].map((item) => (
                <div key={item.label} className="glass-panel" style={{ padding: '16px' }}>
                  <h3 style={{ fontSize: '0.95rem', marginBottom: '6px' }}>{item.label}</h3>
                  <p style={{ fontSize: '1.3rem', fontWeight: 700, margin: 0 }}>{item.value}</p>
                </div>
              ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '20px' }}>
              <div className="glass-panel" style={{ padding: '16px' }}>
                <h3 style={{ marginBottom: '10px' }}>Weak Topics</h3>
                {data.weak_topics?.length ? data.weak_topics.map((topic) => (
                  <div key={topic.topic_id} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span>{topic.topic_name}</span>
                    <span>{topic.mastery_level}%</span>
                  </div>
                )) : <p>No weak topics yet.</p>}
              </div>
              <div className="glass-panel" style={{ padding: '16px' }}>
                <h3 style={{ marginBottom: '10px' }}>Recent Activity</h3>
                {data.recent_quizzes?.length ? data.recent_quizzes.map((quiz) => (
                  <div key={quiz.id} style={{ marginBottom: '8px' }}>
                    <div>{quiz.topic_name || 'General Study'} — {quiz.score}%</div>
                    <small style={{ color: 'hsl(var(--text-secondary))' }}>{quiz.attempted_at}</small>
                  </div>
                )) : <p>No recent quizzes yet.</p>}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Analytics;
