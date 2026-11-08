import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import LandingPage from './pages/LandingPage';
import IntelligenceHub from './pages/IntelligenceHub';
import LiveCenter from './pages/LiveCenter';
import PlayerComparePage from './pages/PlayerComparePage';
import HistoricalVault from './pages/HistoricalVault';

export default function App() {
  return (
    <Router>
      <div className="flex flex-col min-h-screen bg-[#050505] text-white">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/chat" element={<IntelligenceHub />} />
            <Route path="/live" element={<LiveCenter />} />
            <Route path="/compare" element={<PlayerComparePage />} />
            <Route path="/vault" element={<HistoricalVault />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}
