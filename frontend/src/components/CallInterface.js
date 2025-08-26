import React, { useState, useEffect, useRef, useLayoutEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSession } from '../services/useSession';
import './styles/call-interface.css';

const CallInterface = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { terminateSession, getSession, sendMessage, createSession } = useSession();
  
  const [conversation, setConversation] = useState([]);
  const [sessionInfo, setSessionInfo] = useState(null);
  const [inputMessage, setInputMessage] = useState('');
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);
  
  const transcriptRef = useRef(null);
  const isSendingRef = useRef(false);
  const inputRef = useRef(null);
  const hasLoadedSession = useRef(false);

  useEffect(() => {
    if (sessionId && !hasLoadedSession.current) {
      hasLoadedSession.current = true;
      
      const loadSession = async () => {
        try {
          const sessionData = await getSession(sessionId);
          setSessionInfo(sessionData);
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

  const handleRetry = async () => {
    setIsRestarting(true);
    try {
      const traineeId = localStorage.getItem('trainee_id') || 'default-trainee-id';
      
      if (sessionInfo && sessionInfo.scenario_type) {
        const newSession = await createSession({
          trainee_id: traineeId,
          scenario_type: sessionInfo.scenario_type
        });

        navigate(`/call/${newSession.session_id}`);
        window.location.reload(); 
      }
    } catch (error) {
      console.error('Failed to restart session:', error);
      alert('Failed to restart the call. Please try again.');
    } finally {
      setIsRestarting(false);
    }
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
        <button 
          className="retry-btn" 
          onClick={handleRetry}
          disabled={isRestarting}
        >
          <img src="/images/retry.png" alt="retry" className="retry-icon"/>
          {isRestarting ? 'Restarting...' : 'Retry Call'}
        </button>
      </div>

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
            {conversation.length === 0 ? (
              <div className="message system">
                <span className="role">System:</span>
                <span className="content">Type a message to start the conversation...</span>
              </div>
            ) : (
              conversation.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>
                  <span className="role">
                    {message.role === 'call_taker' ? 'Call Taker:' : 
                     message.role === 'system' ? 'System:' : 'Caller:'}
                  </span>
                  <span className="content">{message.content}</span>
                </div>
              ))
            )}
            
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
            placeholder={isSending ? "Waiting for response..." : "Type your response ..."}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault(); 
                if (!isSending && !isRestarting && inputMessage.trim()) {
                  handleSendMessage();
                }
              }
            }}
            disabled={isSending || isRestarting}
          />
          <button 
            className="send-button"
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isSending || isRestarting}
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
