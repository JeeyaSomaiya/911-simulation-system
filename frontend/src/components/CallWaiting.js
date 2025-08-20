import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSession } from '../services/useSession';
import './styles/call-waiting.css';

const CallWaiting = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { terminateSession } = useSession();

  const handleTerminate = async () => {
    try {
      await terminateSession(sessionId);
    } catch (error) {
      console.error('Failed to terminate session:', error);
    }
    navigate('/');
  };

  const handlePickup = () => {
    navigate(`/call/${sessionId}`);
  };

  return (
    <div className="call-waiting">
      <div className="call-waiting-card">
        <div className="call-controls-top">
          <button className="terminate-btn" onClick={handleTerminate}>
            Terminate Session
          </button>
          <button className="retry-btn" disabled={true}>
            <img src="/images/retry.png" alt="retry" className="retry-icon"/>
            Retry Call
          </button>
        </div>

        <div className="call-icon-container">
          <button className="call-icon green active pickup-button" onClick={handlePickup}>
            <img src="/images/phone.png" alt="phone" className="pickup-icon"/>
          </button>
        </div>
      </div>
    </div>
  );
};

export default CallWaiting;
