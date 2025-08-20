import { useState, useCallback } from 'react';
import { useAuth } from './authContext';

const API_BASE_URL = 'http://130.250.171.84:5000';

export const useSession = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const { user, saveSession: saveSessionToAuth } = useAuth();

  const createSession = useCallback(async ({ trainee_id, scenario_type, selected_subtype })  => {
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
          trainee_id: trainee_id || user?.id,
          scenario_type
        }),
      });

      console.log('Session creation response status:', response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Session creation response data:', data);

      if (user) {
        const userSessions = JSON.parse(localStorage.getItem(`user_${user.id}_sessions`) || '[]');
        userSessions.push({
          session_id: data.session_id,
          scenario_type: data.scenario_type,
          selected_subtype: data.selected_subtype,
          start_time: data.start_time || new Date().toISOString(),
          status: 'active'
        });
        localStorage.setItem(`user_${user.id}_sessions`, JSON.stringify(userSessions));
      }
      
      return data;
    } catch (err) {
      console.error('Session creation error:', err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  const getSession = useCallback(async (sessionId) => {
    setIsLoading(true);
    setError(null);
    
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
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (sessionId, message) => {
    setIsLoading(true);
    setError(null);
    
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
    } finally {
      setIsLoading(false);
    }
  }, []);

  const terminateSession = useCallback(async (sessionId) => {
    setIsLoading(true);
    setError(null);
    
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

      if (user && data) {
        try {
          const sessionData = await getSession(sessionId);
          
          const completedSession = {
            id: sessionId,
            sessionId: sessionId,
            scenarioType: sessionData.scenario_type,
            startTime: sessionData.start_time,
            endTime: new Date().toISOString(),
            conversation: sessionData.conversation || [],
            scenarioProgress: sessionData.scenario_progress || 0,
            emotionalState: sessionData.emotional_state || 'unknown',
            keyDetailsRevealed: sessionData.key_details_revealed || [],
            status: 'completed'
          };

          saveSessionToAuth(completedSession);

          const userSessions = JSON.parse(localStorage.getItem(`user_${user.id}_sessions`) || '[]');
          const updatedSessions = userSessions.map(session => 
            session.session_id === sessionId 
              ? { ...session, status: 'completed', end_time: new Date().toISOString() }
              : session
          );
          localStorage.setItem(`user_${user.id}_sessions`, JSON.stringify(updatedSessions));
        } catch (saveError) {
          console.error('Error saving session to history:', saveError);
        }
      }
      
      return data;
    } catch (err) {
      console.error('Terminate session error:', err);
      setError(err.message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [user, saveSessionToAuth, getSession]);

  const getUserSessionHistory = useCallback(async () => {
    if (!user) return [];
    
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('Getting user session history for:', user.id);
      const response = await fetch(`${API_BASE_URL}/api/sessions/user/${user.id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('User session history:', data);
      
      const transformedSessions = data.sessions?.map(session => ({
        id: session.session_id,
        sessionId: session.session_id,
        scenarioType: session.scenario_type,
        startTime: session.start_time,
        endTime: session.end_time,
        conversation: session.conversation || [],
        scenarioProgress: session.scenario_progress || 0,
        emotionalState: session.emotional_state || 'unknown',
        keyDetailsRevealed: session.key_details_revealed || [],
        status: session.status || 'completed'
      })) || [];
      
      return transformedSessions;
    } catch (err) {
      console.error('Get user session history error:', err);
      setError(err.message);
      const localSessions = JSON.parse(localStorage.getItem(`user_${user.id}_sessions`) || '[]');
      return localSessions;
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  const updateSession = useCallback(async (sessionId, updates) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('Updating session:', sessionId, 'Updates:', updates);
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Update session response data:', data);
      return data;
    } catch (err) {
      console.error('Update session error:', err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    createSession,
    getSession,
    sendMessage,
    terminateSession,
    updateSession,
    getUserSessionHistory,
    isLoading,
    error
  };
};
