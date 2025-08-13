import React, { createContext, useContext, useState } from 'react';

const WebSocketContext = createContext();

export const WebSocketProvider = ({ children }) => {
  const [connections, setConnections] = useState({});

  const addConnection = (sessionId, socket) => {
    setConnections(prev => ({ ...prev, [sessionId]: socket }));
  };

  const removeConnection = (sessionId) => {
    setConnections(prev => {
      const newConnections = { ...prev };
      delete newConnections[sessionId];
      return newConnections;
    });
  };

  return (
    <WebSocketContext.Provider value={{
      connections,
      addConnection,
      removeConnection
    }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocketContext = () => useContext(WebSocketContext);
