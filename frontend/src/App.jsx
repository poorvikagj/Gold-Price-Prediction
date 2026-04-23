import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Pages
import Dashboard from './components/Dashboard';
import Predictions from './components/Predictions';
import FeatureAnalysis from './components/FeatureAnalysis';
import Performance from './components/Performance';
import About from './components/About';

// Navigation component
function Navigation({ currentPage, onPageChange, isDarkMode, onDarkModeToggle }) {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <h1>Gold Price Intelligence</h1>
          <p className="tagline">Forecasting Workspace for Economic Signals</p>
        </div>
        
        <ul className="nav-links">
          <li><button 
            className={currentPage === 'dashboard' ? 'active' : ''} 
            onClick={() => onPageChange('dashboard')}
          >Dashboard</button></li>
          <li><button 
            className={currentPage === 'predictions' ? 'active' : ''} 
            onClick={() => onPageChange('predictions')}
          >Predictions</button></li>
          <li><button 
            className={currentPage === 'features' ? 'active' : ''} 
            onClick={() => onPageChange('features')}
          >Feature Analysis</button></li>
          <li><button 
            className={currentPage === 'performance' ? 'active' : ''} 
            onClick={() => onPageChange('performance')}
          >Performance</button></li>
          <li><button 
            className={currentPage === 'about' ? 'active' : ''} 
            onClick={() => onPageChange('about')}
          >About</button></li>
        </ul>
        
        <div className="navbar-actions ">
          <button className="dark-mode-toggle" onClick={onDarkModeToggle}>
            {isDarkMode ? '☀️' : '🌙'}
          </button>
        </div>
      </div>
    </nav>
  );
}

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize dark mode
  useEffect(() => {
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode !== null) {
      setIsDarkMode(JSON.parse(savedDarkMode));
    }
  }, []);

  // Apply dark mode class
  useEffect(() => {
    if (isDarkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
  }, [isDarkMode]);

  // Fetch models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        setLoading(true);
        const response = await axios.get('http://localhost:5000/api/models');
        if (response.data.success) {
          setModels(response.data.data);
        }
      } catch (err) {
        setError('Failed to load models. Make sure the backend is running on http://localhost:5000');
        console.error('API Error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, []);

  if (loading) {
    return (
      <div className="app">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading Gold Price Prediction App...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <Navigation 
          currentPage={currentPage} 
          onPageChange={setCurrentPage}
          isDarkMode={isDarkMode}
          onDarkModeToggle={() => setIsDarkMode(!isDarkMode)}
        />
        <div className="error-container">
          <h2>Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <Navigation 
        currentPage={currentPage} 
        onPageChange={setCurrentPage}
        isDarkMode={isDarkMode}
        onDarkModeToggle={() => setIsDarkMode(!isDarkMode)}
      />
      
      <main className="main-content">
        {currentPage === 'dashboard' && <Dashboard models={models} />}
        {currentPage === 'predictions' && <Predictions models={models} />}
        {currentPage === 'features' && <FeatureAnalysis />}
        {currentPage === 'performance' && <Performance models={models} />}
        {currentPage === 'about' && <About />}
      </main>

      <footer className="footer">
        <p>&copy; 2026 Gold Price Intelligence | Built for Applied ML Analysis</p>
      </footer>
    </div>
  );
}

export default App;
