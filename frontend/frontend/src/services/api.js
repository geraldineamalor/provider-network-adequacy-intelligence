import axios from 'axios';

// Base API URL - Updated to match BE-1 contract: /api/v1
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Mock data for development when backend is not available
const USE_MOCK_DATA = true; // Set to false when backend is ready

/**
 * API CONTRACT ALIGNMENT WITH BE-1
 * 
 * Base URL: http://localhost:8000/api/v1
 * 
 * Analysis Endpoint: POST /api/v1/analysis/
 * 
 * Request Payload Format:
 * {
 *   "state": "CA",                        // State code as string
 *   "counties": ["Los Angeles", "..."],    // County NAMES (not IDs)
 *   "specialties": ["Cardiology", "..."]   // Specialty NAMES (not IDs)
 * }
 * 
 * Frontend keeps IDs internally for UI selection, but sends NAMES to backend.
 * 
 * GEOGRAPHIC GRANULARITY:
 * - ML-1 operates at ZIP/ZCTA level (16,934 rows)
 * - Frontend uses County for better UX
 * - Backend will need to aggregate ZIP → County internally
 * 
 * Current Status:
 * - Mock data enabled (USE_MOCK_DATA = true)
 * - API service layer prepared for BE-1 integration
 * - UI unchanged, only API contract aligned
 */

// Mock Data
const mockStates = [
  { id: 1, name: 'California', code: 'CA', counties: 58 },
  { id: 2, name: 'Texas', code: 'TX', counties: 254 },
  { id: 3, name: 'Florida', code: 'FL', counties: 67 },
  { id: 4, name: 'New York', code: 'NY', counties: 62 },
  { id: 5, name: 'Pennsylvania', code: 'PA', counties: 67 },
  { id: 6, name: 'Illinois', code: 'IL', counties: 102 },
  { id: 7, name: 'Ohio', code: 'OH', counties: 88 },
  { id: 8, name: 'Georgia', code: 'GA', counties: 159 },
  { id: 9, name: 'North Carolina', code: 'NC', counties: 100 },
  { id: 10, name: 'Michigan', code: 'MI', counties: 83 },
];

// Mock Counties
const mockCounties = {
  'CA': [
    { id: 1, name: 'Los Angeles', state: 'CA', population: 10000000, lat: 34.0522, lng: -118.2437 },
    { id: 2, name: 'San Diego', state: 'CA', population: 3300000, lat: 32.7157, lng: -117.1611 },
    { id: 3, name: 'Orange', state: 'CA', population: 3200000, lat: 33.7175, lng: -117.8311 },
    { id: 4, name: 'Riverside', state: 'CA', population: 2470000, lat: 33.9533, lng: -117.3962 },
    { id: 5, name: 'San Bernardino', state: 'CA', population: 2180000, lat: 34.1083, lng: -117.2898 },
  ],
  'TX': [
    { id: 11, name: 'Harris', state: 'TX', population: 4700000, lat: 29.7604, lng: -95.3698 },
    { id: 12, name: 'Dallas', state: 'TX', population: 2630000, lat: 32.7767, lng: -96.7970 },
    { id: 13, name: 'Tarrant', state: 'TX', population: 2100000, lat: 32.7555, lng: -97.3308 },
    { id: 14, name: 'Bexar', state: 'TX', population: 2000000, lat: 29.4241, lng: -98.4936 },
    { id: 15, name: 'Travis', state: 'TX', population: 1270000, lat: 30.2672, lng: -97.7431 },
  ],
  'FL': [
    { id: 21, name: 'Miami-Dade', state: 'FL', population: 2700000, lat: 25.7617, lng: -80.1918 },
    { id: 22, name: 'Broward', state: 'FL', population: 1950000, lat: 26.1224, lng: -80.1373 },
    { id: 23, name: 'Palm Beach', state: 'FL', population: 1500000, lat: 26.7153, lng: -80.0534 },
    { id: 24, name: 'Hillsborough', state: 'FL', population: 1460000, lat: 27.9506, lng: -82.4572 },
    { id: 25, name: 'Orange', state: 'FL', population: 1390000, lat: 28.5383, lng: -81.3792 },
  ],
};

