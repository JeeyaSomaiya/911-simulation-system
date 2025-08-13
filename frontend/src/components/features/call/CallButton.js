import React from 'react';
import LoadingSpinner from '../ui/LoadingSpinner';

const CallButton = ({ onClick, text, variant = 'primary', isLoading = false, disabled = false }) => {
  const className = `call-button btn-${variant} ${isLoading ? 'loading' : ''}`;

  return (
    <button
      className={className}
      onClick={onClick}
      disabled={disabled || isLoading}
    >
      {isLoading ? (
        <LoadingSpinner size="small" />
      ) : (
        <>
          <span className="phone-icon">📞</span>
          {text}
        </>
      )}
    </button>
  );
};

export default CallButton;
