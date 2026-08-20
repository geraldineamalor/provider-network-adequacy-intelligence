import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import SearchBox from '../components/SearchBox';
import Badge from '../components/Badge';
import apiService from '../services/api';
import './SelectSpecialty.css';

const SelectSpecialty = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [specialties, setSpecialties] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedSpecialties, setSelectedSpecialties] = useState([]);
  const [selectedArea, setSelectedArea] = useState(null);

  useEffect(() => {
    // Check if area was selected
    const state = sessionStorage.getItem('selectedState');
    const counties = sessionStorage.getItem('selectedCounties');
    
    if (!state || !counties) {
      alert('Please select a geographic area first.');
      navigate('/select-area');
      return;
    }
    
    setSelectedArea({
      state: JSON.parse(state),
      counties: JSON.parse(counties),
    });
    
    loadSpecialties();
  }, [navigate]);

  const loadSpecialties = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getSpecialties();
      setSpecialties(response.data);
    } catch (err) {
      setError('Failed to load specialties. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSpecialtyToggle = (specialty) => {
    setSelectedSpecialties(prev => {
      const isSelected = prev.some(s => s.id === specialty.id);
      if (isSelected) {
        return prev.filter(s => s.id !== specialty.id);
      } else {
        return [...prev, specialty];
      }
    });
  };

  const handleCategoryFilter = (category) => {
    setSelectedCategory(category);
  };

  const handleSelectAll = () => {
    const filtered = getFilteredSpecialties();
    if (selectedSpecialties.length === filtered.length) {
      setSelectedSpecialties([]);
    } else {
      setSelectedSpecialties(filtered);
    }
  };

  const handleRunAnalysis = () => {
    if (selectedSpecialties.length === 0) {
      alert('Please select at least one specialty.');
      return;
    }
    
    // Store selections
    sessionStorage.setItem('selectedSpecialties', JSON.stringify(selectedSpecialties));
    
    navigate('/analysis');
  };

  const getFilteredSpecialties = () => {
    let filtered = specialties;
    
    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(s => s.category === selectedCategory);
    }
    
    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(s =>
        s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.category.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    return filtered;
  };

  const categories = [...new Set(specialties.map(s => s.category))];
  const filteredSpecialties = getFilteredSpecialties();

  if (loading) {
    return <LoadingSpinner text="Loading specialties..." />;
  }

  return (
    <div className="select-specialty fade-in">
      <div className="page-header">
        <div>
          <h1>Select Specialties</h1>
          <p className="page-subtitle">
            Choose the medical specialties to analyze for network adequacy.
          </p>
          {selectedArea && (
            <div className="area-context">
              <span className="context-label">Selected Area:</span>
              <Badge variant="primary">
                {selectedArea.state.name} • {selectedArea.counties.length} {selectedArea.counties.length === 1 ? 'county' : 'counties'}
              </Badge>
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
          <Button variant="outline" onClick={() => navigate('/select-area')}>
            ← Change Area
          </Button>
        </div>
      </div>

      {error && <ErrorMessage message={error} onRetry={loadSpecialties} />}

      <div className="specialty-controls">
        <Card>
          <div className="controls-row">
            <SearchBox
              value={searchTerm}
              onChange={setSearchTerm}
              placeholder="Search specialties..."
              className="specialty-search"
            />
            
            <div className="category-filters">
              <button
                className={`filter-btn ${selectedCategory === 'all' ? 'active' : ''}`}
                onClick={() => handleCategoryFilter('all')}
              >
                All
              </button>
              {categories.map(category => (
                <button
                  key={category}
                  className={`filter-btn ${selectedCategory === category ? 'active' : ''}`}
                  onClick={() => handleCategoryFilter(category)}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>
          
          <div className="selection-info">
            <span className="selection-count">
              {selectedSpecialties.length} of {specialties.length} specialties selected
            </span>
            <Button variant="outline" size="sm" onClick={handleSelectAll}>
              {selectedSpecialties.length === filteredSpecialties.length && filteredSpecialties.length > 0 
                ? 'Deselect All' 
                : 'Select All Visible'}
            </Button>
          </div>
        </Card>
      </div>

      <div className="specialty-grid">
        {filteredSpecialties.length === 0 ? (
          <Card>
            <div className="placeholder-message">
              <span className="placeholder-icon">🔍</span>
              <p>No specialties found matching your criteria.</p>
            </div>
          </Card>
        ) : (
          filteredSpecialties.map(specialty => (
            <Card
              key={specialty.id}
              className={`specialty-card ${selectedSpecialties.some(s => s.id === specialty.id) ? 'selected' : ''}`}
              onClick={() => handleSpecialtyToggle(specialty)}
              hoverable
            >
              <div className="specialty-content">
                <div className="specialty-header">
                  <input
                    type="checkbox"
                    checked={selectedSpecialties.some(s => s.id === specialty.id)}
                    onChange={() => {}}
                    className="specialty-checkbox"
                    onClick={(e) => e.stopPropagation()}
                  />
                  <h3 className="specialty-name">{specialty.name}</h3>
                </div>
                
                <div className="specialty-meta">
                  <Badge variant="info">{specialty.category}</Badge>
                </div>
              </div>
              
              {selectedSpecialties.some(s => s.id === specialty.id) && (
                <div className="selected-indicator">
                  <span>✓</span>
                </div>
              )}
            </Card>
          ))
        )}
      </div>

      {/* Action Button */}
      {selectedSpecialties.length > 0 && (
        <Card className="action-summary slide-up">
          <div className="summary-content">
            <div className="summary-info">
              <h3>Ready to Analyze</h3>
              <p>
                {selectedSpecialties.length} {selectedSpecialties.length === 1 ? 'specialty' : 'specialties'} selected 
                • {selectedArea?.state.name} • {selectedArea?.counties.length} {selectedArea?.counties.length === 1 ? 'county' : 'counties'}
              </p>
              <div className="selected-specialties-list">
                {selectedSpecialties.slice(0, 5).map(specialty => (
                  <Badge key={specialty.id} variant="primary">
                    {specialty.name}
                  </Badge>
                ))}
                {selectedSpecialties.length > 5 && (
                  <Badge variant="info">
                    +{selectedSpecialties.length - 5} more
                  </Badge>
                )}
              </div>
            </div>
            <div className="summary-actions">
              <Button variant="primary" size="lg" onClick={handleRunAnalysis}>
                Run Analysis 🚀
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default SelectSpecialty;
