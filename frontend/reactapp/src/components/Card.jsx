import React from 'react';

const Card = ({ children, title, subtitle, className = '', onClick, hoverable = false }) => {
  const cardClass = `card ${hoverable ? 'card-hoverable' : ''} ${className}`.trim();
  
  return (
    <div className={cardClass} onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
      {(title || subtitle) && (
        <div className="card-header">
          {title && <h3 className="card-title">{title}</h3>}
          {subtitle && <p className="card-subtitle">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
};

export default Card;
