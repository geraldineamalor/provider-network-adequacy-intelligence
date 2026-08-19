import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, MapPin, Users, Activity, AlertTriangle, Grid3x3, Map as MapIcon, Download } from 'lucide-react';
import Button from '../components/Button';
import Badge from '../components/Badge';
import EmptyState from '../components/EmptyState';
import MapView from '../components/MapView';
import './Results.css';

const Results = () => {
  const navigate = useNavigate();
  const [results, setResults] = useState(null);
  const [viewMode, setViewMode] = useState('map'); // 'map' or 'table'
  const [sortBy, setSortBy] = useState('severity');
  const [filterSeverity, setFilterSeverity] = useState('all');

  useEffect(() => {
    const storedResults = sessionStorage.getItem('analysisResults');
    
    if (!storedResults) {
      return;
    }
    
    setResults(JSON.parse(storedResults));
  }, []);

  const getSeverityOrder = (severity) => {
    const order = { 'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3 };
    return order[severity] || 4;
  };

  const getSortedAndFilteredGapAreas = () => {
    if (!results || !results.gapAreas) return [];
    
    let filtered = [...results.gapAreas];
    
    if (filterSeverity !== 'all') {
      filtered = filtered.filter(area => area.severity === filterSeverity);
    }
    
    filtered.sort((a, b) => {
      if (sortBy === 'severity') {
        return getSeverityOrder(a.severity) - getSeverityOrder(b.severity);
      } else if (sortBy === 'gapScore') {
        return b.gapScore - a.gapScore;
      } else if (sortBy === 'deficit') {
        return b.deficit - a.deficit;
      }
      return 0;
    });
    
    return filtered;
  };

  const handleViewRecommendations = () => {
    navigate('/recommendations');
  };

  const handleNewAnalysis = () => {
    navigate('/select-area');
  };

  if (!results) {
    return (
      <div className="results-page">
        <EmptyState
          title="No Analysis Results"
          message="You haven't run any analysis yet. Start by selecting a geographic area and specialties."
          icon="📊"
          action={
            <Button variant="primary" onClick={handleNewAnalysis}>
              Start New Analysis
            </Button>
          }
        />
      </div>
    );
  }

  const gapAreas = getSortedAndFilteredGapAreas();
  const { summary } = results;

  return (
    <div className="results-page fade-in">
      {/* Page Header */}
      <div className="page-header">
        <div className="header-text">
          <h1>Network Analysis Results</h1>
          <p className="header-subtitle">
            Geographic access gap analysis with provider density metrics
          </p>
        </div>
        <div className="header-actions">
          <Button variant="outline" onClick={handleNewAnalysis}>
            New Analysis
          </Button>
          <Button variant="primary" onClick={handleViewRecommendations}>
            View Recommendations <ArrowRight size={18} />
          </Button>
        </div>
      </div>

      {/* Network Adequacy Score - Prominent */}
      <div className="adequacy-score-section">
        <div className="score-primary">
          <div className="score-label">Network Adequacy Score</div>
          <div className="score-value">{summary.accessGapScore}</div>
          <div className="score-status">
            <Badge variant={summary.accessGapScore >= 75 ? 'adequate' : summary.accessGapScore >= 50 ? 'moderate' : 'high'}>
              {summary.accessGapScore >= 75 ? 'ADEQUATE' : summary.accessGapScore >= 50 ? 'MODERATE' : 'NEEDS IMPROVEMENT'}
            </Badge>
          </div>
        </div>
        
        <div className="score-metrics">
          <div className="metric-item">
            <div className="metric-icon">
              <Users size={20} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Total Providers</div>
              <div className="metric-value">{summary.totalProviders.toLocaleString()}</div>
            </div>
          </div>
          
          <div className="metric-item">
            <div className="metric-icon">
              <Activity size={20} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Average Distance</div>
              <div className="metric-value">{summary.averageDistance} mi</div>
            </div>
          </div>
          
          <div className="metric-item critical">
            <div className="metric-icon">
              <AlertTriangle size={20} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Critical Gap Areas</div>
              <div className="metric-value">{summary.criticalAreas}</div>
            </div>
          </div>
        </div>
      </div>

      {/* View Controls */}
      <div className="view-controls">
        <div className="view-left">
          <h2>Geographic Access Gaps</h2>
          <p className="section-subtitle">Identified areas with provider shortages</p>
        </div>
        
        <div className="view-right">
          <div className="view-toggle">
            <button
              className={`toggle-btn ${viewMode === 'map' ? 'active' : ''}`}
              onClick={() => setViewMode('map')}
            >
              <MapIcon size={16} />
              Map View
            </button>
            <button
              className={`toggle-btn ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => setViewMode('table')}
            >
              <Grid3x3 size={16} />
              Table View
            </button>
          </div>
          
          <select
            className="filter-select"
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
          >
            <option value="all">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Moderate</option>
          </select>
          
          <select
            className="filter-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="severity">Sort by Severity</option>
            <option value="gapScore">Sort by Gap Score</option>
            <option value="deficit">Sort by Deficit</option>
          </select>
          
          <Button variant="outline" size="sm">
            <Download size={16} />
            Export
          </Button>
        </div>
      </div>

      {/* Map View - Large and Prominent */}
      {viewMode === 'map' && (
        <div className="map-section">
          <div className="map-container">
            <MapView 
              gapAreas={gapAreas} 
              center={gapAreas[0] ? [gapAreas[0].lat, gapAreas[0].lng] : undefined} 
            />
          </div>
          <div className="map-legend">
            <h4>Severity Legend</h4>
            <div className="legend-items">
              <div className="legend-item">
                <span className="legend-dot critical"></span>
                <span>Critical</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot high"></span>
                <span>High</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot moderate"></span>
                <span>Moderate</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot adequate"></span>
                <span>Adequate</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Table View - Data Dense */}
      {viewMode === 'table' && (
        <div className="table-section">
          {gapAreas.length === 0 ? (
            <EmptyState
              title="No Results"
              message="No gap areas match your current filters."
              icon="🔍"
            />
          ) : (
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Area</th>
                    <th>Specialty</th>
                    <th>Severity</th>
                    <th className="text-right">Gap Score</th>
                    <th className="text-right">Population</th>
                    <th className="text-right">Current Providers</th>
                    <th className="text-right">Provider Deficit</th>
                    <th>Analysis</th>
                  </tr>
                </thead>
                <tbody>
                  {gapAreas.map((area) => (
                    <tr key={area.id}>
                      <td>
                        <div className="cell-primary">
                          <MapPin size={14} />
                          {area.county}, {area.state}
                        </div>
                      </td>
                      <td>{area.specialty}</td>
                      <td>
                        <Badge variant={area.severity.toLowerCase()}>
                          {area.severity}
                        </Badge>
                      </td>
                      <td className="text-right">
                        <span className="metric-highlight">{area.gapScore}</span>
                      </td>
                      <td className="text-right">{area.population.toLocaleString()}</td>
                      <td className="text-right">{area.currentProviders}</td>
                      <td className="text-right">
                        <span className="deficit-value">-{area.deficit}</span>
                      </td>
                      <td>
                        <button className="link-button">View Details</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Gap Area Details - Only show key information */}
      {viewMode === 'table' && gapAreas.length > 0 && (
        <div className="details-section">
          <h3>Why These Areas?</h3>
          <div className="details-grid">
            {gapAreas.slice(0, 3).map((area) => (
              <div key={area.id} className="detail-card">
                <div className="detail-header">
                  <Badge variant={area.severity.toLowerCase()}>{area.severity}</Badge>
                  <span className="detail-location">{area.county}, {area.state}</span>
                </div>
                <div className="detail-specialty">{area.specialty}</div>
                <p className="detail-reason">{area.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Footer */}
      <div className="action-footer">
        <div className="action-content">
          <div className="action-text">
            <h3>Review AI-Powered Recommendations</h3>
            <p>Based on this analysis, we've generated prioritized provider recruitment recommendations</p>
          </div>
          <Button variant="primary" size="lg" onClick={handleViewRecommendations}>
            View Recommendations <ArrowRight size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Results;
