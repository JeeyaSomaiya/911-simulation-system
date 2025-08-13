import { useState, useCallback } from 'react';
import { sessionApi } from '../services/api/sessionApi';

export const useSession = () => {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const createSession = useCallback(async (sessionData) => {
    setLoading(true);
    setError(null);
    try {
      const newSession = await sessionApi.createSession(sessionData);
      setSession(newSession);
      return newSession;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (sessionId, message) => {
    try {
      const response = await sessionApi.sendMessage(sessionId, message);
      return response;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const terminateSession = useCallback(async (sessionId) => {
    try {
      await sessionApi.terminateSession(sessionId);
      setSession(null);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  return {
    session,
    loading,
    error,
    createSession,
    sendMessage,
    terminateSession
  };
};
