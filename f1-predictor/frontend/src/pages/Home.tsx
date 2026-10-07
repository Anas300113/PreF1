import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Race, PredictionResponse } from '../types';
import { fetchNextRace, fetchPrediction } from '../api/client';
import { CircuitSVG } from '../components/CircuitSVG';
import { LoadingState, StatusPill } from '../components/ui';
import { ArrowRight, Timer, CloudSun, Trophy } from 'lucide-react';

export const Home: React.FC = () => {
  const [race, setRace] = useState<Race | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const nextRace = await fetchNextRace();
      setRace(nextRace);
      const pred = await fetchPrediction(nextRace.id, 50000);
      setPrediction(pred);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  if (loading && !prediction) {
    return <LoadingState label="Running Monte Carlo simulations..." />;
  }

  const drivers = prediction?.drivers ? [...prediction.drivers].sort((a, b) => b.win_probability - a.win_probability) : [];
  const top5 = drivers.slice(0, 5);

  return (
    <div className="space-y-5 animate-fade-in">
      {race && (
        <section className="panel-strong overflow-hidden">
          <div className="h-[3px] bg-gradient-to-r from-[#E10600] via-[#E10600]/40 to-transparent" />
          <div className="p-5 sm:p-7">
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <StatusPill tone="live">Next race</StatusPill>
              <span className="text-[11px] font-mono text-[#636973]">R{race.round_number} · {race.season_year}</span>
              {race.is_sprint_weekend && <StatusPill tone="warn">Sprint</StatusPill>}
              {race.status && race.status !== 'scheduled' && <StatusPill tone="muted">{race.status}</StatusPill>}
            </div>
            <div className="flex flex-col lg:flex-row lg:items-center gap-6">
              <div className="flex-1 min-w-0">
                <h1 className="font-display font-bold text-white tracking-tight text-[30px] sm:text-[40px] leading-[1.02]">{race.name}</h1>
                <p className="text-[#9BA1AA] mt-2 text-[13.5px]">{race.circuit?.name} · {race.circuit?.locality}, {race.circuit?.country}</p>
                <Countdown targetDate={race.race_date} />
                <div className="flex flex-wrap gap-2.5 mt-5">
                  <Link to="/prediction" className="btn-primary inline-flex items-center gap-2">Open live timing <ArrowRight className="w-4 h-4" /></Link>
                  <Link to="/race" className="btn-ghost inline-flex items-center gap-2">Weekend brief</Link>
                </div>
              </div>
              <div className="w-full lg:w-[300px] shrink-0 panel p-3">
                <CircuitSVG circuitId={race.circuit?.id} className="w-full h-[120px]" />
                <div className="flex justify-between mt-2 px-1 text-[11px] font-mono text-[#636973]">
                  <span>{prediction ? `${prediction.model.simulation_count.toLocaleString()} SIMS` : 'MODEL WARMING'}</span>
                  <span>v{prediction?.model.version || '—'}</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}
      {prediction && top5.length > 0 && (
        <section className="panel overflow-hidden">
          <div className="flex items-center justify-between px-4 sm:px-5 py-3.5 border-b border-white/[0.05]">
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-[#E10600]" />
              <h2 className="eyebrow !text-[#9BA1AA]">Win favourites</h2>
            </div>
            <Link to="/prediction" className="text-[12px] font-semibold text-[#9BA1AA] hover:text-white inline-flex items-center gap-1">Full timing <ArrowRight className="w-3.5 h-3.5" /></Link>
          </div>
          <div className="overflow-x-auto">
            <table className="timing-table min-w-[560px]">
              <thead><tr><th className="!text-center w-12">Pos</th><th>Driver</th><th className="!text-right">Win</th><th className="!text-right">Podium</th><th className="!text-right">Exp pos</th><th className="!text-right">Exp pts</th></tr></thead>
              <tbody>
                {top5.map((d, i) => (
                  <tr key={d.driver_id}>
                    <td className="!text-center"><span className={`inline-flex w-7 h-7 items-center justify-center rounded-md font-display font-bold text-[13px] ${i === 0 ? 'bg-[#E10600]/15 text-[#FF6B61]' : 'bg-white/[0.05] text-white'}`}>{i + 1}</span></td>
                    <td><div className="flex items-center gap-2.5"><span className="w-[3px] h-7 rounded-full" style={{ backgroundColor: d.team_color }} /><div><div className="font-bold text-white text-[14px] leading-none">{d.code}</div><div className="text-[11px] text-[#636973] mt-0.5">{d.team}</div></div></div></td>
                    <td className="num"><span className="text-white font-bold">{(d.win_probability * 100).toFixed(1)}%</span></td>
                    <td className="num text-[#9BA1AA]">{(d.podium_probability * 100).toFixed(1)}%</td>
                    <td className="num text-[#9BA1AA]">P{d.expected_position.toFixed(1)}</td>
                    <td className="num text-[#9BA1AA]">{d.expected_points.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
      <section className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Link to="/strategy" className="panel p-4 hover:border-white/15 transition-colors"><div className="flex items-center gap-2 text-[#E10600]"><Timer className="w-4 h-4" /><span className="eyebrow">Strategy</span></div><p className="text-white font-semibold mt-2 text-[14px]">Pit windows & compounds</p><p className="text-[12px] text-[#636973]">1-stop vs 2-stop deltas</p></Link>
        <Link to="/weather" className="panel p-4 hover:border-white/15 transition-colors"><div className="flex items-center gap-2 text-[#E10600]"><CloudSun className="w-4 h-4" /><span className="eyebrow">Weather</span></div><p className="text-white font-semibold mt-2 text-[14px]">{prediction ? `${prediction.weather.temperature_c ?? '—'}°C · rain ${prediction.weather.precipitation_probability ?? 0}%` : 'Track conditions'}</p><p className="text-[12px] text-[#636973]">Impact on deg & grip</p></Link>
        <Link to="/championship" className="panel p-4 hover:border-white/15 transition-colors"><div className="flex items-center gap-2 text-[#E10600]"><Trophy className="w-4 h-4" /><span className="eyebrow">Title race</span></div><p className="text-white font-semibold mt-2 text-[14px]">Championship odds</p><p className="text-[12px] text-[#636973]">Monte Carlo run-out</p></Link>
      </section>
    </div>
  );
};

const Countdown: React.FC<{ targetDate?: string }> = ({ targetDate }) => {
  const [now, setNow] = React.useState(() => Date.now());

  React.useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  if (!targetDate) return null;

  const target = Date.parse(`${targetDate}T14:00:00Z`);
  if (Number.isNaN(target)) return null;

  const diff = Math.max(0, target - now);
  const days = Math.floor(diff / 86_400_000);
  const hours = Math.floor((diff % 86_400_000) / 3_600_000);
  const minutes = Math.floor((diff % 3_600_000) / 60_000);
  const seconds = Math.floor((diff % 60_000) / 1000);

  if (diff === 0) {
    return (
      <div className="mt-4 inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-[#E10600]/10 border border-[#E10600]/30">
        <span className="live-dot pulse" />
        <span className="text-[12px] font-bold text-[#FF6B61] tracking-wide">RACE WEEKEND IN PROGRESS</span>
      </div>
    );
  }

  const cells: Array<[string, string]> = [
    [String(days), 'DAYS'],
    [String(hours).padStart(2, '0'), 'HRS'],
    [String(minutes).padStart(2, '0'), 'MIN'],
    [String(seconds).padStart(2, '0'), 'SEC'],
  ];

  return (
    <div className="mt-4">
      <div className="text-[10px] font-bold text-[#636973] tracking-[0.16em] mb-1.5">LIGHTS OUT IN</div>
      <div className="flex gap-1.5" aria-live="off">
        {cells.map(([value, label]) => (
          <div key={label} className="min-w-[56px] px-2.5 py-2 rounded-lg bg-black/40 border border-white/[0.06] text-center">
            <div className="font-mono font-bold text-white text-[22px] leading-none tnum">{value}</div>
            <div className="text-[9px] font-bold text-[#636973] tracking-wider mt-1">{label}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
