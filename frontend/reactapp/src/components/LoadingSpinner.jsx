import React from 'react';

const LoadingSpinner = ({ size = 'md', text = '' }) => {
  return (
    <div style={{ textAlign: 'center', padding: '40px 20px' }}>
      <div className={`spinner ${size === 'sm' ? 'spinner-sm' : ''}`}></div>
      {text && <p style={{ marginTop: '16px', color: 'var(--text-secondary)' }}>{text}</p>}
    </div>
  );
};

export default LoadingSpinner;
