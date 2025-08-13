import React from 'react';
import CallIcon from '../ui/CallIcon';

const CallControls = ({ onTerminate }) => {
  return (
    <div className="call-controls">
      <button
        className="hang-up-button"
        onClick={onTerminate}
      >
        <CallIcon isActive={false} color="red" />
      </button>
    </div>
  );
};

export default CallControls;
