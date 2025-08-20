import React from 'react';
import './styles/header.css';

const Header = () => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">
          <img src="/images/headset.png" alt="logo" className='logo-icon'/>
          <h1>AI Call Simulator</h1>
        </div>
      </div>
    </header>
  );
};

export default Header;
