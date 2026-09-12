import React, { useState } from 'react';
import { Sliders, Play } from 'lucide-react';

interface ScenarioPanelProps {
  onRunScenario: (scenario: { weather: string; safetyCar: string; tyreDeg: string }) => void;
  loading?: boolean;
}

export const ScenarioPanel: React.FC<ScenarioPanelProps> = ({ onRunScenario, loading }) => {
  const [weather, setWeather] = useState('dry');
  const [safetyCar, setSafetyCar] = useState('normal');
  const [tyreDeg, setTyreDeg] = useState('normal');

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <div className="flex items-center space-x-2 mb-4">
        <Sliders className="w-4 h-4 text-f1-red" />
        <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">
          Interactive What-If Scenario Engine
        </h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4 text-xs">
        <div>
          <label className="text-gray-400 block mb-1 font-medium">WEATHER CONDITIONS</label>
          <select
            value={weather}
            onChange={(e) => setWeather(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-2.5 py-1.5 text-white focus:outline-none focus:border-f1-red"
          >
            <option value="dry">Dry (Clear Track)</option>
            <option value="mixed">Mixed (Uncertain Rain)</option>
            <option value="wet">Wet (Full Wet/Inter)</option>
          </select>
        </div>

        <div>
          <label className="text-gray-400 block mb-1 font-medium">SAFETY CAR PROBABILITY</label>
          <select
            value={safetyCar}
            onChange={(e) => setSafetyCar(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-2.5 py-1.5 text-white focus:outline-none focus:border-f1-red"
          >
            <option value="low">Low (Clean Race)</option>
            <option value="normal">Normal (Standard ~50%)</option>
            <option value="high">High (Chaos / High SC)</option>
          </select>
        </div>

        <div>
          <label className="text-gray-400 block mb-1 font-medium">TYRE DEGRADATION RATE</label>
          <select
            value={tyreDeg}
            onChange={(e) => setTyreDeg(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-2.5 py-1.5 text-white focus:outline-none focus:border-f1-red"
          >
            <option value="low">Low (1-Stop Dominant)</option>
            <option value="normal">Normal (Balanced)</option>
            <option value="high">High (2/3-Stop Dominant)</option>
          </select>
        </div>
      </div>

      <button
        onClick={() => onRunScenario({ weather, safetyCar, tyreDeg })}
        disabled={loading}
        className="w-full bg-f1-red hover:bg-red-700 text-white font-bold py-2 px-4 rounded text-xs transition-colors flex items-center justify-center space-x-2 disabled:opacity-50"
      >
        <Play className="w-3.5 h-3.5 fill-current" />
        <span>{loading ? 'RE-SIMULATING...' : 'RERUN MONTE CARLO SIMULATION'}</span>
      </button>
    </div>
  );
};
