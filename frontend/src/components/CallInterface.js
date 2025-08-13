import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSession } from '../services/useSession';
import { useWebSocket } from '../services/useWebSocket';
import './styles/call-interface.css';

const CallInterface = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { sendMessage, terminateSession } = useSession();
  const { transcript, isConnected } = useWebSocket(sessionId);
  const [conversation, setConversation] = useState([
    { role: 'call_taker', content: "What's the address of the emergency?" },
    { role: 'caller', content: "My address is 65 Eldorado CL NE" },
    { role: 'call_taker', content: "What's the phone number you're calling from?" },
    { role: 'caller', content: "403-441-7845" },
    { role: 'call_taker', content: "What's your name?" },
    { role: 'caller', content: "Harry Winston" },
    { role: 'call_taker', content: "Ok, tell me exactly what happened." },
    { role: 'caller', content: "I heard 2 gunshots across the street about 60 seconds ago. I saw the guy who lives at 68 Eldorado CL NE go into the house. He had a hand gun in his right hand. I heard yelling and screaming coming from that house earlier today" }
  ]);

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
        <div className="transcript-display">
          <div className="transcript-header">
            <h3>Live Transcript</h3>
            {isConnected && <span className="live-indicator">🔴 LIVE</span>}
          </div>
          
          <div className="transcript-content">
            {conversation.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <span className="role">
                  {message.role === 'call_taker' ? 'Call Taker:' : 'Caller:'}
                </span>
                <span className="content">{message.content}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="call-controls-bottom">
        <button className="hang-up-button" onClick={handleTerminate}>
          <div className="call-icon red">
            <span className="phone-symbol">📞</span>
          </div>
        </button>
      </div>
    </div>
  );
};

export default CallInterface;
