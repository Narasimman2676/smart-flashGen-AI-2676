import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  UploadCloud, FileText, CheckCircle, 
  AlertTriangle, Trash2, ArrowRight, Layers, HelpCircle
} from 'lucide-react';
import API from '../services/api';
import '../styles/upload.css';

const Upload = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  
  const [file, setFile] = useState(null);
  const [numCards, setNumCards] = useState(10);
  const [topicId, setTopicId] = useState('');
  const [newTopicName, setNewTopicName] = useState('');
  
  const [topicsList, setTopicsList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [activeStep, setActiveStep] = useState(0); // 0: Idle, 1: Uploading, 2: Parsing, 3: Generating, 4: Done
  const [error, setError] = useState('');
  const [dragging, setDragging] = useState(false);

  useEffect(() => {
    const fetchTopics = async () => {
      try {
        const response = await API.get('/progress');
        // progress endpoint returns list of studied topics
        setTopicsList(response.data);
      } catch (err) {
        console.error('Failed to load topics:', err);
      }
    };
    fetchTopics();
  }, []);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    setError('');
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      validateAndSetFile(files[0]);
    }
  };

  const handleFileChange = (e) => {
    setError('');
    const files = e.target.files;
    if (files && files.length > 0) {
      validateAndSetFile(files[0]);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    const allowedExtensions = ['pdf', 'docx', 'txt'];
    const extension = selectedFile.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(extension)) {
      setError("Unsupported file format. Please upload PDF, DOCX or TXT files.");
      return;
    }
    
    // Limit to 16MB
    if (selectedFile.size > 16 * 1024 * 1024) {
      setError("File size exceeds the 16MB limit.");
      return;
    }
    
    setFile(selectedFile);
  };

  const triggerFileSelect = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const removeSelectedFile = (e) => {
    e.stopPropagation();
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file to upload.");
      return;
    }

    setUploading(true);
    setError('');
    
    // Step 1: Uploading File
    setActiveStep(1);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      // POST file upload
      const uploadResp = await API.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      const doc = uploadResp.data.document;
      
      // Step 2: Extracting Text (represented by backend parsing stage)
      setActiveStep(2);
      await new Promise(resolve => setTimeout(resolve, 1500)); // Slight pause for visual fluid transition
      
      // Step 3: Flashcard Generation Pipeline
      setActiveStep(3);
      
      await API.post('/generate', {
        document_id: doc.id,
        num_cards: parseInt(numCards),
        topic_id: topicId ? parseInt(topicId) : null,
        topic_name: newTopicName.trim() || null
      });

      // Step 4: Done
      setActiveStep(4);
      
      setTimeout(() => {
        // Redirect to Flashcards list to study cards
        navigate(`/flashcards?document_id=${doc.id}`);
      }, 2000);

    } catch (err) {
      const msg = err.response?.data?.error || "Pipeline failure. Please check file formatting.";
      setError(msg);
      setActiveStep(0);
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="upload-container">
      <div className="upload-card glass-panel">
        <h1 className="upload-title">Generate Flashcards</h1>
        <p className="upload-subtitle">Upload PDF, DOCX, or TXT documents to generate study decks</p>

        {error && (
          <div className="alert alert-error" style={{ marginBottom: '24px' }}>
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}

        {!uploading ? (
          <form onSubmit={handleSubmit}>
            {/* Dropzone container */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              style={{ display: 'none' }}
              accept=".pdf,.docx,.txt"
            />
            
            <div 
              className={`dropzone ${dragging ? 'dragging' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={triggerFileSelect}
            >
              <UploadCloud className="dropzone-icon" />
              <p className="dropzone-text">Drag & drop your document here, or <span className="auth-link">browse</span></p>
              <p className="dropzone-subtext">Supports PDF, DOCX, and TXT up to 16MB</p>
            </div>

            {/* Selected File Details */}
            {file && (
              <div className="selected-file-info">
                <FileText size={18} className="file-icon" />
                <div style={{ flexGrow: 1, overflow: 'hidden' }}>
                  <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {file.name}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'hsl(var(--text-muted))' }}>
                    {formatFileSize(file.size)}
                  </div>
                </div>
                <button type="button" onClick={removeSelectedFile} className="btn-logout" style={{ padding: '4px' }}>
                  <Trash2 size={16} style={{ color: 'hsl(var(--text-muted))' }} />
                </button>
              </div>
            )}

            {/* Form Inputs (Topic, Cards Count) */}
            <div className="config-group">
              <div className="form-group">
                <label className="form-label">Link to Topic</label>
                <select 
                  value={topicId} 
                  onChange={(e) => {
                    setTopicId(e.target.value);
                    if (e.target.value) setNewTopicName(''); // Reset custom topic if select is chosen
                  }}
                  disabled={newTopicName !== ''}
                >
                  <option value="">-- Select Existing Topic --</option>
                  {topicsList.map(t => (
                    <option key={t.topic_id} value={t.topic_id}>{t.topic_name}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Or Create New Topic</label>
                <input
                  type="text"
                  placeholder="e.g. Data Structures"
                  value={newTopicName}
                  onChange={(e) => {
                    setNewTopicName(e.target.value);
                    if (e.target.value) setTopicId(''); // Reset select if typing custom name
                  }}
                  disabled={topicId !== ''}
                />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: '32px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <label className="form-label">Number of Cards</label>
                <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'hsl(var(--primary))' }}>{numCards} Cards</span>
              </div>
              <input
                type="range"
                min="5"
                max="30"
                step="5"
                value={numCards}
                onChange={(e) => setNumCards(e.target.value)}
                style={{ cursor: 'pointer', height: '6px', padding: '0' }}
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={!file}>
              <span>Generate Flashcards</span>
              <ArrowRight size={18} />
            </button>
          </form>
        ) : (
          /* Multi-step progress pipeline tracker */
          <div className="pipeline-progress-container">
            <h3 style={{ fontSize: '1.05rem', marginBottom: '8px', textAlign: 'center' }}>
              {activeStep === 4 ? "Deck Generated!" : "Analyzing Document..."}
            </h3>
            
            <div className="pipeline-step-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className={`pipeline-step ${activeStep === 1 ? 'active' : ''} ${activeStep > 1 ? 'completed' : ''}`}>
                <div className="step-icon-status">
                  {activeStep === 1 ? <div className="spinner" style={{ width: '14px', height: '14px' }} /> : <div className="step-dot" />}
                </div>
                <span>Uploading document to storage...</span>
              </div>

              <div className={`pipeline-step ${activeStep === 2 ? 'active' : ''} ${activeStep > 2 ? 'completed' : ''}`}>
                <div className="step-icon-status">
                  {activeStep === 2 ? <div className="spinner" style={{ width: '14px', height: '14px' }} /> : <div className="step-dot" />}
                </div>
                <span>Extracting raw text layer...</span>
              </div>

              <div className={`pipeline-step ${activeStep === 3 ? 'active' : ''} ${activeStep > 3 ? 'completed' : ''}`}>
                <div className="step-icon-status">
                  {activeStep === 3 ? <div className="spinner" style={{ width: '14px', height: '14px' }} /> : <div className="step-dot" />}
                </div>
                <span>Running AI pipelines (generating questions)...</span>
              </div>

              <div className={`pipeline-step ${activeStep === 4 ? 'completed' : ''}`}>
                <div className="step-icon-status">
                  {activeStep === 4 ? <CheckCircle size={16} style={{ color: '#64e393' }} /> : <div className="step-dot" />}
                </div>
                <span>Success! Redirection in progress...</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Upload;
