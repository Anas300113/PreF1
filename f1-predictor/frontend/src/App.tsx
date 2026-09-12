import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { NextRace } from './pages/NextRace';
import { RaceDetail } from './pages/RaceDetail';
import { Backtesting } from './pages/Backtesting';
import { ModelInfo } from './pages/ModelInfo';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<NextRace />} />
          <Route path="/races/:raceId" element={<RaceDetail />} />
          <Route path="/backtesting" element={<Backtesting />} />
          <Route path="/models" element={<ModelInfo />} />
        </Routes>
      </main>
    </div>
  );
};
