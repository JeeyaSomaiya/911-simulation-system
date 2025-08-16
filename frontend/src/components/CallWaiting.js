import { useParams, useNavigate } from 'react-router-dom';
import { useSession } from '../services/useSession';
import './styles/call-waiting.css';

const CallWaiting = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { terminateSession } = useSession();

  const handleTerminate = async () => {
    await terminateSession(sessionId);
    navigate('/');
  };

  const handleRetry = () => {
    navigate('/new-call');
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
          <div className="call-icon green active">
          <img src="/images/phone.png" alt="phone" className="pickup-icon"/>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CallWaiting;
