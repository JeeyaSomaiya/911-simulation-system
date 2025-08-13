import React from 'react';

const HistorySection = ({ history = [] }) => {
  return (
    <div className="history-section card">
      <h3>History</h3>
      {history.length === 0 ? (
        <p className="empty-state">No calls found</p>
      ) : (
        <div className="history-list">
          {history.map((call, index) => (
            <div key={index} className="history-item">
              <span className="call-type">{call.scenario_type}</span>
              <span className="call-date">{call.date}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HistorySection;
