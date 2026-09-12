import React, { useState } from 'react';
import { ChampionshipResponse, ChampionshipDriverStanding } from '../types';
import { simulateChampionship } from '../api/client';
import { Trophy, Flag, AlertCircle } from 'lucide-react';

const SAMPLE_DRIVERS = [
  { driver_id: 'VER', code: 'VER', full_name: 'Max Verstappen', team_id: 'RBR', team_name: 'Red Bull Racing', current_points: 210 },
  { driver_id: 'NOR', code: 'NOR', full_name: 'Lando Norris', team_id: 'MCL', team_name: 'McLaren', current_points: 180 },
  { driver_id: 'LEC', code: 'LEC', full_name: 'Charles Leclerc', team_id: 'FER', team_name: 'Ferrari', current_points: 160 },
  { driver_id: 'PIA', code: 'PIA', full_name: 'Oscar Piastri', team_id: 'MCL', team_name: 'McLaren', current_points: 150 },
  { driver_id: 'SAI', code: 'SAI', full_name: 'Carlos Sainz', team_id: 'FER', team_name: 'Ferrari', current_points: 140 },
  { driver_id: 'HAM', code: 'HAM', full_name: 'Lewis Hamilton', team_id: 'MER', team_name: 'Mercedes', current_points: 120 },
  { driver_id: 'RUS', code: 'RUS', full_name: 'George Russell', team_id: 'MER', team_name: 'Mercedes', current_points: 110 },
  { driver_id: 'ALO', code: 'ALO', full_name: 'Fernando Alonso', team_id: 'AMR', team_name: 'Aston Martin', current_points: 80 },
];

const SAMPLE_RACES = [
  { race_id: '2025_15', name: 'Belgian GP', round_number: 15, total_laps: 44 },
  { race_id: '2025_16', name: 'Hungarian GP', round_number: 16, total_laps: 70 },
  { race_id: '2025_17', name: 'Dutch GP', round_number: 17, total_laps: 72 },
  { race_id: '2025_18', name: 'Italian GP', round_number: 18, total_laps: 53 },
  { race_id: '2025_19', name: 'Azerbaijan GP', round_number: 19, total_laps: 51 },
];

const TEAM_COLORS: Record<string, string> = {
  RBR: '#6692FF',
  MCL: '#FF8000',
  FER: '#E8002D',
  MER: '#27F4D2',
  AMR: '#229971',
};

export const Championship: React.FC = () => {
  const [result, setResult] = useState<ChampionshipResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [nSims, setNSims] = useState(5000);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await simulateChampionship(2025, SAMPLE_DRIVERS, SAMPLE_RACES, nSims);
      setResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <div className="bg-gradient-to-r from-gray-800 via-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
        <div className="flex items-center space-x-3">
          <Trophy className="w-7 h-7 text-yellow-400" />
          <div>
            <h1 className="text-2xl font-black text-white tracking-tight">Championship Simulator</h1>
            <p className="text-sm text-gray-400">
              Monte Carlo simulation of the remaining season
            </p>
          </div>
        </div>
      </div>

      <div className="bg-gray-800/60 border border-gray-700/50 rounded-lg p-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div>
            <label className="text-xs font-semibold text-gray-400 uppercase">Simulations</label>
            <select
              value={nSims}
              onChange={(e) => setNSims(Number(e.target.value))}
              className="block mt-1 bg-gray-700 border border-gray-600 rounded px-3 py-1.5 text-sm text-white"
            >
              <option value={1000}>1,000</option>
              <option value={5000}>5,000</option>
              <option value={10000}>10,000</option>
              <option value={50000}>50,000</option>
            </select>
          </div>
          <div className="text-xs text-gray-500">
            <p>{SAMPLE_DRIVERS.length} drivers</p>
            <p>{SAMPLE_RACES.length} races remaining</p>
          </div>
        </div>
        <button
          onClick={handleSimulate}
          disabled={loading}
          className="bg-f1-red hover:bg-red-700 disabled:opacity-50 text-white font-bold px-6 py-2 rounded-lg text-sm transition"
        >
          {loading ? 'Simulating Season...' : 'Run Championship Simulation'}
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="text-center space-y-3">
            <div className="w-10 h-10 border-4 border-f1-red border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm font-semibold text-gray-400">
              Running {nSims.toLocaleString()} simulations × {SAMPLE_RACES.length} races...
            </p>
          </div>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-6">
          <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-700/50 flex items-center space-x-2">
              <Flag className="w-5 h-5 text-yellow-400" />
              <h2 className="text-lg font-bold text-white">Driver Championship Probabilities</h2>
            </div>
            <div className="divide-y divide-gray-700/30">
              {result.driver_standings
                .sort((a, b) => b.championship_win_probability - a.championship_win_probability)
                .map((d: ChampionshipDriverStanding, idx: number) => (
                  <div key={d.driver_id} className="px-6 py-3 flex items-center justify-between hover:bg-gray-700/20 transition">
                    <div className="flex items-center space-x-4">
                      <span className={`text-lg font-black ${idx === 0 ? 'text-yellow-400' : 'text-gray-500'}`}>
                        {idx + 1}
                      </span>
                      <div className="w-1 h-8 rounded" style={{ backgroundColor: TEAM_COLORS[d.team_id] || '#888' }} />
                      <div>
                        <p className="text-sm font-bold text-white">{d.code}</p>
                        <p className="text-xs text-gray-500">{d.team_id}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-6">
                      <div className="text-right">
                        <p className="text-sm font-bold text-yellow-400">{(d.championship_win_probability * 100).toFixed(1)}%</p>
                        <p className="text-xs text-gray-500">win</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-white">{d.expected_championship_points.toFixed(0)}</p>
                        <p className="text-xs text-gray-500">exp. pts</p>
                      </div>
                      <div className="w-32 bg-gray-700 rounded-full h-2">
                        <div className="bg-yellow-400 h-2 rounded-full" style={{ width: `${d.championship_win_probability * 100}%` }} />
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-700/50">
              <h2 className="text-lg font-bold text-white">Constructor Championship</h2>
            </div>
            <div className="divide-y divide-gray-700/30">
              {result.constructor_standings
                .sort((a, b) => b.championship_win_probability - a.championship_win_probability)
                .map((c, idx) => (
                  <div key={c.team_id} className="px-6 py-3 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className={`text-lg font-black ${idx === 0 ? 'text-yellow-400' : 'text-gray-500'}`}>{idx + 1}</span>
                      <p className="text-sm font-bold text-white">{c.team_id}</p>
                    </div>
                    <div className="flex items-center space-x-6">
                      <p className="text-sm font-bold text-yellow-400">{(c.championship_win_probability * 100).toFixed(1)}%</p>
                      <p className="text-sm text-gray-300">{c.expected_championship_points.toFixed(0)} pts</p>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      <div className="bg-gray-800/60 border border-gray-700/50 rounded-lg p-3 flex items-start space-x-2.5 text-xs text-gray-400">
        <AlertCircle className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
        <p>Probabilistic forecasts based on Monte Carlo simulation. Actual outcomes depend on unpredictable factors.</p>
      </div>
    </div>
  );
};