// Mock Specialties - Keeping ID + name + category for frontend UI
// Category is frontend-only, not sent to backend
const mockSpecialties = [
  { id: 1, name: 'Cardiology', category: 'Specialty Care' },
  { id: 2, name: 'Pediatrics', category: 'Primary Care' },
  { id: 3, name: 'Orthopedics', category: 'Specialty Care' },
  { id: 4, name: 'Dermatology', category: 'Specialty Care' },
  { id: 5, name: 'Family Medicine', category: 'Primary Care' },
  { id: 6, name: 'Psychiatry', category: 'Mental Health' },
  { id: 7, name: 'Neurology', category: 'Specialty Care' },
  { id: 8, name: 'Oncology', category: 'Specialty Care' },
  { id: 9, name: 'Internal Medicine', category: 'Primary Care' },
  { id: 10, name: 'Emergency Medicine', category: 'Emergency Care' },
  { id: 11, name: 'Obstetrics & Gynecology', category: 'Specialty Care' },
  { id: 12, name: 'Endocrinology', category: 'Specialty Care' },
];

const mockProviders = [
  { id: 1, name: 'Dr. Sarah Johnson', specialty: 'Cardiology', location: 'Los Angeles, CA', lat: 34.0522, lng: -118.2437, patients: 1200, availability: 'Limited' },
  { id: 2, name: 'Dr. Michael Chen', specialty: 'Pediatrics', location: 'Los Angeles, CA', lat: 34.0622, lng: -118.2537, patients: 800, availability: 'Available' },
  { id: 3, name: 'Dr. Emily Rodriguez', specialty: 'Orthopedics', location: 'San Diego, CA', lat: 32.7157, lng: -117.1611, patients: 950, availability: 'Limited' },
  { id: 4, name: 'Dr. David Kim', specialty: 'Dermatology', location: 'Orange, CA', lat: 33.7175, lng: -117.8311, patients: 600, availability: 'Available' },
  { id: 5, name: 'Dr. Jennifer Martinez', specialty: 'Family Medicine', location: 'Riverside, CA', lat: 33.9533, lng: -117.3962, patients: 1500, availability: 'Full' },
];

// Mock Analysis Results - Aligned with ML-1 Backend Capabilities
// Based on ML-1 dataset: ZIP-level aggregation, provider counts, population, density metrics
const mockAnalysisResults = {
  summary: {
    totalProviders: 1247,
    averageDistance: 8.3, // TODO: Remove when backend ready - not in ML-1 dataset
    accessGapScore: 67, // Network adequacy score (0-100)
    criticalAreas: 5,
  },
  gapAreas: [
    {
      id: 1,
      county: 'Los Angeles',
      state: 'CA',
      specialty: 'Cardiology',
      gapScore: 78, // ML model output
      severity: 'High',
      population: 10000000,
      currentProviders: 45, // From ML-1: provider_count
      deficit: 75, // Calculated: target - current
      reason: 'High population density with low provider-to-population ratio. Analysis shows 0.45 providers per 10,000 population, below adequacy threshold.',
      lat: 34.0522,
      lng: -118.2437,
    },
    {
      id: 2,
      county: 'San Diego',
      state: 'CA',
      specialty: 'Psychiatry',
      gapScore: 85,
      severity: 'Critical',
      population: 3300000,
      currentProviders: 12,
      deficit: 53,
      reason: 'Critical shortage in mental health services with 0.36 providers per 10,000 population. Significantly below national adequacy standards.',
      lat: 32.7157,
      lng: -117.1611,
    },
    {
      id: 3,
      county: 'Riverside',
      state: 'CA',
      specialty: 'Oncology',
      gapScore: 72,
      severity: 'High',
      population: 2470000,
      currentProviders: 8,
      deficit: 27,
      reason: 'Rural area with 0.32 providers per 10,000 population. Geographic distribution analysis shows access gap for growing population.',
      lat: 33.9533,
      lng: -117.3962,
    },
    {
      id: 4,
      county: 'Orange',
      state: 'CA',
      specialty: 'Neurology',
      gapScore: 65,
      severity: 'Medium',
      population: 3200000,
      currentProviders: 38,
      deficit: 37,
      reason: 'Provider density of 1.19 per 10,000 population indicates moderate gap. Network adequacy model identifies need for additional specialists.',
      lat: 33.7175,
      lng: -117.8311,
    },
    {
      id: 5,
      county: 'San Bernardino',
      state: 'CA',
      specialty: 'Family Medicine',
      gapScore: 58,
      severity: 'Medium',
      population: 2180000,
      currentProviders: 92,
      deficit: 53,
      reason: 'Primary care density of 4.22 per 10,000 population below target threshold. Growing population increases adequacy gap.',
      lat: 34.1083,
      lng: -117.2898,
    },
  ],
  recommendations: [
    {
      id: 1,
      priority: 1,
      county: 'San Diego',
      state: 'CA',
      specialty: 'Psychiatry',
      providersNeeded: 53,
      estimatedImpact: 'High', // Based on population impact and severity
      reasoning: 'Critical mental health shortage with 0.36 providers per 10,000 population. Highest gap score (85) and affects 3.3M residents. Priority 1 based on severity and population impact.',
      targetAreas: ['Downtown', 'La Jolla', 'Chula Vista'],
      lat: 32.7157,
      lng: -117.1611,
    },
    {
      id: 2,
      priority: 2,
      county: 'Los Angeles',
      state: 'CA',
      specialty: 'Cardiology',
      providersNeeded: 75,
      estimatedImpact: 'High',
      reasoning: 'Large population (10M) with cardiovascular specialist shortage. Gap score of 78 indicates high priority. Provider density significantly below adequacy threshold.',
      targetAreas: ['South LA', 'San Fernando Valley', 'Long Beach'],
      lat: 34.0522,
      lng: -118.2437,
    },
    {
      id: 3,
      priority: 3,
      county: 'Riverside',
      state: 'CA',
      specialty: 'Oncology',
      providersNeeded: 27,
      estimatedImpact: 'Medium-High',
      reasoning: 'Cancer care gap in growing suburban/rural area. Gap score 72. Strategic location for regional coverage improvement.',
      targetAreas: ['Riverside', 'Moreno Valley', 'Corona'],
      lat: 33.9533,
      lng: -117.3962,
    },
    {
      id: 4,
      priority: 4,
      county: 'Orange',
      state: 'CA',
      specialty: 'Neurology',
      providersNeeded: 37,
      estimatedImpact: 'Medium',
      reasoning: 'Moderate adequacy gap (score: 65) in high-population county. Provider density analysis indicates need for specialist expansion.',
      targetAreas: ['Anaheim', 'Irvine', 'Santa Ana'],
      lat: 33.7175,
      lng: -117.8311,
    },
    {
      id: 5,
      priority: 5,
      county: 'San Bernardino',
      state: 'CA',
      specialty: 'Family Medicine',
      providersNeeded: 53,
      estimatedImpact: 'Medium',
      reasoning: 'Primary care gap with 4.22 providers per 10,000 population. Gap score 58 indicates moderate priority for network adequacy improvement.',
      targetAreas: ['San Bernardino', 'Fontana', 'Rancho Cucamonga'],
      lat: 34.1083,
      lng: -117.2898,
    },
  ],
};

