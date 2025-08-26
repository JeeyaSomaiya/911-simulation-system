import React from 'react';
import './styles/session-transcript-modal.css';

const SessionTranscriptModal = ({ session, scenarios, onClose }) => {
  if (!session) return null;

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

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getDuration = () => {
    if (session.endTime && session.startTime) {
      const duration = Math.round((new Date(session.endTime) - new Date(session.startTime)) / (1000 * 60));
      return `${duration} minute${duration !== 1 ? 's' : ''}`;
    }
    return 'Unknown';
  };

  const getEmotionalStateColor = (state) => {
    const colors = {
      'calm': '#10B981',
      'neutral': '#6B7280',
      'anxious': '#F59E0B',
      'distressed': '#EF4444',
      'angry': '#DC2626',
      'panicked': '#B91C1C',
      'cooperative': '#059669',
      'uncooperative': '#D97706'
    };
    return colors[state?.toLowerCase()] || '#6B7280';
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-section">
            <h2>{getScenarioDisplayName(session.scenarioType, session.selectedSubtype)}</h2>
            <p className="session-date">
              {new Date(session.startTime).toLocaleDateString()} at{' '}
              {new Date(session.startTime).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </p>
          </div>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="session-summary">
          <div className="summary-stats">
            <div className="summary-stat">
              <span className="stat-label">Duration</span>
              <span className="stat-value">{getDuration()}</span>
            </div>
            <div className="summary-stat">
              <span className="stat-label">Messages</span>
              <span className="stat-value">{session.conversation?.length || 0}</span>
            </div>
            <div className="summary-stat">
              <span className="stat-label">Progress</span>
              <span className="stat-value">{Math.round(session.scenarioProgress * 100) || 0}%</span>
            </div>
            <div className="summary-stat">
              <span className="stat-label">Final State</span>
              <span 
                className="stat-value emotional-state"
                style={{ color: getEmotionalStateColor(session.emotionalState) }}
              >
                {session.emotionalState || 'Unknown'}
              </span>
            </div>
          </div>

          {session.keyDetailsRevealed && session.keyDetailsRevealed.length > 0 && (
            <div className="details-revealed">
              <h4>Key Details Revealed:</h4>
              <div className="details-list">
                {session.keyDetailsRevealed.map((detail, index) => (
                  <span key={index} className="detail-tag">
                    {detail}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="transcript-modal-section">
          <h3>Call Transcript</h3>
          <div className="transcript-modal-container">
            {(!session.conversation || session.conversation.length === 0) ? (
              <div className="no-transcript">
                <p>No conversation data available for this session.</p>
              </div>
            ) : (
              <div className="transcript-modal-messages">
                {session.conversation.map((message, index) => (
                  <div 
                    key={index} 
                    className={`modal-message ${message.role === 'call_taker' ? 'call-taker' : 'caller'}`}
                  >
                    <div className="message-header">
                      <span className="message-role">
                        {message.role === 'call_taker' ? 'Call Taker' : 'Caller'}
                      </span>
                      {message.timestamp && (
                        <span className="message-time">
                          {formatTimestamp(message.timestamp)}
                        </span>
                      )}
                      {message.emotional_state && (
                        <span 
                          className="message-emotion"
                          style={{ 
                            backgroundColor: getEmotionalStateColor(message.emotional_state) + '20',
                            color: getEmotionalStateColor(message.emotional_state)
                          }}
                        >
                          {message.emotional_state}
                        </span>
                      )}
                    </div>
                    <div className="message-content">
                      {message.content}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="close-modal-button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default SessionTranscriptModal;
