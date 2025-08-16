import React, { useState, useEffect, useRef, useLayoutEffect } from 'react';
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
  
  const transcriptRef = useRef(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [inputMessage, setInputMessage] = useState('');

  // Use useLayoutEffect to ensure scroll happens after DOM update
  useLayoutEffect(() => {
    if (shouldAutoScroll && transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [conversation, shouldAutoScroll]);

  const handleScroll = () => {
    if (transcriptRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = transcriptRef.current;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
      setShouldAutoScroll(isAtBottom);
    }
  };

  useEffect(() => {
    if (transcript) {
      setConversation(prev => [...prev, transcript]);
    }
  }, [transcript]);

  const handleSendMessage = () => {
    if (inputMessage.trim()) {
      const newMessage = {
        role: 'call_taker',
        content: inputMessage.trim()
      };
      
      setShouldAutoScroll(true);
      setConversation(prev => [...prev, newMessage]);

      sendMessage(inputMessage.trim());
      
      setInputMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

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
        <button className="terminate-btn" onClick={handleTerminate}>
          Terminate Session
        </button>
        <button className="retry-btn" onClick={handleRetry}>
        <img src="/images/retry.png" alt="retry" className="retry-icon"/>
          Retry Call
        </button>
      </div>

      <div className="transcript-container">
        <div className="transcript-display">
          <div className="transcript-header">
            <h3>Live Transcript</h3>
          </div>
          
          <div 
            className="transcript-content"
            ref={transcriptRef}
            onScroll={handleScroll}
          >
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
        
        <div className="message-input-container">
          <input
            type="text"
            className="message-input"
            placeholder="Type your response..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button 
            className="send-button"
            onClick={handleSendMessage}
            disabled={!inputMessage.trim()}
          >
            Send
          </button>
        </div>
      </div>

      <div className="call-controls-bottom">
        <button className="hang-up-button" onClick={handleTerminate}>
          <div className="call-icon red">
          <img src="/images/phone.png" alt="phone" className="hangup-icon"/>
          </div>
        </button>
      </div>
    </div>
  );
};

export default CallInterface;
