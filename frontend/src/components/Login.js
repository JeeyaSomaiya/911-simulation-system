import React, { useState } from 'react';
import './styles/login.css';

const Login = ({ onLogin, onNavigate }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (error) setError('');
  };

  const validateForm = () => {
    if (!formData.email.trim()) {
      setError('Email is required');
      return false;
    }
    if (!formData.email.includes('@')) {
      setError('Please enter a valid email address');
      return false;
    }
    if (!formData.password.trim()) {
      setError('Password is required');
      return false;
    }
    if (isSignUp && formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const existingUsers = JSON.parse(localStorage.getItem('users') || '[]');
      
      if (isSignUp) {
        const userExists = existingUsers.find(user => user.email === formData.email);
        if (userExists) {
          setError('An account with this email already exists');
          return;
        }
        
        const newUser = {
          id: Date.now().toString(),
          email: formData.email,
          password: formData.password,
          name: formData.email.split('@')[0],
          createdAt: new Date().toISOString(),
          sessions: []
        };
        
        existingUsers.push(newUser);
        localStorage.setItem('users', JSON.stringify(existingUsers));
 
        const userData = { ...newUser };
        delete userData.password;
        
        onLogin(userData);
        
      } else {
        const user = existingUsers.find(
          u => u.email === formData.email && u.password === formData.password
        );
        
        if (!user) {
          setError('Invalid email or password');
          return;
        }
        
        const userData = { ...user };
        delete userData.password;
        
        onLogin(userData);
      }
      
    } catch (error) {
      console.error('Authentication error:', error);
      setError('Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setIsLoading(true);
    
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const demoUser = {
        id: 'demo-user',
        email: 'demo@example.com',
        name: 'Demo User',
        createdAt: new Date().toISOString(),
        sessions: []
      };
      
      onLogin(demoUser);
      
    } catch (error) {
      setError('Demo login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <div className="logo">
            <img src="/images/headset.png" alt="logo" className='logo-icon'/>
            <h1>AI Call Simulator</h1>
          </div>
          <h2>{isSignUp ? 'Create Account' : 'Welcome Back'}</h2>
          <p>
            {isSignUp 
              ? 'Sign up to start your call simulation training'
              : 'Sign in to continue your call simulation training'
            }
          </p>
        </div>

        <div className="login-form">
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠</span>
              <span className="error-text">{error}</span>
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="Enter your email"
              disabled={isLoading}
              className={isLoading ? 'disabled' : ''}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder={isSignUp ? "Create a password (min. 6 characters)" : "Enter your password"}
              disabled={isLoading}
              className={isLoading ? 'disabled' : ''}
              required
            />
          </div>

          <button 
            onClick={handleSubmit}
            disabled={isLoading}
            className={`login-button ${isLoading ? 'loading' : ''}`}
          >
            <span className="button-content">
                {isSignUp ? 'Create Account' : 'Sign In'}
            </span>
          </button>
        </div>

        <div className="login-divider">
          <span>or</span>
        </div>

        <button 
          onClick={handleDemoLogin}
          disabled={isLoading}
          className={`demo-button ${isLoading ? 'disabled' : ''}`}
        >
          Try Demo (No Account Required)
        </button>

        <div className="login-footer">
          <p>
            {isSignUp ? 'Already have an account? ' : "Don't have an account? "}
            <button 
              type="button"
              className="link-button"
              onClick={() => {
                setIsSignUp(!isSignUp);
                setError('');
                setFormData({ email: '', password: '' });
              }}
              disabled={isLoading}
            >
              {isSignUp ? 'Sign In' : 'Sign Up'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;