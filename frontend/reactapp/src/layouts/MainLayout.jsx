import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, MapPin, Stethoscope, BarChart3, Lightbulb, Bell, Settings, User } from 'lucide-react';
import './MainLayout.css';

const MainLayout = ({ children }) => {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/select-area', label: 'Select Area', icon: MapPin },
    { path: '/select-specialty', label: 'Specialties', icon: Stethoscope },
    { path: '/results', label: 'Results', icon: BarChart3 },
    { path: '/recommendations', label: 'Recommendations', icon: Lightbulb },
  ];

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="main-layout">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="header-left">
            <Link to="/" className="app-logo">
              <div className="logo-icon">
                <Stethoscope size={24} strokeWidth={2} />
              </div>
              <div className="logo-text">
                <span className="logo-primary">Network Adequacy</span>
                <span className="logo-secondary">Intelligence Platform</span>
              </div>
            </Link>
          </div>
          
          <nav className="header-nav">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`nav-link ${isActive(item.path) ? 'active' : ''}`}
                >
                  <Icon size={18} strokeWidth={2} />
                  <span className="nav-label">{item.label}</span>
                </Link>
              );
            })}
          </nav>
          
         
        </div>
      </header>

      {/* Main Content */}
      <main className="app-content">
        <div className="content-wrapper">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-content">
          <p>&copy; 2026 Provider Network Adequacy Intelligence Platform. All rights reserved.</p>
          <div className="footer-links">
            <a href="#help">Help</a>
            <a href="#privacy">Privacy</a>
            <a href="#terms">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default MainLayout;
