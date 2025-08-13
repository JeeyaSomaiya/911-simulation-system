import React from 'react';
import { useNavigate } from 'react-router-dom';
import './styles/homepage.css';

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <div className="homepage">
      <div className="stats-container">
        <div className="stats-card">
          <div className="stats-value">0</div>
          <div className="stats-title">Calls</div>
        </div>
        <div className="stats-card">
          <div className="stats-value">0</div>
          <div className="stats-title">Complete Assignments</div>
        </div>
      </div>

      <div className="cta-section">
        <button 
          className="simulate-call-btn"
          onClick={() => navigate('/new-call')}
        >
          <span className="phone-icon">📞</span>
          Simulate Call
        </button>
      </div>

      <div className="sections-container">
        <div className="assignments-section card">
          <h3>Assignments</h3>
          <p className="empty-state">No assignments found</p>
        </div>
        
        <div className="history-section card">
          <h3>History</h3>
          <p className="empty-state">No calls found</p>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
