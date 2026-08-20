import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';
import './Analysis.css';
import apiService from '../services/api';

const Analysis = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  
  const steps = [
    { label: 'Loading provider data', description: 'Retrieving network provider information' },
    { label: 'Preparing geographic features', description: 'Processing location and population data' },
    { label: 'Calculating network adequacy', description: 'Computing provider density metrics' },
    { label: 'Running gap analysis', description: 'Identifying underserved areas' },
    { label: 'Generating recommendations', description: 'Creating strategic insights' },
  ];

  const runAnalysis = useCallback(async (state, counties, specialties) => {
    try {
      // Progress through steps
      for (let i = 0; i < steps.length; i++) {
        setCurrentStep(i);
        // Wait for each step (simulate processing)
        await new Promise(resolve => setTimeout(resolve, 1500));
      }
      
      // When complete, mark final step
      setCurrentStep(steps.length);
      
      // Prepare payload for BE-1: Send NAMES not IDs
      // BE-1 Contract: { state: "CA", counties: ["Los Angeles"], specialties: ["Cardiology"] }
      const payload = {
        state: state.code,                        // State code (e.g., "CA")
        counties: counties.map(c => c.name),      // County NAMES
        specialties: specialties.map(s => s.name) // Specialty NAMES
      };
      
      const response = await apiService.submitAnalysis(payload);
      
      // Store results for Results and Recommendations pages
      // The API returns { data: { analysisId, status, results } }
      sessionStorage.setItem('analysisResults', JSON.stringify(response.data.results));
      
      // Wait a moment before navigation
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Navigate to results
      navigate('/results');
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Analysis failed. Please try again.');
      navigate('/select-specialty');
    }
  }, [navigate, steps.length]);

  useEffect(() => {
    // Check if selections were made
    const state = sessionStorage.getItem('selectedState');
    const counties = sessionStorage.getItem('selectedCounties');
    const specialties = sessionStorage.getItem('selectedSpecialties');
    
    if (!state || !counties || !specialties) {
      alert('Please complete the selection process first.');
      navigate('/select-area');
      return;
    }
    
    runAnalysis(JSON.parse(state), JSON.parse(counties), JSON.parse(specialties));
  }, [navigate, runAnalysis]);

  const getStepStatus = (index) => {
    if (index < currentStep) return 'completed';
    if (index === currentStep) return 'active';
    return 'pending';
  };

  return (
    <div className="analysis-page fade-in">
      <div className="analysis-container">
        <div className="analysis-card">
          {/* Header */}
          <div className="analysis-header">
            <div className="analysis-icon-wrapper">
              <Loader2 className="analysis-icon-spin" size={48} />
            </div>
            <h1>Running Network Analysis</h1>
            <p className="analysis-subtitle">
              Analyzing provider network data and identifying access gaps
            </p>
          </div>

          {/* Progress Steps */}
          <div className="steps-container">
            {steps.map((step, index) => {
              const status = getStepStatus(index);
              
              return (
                <div key={index} className={`step-row ${status}`}>
                  <div className="step-indicator">
                    {status === 'completed' && (
                      <CheckCircle2 size={24} className="step-icon completed" />
                    )}
                    {status === 'active' && (
                      <Loader2 size={24} className="step-icon active spin" />
                    )}
                    {status === 'pending' && (
                      <Circle size={24} className="step-icon pending" />
                    )}
                  </div>
                  
                  <div className="step-content">
                    <div className="step-label">{step.label}</div>
                    <div className="step-description">{step.description}</div>
                  </div>
                  
                  {status === 'completed' && (
                    <div className="step-status">
                      <span className="status-badge completed">Completed</span>
                    </div>
                  )}
                  {status === 'active' && (
                    <div className="step-status">
                      <span className="status-badge active">In progress...</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Info Box */}
          <div className="analysis-info">
            <h4>What's Happening?</h4>
            <p>
              The system is processing provider distribution data, calculating density metrics, 
              and identifying geographic areas with insufficient healthcare provider coverage. 
              Machine learning models analyze multiple factors including population density, 
              provider counts, and specialty distribution to generate network adequacy scores.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analysis;
