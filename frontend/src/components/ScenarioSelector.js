import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { useSession } from '../services/useSession';
import './styles/scenario-selector.css';

const ScenarioSelector = () => {
  const navigate = useNavigate();
  const { createSession } = useSession();
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [realtimeTranscription, setRealtimeTranscription] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    // Load scenarios from the real JSON structure
    const loadScenarios = async () => {
      try {
        const response = await fetch('/scenarios.json');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // Validate that data is an array
        if (Array.isArray(data) && data.length > 0) {
          setScenarios(data);
          setSelectedScenario(data[0]);
        } else {
          throw new Error('No scenarios found in JSON file');
        }
      } catch (error) {
        console.error('Error loading scenarios:', error);
        setLoadError(error.message);
      }
    };

    loadScenarios();

    // Update time every second
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleSimulateCall = async () => {
    if (!selectedScenario) {
      alert('Please select a scenario first');
      return;
    }
    
    setIsLoading(true);
    try {
      const session = await createSession({
        trainee_id: 'user_' + Date.now(),
        scenario_type: selectedScenario.Code
      });
      
      navigate(`/call-waiting/${session.session_id}`);
    } catch (error) {
      console.error('Failed to create session:', error);
      alert('Failed to create session. Please try again.');
      setIsLoading(false);
    }
  };

  // Show loading state while scenarios are being loaded
  if (scenarios.length === 0 && !loadError) {
    return (
      <div className="scenario-selector">
        <div className="scenario-card">
          <h2>Loading scenarios...</h2>
          <p>Please wait while we load the available scenarios.</p>
        </div>
      </div>
    );
  }

  // Show error state if scenarios failed to load
  if (loadError) {
    return (
      <div className="scenario-selector">
        <div className="scenario-card">
          <h2>Error Loading Scenarios</h2>
          <p className="error-message">Failed to load scenarios: {loadError}</p>
          <p>Please check that scenarios.json is available in the public folder.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="scenario-selector">
      <div className="scenario-card">
        <h2>Create a new call</h2>
        <p>Select a scenario to simulate</p>

        <div className="form-section">
          <div className="dropdown-container">
            <div 
              className="dropdown-trigger"
              onClick={() => setDropdownOpen(!dropdownOpen)}
            >
              <span>
                {selectedScenario ? `${selectedScenario.Code} ${selectedScenario.EventType}` : 'Select scenario'}
              </span>
              <span className={`dropdown-arrow ${dropdownOpen ? 'open' : ''}`}>▼</span>
            </div>
            
            {dropdownOpen && (
              <div className="dropdown-menu">
                {scenarios.map((scenario, index) => (
                  <div
                    key={`${scenario.Code}-${index}`}
                    className="dropdown-item"
                    onClick={() => {
                      setSelectedScenario(scenario);
                      setDropdownOpen(false);
                    }}
                  >
                    {scenario.Code} {scenario.EventType}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="location-time-display">
            <div className="location">
              <span className="icon">📍</span>
              <span>Calgary, Alberta</span>
            </div>
            <div className="time">
              <span className="icon">🕐</span>
              <span>{format(currentTime, 'h:mm a')}</span>
            </div>
          </div>
          
          <div className="option-row">
            <label className="checkbox-container">
              <input
                type="checkbox"
                checked={realtimeTranscription}
                onChange={(e) => setRealtimeTranscription(e.target.checked)}
              />
              <span className="checkmark"></span>
              Real-time transcription
            </label>
          </div>
        </div>

        <button 
          className="simulate-call-btn"
          onClick={handleSimulateCall}
          disabled={!selectedScenario || isLoading}
        >
          <span className="phone-icon">📞</span>
          {isLoading ? 'Creating...' : 'Simulate Call'}
        </button>
        
        {selectedScenario && (
          <div className="selected-scenario-info">
            <small>
              Selected: {selectedScenario.Code} - {selectedScenario.EventType}
              {selectedScenario.EventSubtypes && selectedScenario.EventSubtypes.length > 0 && (
                <span> ({selectedScenario.EventSubtypes.join(', ')})</span>
              )}
            </small>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScenarioSelector;
