import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Layout from './components/Layout';
import HomePage from './components/HomePage';
import ScenarioSelector from './components/ScenarioSelector';
import CallWaiting from './components/CallWaiting';
import CallInterface from './components/CallInterface';
import SessionHistory from './components/SessionHistory';
import { AuthProvider, useAuth } from './services/authContext';
import './App.css';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  return user ? children : <Navigate to="/login" replace />;
};

const AppContent = () => {
  const { user, login } = useAuth();

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login onLogin={login} />} />
        <Route path="*" element={<Login onLogin={login} />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<Navigate to="/" replace />} />
      
      <Route path="/" element={
        <Layout>
          <HomePage />
        </Layout>
      } />
      
      <Route path="/new-call" element={
        <Layout>
          <ScenarioSelector />
        </Layout>
      } />
      
      <Route path="/history" element={
        <Layout>
          <SessionHistory />
        </Layout>
      } />
      
      <Route path="/call-waiting/:sessionId" element={
        <Layout>
          <CallWaiting />
        </Layout>
      } />

      <Route path="/call/:sessionId" element={
        <Layout>
          <CallInterface />
        </Layout>
      } />
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <div className="App">
        <AppContent />
      </div>
    </AuthProvider>
  );
};

export default App;
