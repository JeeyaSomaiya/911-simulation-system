import { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = 'http://localhost:5000';

export const useWebSocket = (sessionId) => {
  const [isConnected, setIsConnected] = useState(false);
  const [transcript, setTranscript] = useState(null);
  const [error, setError] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!sessionId) return;

    socketRef.current = io(SOCKET_URL, {
      transports: ['websocket', 'polling']
    });

    const socket = socketRef.current;

    socket.on('connect', () => {
      console.log('Connected to WebSocket server');
      setIsConnected(true);
      setError(null);
      
      socket.emit('join_session', { session_id: sessionId });
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket server');
      setIsConnected(false);
    });

    socket.on('connect_error', (err) => {
      console.error('Connection error:', err);
      setError('Failed to connect to server');
      setIsConnected(false);
    });

    socket.on('caller_response', (data) => {
      console.log('Received caller response:', data);
      setTranscript({
        role: 'caller',
        content: data.caller_response,
        emotional_state: data.emotional_state,
        intensity: data.intensity,
        scenario_progress: data.scenario_progress,
        key_details_revealed: data.key_details_revealed,
        timestamp: new Date().toISOString()
      });
    });

    socket.on('error', (data) => {
      console.error('Socket error:', data);
      setError(data.message || 'An error occurred');
    });

    return () => {
      if (socket) {
        socket.emit('leave_session', { session_id: sessionId });
        socket.disconnect();
      }
    };
  }, [sessionId]);

  const sendCallTakerMessage = (message) => {
    if (socketRef.current && isConnected && sessionId) {
      socketRef.current.emit('call_taker_message', {
        session_id: sessionId,
        message: message
      });
    } else {
      console.error('Socket not connected or missing session ID');
      setError('Not connected to server');
    }
  };

  return {
    isConnected,
    transcript,
    error,
    sendCallTakerMessage
  };
};
