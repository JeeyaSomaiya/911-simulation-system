import React, { useState, useEffect, useRef, useLayoutEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSession } from '../services/useSession';
import { useWebSocket } from '../services/useWebSocket';
import './styles/call-interface.css';

const CallInterface = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { terminateSession, getSession } = useSession();
  const { transcript, isConnected, sendCallTakerMessage, error: wsError } = useWebSocket(sessionId);
  
  const [conversation, setConversation] = useState([]);
  const [sessionInfo, setSessionInfo] = useState(null);
  const [inputMessage, setInputMessage] = useState('');
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  
  const transcriptRef = useRef(null);

  useEffect(() => {
    const loadSession = async () => {
      try {
        const sessionData = await getSession(sessionId);
        setSessionInfo(sessionData);
        
        const initialMessage = {
          role: 'caller',
          content: getInitialCallerMessage(sessionData.scenario_type),
          timestamp: new Date().toISOString()
        };
        setConversation([initialMessage]);
      } catch (error) {
        console.error('Failed to load session:', error);
        alert('Failed to load session. Returning to main menu.');
        navigate('/');
      } finally {
        setIsLoading(false);
      }
    };

    if (sessionId) {
      loadSession();
    }
  }, [sessionId, getSession, navigate]);

  useEffect(() => {
    if (transcript) {
      setConversation(prev => [...prev, transcript]);
      setShouldAutoScroll(true);
    }
  }, [transcript]);

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

  const handleSendMessage = () => {
    if (inputMessage.trim() && isConnected) {
      const newMessage = {
        role: 'call_taker',
        content: inputMessage.trim(),
        timestamp: new Date().toISOString()
      };
      
      setConversation(prev => [...prev, newMessage]);
      setShouldAutoScroll(true);

      sendCallTakerMessage(inputMessage.trim());
      
      setInputMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  const handleTerminate = async () => {
    try {
      await terminateSession(sessionId);
      navigate('/');
    } catch (error) {
      console.error('Failed to terminate session:', error);
      navigate('/');
    }
  };

  const handleRetry = () => {
    navigate('/');
  };

  const getInitialCallerMessage = (scenarioType) => {
    const initialMessages = {
      '10-01': "There's been a bad accident!",
      '10-02': "I just saw a car accident!",
      '10-30': "I found someone bleeding!",
      '10-08H': "Intruders broke into my home!",
      '10-83': "I'm seeing a dangerous driver!",
      '10-34': "Someone stole gas!",
      '10-21': "People are acting suspiciously!",
      '10-07': "A man threatened to kill himself!",
      '10-88': "I saw a car stopped on the road!"
    };
    return initialMessages[scenarioType] || "I need help!";
  };

  if (isLoading) {
    return (
      <div className="call-interface">
        <div className="loading-container">
          <h3>Loading call session...</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="call-interface">
      <div className="call-controls-top">
        <button className="terminate-btn" onClick={handleTerminate}>
          Terminate Session
        </button>
        <button className="retry-btn" onClick={handleRetry}>
          <img src="/images/retry.png" alt="retry" className="retry-icon"/>
          New Call
        </button>
      </div>

      {/* Connection Status */}
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        {wsError && <span className="error-text"> - {wsError}</span>}
      </div>

      {/* Session Info */}
      {sessionInfo && (
        <div className="session-info">
          <span>Scenario: {sessionInfo.scenario_type}</span>
          <span>Emotional State: {sessionInfo.emotional_state}</span>
          <span>Progress: {Math.round(sessionInfo.scenario_progress * 100)}%</span>
        </div>
      )}

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
                {message.emotional_state && (
                  <span className="emotional-state">({message.emotional_state})</span>
                )}
              </div>
            ))}
          </div>
        </div>
        
        <div className="message-input-container">
          <input
            type="text"
            className="message-input"
            placeholder={isConnected ? "Type your response..." : "Connecting..."}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={!isConnected}
          />
          <button 
            className="send-button"
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || !isConnected}
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
