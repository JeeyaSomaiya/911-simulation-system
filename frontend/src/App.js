import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './screens/HomePage';
import ScenarioSelector from './screens/ScenarioSelector';
import CallWaiting from './screens/CallWaiting';
import CallInterface from './screens/CallInterface';
import { SessionProvider } from './context/SessionContext';
import { WebSocketProvider } from './context/WebSocketContext';
import './App.css';

function App() {
  return (
    <SessionProvider>
      <WebSocketProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/new-call" element={<ScenarioSelector />} />
            <Route path="/call-waiting/:sessionId" element={<CallWaiting />} />
            <Route path="/call/:sessionId" element={<CallInterface />} />
          </Routes>
        </Layout>
      </WebSocketProvider>
    </SessionProvider>
  );
}

export default App;
