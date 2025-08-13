import React from 'react';

const NavItem = ({ path, label, icon, isActive, onClick }) => {
  const getIcon = (iconName) => {
    const icons = {
      home: '🏠',
      plus: '➕'
    };
    return icons[iconName] || '📄';
  };

  return (
    <div
      className={`nav-item ${isActive ? 'active' : ''}`}
      onClick={onClick}
    >
      <span className="nav-icon">{getIcon(icon)}</span>
      <span className="nav-label">{label}</span>
    </div>
  );
};

export default NavItem;
