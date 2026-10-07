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
    <div className="panel p-4">
      <div className="flex items-center gap-2 mb-4">
        <Sliders className="w-4 h-4 text-[#E10600]" />
        <h3 className="eyebrow !text-[#9BA1AA]">What-if scenario</h3>
      </div>

      <div className="grid grid-cols-1 gap-3 mb-4 text-xs">
        <div>
          <label htmlFor="sc-weather" className="text-[#636973] block mb-1.5 font-semibold text-[11px] tracking-wide">WEATHER</label>
          <select
            id="sc-weather"
            value={weather}
            onChange={(e) => setWeather(e.target.value)}
            className="field"
          >
            <option value="dry">Dry — clear track</option>
            <option value="mixed">Mixed — rain risk</option>
            <option value="wet">Wet — inter / full wet</option>
          </select>
        </div>

        <div>
          <label htmlFor="sc-safety" className="text-[#636973] block mb-1.5 font-semibold text-[11px] tracking-wide">SAFETY CAR</label>
          <select
            id="sc-safety"
            value={safetyCar}
            onChange={(e) => setSafetyCar(e.target.value)}
            className="field"
          >
            <option value="low">Low — clean race</option>
            <option value="normal">Normal — ~50%</option>
            <option value="high">High — chaos</option>
          </select>
        </div>

        <div>
          <label htmlFor="sc-tyre" className="text-[#636973] block mb-1.5 font-semibold text-[11px] tracking-wide">TYRE DEG</label>
          <select
            id="sc-tyre"
            value={tyreDeg}
            onChange={(e) => setTyreDeg(e.target.value)}
            className="field"
          >
            <option value="low">Low — 1-stop</option>
            <option value="normal">Normal — balanced</option>
            <option value="high">High — 2/3-stop</option>
          </select>
        </div>
      </div>

      <button
        onClick={() => onRunScenario({ weather, safetyCar, tyreDeg })}
        disabled={loading}
        className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
      >
        <Play className="w-3.5 h-3.5 fill-current" />
        <span>{loading ? 'SIMULATING...' : 'RERUN SIMULATION'}</span>
      </button>
    </div>
  );
};
