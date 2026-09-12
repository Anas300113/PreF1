import React, { useState, useEffect } from 'react';
import { fetchBacktests } from '../api/client';
import { BacktestResult } from '../types';
import { BarChart3, TrendingUp, TrendingDown, Minus } from 'lucide-react';

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
    return <div className="p-8 text-center text-gray-400 text-sm">Loading backtest metrics...</div>;
  }

  if (error) {
    return <div className="p-8 text-center text-gray-400 text-sm">{error}</div>;
  }

  if (results.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center space-x-3 mb-6">
          <BarChart3 className="w-6 h-6 text-f1-red" />
          <h1 className="text-2xl font-black text-white tracking-tight">
            HISTORICAL BACKTESTING ENGINE &amp; BENCHMARKS
          </h1>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-8 text-center">
          <p className="text-gray-300 font-semibold mb-2">No backtest results available yet.</p>
          <p className="text-gray-500 text-sm">
            Run <code className="text-f1-red">python scripts/run_backtest.py --season &lt;year&gt;</code> after
            ingesting historical data and training models. This page only shows metrics from real,
            leakage-safe evaluations — never fabricated numbers.
          </p>
        </div>
      </div>
    );
  }

  const latest = results[0];
  const standingsComp = latest.comparison?.championship_standings;
  const beats = standingsComp ? (standingsComp.beats_on_winner || standingsComp.beats_on_mae) : null;
  const BeatIcon = beats === null ? Minus : beats ? TrendingUp : TrendingDown;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <div className="flex items-center space-x-3">
        <BarChart3 className="w-6 h-6 text-f1-red" />
        <h1 className="text-2xl font-black text-white tracking-tight">
          HISTORICAL BACKTESTING ENGINE &amp; BENCHMARKS
        </h1>
      </div>
      <p className="text-xs text-gray-500">
        Leakage-safe chronological evaluation: every race predicted using only information
        available before it, then scored against the actual result. Model version{' '}
        <span className="text-gray-400">{latest.model_version}</span>, training cutoff{' '}
        <span className="text-gray-400">{latest.training_cutoff || 'n/a'}</span>.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <span className="text-gray-400 text-xs font-semibold block">
            WINNER PREDICTION ACCURACY ({latest.season})
          </span>
          <span className="text-3xl font-black text-green-400">{pct(latest.winner_accuracy)}</span>
          {standingsComp && (
            <span className="text-[10px] text-gray-400 block mt-1">
              {standingsComp.winner_accuracy_delta >= 0 ? '+' : ''}
              {(standingsComp.winner_accuracy_delta * 100).toFixed(1)}% vs Standings Baseline
            </span>
          )}
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <span className="text-gray-400 text-xs font-semibold block">PODIUM ACCURACY (TOP 3)</span>
          <span className="text-3xl font-black text-yellow-400">{pct(latest.podium_accuracy)}</span>
          {standingsComp && (
            <span className="text-[10px] text-gray-400 block mt-1">
              {standingsComp.podium_accuracy_delta >= 0 ? '+' : ''}
              {(standingsComp.podium_accuracy_delta * 100).toFixed(1)}% vs Standings Baseline
            </span>
          )}
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <span className="text-gray-400 text-xs font-semibold block">MEAN POSITION ERROR (MAE)</span>
          <span className="text-3xl font-black text-blue-400">{latest.mean_abs_position_error.toFixed(2)} pos</span>
          <span className="text-[10px] text-gray-400 block mt-1">
            Brier (win): {latest.brier_score_win.toFixed(3)} · Log loss: {latest.log_loss_win.toFixed(3)}
          </span>
        </div>
      </div>
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-bold text-gray-200 mb-4 uppercase tracking-wide">
          Backtesting Performance Across Evaluated Seasons
        </h3>
        <table className="w-full text-xs text-left">
          <thead>
            <tr className="border-b border-gray-700 text-gray-400">
              <th className="py-2 px-3">Season</th>
              <th className="py-2 px-3">Races</th>
              <th className="py-2 px-3">Winner Acc</th>
              <th className="py-2 px-3">Podium Acc</th>
              <th className="py-2 px-3">Top 5 Acc</th>
              <th className="py-2 px-3">MAE</th>
              <th className="py-2 px-3">Brier</th>
              <th className="py-2 px-3">vs Standings</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => {
              const comp = r.comparison?.championship_standings;
              const rBeats = comp ? (comp.beats_on_winner || comp.beats_on_mae) : null;
              return (
                <tr key={r.season} className="border-b border-gray-700/50">
                  <td className="py-2.5 px-3 font-bold text-white">{r.season}</td>
                  <td className="py-2.5 px-3 text-gray-300">{r.n_races}</td>
                  <td className="py-2.5 px-3 font-semibold text-green-400">{pct(r.winner_accuracy)}</td>
                  <td className="py-2.5 px-3 font-semibold text-yellow-400">{pct(r.podium_accuracy)}</td>
                  <td className="py-2.5 px-3 font-semibold text-blue-400">{pct(r.top5_accuracy)}</td>
                  <td className="py-2.5 px-3 font-mono text-gray-200">{r.mean_abs_position_error.toFixed(2)}</td>
                  <td className="py-2.5 px-3 font-mono text-gray-200">{r.brier_score_win.toFixed(3)}</td>
                  <td className="py-2.5 px-3">
                    {rBeats === null ? (
                      <span className="text-gray-500">n/a</span>
                    ) : rBeats ? (
                      <span className="text-green-400 flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" /> beats
                      </span>
                    ) : (
                      <span className="text-red-400 flex items-center gap-1">
                        <TrendingDown className="w-3 h-3" /> does not beat
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-bold text-gray-200 mb-4 uppercase tracking-wide">
          Baseline Comparison ({latest.season})
        </h3>
        <table className="w-full text-xs text-left">
          <thead>
            <tr className="border-b border-gray-700 text-gray-400">
              <th className="py-2 px-3">Baseline</th>
              <th className="py-2 px-3">Winner Acc</th>
              <th className="py-2 px-3">MAE</th>
              <th className="py-2 px-3">Model Δ Winner</th>
              <th className="py-2 px-3">Model Δ MAE</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(latest.baselines || {}).map(([name, b]) => {
              const comp = latest.comparison?.[name];
              return (
                <tr key={name} className="border-b border-gray-700/50">
                  <td className="py-2.5 px-3 font-semibold text-white capitalize">
                    {name.replace(/_/g, ' ')}
                  </td>
                  <td className="py-2.5 px-3 text-gray-300">{pct(b.winner_accuracy)}</td>
                  <td className="py-2.5 px-3 font-mono text-gray-300">{b.mae_position.toFixed(2)}</td>
                  <td className={`py-2.5 px-3 font-mono ${(comp?.winner_accuracy_delta ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {comp ? ((comp.winner_accuracy_delta >= 0 ? '+' : '') + (comp.winner_accuracy_delta * 100).toFixed(1) + '%') : '—'}
                  </td>
                  <td className={`py-2.5 px-3 font-mono ${(comp?.mae_delta ?? 0) <= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {comp ? ((comp.mae_delta >= 0 ? '+' : '') + comp.mae_delta.toFixed(2)) : '—'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div className="mt-3 flex items-center gap-2 text-[10px] text-gray-500">
          <BeatIcon className="w-3 h-3" />
          <span>
            A negative MAE delta means the model beats the baseline (fewer positions of error on
            average). Probabilistic metrics are Monte Carlo estimates with{' '}
            {latest.n_simulations.toLocaleString()} simulations per race (seed {latest.simulation_seed}).
          </span>
        </div>
      </div>
    </div>
  );
};
