import { useState } from 'react';

const API_BASE_URL = 'http://130.250.171.84:5000';

export const useSession = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const createSession = async ({ trainee_id, scenario_type }) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('Creating session with:', { trainee_id, scenario_type });
      const response = await fetch(`${API_BASE_URL}/api/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          trainee_id,
          scenario_type
        }),
      });

      console.log('Session creation response status:', response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Session creation response data:', data);
      return data;
    } catch (err) {
      console.error('Session creation error:', err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const getSession = async (sessionId) => {
    try {
      console.log('Getting session:', sessionId);
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`);
      console.log('Get session response status:', response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Get session response data:', data);
      return data;
    } catch (err) {
      console.error('Get session error:', err);
      setError(err.message);
      throw err;
    }
  };

  const sendMessage = async (sessionId, message) => {
    try {
      console.log('Sending message to session:', sessionId, 'Message:', message);
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      console.log('Send message response status:', response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Send message response data:', data);
      return data;
    } catch (err) {
      console.error('Send message error:', err);
      setError(err.message);
      throw err;
    }
  };

  const terminateSession = async (sessionId) => {
    try {
      console.log('Terminating session:', sessionId);
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/end`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('Terminate session response status:', response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Terminate session response data:', data);
      return data;
    } catch (err) {
      console.error('Terminate session error:', err);
      setError(err.message);
      return null;
    }
  };

  return {
    createSession,
    getSession,
    sendMessage,
    terminateSession,
    isLoading,
    error
  };
};
