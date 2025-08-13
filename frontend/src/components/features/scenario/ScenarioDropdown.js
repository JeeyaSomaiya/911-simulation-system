import React, { useState } from 'react';

const ScenarioDropdown = ({ scenarios, selectedScenario, onScenarioChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = (scenario) => {
    onScenarioChange(scenario);
    setIsOpen(false);
  };

  return (
    <div className="scenario-dropdown">
      <div
        className="dropdown-trigger"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span>{selectedScenario?.code} {selectedScenario?.name}</span>
        <span className={`dropdown-arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </div>
      
      {isOpen && (
        <div className="dropdown-menu">
          {scenarios.map((scenario) => (
            <div
              key={scenario.code}
              className="dropdown-item"
              onClick={() => handleSelect(scenario)}
            >
              {scenario.code} {scenario.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ScenarioDropdown;
