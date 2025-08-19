import React, { useState, useEffect, useRef, useLayoutEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSession } from '../services/useSession';
import './styles/call-interface.css';

const CallInterface = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { terminateSession, getSession, sendMessage } = useSession();
  
  const [conversation, setConversation] = useState([]);
  const [sessionInfo, setSessionInfo] = useState(null);
  const [inputMessage, setInputMessage] = useState('');
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  
  const transcriptRef = useRef(null);
  const isSendingRef = useRef(false);
  const inputRef = useRef(null);
  const hasLoadedSession = useRef(false);

  // Load session info and initial message on mount - ONLY ONCE
  useEffect(() => {
    if (sessionId && !hasLoadedSession.current) {
      hasLoadedSession.current = true;
      
      const loadSession = async () => {
        try {
          const sessionData = await getSession(sessionId);
          setSessionInfo(sessionData);
          
          // Add initial caller message based on scenario
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

      loadSession();
    }
  }, [sessionId, getSession, navigate]);

  // Auto-scroll to bottom
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

  // Use useEffect to set up event listeners only once
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'Enter' && !isSendingRef.current && inputRef.current === document.activeElement) {
        e.preventDefault();
        handleSendMessage();
      }
    };

    document.addEventListener('keydown', handleKeyPress);

    return () => {
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, []);

  const handleSendMessage = async () => {
    if (inputMessage.trim() && !isSendingRef.current) {
      isSendingRef.current = true;
      setIsSending(true);
      
      const callTakerMessage = {
        role: 'call_taker',
        content: inputMessage.trim(),
        timestamp: new Date().toISOString()
      };
      
      setConversation(prev => [...prev, callTakerMessage]);
      const messageToSend = inputMessage.trim();
      setInputMessage('');

      try {
        const response = await sendMessage(sessionId, messageToSend);
        
        const callerMessage = {
          role: 'caller',
          content: response.caller_response,
          emotional_state: response.emotional_state,
          intensity: response.intensity,
          scenario_progress: response.scenario_progress,
          timestamp: new Date().toISOString()
        };
        
        setConversation(prev => [...prev, callerMessage]);
        
        setSessionInfo(prev => ({
          ...prev,
          emotional_state: response.emotional_state,
          intensity: response.intensity,
          scenario_progress: response.scenario_progress,
          key_details_revealed: response.key_details_revealed
        }));
        
      } catch (error) {
        console.error('Failed to send message:', error);
        
        const errorMessage = {
          role: 'system',
          content: 'Failed to get response from caller. Please try again.',
          timestamp: new Date().toISOString()
        };
        setConversation(prev => [...prev, errorMessage]);
      } finally {
        setIsSending(false);
        isSendingRef.current = false;
      }
    }
  };

  const handleTerminate = async () => {
    try {
      await terminateSession(sessionId);
    } catch (error) {
      console.error('Failed to terminate session:', error);
    }
    navigate('/');
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

      {/* Session Info - Show emotional state here instead of in transcript */}
      {sessionInfo && (
        <div className="session-info">
          <span>Scenario: {sessionInfo.scenario_type}</span>
          <span>Emotional State: {sessionInfo.emotional_state}</span>
          <span>Progress: {Math.round((sessionInfo.scenario_progress || 0) * 100)}%</span>
        </div>
      )}

      <div className="transcript-container">
        <div className="transcript-display">
          <div className="transcript-header">
            <h3>Call Transcript</h3>
          </div>
          
          <div 
            className="transcript-content"
            ref={transcriptRef}
            onScroll={handleScroll}
          >
            {conversation.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <span className="role">
                  {message.role === 'call_taker' ? 'Call Taker:' : 
                   message.role === 'system' ? 'System:' : 'Caller:'}
                </span>
                {/* Only show the message content, not the emotional state */}
                <span className="content">{message.content}</span>
              </div>
            ))}
            
            {isSending && (
              <div className="message caller typing">
                <span className="role">Caller:</span>
                <span className="content typing-indicator">...</span>
              </div>
            )}
          </div>
        </div>
        
        <div className="message-input-container">
          <input
            ref={inputRef}
            type="text"
            className="message-input"
            placeholder={isSending ? "Waiting for response..." : "Type your response..."}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={isSending}
          />
          <button 
            className="send-button"
            onClick={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            disabled={!inputMessage.trim() || isSending}
          >
            {isSending ? 'Sending...' : 'Send'}
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
