import React from 'react';

const EmptyState = ({ 
  title = 'No data available', 
  message = 'There is no data to display at the moment.',
  icon = '📭',
  action
}) => {
  return (
    <div style={{ 
      textAlign: 'center', 
      padding: '60px 20px',
      color: 'var(--text-secondary)'
    }}>
      <div style={{ fontSize: '4rem', marginBottom: '16px' }}>{icon}</div>
      <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>{title}</h3>
      <p style={{ marginBottom: '24px' }}>{message}</p>
      {action && action}
    </div>
  );
};

export default EmptyState;
