import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Activity, MapPin, Stethoscope, TrendingUp, AlertCircle } from 'lucide-react';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import apiService from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalStates: 0,
    totalSpecialties: 0,
    recentAnalyses: 0,
    criticalGaps: 0,
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [areasRes, specialtiesRes] = await Promise.all([
        apiService.getAreas(),
        apiService.getSpecialties(),
      ]);
      
      setStats({
        totalStates: areasRes.data.length,
        totalSpecialties: specialtiesRes.data.length,
        recentAnalyses: 12,
        criticalGaps: 5,
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const startNewAnalysis = () => {
    navigate('/select-area');
  };

  if (loading) {
    return <LoadingSpinner text="Loading dashboard..." />;
  }

  return (
    <div className="dashboard">
      {/* Page Header */}
      <div className="dashboard-header">
        <div className="header-text">
          <h1>Provider Network Adequacy Analysis</h1>
          <p className="header-subtitle">
            Identify access gaps, analyze provider distribution, and generate data-driven recommendations 
            for strategic network expansion.
          </p>
        </div>
        <div className="header-actions">
          <Button variant="primary" size="lg" onClick={startNewAnalysis}>
            New Analysis <ArrowRight size={18} />
          </Button>
        </div>
      </div>

      {/* Quick Stats Bar */}
      <div className="stats-bar">
        <div className="stat-item">
          <div className="stat-icon">
            <MapPin size={20} />
          </div>
          <div className="stat-content">
            <div className="stat-label">Geographic Areas</div>
            <div className="stat-value">{stats.totalStates}</div>
          </div>
        </div>
        
        <div className="stat-divider"></div>
        
        <div className="stat-item">
          <div className="stat-icon">
            <Stethoscope size={20} />
          </div>
          <div className="stat-content">
            <div className="stat-label">Medical Specialties</div>
            <div className="stat-value">{stats.totalSpecialties}</div>
          </div>
        </div>
        
        <div className="stat-divider"></div>
        
        <div className="stat-item">
          <div className="stat-icon">
            <Activity size={20} />
          </div>
          <div className="stat-content">
            <div className="stat-label">Recent Analyses</div>
            <div className="stat-value">{stats.recentAnalyses}</div>
          </div>
        </div>
        
        <div className="stat-divider"></div>
        
        <div className="stat-item highlight">
          <div className="stat-icon">
            <AlertCircle size={20} />
          </div>
          <div className="stat-content">
            <div className="stat-label">Critical Gaps Identified</div>
            <div className="stat-value">{stats.criticalGaps}</div>
          </div>
        </div>
      </div>

      {/* Main Content Sections */}
      <div className="dashboard-content">
        {/* Getting Started Section */}
        <section className="content-section">
          <div className="section-header">
            <h2>Getting Started</h2>
            <p>Run a network adequacy analysis in three steps</p>
          </div>
          
          <div className="process-steps">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3>Select Geographic Area</h3>
                <p>Choose states and specific counties to analyze for provider network adequacy</p>
              </div>
            </div>
            
            <div className="step-arrow">
              <ArrowRight size={20} />
            </div>
            
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3>Choose Specialties</h3>
                <p>Select medical specialties to focus your network analysis</p>
              </div>
            </div>
            
            <div className="step-arrow">
              <ArrowRight size={20} />
            </div>
            
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3>Review Results</h3>
                <p>Analyze gaps, view geographic distribution, and review AI-powered recommendations</p>
              </div>
            </div>
          </div>
          
          <div className="section-action">
            <Button variant="primary" onClick={startNewAnalysis}>
              Start Network Analysis
            </Button>
          </div>
        </section>

        {/* Features Grid */}
        <section className="content-section">
          <div className="section-header">
            <h2>Analysis Capabilities</h2>
            <p>Comprehensive network adequacy assessment tools</p>
          </div>
          
          <div className="features-grid">
            <div className="feature-box">
              <div className="feature-icon">
                <MapPin size={24} />
              </div>
              <h3>Geographic Analysis</h3>
              <p>Visualize provider distribution across states, counties, and ZIP codes with interactive mapping</p>
            </div>
            
            <div className="feature-box">
              <div className="feature-icon">
                <Activity size={24} />
              </div>
              <h3>Provider Density Metrics</h3>
              <p>Calculate providers per 10,000 population and identify areas below adequacy thresholds</p>
            </div>
            
            <div className="feature-box">
              <div className="feature-icon">
                <TrendingUp size={24} />
              </div>
              <h3>Gap Scoring</h3>
              <p>Machine learning models analyze multiple factors to score network adequacy gaps</p>
            </div>
            
            <div className="feature-box">
              <div className="feature-icon">
                <Stethoscope size={24} />
              </div>
              <h3>Specialty Coverage</h3>
              <p>Assess availability of specialists across primary care, specialty care, and mental health</p>
            </div>
          </div>
        </section>

        {/* Info Box */}
        <div className="info-box">
          <div className="info-icon">
            <AlertCircle size={20} />
          </div>
          <div className="info-content">
            <strong>About Network Adequacy Analysis</strong>
            <p>
              This platform analyzes provider network data to identify geographic areas with insufficient 
              healthcare provider coverage. Analysis includes provider counts, population density, 
              specialty distribution, and geographic accessibility metrics to generate evidence-based 
              recommendations for network expansion.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
