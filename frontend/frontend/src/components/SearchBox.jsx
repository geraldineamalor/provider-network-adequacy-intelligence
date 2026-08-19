import React from 'react';

const SearchBox = ({ value, onChange, placeholder = 'Search...', className = '' }) => {
  return (
    <div className={`search-box ${className}`}>
      <span className="search-icon">🔍</span>
      <input
        type="text"
        className="search-input"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
};

export default SearchBox;
