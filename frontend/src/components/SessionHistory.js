// SessionHistory.js - Updated to use scenarios.json
import React, { useState, useEffect } from 'react';
import { useAuth } from '../services/authContext'; 
import './styles/session-history.css';

const SessionHistory = () => { 
  const { user, getUserSessions, deleteSession, getUserStats } = useAuth(); 
  const [sessions, setSessions] = useState([]);
  const [scenarios, setScenarios] = useState([]); // Add scenarios state
  const [filterBy, setFilterBy] = useState('all');
  const [sortBy, setSortBy] = useState('newest');
  const [stats, setStats] = useState(null);

  // Load scenarios from JSON file
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
        }
      } catch (error) {
        console.error('Error loading scenarios:', error);
        // Fallback to hardcoded scenarios if JSON fails
        setScenarios([]);
      }
    };

    loadScenarios();
  }, []);

  useEffect(() => {
    if (user) {
      const userSessions = getUserSessions();
      setSessions(userSessions);
      setStats(getUserStats());
      console.log('User found:', user); 
      console.log('Sessions loaded:', userSessions); 
    }
  }, [user, getUserSessions, getUserStats]);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffTime / (1000 * 60));

    if (diffMinutes === 1) {
      return `${diffMinutes} minute ago`;
    } else if (diffMinutes < 60) {
      return `${diffMinutes} minutes ago`;
    } else if (diffHours === 1) {
      return `${diffHours} hour ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hours ago`;
    } else if (diffDays === 1) {
      return `${diffDays} day ago`;
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getScenarioDisplayName = (scenarioType, selectedSubtype) => {
    const scenario = scenarios.find(s => s.Code === scenarioType);
    if (scenario) {
      const subtype = selectedSubtype || 
        (scenario.EventSubtypes && scenario.EventSubtypes.length > 0 
          ? scenario.EventSubtypes[0] 
          : '');
      
      return subtype 
        ? `${scenario.Code} - ${scenario.EventType} - ${subtype}`
        : `${scenario.Code} - ${scenario.EventType}`;
    }

    return scenarioType || 'Unknown';
  };

  const filteredAndSortedSessions = sessions
    .filter(session => {
      if (filterBy === 'all') return true;
      if (filterBy === 'completed') return session.status === 'completed';
      if (filterBy === 'recent') {
        const sessionDate = new Date(session.startTime);
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        return sessionDate >= weekAgo;
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'newest') {
        return new Date(b.startTime) - new Date(a.startTime);
      } else if (sortBy === 'oldest') {
        return new Date(a.startTime) - new Date(b.startTime);
      } else if (sortBy === 'scenario') {
        return (a.scenarioType || '').localeCompare(b.scenarioType || '');
      }
      return 0;
    });

  const handleDeleteSession = (sessionId, e) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
      deleteSession(sessionId);
      const updatedSessions = getUserSessions();
      setSessions(updatedSessions);
      setStats(getUserStats());
    }
  };

  const handleViewSession = (session) => {
    const scenario = scenarios.find(s => s.Code === session.scenarioType);
    const scenarioDetails = scenario ? 
      `${scenario.Code} - ${scenario.EventType}` : 
      getScenarioDisplayName(session.scenarioType);
    
    alert(`Session Details:\n\nScenario: ${scenarioDetails}\nProgress: ${session.scenarioProgress}%\nDuration: ${session.endTime && session.startTime ? Math.round((new Date(session.endTime) - new Date(session.startTime)) / (1000 * 60)) : 'Unknown'} minutes\nMessages: ${session.conversation?.length || 0} exchanges`);
  };

  console.log('Current user:', user);
  console.log('Is user logged in:', !!user);
  console.log('Loaded scenarios:', scenarios.length);

  if (!user) {
    return (
      <div className="session-history-container">
        <div className="login-prompt">
          <h3>Please log in to view your session history</h3>
          <p>You need to be logged in to access your session data.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="session-history-container">
      <div className="session-history-header">
        <h2>Session History</h2>
        
        <div className="filter-controls">
          <select
            value={filterBy}
            onChange={(e) => setFilterBy(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Sessions</option>
            <option value="recent">Last 7 Days</option>
          </select>
          
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="sort-select"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="scenario">By Scenario</option>
          </select>
        </div>
      </div>

      {stats && (
        <div className="session-statistics">
          <h4>Session Statistics</h4>
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-value">{stats.totalSessions}</div>
              <div className="stat-label">Total Sessions</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{stats.totalConversations}</div>
              <div className="stat-label">Total Exchanges</div>
            </div>
          </div>
        </div>
      )}

      {filteredAndSortedSessions.length === 0 ? (
        <div className="empty-state">
          <h3>No sessions found</h3>
          <p>
            {filterBy === 'all' 
              ? 'Start your first call simulation to see your session history here.'
              : 'No sessions match your current filter. Try adjusting your filters above.'
            }
          </p>
        </div>
      ) : (
        <div className="sessions-grid">
          {filteredAndSortedSessions.map((session) => (
            <div
              key={session.id}
              onClick={() => handleViewSession(session)}
              className="session-card clickable"
            >
              <div className="session-card-header">
                <div className="session-info">
                  <h3 className="session-title">
                    {getScenarioDisplayName(session.scenarioType)}
                  </h3>
                  <p className="session-date">
                    {formatDate(session.startTime)}
                  </p>
                </div>
                
                <div className="session-actions">
                  <button
                    onClick={(e) => handleDeleteSession(session.sessionId, e)}
                    className="delete-button"
                    title="Delete session"
                  >
                    Delete
                  </button>
                </div>
              </div>
              
              <div className="session-metrics">
                <div className="metric">
                  <span className="metric-label">Duration</span>
                  <p className="metric-value">
                    {session.endTime && session.startTime ? 
                      Math.round((new Date(session.endTime) - new Date(session.startTime)) / (1000 * 60)) + ' min' :
                      'In progress'
                    }
                  </p>
                </div>
                
                <div className="metric">
                  <span className="metric-label">Messages</span>
                  <p className="metric-value">
                    {session.conversation?.length || 0} exchanges
                  </p>
                </div>
                
                <div className="metric">
                  <span className="metric-label">Progress</span>
                  <p className="metric-value">
                    {session.scenarioProgress || 0}%
                  </p>
                </div>
                
                <div className="metric">
                  <span className="metric-label">Details Revealed</span>
                  <p className="metric-value">
                    {session.keyDetailsRevealed?.length || 0}
                  </p>
                </div>
              </div>
              
              {session.conversation && session.conversation.length > 0 && (
                <div className="last-exchange">
                  <span className="last-exchange-label">Last Exchange</span>
                  <p className="last-exchange-content">
                    {session.conversation[session.conversation.length - 1]?.content || 'No messages'}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
    </div>
  );
};

export default SessionHistory;
