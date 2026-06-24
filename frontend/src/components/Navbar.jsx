import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, Layers, HelpCircle, BarChart3, LogOut, Zap } from 'lucide-react';
import API from '../services/api';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  if (!token) return null;

  const handleLogout = async () => {
    try {
      // Notify backend to blocklist token
      await API.post('/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear storage and route to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      navigate('/login');
    }
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="navbar glass-panel">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          <Zap className="logo-icon" />
          <span>FlashGen AI</span>
        </Link>
        
        <div className="nav-links">
          <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
            <LayoutDashboard className="nav-icon" />
            <span>Dashboard</span>
          </Link>
          <Link to="/upload" className={`nav-link ${isActive('/upload') ? 'active' : ''}`}>
            <UploadCloud className="nav-icon" />
            <span>Upload</span>
          </Link>
          <Link to="/flashcards" className={`nav-link ${isActive('/flashcards') ? 'active' : ''}`}>
            <Layers className="nav-icon" />
            <span>Flashcards</span>
          </Link>
          <Link to="/quiz" className={`nav-link ${isActive('/quiz') ? 'active' : ''}`}>
            <HelpCircle className="nav-icon" />
            <span>Quiz</span>
          </Link>
          <Link to="/analytics" className={`nav-link ${isActive('/analytics') ? 'active' : ''}`}>
            <BarChart3 className="nav-icon" />
            <span>Analytics</span>
          </Link>
        </div>
        
        <div className="nav-user-actions">
          <span className="user-email" title={user.email}>
            {user.email ? user.email.split('@')[0] : 'User'}
          </span>
          <button onClick={handleLogout} className="btn-logout" title="Logout">
            <LogOut className="logout-icon" />
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
