import { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';

export const useWebSocket = (sessionId) => {
  const [isConnected, setIsConnected] = useState(false);
  const [transcript, setTranscript] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    if (sessionId) {
      // Load config
      fetch('/config.json')
        .then(response => response.json())
        .then(config => {
          socketRef.current = io(config.websocketUrl || 'http://localhost:5000');

          socketRef.current.on('connect', () => {
            setIsConnected(true);
            socketRef.current.emit('join_session', { session_id: sessionId });
          });

          socketRef.current.on('disconnect', () => {
            setIsConnected(false);
          });

          socketRef.current.on('caller_response', (data) => {
            setTranscript({
              role: 'caller',
              content: data.caller_response,
              emotional_state: data.emotional_state,
              intensity: data.intensity
            });
          });
        });

      return () => {
        if (socketRef.current) {
          socketRef.current.disconnect();
        }
      };
    }
  }, [sessionId]);

  return { isConnected, transcript };
};
