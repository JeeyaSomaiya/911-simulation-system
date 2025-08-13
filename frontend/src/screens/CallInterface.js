import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import TranscriptDisplay from '../components/features/call/TranscriptDisplay';
import CallControls from '../components/features/call/CallControls';
import { useSession } from '../hooks/useSession';
import { useWebSocket } from '../hooks/useWebSocket';

const CallInterface = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { session, sendMessage, terminateSession } = useSession();
  const { transcript, isConnected } = useWebSocket(sessionId);
  const [conversation, setConversation] = useState([]);

  useEffect(() => {
    if (transcript) {
      setConversation(prev => [...prev, transcript]);
    }
  }, [transcript]);

  const handleTerminate = async () => {
    await terminateSession(sessionId);
    navigate('/');
  };

  const handleRetry = () => {
    navigate('/new-call');
  };

  const handleSendMessage = async (message) => {
    const response = await sendMessage(sessionId, message);
    if (response) {
      setConversation(prev => [
        ...prev,
        { role: 'call_taker', content: message },
        { role: 'caller', content: response.caller_response }
      ]);
    }
  };

  return (
    <div className="call-interface">
      <div className="call-controls-top">
        <button className="btn-secondary" onClick={handleTerminate}>
          Terminate Session
        </button>
        <button className="btn-secondary" onClick={handleRetry}>
          🔄 Retry Call
        </button>
      </div>

      <div className="transcript-container">
        <TranscriptDisplay
          conversation={conversation}
          isLive={isConnected}
        />
      </div>

      <div className="call-controls-bottom">
        <CallControls
          onTerminate={handleTerminate}
          onSendMessage={handleSendMessage}
        />
      </div>
    </div>
  );
};

export default CallInterface;
