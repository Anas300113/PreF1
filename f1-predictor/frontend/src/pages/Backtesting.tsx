import React, { useState, useEffect } from 'react';
import { fetchBacktests } from '../api/client';
import { BacktestResult } from '../types';
import { History, TrendingUp, TrendingDown } from 'lucide-react';
import { LoadingState, EmptyState } from '../components/ui';

const pct = (v: number | undefined) => ((v ?? 0) * 100).toFixed(1) + '%';

export const Backtesting: React.FC = () => {
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBacktests()
      .then((data) => {
        setResults(data);
        setLoading(false);
      })
      .catch(() => {
        setError('Could not load backtest results.');
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <LoadingState label="Loading backtest metrics..." />;
  }

  if (error) {
    return <EmptyState title="Backtests unavailable" body={error} />;
  }

  if (results.length === 0) {
    return (
      <div className="space-y-5 animate-fade-in">
        <div className="flex items-center gap-3">
          <span className="w-9 h-9 rounded-[10px] bg-[#15191F] border border-[rgba(255,255,255,0.08)] flex items-center justify-center text-[#E10600]"><History className="w-[18px] h-[18px]" /></span>
          <div>
            <div className="eyebrow">Validation</div>
            <h1 className="font-display font-bold text-white text-[24px] tracking-tight leading-none">Backtests</h1>
          </div>
        </div>
        <EmptyState title="No backtest results yet" body="Run python scripts/run_backtest.py after ingesting data. This page only shows real leakage-safe metrics." />
      </div>
    );
  }

  const latest = results[0];
  const standingsComp = latest.comparison?.championship_standings;
  const beats = standingsComp ? (standingsComp.beats_on_winner || standingsComp.beats_on_mae) : null;

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <span className="w-9 h-9 rounded-[10px] bg-[#15191F] border border-[rgba(255,255,255,0.08)] flex items-center justify-center text-[#E10600]"><History className="w-[18px] h-[18px]" /></span>
        <div>
          <div className="eyebrow">Validation · {latest.model_version} · cutoff {latest.training_cutoff || 'n/a'}</div>
          <h1 className="font-display font-bold text-white text-[24px] tracking-tight leading-none">Backtests</h1>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        <div className="panel p-4">
          <span className="text-[10px] font-bold text-[#636973] tracking-wide">WINNER ACC · {latest.season}</span>
          <div className="font-display font-bold text-white text-[30px] tnum mt-1">{pct(latest.winner_accuracy)}</div>
        </div>

        <div className="panel p-4">
          <span className="text-[10px] font-bold text-[#636973] tracking-wide">PODIUM ACC</span>
          <div className="font-display font-bold text-white text-[30px] tnum mt-1">{pct(latest.podium_accuracy)}</div>
        </div>

        <div className="panel p-4">
          <span className="text-[10px] font-bold text-[#636973] tracking-wide">MEAN ERROR</span>
          <div className="font-display font-bold text-white text-[30px] tnum mt-1">{latest.mean_abs_position_error.toFixed(2)}</div>
          <div className="text-[11px] text-[#636973] font-mono mt-1">BRIER {latest.brier_score_win.toFixed(3)} · LL {latest.log_loss_win.toFixed(3)}</div>
        </div>
      </div>
      <div className="panel overflow-hidden">
        <div className="px-4 sm:px-5 py-3.5 border-b border-white/[0.05]">
          <h3 className="eyebrow !text-[#9BA1AA]">Season history</h3>
        </div>
        <div className="overflow-x-auto">
        <table className="timing-table min-w-[680px]">
          <thead>
            <tr>
              <th>Season</th>
              <th className="!text-right">Races</th>
              <th className="!text-right">Winner</th>
              <th className="!text-right">Podium</th>
              <th className="!text-right">Top 5</th>
              <th className="!text-right">MAE</th>
              <th className="!text-right">Brier</th>
              <th className="!text-right">vs base</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => {
              const comp = r.comparison?.championship_standings;
              const rBeats = comp ? (comp.beats_on_winner || comp.beats_on_mae) : null;
              return (
                <tr key={r.season}>
                  <td className="font-bold text-white">{r.season}</td>
                  <td className="num text-[#9BA1AA]">{r.n_races}</td>
                  <td className="num text-white font-bold">{pct(r.winner_accuracy)}</td>
                  <td className="num text-[#9BA1AA]">{pct(r.podium_accuracy)}</td>
                  <td className="num text-[#9BA1AA]">{pct(r.top5_accuracy)}</td>
                  <td className="num text-[#9BA1AA]">{r.mean_abs_position_error.toFixed(2)}</td>
                  <td className="num text-[#9BA1AA]">{r.brier_score_win.toFixed(3)}</td>
                  <td className="!text-right">
                    {rBeats === null ? (
                      <span className="text-[#636973]">n/a</span>
                    ) : rBeats ? (
                      <span className="text-[#20C997] inline-flex items-center gap-1 font-bold text-[12px]">
                        <TrendingUp className="w-3 h-3" /> BEATS
                      </span>
                    ) : (
                      <span className="text-[#FF6B61] inline-flex items-center gap-1 font-bold text-[12px]">
                        <TrendingDown className="w-3 h-3" /> TRAILS
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        </div>
      </div>
      <div className="panel overflow-hidden">
        <div className="px-4 sm:px-5 py-3.5 border-b border-white/[0.05]">
          <h3 className="eyebrow !text-[#9BA1AA]">Baseline comparison · {latest.season}</h3>
        </div>
        <div className="overflow-x-auto">
        <table className="timing-table min-w-[560px]">
          <thead>
            <tr>
              <th>Baseline</th>
              <th className="!text-right">Winner</th>
              <th className="!text-right">MAE</th>
              <th className="!text-right">Δ winner</th>
              <th className="!text-right">Δ MAE</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(latest.baselines || {}).map(([name, b]) => {
              const comp = latest.comparison?.[name];
              return (
                <tr key={name}>
                  <td className="font-semibold text-white capitalize">
                    {name.replace(/_/g, ' ')}
                  </td>
                  <td className="num text-[#9BA1AA]">{pct(b.winner_accuracy)}</td>
                  <td className="num text-[#9BA1AA]">{b.mae_position.toFixed(2)}</td>
                  <td className={`num font-bold ${(comp?.winner_accuracy_delta ?? 0) >= 0 ? 'text-[#20C997]' : 'text-[#FF6B61]'}`}>
                    {comp ? ((comp.winner_accuracy_delta >= 0 ? '+' : '') + (comp.winner_accuracy_delta * 100).toFixed(1) + '%') : '—'}
                  </td>
                  <td className={`num font-bold ${(comp?.mae_delta ?? 0) <= 0 ? 'text-[#20C997]' : 'text-[#FF6B61]'}`}>
                    {comp ? ((comp.mae_delta >= 0 ? '+' : '') + comp.mae_delta.toFixed(2)) : '—'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        </div>
        <p className="px-4 sm:px-5 py-3 text-[11px] text-[#636973] leading-relaxed">
          Negative MAE delta beats baseline. Monte Carlo estimates use{' '}
          {latest.n_simulations.toLocaleString()} sims per race (seed {latest.simulation_seed}).
        </p>
      </div>
    </div>
  );
};
