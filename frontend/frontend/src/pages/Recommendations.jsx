import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin, Users, TrendingUp, AlertTriangle, Download, ChevronRight } from 'lucide-react';
import Button from '../components/Button';
import Badge from '../components/Badge';
import EmptyState from '../components/EmptyState';
import './Recommendations.css';

const Recommendations = () => {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [filterImpact, setFilterImpact] = useState('all');

  useEffect(() => {
    const storedResults = sessionStorage.getItem('analysisResults');
    
    if (!storedResults) {
      return;
    }
    
    const results = JSON.parse(storedResults);
    setRecommendations(results.recommendations || []);
  }, []);

  const handleNewAnalysis = () => {
    navigate('/select-area');
  };

  const getFilteredRecommendations = () => {
    if (filterImpact === 'all') return recommendations;
    return recommendations.filter(r => r.estimatedImpact === filterImpact);
  };

  const filteredRecommendations = getFilteredRecommendations();

  if (recommendations.length === 0) {
    return (
      <div className="recommendations-page">
        <EmptyState
          title="No Recommendations Available"
          message="Run an analysis first to get AI-powered provider recruitment recommendations."
          icon="💡"
          action={
            <Button variant="primary" onClick={handleNewAnalysis}>
              Start New Analysis
            </Button>
          }
        />
      </div>
    );
  }

  const totalProvidersNeeded = recommendations.reduce((sum, r) => sum + r.providersNeeded, 0);

  return (
    <div className="recommendations-page fade-in">
      {/* Page Header */}
      <div className="page-header">
        <div className="header-text">
          <h1>Provider Recruitment Recommendations</h1>
          <p className="header-subtitle">
            Evidence-based strategic recommendations for addressing network gaps
          </p>
        </div>
        <div className="header-actions">
          <Button variant="outline" onClick={() => navigate('/results')}>
            <ArrowLeft size={18} />
            Back to Results
          </Button>
          <Button variant="outline">
            <Download size={18} />
            Export Report
          </Button>
          <Button variant="primary" onClick={handleNewAnalysis}>
            New Analysis
          </Button>
        </div>
      </div>

      {/* Summary Section */}
      <div className="summary-section">
        <div className="summary-card">
          <div className="summary-icon">
            <TrendingUp size={24} />
          </div>
          <div className="summary-content">
            <div className="summary-label">Strategic Recruitment Plan</div>
            <div className="summary-text">
              Based on network analysis, we've identified <strong>{recommendations.length} priority areas</strong> for 
              provider recruitment with an estimated total need of <strong>{totalProvidersNeeded} providers</strong> 
              to achieve adequate network coverage.
            </div>
          </div>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="filter-bar">
        <div className="filter-left">
          <h2>Priority Recommendations</h2>
          <p className="filter-subtitle">Ordered by severity and population impact</p>
        </div>
        <div className="filter-right">
          <select
            className="filter-select"
            value={filterImpact}
            onChange={(e) => setFilterImpact(e.target.value)}
          >
            <option value="all">All Impact Levels</option>
            <option value="High">High Impact</option>
            <option value="Medium-High">Medium-High Impact</option>
            <option value="Medium">Medium Impact</option>
          </select>
          <span className="result-count">
            {filteredRecommendations.length} of {recommendations.length} recommendations
          </span>
        </div>
      </div>

      {/* Recommendations List */}
      <div className="recommendations-list">
        {filteredRecommendations.map((rec) => (
          <div key={rec.id} className="recommendation-item">
            {/* Header */}
            <div className="rec-header">
              <div className="rec-priority">
                <div className="priority-number">#{rec.priority}</div>
                <div className="priority-label">Priority</div>
              </div>
              
              <div className="rec-title">
                <div className="rec-location">
                  <MapPin size={18} />
                  {rec.county}, {rec.state}
                </div>
                <div className="rec-specialty">{rec.specialty}</div>
              </div>
              
              <Badge variant={rec.estimatedImpact === 'High' ? 'critical' : rec.estimatedImpact === 'Medium-High' ? 'high' : 'moderate'}>
                {rec.estimatedImpact} Impact
              </Badge>
            </div>

            {/* Key Metrics */}
            <div className="rec-metrics">
              <div className="metric-box">
                <div className="metric-icon">
                  <Users size={20} />
                </div>
                <div className="metric-data">
                  <div className="metric-value">{rec.providersNeeded}</div>
                  <div className="metric-label">Providers Needed</div>
                </div>
              </div>
              
              <div className="metric-box">
                <div className="metric-icon">
                  <AlertTriangle size={20} />
                </div>
                <div className="metric-data">
                  <div className="metric-value">
                    <Badge variant={rec.estimatedImpact === 'High' ? 'critical' : 'high'}>
                      {rec.estimatedImpact === 'High' ? 'Critical' : 'High'}
                    </Badge>
                  </div>
                  <div className="metric-label">Gap Severity</div>
                </div>
              </div>
            </div>

            {/* Strategic Rationale */}
            <div className="rec-rationale">
              <h4>Why This Area?</h4>
              <p>{rec.reasoning}</p>
            </div>

            {/* Target Areas */}
            {rec.targetAreas && rec.targetAreas.length > 0 && (
              <div className="rec-details">
                <h4>Geographic Focus Areas</h4>
                <div className="target-areas">
                  {rec.targetAreas.map((area, idx) => (
                    <span key={idx} className="area-tag">
                      <MapPin size={14} />
                      {area}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Recommended Actions */}
            <div className="rec-actions-section">
              <h4>Recommended Actions</h4>
              <ul className="action-list">
                <li>Prioritize recruitment efforts in identified target areas</li>
                <li>Assess local provider market and competition</li>
                <li>Develop competitive compensation packages</li>
                <li>Establish partnerships with local healthcare facilities</li>
              </ul>
            </div>

            {/* Expected Impact */}
            <div className="rec-footer">
              <div className="footer-impact">
                <strong>Expected Impact:</strong> Addressing this gap will improve network adequacy 
                for approximately {(rec.providersNeeded * 1000).toLocaleString()} potential patients
              </div>
              <Button variant="primary" size="sm">
                View Full Analysis <ChevronRight size={16} />
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Next Steps Section */}
      <div className="next-steps-section">
        <h2>Implementation Guidance</h2>
        <p className="section-subtitle">Recommended approach for addressing identified gaps</p>
        
        <div className="guidance-grid">
          <div className="guidance-item">
            <div className="guidance-number">1</div>
            <div className="guidance-content">
              <h3>Review Priority Rankings</h3>
              <p>Focus on critical and high-severity areas first. Priority rankings consider population impact, severity level, and geographic accessibility.</p>
            </div>
          </div>
          
          <div className="guidance-item">
            <div className="guidance-number">2</div>
            <div className="guidance-content">
              <h3>Assess Resource Allocation</h3>
              <p>Evaluate recruitment budgets and timelines. Consider phased implementation starting with highest-priority areas.</p>
            </div>
          </div>
          
          <div className="guidance-item">
            <div className="guidance-number">3</div>
            <div className="guidance-content">
              <h3>Engage Recruitment Team</h3>
              <p>Share analysis results with provider recruitment specialists. Coordinate outreach to target specialties in identified geographic areas.</p>
            </div>
          </div>
          
          <div className="guidance-item">
            <div className="guidance-number">4</div>
            <div className="guidance-content">
              <h3>Monitor and Re-analyze</h3>
              <p>Track recruitment progress and periodically re-run network adequacy analysis to measure improvements and identify emerging gaps.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Recommendations;
