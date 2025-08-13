import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import NavItem from '../features/navigation/NavItem';
import CallHistoryList from '../features/navigation/CallHistoryList';
import { useCallHistory } from '../../hooks/useCallHistory';

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { callHistory } = useCallHistory();

  const navigationItems = [
    { path: '/', label: 'Home', icon: 'home' },
    { path: '/new-call', label: 'New Call', icon: 'plus' }
  ];

  return (
    <div className="sidebar">
      <nav className="sidebar-nav">
        {navigationItems.map((item) => (
          <NavItem
            key={item.path}
            path={item.path}
            label={item.label}
            icon={item.icon}
            isActive={location.pathname === item.path}
            onClick={() => navigate(item.path)}
          />
        ))}
      </nav>
      
      <div className="call-history">
        <h3>Previous 30 Days</h3>
        <CallHistoryList calls={callHistory} />
      </div>
    </div>
  );
};

export default Sidebar;
