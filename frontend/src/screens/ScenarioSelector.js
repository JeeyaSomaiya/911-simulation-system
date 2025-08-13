import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ScenarioDropdown from '../components/features/scenario/ScenarioDropdown';
import LocationTimeDisplay from '../components/features/scenario/LocationTimeDisplay';
import CallButton from '../components/features/call/CallButton';
import { useSession } from '../hooks/useSession';
import { scenarios } from '../utils/constants/scenarios';

const ScenarioSelector = () => {
  const navigate = useNavigate();
  const { createSession } = useSession();
  const [selectedScenario, setSelectedScenario] = useState(scenarios[0]);
  const [realtimeTranscription, setRealtimeTranscription] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSimulateCall = async () => {
    setIsLoading(true);
    try {
      const session = await createSession({
        trainee_id: 'user_' + Date.now(),
        scenario_type: selectedScenario.type
      });
      
      navigate(`/call-waiting/${session.session_id}`);
    } catch (error) {
      console.error('Failed to create session:', error);
      setIsLoading(false);
    }
  };

  return (
    <div className="scenario-selector">
      <div className="scenario-card">
        <h2>Create a new call</h2>
        <p>Select a scenario to simulate</p>

        <div className="form-section">
          <ScenarioDropdown
            scenarios={scenarios}
            selectedScenario={selectedScenario}
            onScenarioChange={setSelectedScenario}
          />
          
          <LocationTimeDisplay />
          
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

        <CallButton
          onClick={handleSimulateCall}
          text="Simulate Call"
          variant="primary"
          isLoading={isLoading}
          disabled={!selectedScenario}
        />
      </div>
    </div>
  );
};

export default ScenarioSelector;
