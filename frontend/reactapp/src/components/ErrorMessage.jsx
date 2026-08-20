import React from 'react';

const ErrorMessage = ({ message = 'Something went wrong. Please try again.', onRetry }) => {
  return (
    <div className="alert alert-error fade-in">
      <div style={{ flex: 1 }}>
        <strong>Error</strong>
        <p style={{ margin: '8px 0 0 0' }}>{message}</p>
      </div>
      {onRetry && (
        <button className="btn btn-sm btn-outline" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;