// Simulate API delay
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// API Service Functions
export const apiService = {
  // Get all states/geographic areas
  getAreas: async () => {
    if (USE_MOCK_DATA) {
      await delay(500);
      return { data: mockStates };
    }
    const response = await api.get('/areas');
    return response;
  },

  // Get counties for a specific state
  getCounties: async (stateCode) => {
    if (USE_MOCK_DATA) {
      await delay(300);
      return { data: mockCounties[stateCode] || [] };
    }
    const response = await api.get(`/areas/${stateCode}/counties`);
    return response;
  },

  // Get all specialties
  getSpecialties: async () => {
    if (USE_MOCK_DATA) {
      await delay(400);
      return { data: mockSpecialties };
    }
    const response = await api.get('/specialties');
    return response;
  },

  // Get providers (optional filters)
  getProviders: async (filters = {}) => {
    if (USE_MOCK_DATA) {
      await delay(600);
      let filtered = [...mockProviders];
      
      if (filters.specialty) {
        filtered = filtered.filter(p => p.specialty === filters.specialty);
      }
      if (filters.location) {
        filtered = filtered.filter(p => p.location.includes(filters.location));
      }
      
      return { data: filtered };
    }
    const response = await api.get('/providers', { params: filters });
    return response;
  },

  // Submit analysis request
  // BE-1 Contract: POST /api/v1/analysis/
  // Payload: { state: "CA", counties: ["Los Angeles"], specialties: ["Cardiology"] }
  submitAnalysis: async (payload) => {
    if (USE_MOCK_DATA) {
      await delay(2000); // Simulate processing time
      
      // Log the payload that would be sent to backend (for testing)
      console.log('[API] Analysis payload prepared for BE-1:', JSON.stringify(payload, null, 2));
      
      return { 
        data: {
          analysisId: `analysis_${Date.now()}`,
          status: 'completed',
          results: mockAnalysisResults,
        }
      };
    }
    
    // Real backend call to /api/v1/analysis/
    const response = await api.post('/analysis/', payload);
    return response;
  },

  // Get analysis results
  getAnalysisResults: async (analysisId) => {
    if (USE_MOCK_DATA) {
      await delay(500);
      return { data: mockAnalysisResults };
    }
    const response = await api.get(`/analysis/${analysisId}`);
    return response;
  },

  // Get recommendations
  getRecommendations: async (filters = {}) => {
    if (USE_MOCK_DATA) {
      await delay(400);
      return { data: mockAnalysisResults.recommendations };
    }
    const response = await api.get('/recommendations', { params: filters });
    return response;
  },
};

export default apiService;
