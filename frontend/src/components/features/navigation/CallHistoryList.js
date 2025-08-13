import React from 'react';

const CallHistoryList = ({ calls = [] }) => {
  const mockCalls = [
    { id: 1, type: '10-02 Accident - Non ...', time: '2 hours ago' },
    { id: 2, type: '10-04 Alarm - ATM, C ...', time: '4 hours ago' },
    { id: 3, type: '10-04 Alarm - ATM, C ...', time: '6 hours ago' }
  ];

  const displayCalls = calls.length > 0 ? calls : mockCalls;

  return (
    <div className="call-history-list">
      {displayCalls.map((call) => (
        <div key={call.id} className="history-item">
          <span className="call-type">{call.type}</span>
          <span className="call-time">{call.time}</span>
        </div>
      ))}
    </div>
  );
};

export default CallHistoryList;
