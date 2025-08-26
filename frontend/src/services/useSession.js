import { useState, useCallback } from 'react';
import { useAuth } from './authContext';

const API_BASE_URL = 'http://130.250.171.84:5000';

export const useSession = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const { user, saveSession: saveSessionToAuth } = useAuth();

  const createSession = useCallback(async ({ trainee_id, scenario_type, selected_subtype }) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('Creating session with:', { trainee_id, scenario_type, selected_subtype });
      
      const response = await fetch(`${API_BASE_URL}/api/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          trainee_id: trainee_id || user?.id,
          scenario_type,
          selected_subtype
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Session created:', data);

      if (user) {
        const sessionTracker = {
          session_id: data.session_id,
          scenario_type: data.scenario_type,
          selected_subtype: data.selected_subtype || selected_subtype,
          start_time: data.start_time || new Date().toISOString(),
          status: 'active',
          conversation: [], 
          message_count: 0, 
          scenario_progress: 0,
          emotional_state: 'neutral',
          key_details_revealed: []
        };

        const userSessions = JSON.parse(localStorage.getItem(`user_${user.id}_sessions`) || '[]');
        userSessions.push(sessionTracker);
        localStorage.setItem(`user_${user.id}_sessions`, JSON.stringify(userSessions));
        
        console.log('Session stored locally:', sessionTracker);
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

  const sendMessage = useCallback(async (sessionId, message) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('📤 Sending message:', { sessionId, message });
      
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Message response:', data);

      if (user) {
        const userSessions = JSON.parse(localStorage.getItem(`user_${user.id}_sessions`) || '[]');
        const sessionIndex = userSessions.findIndex(s => s.session_id === sessionId);
        
        if (sessionIndex !== -1) {
          const currentSession = userSessions[sessionIndex];

          const callTakerMessage = {
            role: 'call_taker',
            content: message,
            timestamp: new Date().toISOString()
          };
          
          const callerMessage = {
            role: 'caller',
            content: data.caller_response,
            emotional_state: data.emotional_state,
            intensity: data.intensity,
            timestamp: new Date().toISOString()
          };

          const updatedConversation = [
            ...(currentSession.conversation || []),
            callTakerMessage,
            callerMessage
          ];

          userSessions[sessionIndex] = {
            ...currentSession,
            conversation: updatedConversation,
            message_count: updatedConversation.length,
            scenario_progress: data.scenario_progress || currentSession.scenario_progress,
            emotional_state: data.emotional_state || currentSession.emotional_state,
            key_details_revealed: data.key_details_revealed || currentSession.key_details_revealed,
            last_updated: new Date().toISOString()
          };
          
          localStorage.setItem(`user_${user.id}_sessions`, JSON.stringify(userSessions));
          
          console.log('💬 CONVERSATION UPDATED:');
          console.log('- Session ID:', sessionId);
          console.log('- New message count:', updatedConversation.length);
          console.log('- Call taker message:', callTakerMessage);
          console.log('- Caller response:', callerMessage);
          console.log('- Full conversation:', updatedConversation);
          console.log('- Updated session:', userSessions[sessionIndex]);
        } else {
          console.error('❌ Session not found in localStorage for ID:', sessionId);
        }
      }
      
      return data;
    } catch (err) {
      console.error('❌ Send message error:', err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  const terminateSession = useCallback(async (sessionId) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('🔚 Terminating session:', sessionId);
      
      let localSessionData = null;
      if (user) {
        const userSessions = JSON.parse(localStorage.getItem(`user_${user.id}_sessions`) || '[]');
        localSessionData = userSessions.find(s => s.session_id === sessionId);
        console.log('📋 Local session data before termination:', localSessionData);
        console.log('📊 Local conversation count:', localSessionData?.conversation?.length || 0);
      }

      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/end`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const apiResponse = await response.json();
      console.log('Terminate API response:', apiResponse);

      if (user && localSessionData) {
        const endTime = new Date().toISOString();
        const conversation = localSessionData.conversation || [];
    
        const completedSession = {
          id: sessionId,
          sessionId: sessionId,
          scenarioType: localSessionData.scenario_type,
          selectedSubtype: localSessionData.selected_subtype,
          startTime: localSessionData.start_time,
          endTime: endTime,
          conversation: conversation,
          scenarioProgress: localSessionData.scenario_progress || 0,
          emotionalState: localSessionData.emotional_state || 'unknown',
          keyDetailsRevealed: localSessionData.key_details_revealed || [],
          status: 'completed'
        };

        console.log('💾 SAVING COMPLETED SESSION:');
        console.log('- Session ID:', sessionId);
        console.log('- Start time:', completedSession.startTime);
        console.log('- End time:', completedSession.endTime);
        console.log('- Duration (ms):', new Date(endTime) - new Date(completedSession.startTime));
        console.log('- Conversation array:', conversation);
        console.log('- Message count:', conversation.length);
        console.log('- Complete session data:', completedSession);

        saveSessionToAuth(completedSession);

        const userSessions = JSON.parse(localStorage.getItem(`user_${user.id}_sessions`) || '[]');
        const updatedSessions = userSessions.filter(session => session.session_id !== sessionId);
        localStorage.setItem(`user_${user.id}_sessions`, JSON.stringify(updatedSessions));
        
        console.log('Session saved to history and removed from active sessions');
      } else {
        console.warn('No local session data found or no user logged in');
      }
      
      return apiResponse;
    } catch (err) {
      console.error('Terminate session error:', err);
      setError(err.message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [user, saveSessionToAuth]);

  const getSession = useCallback(async (sessionId) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('📋 Getting session:', sessionId);
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('API session data:', data);
      return data;
    } catch (err) {
      console.error('Get session error:', err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getUserSessionHistory = useCallback(async () => {
    if (!user) return [];
    
    console.log('📚 Getting user session history');
    
    const localHistory = JSON.parse(localStorage.getItem(`user_${user.id}_history`) || '[]');
    console.log('Local history sessions:', localHistory.length);
    
    localHistory.forEach((session, index) => {
      console.log(`📋 Session ${index + 1}:`, {
        id: session.sessionId,
        scenario: session.scenarioType,
        messageCount: session.conversation?.length || 0,
        hasConversation: Array.isArray(session.conversation),
        status: session.status
      });
    });
    
    return localHistory;
  }, [user]);

  const updateSession = useCallback(async (sessionId, updates) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('Updating session:', sessionId, updates);
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
      console.log('Update session response:', data);
      return data;
    } catch (err) {
      console.error('Update session error:', err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const debugSessionData = useCallback(() => {
    if (!user) {
      console.log('No user logged in');
      return;
    }
    
    console.log('DEBUG SESSION DATA:');
    
    const activeSessions = JSON.parse(localStorage.getItem(`user_${user.id}_sessions`) || '[]');
    const sessionHistory = JSON.parse(localStorage.getItem(`user_${user.id}_history`) || '[]');
    
    console.log('Active sessions:', activeSessions);
    console.log('Session history:', sessionHistory);
    
    sessionHistory.forEach((session, index) => {
      console.log(`Session ${index + 1}:`, {
        id: session.sessionId,
        messages: session.conversation?.length || 0,
        conversationType: typeof session.conversation,
        isArray: Array.isArray(session.conversation)
      });
    });
  }, [user]);

  return {
    createSession,
    getSession,
    sendMessage,
    terminateSession,
    updateSession,
    getUserSessionHistory,
    debugSessionData,
    isLoading,
    error
  };
};
