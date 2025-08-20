import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import './styles/sidebar.css';

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, getUserSessions } = useAuth();
  const [recentSessions, setRecentSessions] = useState([]);
  const [scenarios, setScenarios] = useState([]); 
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    const loadScenarios = async () => {
      try {
        const response = await fetch('/scenarios.json');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        if (Array.isArray(data) && data.length > 0) {
          setScenarios(data);
          console.log('Sidebar: Scenarios loaded:', data.length);
        }
      } catch (error) {
        console.error('Sidebar: Error loading scenarios:', error);
      }
    };

    loadScenarios();
  }, []);

  useEffect(() => {
    if (user) {
      const sessions = getUserSessions();
      const recent = sessions
        .sort((a, b) => new Date(b.startTime) - new Date(a.startTime))
        .slice(0, 5);
      setRecentSessions(recent);
    }
  }, [user, getUserSessions]);

  const formatSessionTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffTime / (1000 * 60 * 60));

    if (diffHours === 1) {
      return `${diffHours} hour ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hours ago`;
    } else if (diffDays === 1) {
      return `${diffDays} day ago`;
    } else {
      return `${diffDays} days ago`;
    }
  };

  const getScenarioDisplayName = (scenarioType, selectedSubtype) => {
    const scenario = scenarios.find(s => s.Code === scenarioType);
    if (scenario) {
      const subtype = selectedSubtype || 
        (scenario.EventSubtypes && scenario.EventSubtypes.length > 0 
          ? scenario.EventSubtypes[0] 
          : '');

      const fullName = subtype 
        ? `${scenario.Code} - ${scenario.EventType} - ${subtype}`
        : `${scenario.Code} - ${scenario.EventType}`;
      
      return fullName.length > 35 ? fullName.substring(0, 32) + '...' : fullName;
    }
    
    return scenarioType || 'Unknown';
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleSessionClick = (session) => {
    navigate('/history');
  };

  if (!user) {
    return null;
  }

  return (
    <div className="sidebar">
      {/* User Profile Section */}
      <div className="user-profile">
        <div className="user-avatar">
          {user.name ? user.name.charAt(0).toUpperCase() : '?'}
        </div>
        <div className="user-info">
          <div className="user-name">{user.name || 'User'}</div>
          <div className="user-email">{user.email}</div>
        </div>
        <div className="user-menu-container">
          <button 
            className="user-menu-button"
            onClick={() => setShowUserMenu(!showUserMenu)}
          >
            ⋮
          </button>
          {showUserMenu && (
            <div className="user-menu-dropdown">
              <button 
                onClick={handleLogout}
                className="menu-item logout"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div 
          className={`nav-item ${location.pathname === '/' ? 'active' : ''}`}
          onClick={() => navigate('/')}
        >
          <img src="/images/home.png" alt="home" className="nav-icon"/> 
          <span className="nav-label">Home</span>
        </div>
        
        <div 
          className={`nav-item ${location.pathname === '/new-call' ? 'active' : ''}`}
          onClick={() => navigate('/new-call')}
        >
          <img src="/images/plus.png" alt="plus" className="nav-icon"/> 
          <span className="nav-label">New Call</span>
        </div>
        
        <div 
          className={`nav-item ${location.pathname === '/history' ? 'active' : ''}`}
          onClick={() => navigate('/history')}
        >
          <img src="/images/clock.png" alt="history" className="nav-icon"/> 
          <span className="nav-label">History</span>
        </div>
      </nav>
      
      {/* Recent Sessions */}
      <div className="recent-sessions">
        <div className="section-header">
          <h3>Recent Sessions</h3>
          {recentSessions.length > 0 && (
            <button 
              className="view-all-button"
              onClick={() => navigate('/history')}
            >
              View All
            </button>
          )}
        </div>
        
        <div className="sessions-list">
          {recentSessions.length === 0 ? (
            <div className="no-sessions">
              <p>No recent sessions</p>
              <button 
                className="start-session-button"
                onClick={() => navigate('/new-call')}
              >
                <img src="/images/phone.png" alt="phone" className="phone-icon"/> 
                Start Your First Call
              </button>
            </div>
          ) : (
            recentSessions.map((session) => (
              <div 
                key={session.id} 
                className="session-item"
                onClick={() => handleSessionClick(session)}
              >
                <div className="session-content">
                  <div className="session-type">
                    {getScenarioDisplayName(session.scenarioType)}
                  </div>
                  <div className="session-meta">
                    <span className="session-time">
                      {formatSessionTime(session.startTime)}
                    </span>
                    <span className="session-duration">
                      {session.endTime && session.startTime ? Math.round((new Date(session.endTime) - new Date(session.startTime)) / (1000 * 60)) : 'Unknown'} mins
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Session Statistics */}
      {recentSessions.length > 0 && (
        <div className="session-stats">
          <h4>Your Progress</h4>
          <div className="stats-summary">
            <div className="stat">
              <span className="stat-number">{getUserSessions().length}</span>
              <span className="stat-label">Total Sessions</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;
