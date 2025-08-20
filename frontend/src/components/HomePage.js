import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../services/authContext';
import './styles/homepage.css';

const HomePage = () => {
  const navigate = useNavigate();
  const { user, getUserSessions, getUserStats } = useAuth();
  const [recentSessions, setRecentSessions] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const loadScenarios = async () => {
      try {
        const response = await fetch('/scenarios.json');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        if (Array.isArray(data) && data.length > 0) setScenarios(data);
      } catch (error) {
        console.error('Homepage: Error loading scenarios:', error);
      }
    };

    loadScenarios();
  }, []);

  useEffect(() => {
    if (user) {
      const sessions = getUserSessions();
      const stats = getUserStats();
      const recent = sessions
        .sort((a, b) => new Date(b.startTime) - new Date(a.startTime))
        .slice(0, 5);
      
      setRecentSessions(recent);
      setStats(stats);
    }
  }, [user, getUserSessions, getUserStats]);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffHours === 1) return `${diffHours} hour ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays === 1) return `${diffDays} day ago`;
    return `${diffDays} days ago`;
  };

  const getScenarioDisplayName = (scenarioType, selectedSubtype) => {
    const scenario = scenarios.find(s => s.Code === scenarioType);
    if (!scenario) return scenarioType || 'Unknown';
    
    const subtype = selectedSubtype || 
      (scenario.EventSubtypes && scenario.EventSubtypes.length > 0 
        ? scenario.EventSubtypes[0] 
        : '');
    
    return subtype 
      ? `${scenario.Code} - ${scenario.EventType} - ${subtype}`
      : `${scenario.Code} - ${scenario.EventType}`;
  };

  return (
    <div className="homepage">
      <div className="main-card">
        <div className="stats-container">
          <div className="stats-card">
            <div className="stats-value">{stats?.totalSessions || 0}</div>
            <div className="stats-title">Total Calls</div>
          </div>
          <div className="stats-card">
            <div className="stats-value">0</div>
            <div className="stats-title">Complete Assignments</div>
          </div>
        </div>

        <button className="simulate-call-btn" onClick={() => navigate('/new-call')}>
          <img src="/images/phone.png" alt="phone" className="phone-icon"/>
          Simulate Call
        </button>
      </div>

      <div className="sections-container">
        <div className="assignments-section">
          <h3>Assignments</h3>
          <p className="empty-state">No assignments found</p>
        </div>
        
        <div className="history-section">
          <div className="history-header">
            <h3>Recent History</h3>
            {recentSessions.length > 0 && (
              <button className="view-all-btn" onClick={() => navigate('/history')}>
                View All
              </button>
            )}
          </div>
          
          {recentSessions.length === 0 ? (
            <p className="empty-state">No calls found</p>
          ) : (
            <div className="history-list">
              {recentSessions.map((session) => (
                <div key={session.id} className="history-item" onClick={() => navigate('/history')}>
                  <div className="history-item-content">
                    <div className="history-item-header">
                      <h4 className="scenario-name">
                        {getScenarioDisplayName(session.scenarioType, session.selectedSubtype)}
                      </h4>
                      <span className="session-time">{formatDate(session.startTime)}</span>
                    </div>
                    
                    <div className="history-item-details">
                      <div className="detail-item">
                        <span className="detail-label">Duration:</span>
                        <span className="detail-value">
                          {session.endTime && session.startTime ? 
                            Math.round((new Date(session.endTime) - new Date(session.startTime)) / (1000 * 60)) + ' min' :
                            'In progress'
                          }
                        </span>
                      </div>
                      
                      <div className="detail-item">
                        <span className="detail-label">Progress:</span>
                        <span className="detail-value">{session.scenarioProgress * 100 || 0}%</span>
                      </div>
                      
                      <div className="detail-item">
                        <span className="detail-label">Messages:</span>
                        <span className="detail-value">{session.conversation?.length || 0}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HomePage;
