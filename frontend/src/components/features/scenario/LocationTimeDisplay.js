import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';

const LocationTimeDisplay = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
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
  );
};

export default LocationTimeDisplay;
