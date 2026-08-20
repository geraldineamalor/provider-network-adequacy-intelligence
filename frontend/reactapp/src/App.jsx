import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import SelectArea from './pages/SelectArea';
import SelectSpecialty from './pages/SelectSpecialty';
import Analysis from './pages/Analysis';
import Results from './pages/Results';
import Recommendations from './pages/Recommendations';
import './App.css';

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/select-area" element={<SelectArea />} />
          <Route path="/select-specialty" element={<SelectSpecialty />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/results" element={<Results />} />
          <Route path="/recommendations" element={<Recommendations />} />
        </Routes>
      </MainLayout>
    </Router>
  );
}

export default App;
