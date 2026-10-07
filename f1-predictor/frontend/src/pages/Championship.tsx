import React, { useState } from 'react';
import { ChampionshipResponse, ChampionshipDriverStanding } from '../types';
import { simulateChampionship } from '../api/client';
import { Trophy } from 'lucide-react';

const SAMPLE_DRIVERS = [
  { driver_id: 'VER', code: 'VER', full_name: 'Max Verstappen', team_id: 'RBR', team_name: 'Red Bull Racing', current_points: 318 },
  { driver_id: 'NOR', code: 'NOR', full_name: 'Lando Norris', team_id: 'MCL', team_name: 'McLaren', current_points: 289 },
  { driver_id: 'PIA', code: 'PIA', full_name: 'Oscar Piastri', team_id: 'MCL', team_name: 'McLaren', current_points: 271 },
  { driver_id: 'LEC', code: 'LEC', full_name: 'Charles Leclerc', team_id: 'FER', team_name: 'Ferrari', current_points: 244 },
  { driver_id: 'RUS', code: 'RUS', full_name: 'George Russell', team_id: 'MER', team_name: 'Mercedes', current_points: 210 },
  { driver_id: 'HAM', code: 'HAM', full_name: 'Lewis Hamilton', team_id: 'FER', team_name: 'Ferrari', current_points: 188 },
  { driver_id: 'ANT', code: 'ANT', full_name: 'Kimi Antonelli', team_id: 'MER', team_name: 'Mercedes', current_points: 154 },
  { driver_id: 'SAI', code: 'SAI', full_name: 'Carlos Sainz', team_id: 'WIL', team_name: 'Williams', current_points: 121 },
];

