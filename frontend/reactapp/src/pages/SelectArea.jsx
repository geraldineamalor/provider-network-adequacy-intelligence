import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import SearchBox from '../components/SearchBox';
import apiService from '../services/api';
import './SelectArea.css';

const SelectArea = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [states, setStates] = useState([]);
  const [counties, setCounties] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedState, setSelectedState] = useState(null);
  const [selectedCounties, setSelectedCounties] = useState([]);
  const [loadingCounties, setLoadingCounties] = useState(false);

  useEffect(() => {
    loadStates();
  }, []);

  const loadStates = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getAreas();
      setStates(response.data);
    } catch (err) {
      setError('Failed to load geographic areas. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStateSelect = async (state) => {
    setSelectedState(state);
    setSelectedCounties([]);
    setLoadingCounties(true);
    
    try {
      const response = await apiService.getCounties(state.code);
      setCounties(response.data);
    } catch (err) {
      setError('Failed to load counties. Please try again.');
      console.error(err);
    } finally {
      setLoadingCounties(false);
    }
  };

  const handleCountyToggle = (county) => {
    setSelectedCounties(prev => {
      const isSelected = prev.some(c => c.id === county.id);
      if (isSelected) {
        return prev.filter(c => c.id !== county.id);
      } else {
        return [...prev, county];
      }
    });
  };

  const handleSelectAllCounties = () => {
    if (selectedCounties.length === counties.length) {
      setSelectedCounties([]);
    } else {
      setSelectedCounties(counties);
    }
  };

  const handleContinue = () => {
    if (!selectedState || selectedCounties.length === 0) {
      alert('Please select a state and at least one county.');
      return;
    }
    
    // Store selections in sessionStorage
    sessionStorage.setItem('selectedState', JSON.stringify(selectedState));
    sessionStorage.setItem('selectedCounties', JSON.stringify(selectedCounties));
    
    navigate('/select-specialty');
  };

  const filteredStates = states.filter(state =>
    state.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    state.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <LoadingSpinner text="Loading geographic areas..." />;
  }

  return (
    <div className="select-area fade-in">
      <div className="page-header">
        <div>
          <h1>Select Geographic Area</h1>
          <p className="page-subtitle">
            Choose the state and counties you want to analyze for provider adequacy.
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate('/')}>
          ← Back to Dashboard
        </Button>
      </div>

      {error && <ErrorMessage message={error} onRetry={loadStates} />}

      <div className="selection-grid">
        {/* States Selection */}
        <Card title="1. Select State" subtitle="Choose a state to analyze">
          <SearchBox
            value={searchTerm}
            onChange={setSearchTerm}
            placeholder="Search states..."
            className="area-search"
          />
          
          <div className="state-list">
            {filteredStates.length === 0 ? (
              <p className="no-results">No states found matching "{searchTerm}"</p>
            ) : (
              filteredStates.map(state => (
                <div
                  key={state.id}
                  className={`state-item ${selectedState?.id === state.id ? 'selected' : ''}`}
                  onClick={() => handleStateSelect(state)}
                >
                  <div className="state-info">
                    <div className="state-name">{state.name}</div>
                    <div className="state-meta">
                      {state.code} • {state.counties} counties
                    </div>
                  </div>
                  {selectedState?.id === state.id && (
                    <span className="check-icon">✓</span>
                  )}
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Counties Selection */}
        <Card 
          title="2. Select Counties" 
          subtitle={selectedState ? `Counties in ${selectedState.name}` : 'Select a state first'}
        >
          {!selectedState ? (
            <div className="placeholder-message">
              <span className="placeholder-icon">👈</span>
              <p>Please select a state from the left to view counties.</p>
            </div>
          ) : loadingCounties ? (
            <LoadingSpinner size="sm" text="Loading counties..." />
          ) : counties.length === 0 ? (
            <div className="placeholder-message">
              <span className="placeholder-icon">📍</span>
              <p>No counties available for this state.</p>
            </div>
          ) : (
            <>
              <div className="county-actions">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSelectAllCounties}
                >
                  {selectedCounties.length === counties.length ? 'Deselect All' : 'Select All'}
                </Button>
                <span className="selection-count">
                  {selectedCounties.length} of {counties.length} selected
                </span>
              </div>

              <div className="county-list">
                {counties.map(county => (
                  <div
                    key={county.id}
                    className={`county-item ${selectedCounties.some(c => c.id === county.id) ? 'selected' : ''}`}
                    onClick={() => handleCountyToggle(county)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedCounties.some(c => c.id === county.id)}
                      onChange={() => {}}
                      className="county-checkbox"
                    />
                    <div className="county-info">
                      <div className="county-name">{county.name}</div>
                      <div className="county-meta">
                        Population: {county.population.toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </Card>
      </div>

      {/* Summary and Actions */}
      {selectedState && selectedCounties.length > 0 && (
        <Card className="selection-summary slide-up">
          <div className="summary-content">
            <div className="summary-info">
              <h3>Selection Summary</h3>
              <p>
                <strong>{selectedState.name}</strong> • {selectedCounties.length} {selectedCounties.length === 1 ? 'county' : 'counties'} selected
              </p>
              <div className="selected-counties-list">
                {selectedCounties.map(county => (
                  <span key={county.id} className="badge badge-primary">
                    {county.name}
                  </span>
                ))}
              </div>
            </div>
            <div className="summary-actions">
              <Button variant="primary" size="lg" onClick={handleContinue}>
                Continue to Specialties →
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default SelectArea;
