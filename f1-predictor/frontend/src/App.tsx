import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { NavigationRail } from './components/NavigationRail';
import { Home } from './pages/Home';
import { Race } from './pages/Race';
import { Prediction } from './pages/Prediction';
import { Simulation } from './pages/Simulation';
import { Drivers } from './pages/Drivers';
import { Strategy } from './pages/Strategy';
import { Weather } from './pages/Weather';
import { Model } from './pages/Model';
import { Backtesting } from './pages/Backtesting';
import { Championship } from './pages/Championship';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#08090C] text-[#F5F6F7] flex">
      <NavigationRail />
      <main className="flex-1 lg:ml-[224px] min-h-screen pt-[56px] lg:pt-0 pb-[76px] lg:pb-0">
        <div className="max-w-[1240px] mx-auto px-4 sm:px-6 lg:px-8 py-5 lg:py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/race" element={<Race />} />
            <Route path="/prediction" element={<Prediction />} />
            <Route path="/simulation" element={<Simulation />} />
            <Route path="/drivers" element={<Drivers />} />
            <Route path="/strategy" element={<Strategy />} />
            <Route path="/weather" element={<Weather />} />
            <Route path="/model" element={<Model />} />
            <Route path="/backtesting" element={<Backtesting />} />
            <Route path="/championship" element={<Championship />} />
          </Routes>
        </div>
      </main>
    </div>
  );
};
