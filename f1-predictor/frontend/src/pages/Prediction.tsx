import React, { useState, useEffect } from 'react';
import { fetchPrediction, runScenarioSimulation } from '../api/client';
import { useNextRace } from '../hooks/useRace';
import { PredictionResponse, DriverPrediction } from '../types';
import { PositionHeatmap } from '../components/PositionHeatmap';
import { WeatherWidget } from '../components/WeatherWidget';
import { QualifyingGrid } from '../components/QualifyingGrid';
import { ScenarioPanel } from '../components/ScenarioPanel';
import { ExplanationPanel } from '../components/ExplanationPanel';
import { SimulationControls } from '../components/SimulationControls';
import { LoadingState, EmptyState } from '../components/ui';

export const Prediction: React.FC = () => {
  const { race } = useNextRace();
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
    const [simCount, setSimCount] = useState<number>(10000);
  const [selectedDriver, setSelectedDriver] = useState<DriverPrediction | null>(null);

  useEffect(() => {
    if (race) {
      loadData();
    }
  }, [race, simCount]);

  const loadData = async () => {
    if (!race) return;
    setLoading(true);
    try {
      const predData = await fetchPrediction(race.id, simCount);
      setPrediction(predData);
      if (predData.drivers.length > 0) {
        setSelectedDriver(predData.drivers[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleRunScenario = async (scenario: { weather: string; safetyCar: string; tyreDeg: string }) => {
    if (!race) return;
    setLoading(true);
    try {
      const predData = await runScenarioSimulation(race.id, {
        simulation_count: simCount,
        weather_override: scenario.weather,
        safety_car_override: scenario.safetyCar,
        tyre_deg_override: scenario.tyreDeg,
      });
      setPrediction(predData);
      if (predData.drivers.length > 0) {
        setSelectedDriver(predData.drivers[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (!race) {
    return <LoadingState label="Loading race data..." />;
  }

  if (prediction?.data_status === 'unavailable') {
    return <EmptyState title="Prediction unavailable" body={prediction.disclaimer} />;
  }

    if (loading && !prediction) {
    return <LoadingState label={`Running ${simCount.toLocaleString()} Monte Carlo simulations...`} />;
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {prediction && (
        <section className="panel-strong overflow-hidden">
          <div className="h-[3px] bg-gradient-to-r from-[#E10600] via-[#E10600]/40 to-transparent" />
          <div className="p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="eyebrow">Round {prediction.race.round_number} · {prediction.race.season_year}</div>
              <h1 className="font-display font-bold text-white text-[26px] sm:text-[32px] tracking-tight leading-none mt-1">{prediction.race.name}</h1>
              <p className="text-[13px] text-[#9BA1AA] mt-1.5">{prediction.race.circuit?.name}{prediction.race.circuit?.country && `, ${prediction.race.circuit.country}`}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1.5 rounded-full border bg-[#20C997]/10 text-[#20C997] border-[#20C997]/25"><span className="w-1.5 h-1.5 rounded-full bg-current" />{prediction.model.simulation_count.toLocaleString()} SIMS</span>
            </div>
          </div>
          <div className="px-5 sm:px-6 pb-5"><SimulationControls simCount={simCount} onSimCountChange={(c) => setSimCount(c)} onRun={loadData} loading={loading} /></div>
        </section>
      )}

      {prediction && (
        <section className="panel overflow-hidden">
          <div className="px-4 sm:px-5 py-3.5 border-b border-white/[0.05] flex items-center justify-between">
            <h2 className="eyebrow !text-[#9BA1AA]">Timing tower · win probability</h2>
            <span className="text-[11px] font-mono text-[#636973]">{prediction.drivers.length} DRIVERS</span>
          </div>
          <div className="overflow-x-auto">
            <table className="timing-table min-w-[720px]">
              <thead><tr><th className="!text-center w-12">Pos</th><th>Driver</th><th className="!text-right">Win</th><th className="!text-right">Podium</th><th className="!text-right">Top 5</th><th className="!text-right">Exp pos</th><th className="!text-right">Exp pts</th><th className="!text-right">DNF</th></tr></thead>
              <tbody>
                {[...prediction.drivers].sort((a, b) => b.win_probability - a.win_probability).map((driver, idx) => (
                  <tr key={driver.driver_id} onClick={() => setSelectedDriver(driver)} className={`cursor-pointer ${selectedDriver?.driver_id === driver.driver_id ? 'bg-[#E10600]/[0.07]' : ''}`}>
                    <td className="!text-center"><span className={`inline-flex w-7 h-7 items-center justify-center rounded-md font-display font-bold text-[13px] ${idx < 3 ? 'bg-[#E10600]/15 text-[#FF6B61]' : 'bg-white/[0.05] text-white'}`}>{idx + 1}</span></td>
                    <td><div className="flex items-center gap-2.5"><span className="w-[3px] h-7 rounded-full" style={{ backgroundColor: driver.team_color }} /><div><button className="font-bold text-white text-[14px] leading-none hover:underline" onClick={(e) => { e.stopPropagation(); setSelectedDriver(driver); }}>{driver.code}</button><div className="text-[11px] text-[#636973] mt-0.5">{driver.full_name} · {driver.team}</div></div></div></td>
                    <td className="num text-white font-bold">{(driver.win_probability * 100).toFixed(1)}%</td>
                    <td className="num text-[#9BA1AA]">{(driver.podium_probability * 100).toFixed(1)}%</td>
                    <td className="num text-[#9BA1AA]">{(driver.top5_probability * 100).toFixed(1)}%</td>
                    <td className="num text-[#9BA1AA]">P{driver.expected_position.toFixed(1)}</td>
                    <td className="num text-[#9BA1AA]">{driver.expected_points.toFixed(1)}</td>
                    <td className="num text-[#9BA1AA]">{(driver.dnf_probability * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {prediction && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-4">
            <PositionHeatmap drivers={prediction.drivers} />
            <QualifyingGrid grid={prediction.qualifying_prediction} />
          </div>
          <div className="space-y-4">
            <WeatherWidget weather={prediction.weather} />
            <ScenarioPanel onRunScenario={handleRunScenario} loading={loading} />
            <ExplanationPanel
              driverCode={selectedDriver?.code || 'NOR'}
              explanation={selectedDriver ? prediction.explanations[selectedDriver.driver_id] : undefined}
            />
          </div>
        </div>
      )}

      {prediction && (
        <div className="panel p-4">
          <div className="eyebrow mb-3">Model metadata</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-[12px]">
            <div><span className="text-[#636973]">Version</span><div className="text-white font-mono">{prediction.model.version}</div></div>
            <div><span className="text-[#636973]">Sim seed</span><div className="text-white font-mono tnum">{prediction.model.simulation_seed}</div></div>
            <div><span className="text-[#636973]">Features</span><div className="text-white font-mono">{prediction.model.feature_version}</div></div>
            <div><span className="text-[#636973]">Cutoff</span><div className="text-white font-mono">{prediction.model.training_cutoff}</div></div>
          </div>
        </div>
      )}

      {prediction && (
        <p className="text-[12px] text-[#636973] leading-relaxed">{prediction.disclaimer}</p>
      )}
    </div>
  );
};

