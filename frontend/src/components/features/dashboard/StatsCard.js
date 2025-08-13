import React from 'react';

const StatsCard = ({ title, value, subtitle }) => {
  return (
    <div className="stats-card">
      <div className="stats-value">{value}</div>
      <div className="stats-title">{title}</div>
      {subtitle && <div className="stats-subtitle">{subtitle}</div>}
    </div>
  );
};

export default StatsCard;
