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
      <div className="call-controls-top">
        <button className="btn-secondary" onClick={handleTerminate}>
          Terminate Session
        </button>
        <button className="btn-secondary" onClick={handleRetry}>
          🔄 Retry Call
        </button>
      </div>

      <div className="call-icon-container">
        <div className="call-icon green active">
          <span className="phone-symbol">📞</span>
        </div>
      </div>
    </div>
  );
};

export default CallWaiting;
