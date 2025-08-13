import React from 'react';

const CallIcon = ({ isActive = false, color = 'green', size = 'large' }) => {
  const className = `call-icon ${size} ${color} ${isActive ? 'active' : ''}`;
  
  return (
    <div className={className}>
      <span className="phone-symbol">📞</span>
    </div>
  );
};

export default CallIcon;
