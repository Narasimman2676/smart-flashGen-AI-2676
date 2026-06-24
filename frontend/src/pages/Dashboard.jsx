import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  FileText, Layers, HelpCircle, Award, 
  AlertTriangle, BookOpen, Clock, 
  ArrowRight, ShieldCheck, ChevronRight
} from 'lucide-react';
import API from '../services/api';
import '../styles/dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await API.get('/analytics');
        setStats(response.data);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load dashboard metrics.');
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  const formatDate = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getScoreColorClass = (score) => {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-med';
    return 'score-low';
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <div className="spinner" style={{ width: '40px', height: '40px', color: 'hsl(var(--primary))' }} />
      </div>
    );
  }

  const { statistics, weak_topics, recent_uploads, recent_quizzes } = stats || {
    statistics: { total_documents: 0, total_flashcards: 0, total_quizzes: 0, average_accuracy: 0.0 },
    weak_topics: [],
    recent_uploads: [],
    recent_quizzes: []
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Welcome, {user.email ? user.email.split('@')[0] : 'Student'}</h1>
        <p>Track your learning metrics, manage files, and test your retention levels.</p>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '24px' }}>
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Statistics Cards Grid */}
      <div className="stats-grid">
        <div className="stats-card glass-panel">
          <div className="stats-icon-wrapper">
            <FileText size={24} />
          </div>
          <div className="stats-info">
            <span className="stats-label">Documents</span>
            <span className="stats-value">{statistics.total_documents}</span>
          </div>
        </div>
        <div className="stats-card glass-panel">
          <div className="stats-icon-wrapper">
            <Layers size={24} />
          </div>
          <div className="stats-info">
            <span className="stats-label">Flashcards</span>
            <span className="stats-value">{statistics.total_flashcards}</span>
          </div>
        </div>
        <div className="stats-card glass-panel">
          <div className="stats-icon-wrapper">
            <HelpCircle size={24} />
          </div>
          <div className="stats-info">
            <span className="stats-label">Quizzes Taken</span>
            <span className="stats-value">{statistics.total_quizzes}</span>
          </div>
        </div>
        <div className="stats-card glass-panel">
          <div className="stats-icon-wrapper">
            <Award size={24} />
          </div>
          <div className="stats-info">
            <span className="stats-label">Avg. Accuracy</span>
            <span className="stats-value">{statistics.average_accuracy}%</span>
          </div>
        </div>
      </div>

      {/* Split Panels Section */}
      <div className="dashboard-split">
        
        {/* Left Side: Weak Topics and Recent Quizzes */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          
          {/* Weak Topics Widget */}
          <div className="panel-card glass-panel" style={{ minHeight: 'auto' }}>
            <h2 className="panel-title">
              <AlertTriangle size={20} style={{ color: 'hsl(var(--warning))' }} />
              <span>Recommended Study (Weak Topics)</span>
            </h2>
            {weak_topics.length > 0 ? (
              <div className="weak-topics-list">
                {weak_topics.map((t) => (
                  <div key={t.topic_id} className="weak-topic-item">
                    <div className="weak-topic-header">
                      <span>{t.topic_name}</span>
                      <span style={{ color: 'hsl(var(--error))' }}>{t.mastery_level}% Mastery</span>
                    </div>
                    <div className="progress-track">
                      <div 
                        className="progress-bar" 
                        style={{ width: `${t.mastery_level}%` }}
                      />
                    </div>
                    <span style={{ fontSize: '0.78rem', color: 'hsl(var(--text-muted))' }}>
                      Studied {t.flashcards_viewed} flashcard instances
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <ShieldCheck size={40} style={{ color: '#64e393', marginBottom: '8px' }} />
                <p>No weak topics detected!</p>
                <span style={{ fontSize: '0.85rem' }}>Your mastery levels are above 60%. Excellent work.</span>
              </div>
            )}
          </div>

          {/* Recent Quizzes Widget */}
          <div className="panel-card glass-panel">
            <h2 className="panel-title">
              <Clock size={20} style={{ color: 'hsl(var(--primary))' }} />
              <span>Recent Quizzes</span>
            </h2>
            {recent_quizzes.length > 0 ? (
              <div className="recent-list">
                {recent_quizzes.map((quiz) => (
                  <div key={quiz.id} className="recent-item">
                    <div className="recent-item-info">
                      <HelpCircle size={18} style={{ color: 'hsl(var(--text-muted))' }} />
                      <div>
                        <div className="recent-item-title">{quiz.topic_name}</div>
                        <div className="recent-item-meta">
                          {quiz.correct_answers} of {quiz.total_questions} correct • {formatDate(quiz.attempted_at)}
                        </div>
                      </div>
                    </div>
                    <div className={`score-text ${getScoreColorClass(quiz.score)}`}>
                      {quiz.score}%
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <BookOpen size={40} style={{ color: 'hsl(var(--text-muted))', marginBottom: '8px' }} />
                <p>No quiz attempts yet.</p>
                <Link to="/quiz" className="btn btn-secondary btn-sm" style={{ marginTop: '12px', padding: '8px 16px', fontSize: '0.85rem' }}>
                  Generate Quiz
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Recent Uploads */}
        <div className="panel-card glass-panel">
          <h2 className="panel-title">
            <FileText size={20} style={{ color: 'hsl(var(--secondary))' }} />
            <span>Recent Documents</span>
          </h2>
          {recent_uploads.length > 0 ? (
            <div className="recent-list">
              {recent_uploads.map((doc) => (
                <div key={doc.id} className="recent-item" style={{ flexDirection: 'column', alignItems: 'stretch', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div className="recent-item-info">
                      <FileText size={18} style={{ color: 'hsl(var(--text-secondary))' }} />
                      <div>
                        <div className="recent-item-title" title={doc.filename}>{doc.filename}</div>
                        <div className="recent-item-meta">{formatDate(doc.created_at)}</div>
                      </div>
                    </div>
                    <span className={`badge badge-${doc.status.toLowerCase()}`}>
                      {doc.status}
                    </span>
                  </div>
                  {doc.status === 'completed' && (
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
                      <Link 
                        to={`/flashcards?document_id=${doc.id}`}
                        className="auth-link" 
                        style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                      >
                        <span>Study Cards</span>
                        <ChevronRight size={14} />
                      </Link>
                    </div>
                  )}
                </div>
              ))}
              <Link 
                to="/upload" 
                className="btn btn-secondary" 
                style={{ marginTop: '16px', width: '100%', display: 'flex', gap: '8px', fontSize: '0.9rem' }}
              >
                <span>Upload New Document</span>
                <ArrowRight size={16} />
              </Link>
            </div>
          ) : (
            <div className="empty-state" style={{ height: '80%' }}>
              <UploadCloudMock size={40} />
              <p>No documents uploaded.</p>
              <Link to="/upload" className="btn btn-primary" style={{ marginTop: '16px', padding: '10px 20px', fontSize: '0.9rem' }}>
                Upload File
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper mock icon for clean file upload display
const UploadCloudMock = ({ size }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    style={{ color: 'hsl(var(--text-muted))' }}
  >
    <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242" />
    <path d="M12 12v9" />
    <path d="m16 16-4-4-4 4" />
  </svg>
);

export default Dashboard;
