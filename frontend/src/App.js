import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { SessionProvider } from './context/SessionContext';
import { WebSocketProvider } from './context/WebSocketContext';
import Layout from './components/Layout';
import HomePage from './components/HomePage';
import ScenarioSelector from './components/ScenarioSelector';
import CallWaiting from './components/CallWaiting';
import CallInterface from './components/CallInterface';

function App() {
  return (
    <SessionProvider>
      <WebSocketProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/new-call" element={<ScenarioSelector />} />
            <Route path="/call-waiting" element={<CallWaiting />} />
            <Route path="/call/:sessionId" element={<CallInterface />} />
          </Routes>
        </Layout>
      </WebSocketProvider>
    </SessionProvider>
  );
}

export default App;