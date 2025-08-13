import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './styles/sidebar.css';

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [callHistory, setCallHistory] = useState([]);

  useEffect(() => {
    // Load mock call history
    const mockHistory = [
      { id: 1, type: '10-02 Accident - Non ...', time: '2 hours ago' },
      { id: 2, type: '10-04 Alarm - ATM, C ...', time: '4 hours ago' },
      { id: 3, type: '10-04 Alarm - ATM, C ...', time: '6 hours ago' }
    ];
    setCallHistory(mockHistory);
  }, []);

  return (
    <div className="sidebar">
      <nav className="sidebar-nav">
        <div 
          className={`nav-item ${location.pathname === '/' ? 'active' : ''}`}
          onClick={() => navigate('/')}
        >
          <span className="nav-icon">🏠</span>
          <span className="nav-label">Home</span>
        </div>
        <div 
          className={`nav-item ${location.pathname === '/new-call' ? 'active' : ''}`}
          onClick={() => navigate('/new-call')}
        >
          <span className="nav-icon">➕</span>
          <span className="nav-label">New Call</span>
        </div>
      </nav>
      
      <div className="call-history">
        <h3>Previous 30 Days</h3>
        <div className="call-history-list">
          {callHistory.map((call) => (
            <div key={call.id} className="history-item">
              <div className="call-type">{call.type}</div>
              <div className="call-time">{call.time}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
