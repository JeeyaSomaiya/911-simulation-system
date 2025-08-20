import React, { createContext, useContext, useState, useEffect } from 'react';

const authContext = createContext();

export const useAuth = () => {
  const context = useContext(authContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const currentUser = localStorage.getItem('currentUser');
    if (currentUser) {
      try {
        const userData = JSON.parse(currentUser);
        setUser(userData);
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        localStorage.removeItem('currentUser');
      }
    }
    setLoading(false);
  }, []);

  const login = (userData) => {
    setUser(userData);
    localStorage.setItem('currentUser', JSON.stringify(userData));
    localStorage.setItem('trainee_id', userData.id);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('currentUser');
    localStorage.removeItem('trainee_id');
    
    if (user) {
      localStorage.removeItem(`user_${user.id}_sessions`);
    }
  };

  const updateUser = (updatedUserData) => {
    const newUserData = { ...user, ...updatedUserData };
    setUser(newUserData);
    localStorage.setItem('currentUser', JSON.stringify(newUserData));
    const users = JSON.parse(localStorage.getItem('users') || '[]');
    const userIndex = users.findIndex(u => u.id === newUserData.id);
    if (userIndex !== -1) {
      users[userIndex] = { ...users[userIndex], ...updatedUserData };
      localStorage.setItem('users', JSON.stringify(users));
    }
  };

  const saveSession = (sessionData) => {
    if (!user) return;
  
    const sessionToSave = {
      id: sessionData.session_id || sessionData.sessionId || Date.now().toString(),
      sessionId: sessionData.session_id || sessionData.sessionId,
      scenarioType: sessionData.scenario_type || sessionData.scenarioType,
      selectedSubtype: sessionData.selected_subtype || sessionData.selectedSubtype, // ADD THIS
      startTime: sessionData.start_time || sessionData.startTime || new Date().toISOString(),
      endTime: sessionData.end_time || sessionData.endTime || new Date().toISOString(),
      conversation: sessionData.conversation || [],
      scenarioProgress: sessionData.scenario_progress || sessionData.scenarioProgress || 0,
      emotionalState: sessionData.emotional_state || sessionData.emotionalState || 'unknown',
      keyDetailsRevealed: sessionData.key_details_revealed || sessionData.keyDetailsRevealed || [],
      status: sessionData.status || 'completed'
    };

    const existingSessions = JSON.parse(localStorage.getItem(`user_${user.id}_history`) || '[]');

    const sessionExists = existingSessions.find(s => s.sessionId === sessionToSave.sessionId);
    
    if (!sessionExists) {
      const updatedSessions = [...existingSessions, sessionToSave];
      localStorage.setItem(`user_${user.id}_history`, JSON.stringify(updatedSessions));

      updateUser({ 
        sessions: updatedSessions,
        totalSessions: updatedSessions.length 
      });
    }

    return sessionToSave;
  };

  const getUserSessions = () => {
    if (!user) return [];
    
    const sessions = JSON.parse(localStorage.getItem(`user_${user.id}_history`) || '[]');
    return sessions;
  };

  const getSessionById = (sessionId) => {
    if (!user) return null;
    
    const sessions = getUserSessions();
    return sessions.find(session => session.sessionId === sessionId) || null;
  };

  const deleteSession = (sessionId) => {
    if (!user) return;
    
    const sessions = getUserSessions();
    const updatedSessions = sessions.filter(session => session.sessionId !== sessionId);
    localStorage.setItem(`user_${user.id}_history`, JSON.stringify(updatedSessions));
    
    updateUser({ 
      sessions: updatedSessions,
      totalSessions: updatedSessions.length 
    });
  };

  const clearAllSessions = () => {
    if (!user) return;
    
    localStorage.removeItem(`user_${user.id}_history`);
    localStorage.removeItem(`user_${user.id}_sessions`);
    
    updateUser({ 
      sessions: [],
      totalSessions: 0 
    });
  };

  const getUserStats = () => {
    if (!user) return null;
    
    const sessions = getUserSessions();
    const completedSessions = sessions.filter(s => s.status === 'completed');
    
    return {
      totalSessions: sessions.length,
      completedSessions: completedSessions.length,
      averageProgress: completedSessions.length > 0 
        ? Math.round(completedSessions.reduce((sum, s) => sum + (s.scenarioProgress || 0), 0) / completedSessions.length)
        : 0,
      totalConversations: sessions.reduce((sum, s) => sum + (s.conversation?.length || 0), 0),
      recentSessions: sessions
        .sort((a, b) => new Date(b.startTime) - new Date(a.startTime))
        .slice(0, 5)
    };
  };

  const value = {
    user,
    loading,
    login,
    logout,
    updateUser,
    saveSession,
    getUserSessions,
    getSessionById,
    deleteSession,
    clearAllSessions,
    getUserStats,
    isAuthenticated: !!user
  };

  return (
    <authContext.Provider value={value}>
      {children}
    </authContext.Provider>
  );
};