const SAMPLE_RACES = [
  { race_id: '2026_17', name: 'Singapore GP', round_number: 17, total_laps: 62, is_sprint_weekend: true },
  { race_id: '2026_18', name: 'United States GP', round_number: 18, total_laps: 56, is_sprint_weekend: true },
  { race_id: '2026_19', name: 'Mexico City GP', round_number: 19, total_laps: 71 },
  { race_id: '2026_20', name: 'Brazilian GP', round_number: 20, total_laps: 71, is_sprint_weekend: true },
  { race_id: '2026_21', name: 'Las Vegas GP', round_number: 21, total_laps: 50 },
  { race_id: '2026_22', name: 'Qatar GP', round_number: 22, total_laps: 57, is_sprint_weekend: true },
  { race_id: '2026_23', name: 'Abu Dhabi GP', round_number: 23, total_laps: 58 },
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
      const res = await simulateChampionship(2026, SAMPLE_DRIVERS, SAMPLE_RACES, nSims);
      setResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <span className="w-9 h-9 rounded-[10px] bg-[#15191F] border border-[rgba(255,255,255,0.08)] flex items-center justify-center text-[#E10600]"><Trophy className="w-[18px] h-[18px]" /></span>
        <div>
          <div className="eyebrow">Season run-out · {SAMPLE_RACES.length} races left</div>
          <h1 className="font-display font-bold text-white text-[24px] tracking-tight leading-none">Title race</h1>
        </div>
      </div>

      <div className="panel p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div>
            <label htmlFor="champ-sims" className="text-[11px] font-bold text-[#636973] tracking-wide">SIMULATIONS</label>
            <select
              id="champ-sims"
              value={nSims}
              onChange={(e) => setNSims(Number(e.target.value))}
              className="field !w-auto mt-1 min-h-[38px]"
            >
              <option value={1000}>1,000</option>
              <option value={5000}>5,000</option>
              <option value={10000}>10,000</option>
              <option value={50000}>50,000</option>
            </select>
          </div>
          <div className="text-[12px] text-[#636973] font-mono">
            <p>{SAMPLE_DRIVERS.length} DRIVERS</p>
            <p>{SAMPLE_RACES.length} RACES</p>
          </div>
        </div>
        <button
          onClick={handleSimulate}
          disabled={loading}
          className="btn-primary disabled:opacity-50 min-h-[42px]"
        >
          {loading ? 'Simulating...' : 'Run title simulation'}
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="text-center space-y-3">
            <div className="w-10 h-10 border-[3px] border-[#E10600] border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-[13px] font-medium text-[#9BA1AA]">
              Running {nSims.toLocaleString()} simulations...
            </p>
          </div>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-4">
          <div className="panel overflow-hidden">
            <div className="px-4 sm:px-5 py-3.5 border-b border-white/[0.05] flex items-center justify-between">
              <h2 className="eyebrow !text-[#9BA1AA]">Drivers · title odds</h2>
              <span className="text-[11px] font-mono text-[#636973]">{result.n_simulations.toLocaleString()} SIMS</span>
            </div>
            <div className="overflow-x-auto">
              <table className="timing-table min-w-[560px]">
                <thead><tr><th className="!text-center w-12">Pos</th><th>Driver</th><th className="!text-right">Title</th><th className="!text-right">Exp pts</th><th className="!text-right w-[180px]">Share</th></tr></thead>
                <tbody>
                  {result.driver_standings
                    .sort((a, b) => b.championship_win_probability - a.championship_win_probability)
                    .map((d: ChampionshipDriverStanding, idx: number) => (
                      <tr key={d.driver_id}>
                        <td className="!text-center"><span className={`inline-flex w-7 h-7 items-center justify-center rounded-md font-display font-bold text-[13px] ${idx === 0 ? 'bg-[#E10600]/15 text-[#FF6B61]' : 'bg-white/[0.05] text-white'}`}>{idx + 1}</span></td>
                        <td><div className="flex items-center gap-2.5"><span className="w-[3px] h-7 rounded-full" style={{ backgroundColor: TEAM_COLORS[d.team_id] || '#888' }} /><div><div className="font-bold text-white text-[14px] leading-none">{d.code}</div><div className="text-[11px] text-[#636973] mt-0.5">{d.team_id}</div></div></div></td>
                        <td className="num text-white font-bold">{(d.championship_win_probability * 100).toFixed(1)}%</td>
                        <td className="num text-[#9BA1AA]">{d.expected_championship_points.toFixed(0)}</td>
                        <td><div className="h-[5px] bg-black/40 rounded-full overflow-hidden border border-white/[0.05]"><div className="h-full bg-[#E10600] rounded-full" style={{ width: `${Math.min(100, d.championship_win_probability * 100)}%` }} /></div></td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel overflow-hidden">
            <div className="px-4 sm:px-5 py-3.5 border-b border-white/[0.05]">
              <h2 className="eyebrow !text-[#9BA1AA]">Constructors · title odds</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="timing-table min-w-[480px]">
                <thead><tr><th className="!text-center w-12">Pos</th><th>Team</th><th className="!text-right">Title</th><th className="!text-right">Exp pts</th></tr></thead>
                <tbody>
                  {result.constructor_standings
                    .sort((a, b) => b.championship_win_probability - a.championship_win_probability)
                    .map((c, idx) => (
                      <tr key={c.team_id}>
                        <td className="!text-center"><span className="inline-flex w-7 h-7 items-center justify-center rounded-md bg-white/[0.05] text-white font-display font-bold text-[13px]">{idx + 1}</span></td>
                        <td className="font-bold text-white text-[14px]">{c.team_id}</td>
                        <td className="num text-white font-bold">{(c.championship_win_probability * 100).toFixed(1)}%</td>
                        <td className="num text-[#9BA1AA]">{c.expected_championship_points.toFixed(0)}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {!result && !loading && (
        <div className="panel p-10 text-center">
          <p className="text-white font-bold">No title run yet</p>
          <p className="text-[13px] text-[#9BA1AA] mt-1">Run the simulation to project the remaining season.</p>
        </div>
      )}

      <p className="text-[12px] text-[#636973] leading-relaxed">Probabilistic forecasts from Monte Carlo simulation. Real outcomes depend on unpredictable race events.</p>
    </div>
  );
};
