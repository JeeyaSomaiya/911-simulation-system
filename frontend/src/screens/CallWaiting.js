import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import CallIcon from '../components/features/ui/CallIcon';
import { useSession } from '../hooks/useSession';

const CallWaiting = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { session, terminateSession } = useSession();

  useEffect(() => {
    // Simulate call pickup after 3 seconds
    const timer = setTimeout(() => {
      navigate(`/call/${sessionId}`);
    }, 3000);

    return () => clearTimeout(timer);
  }, [sessionId, navigate]);

  const handleTerminate = async () => {
    await terminateSession(sessionId);
    navigate('/');
  };

  const handleRetry = () => {
    navigate('/new-call');
  };

  return (
    <div className="call-waiting">
      <div className="call-controls-top">
        <button className="btn-secondary" onClick={handleTerminate}>
          Terminate Session
        </button>
        <button className="btn-secondary" onClick={handleRetry}>
          🔄 Retry Call
        </button>
      </div>

      <div className="call-icon-container">
        <CallIcon isActive={true} />
      </div>
    </div>
  );
};

export default CallWaiting;
