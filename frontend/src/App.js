import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './components/HomePage';
import ScenarioSelector from './components/ScenarioSelector';
import CallWaiting from './components/CallWaiting';
import CallInterface from './components/CallInterface';

function App() {
  return (
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/new-call" element={<ScenarioSelector />} />
            <Route path="/call-waiting/:sessionId" element={<CallWaiting />} />
            <Route path="/call/:sessionId" element={<CallInterface />} />
          </Routes>
        </Layout>
  );
}

export default App;