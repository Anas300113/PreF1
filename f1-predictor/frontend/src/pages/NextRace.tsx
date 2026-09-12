import React, { useState, useEffect } from 'react';
import { fetchNextRace, fetchPrediction, runScenarioSimulation } from '../api/client';
import { Race, PredictionResponse, DriverPrediction } from '../types';
import { DriverCard } from '../components/DriverCard';
import { PositionHeatmap } from '../components/PositionHeatmap';
import { WeatherWidget } from '../components/WeatherWidget';
import { QualifyingGrid } from '../components/QualifyingGrid';
import { ScenarioPanel } from '../components/ScenarioPanel';
import { ExplanationPanel } from '../components/ExplanationPanel';
import { SimulationControls } from '../components/SimulationControls';
import { Trophy, AlertCircle } from 'lucide-react';

export const NextRace: React.FC = () => {
  const [race, setRace] = useState<Race | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [simCount, setSimCount] = useState<number>(10000);
  const [selectedDriver, setSelectedDriver] = useState<DriverPrediction | null>(null);

  useEffect(() => {
    loadData();
  }, [simCount]);

  const loadData = async () => {
    setLoading(true);
    try {
      const nextRaceData = await fetchNextRace();
      setRace(nextRaceData);
      const predData = await fetchPrediction(nextRaceData.id, simCount);
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

  if (prediction?.data_status === 'unavailable') {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center space-y-4">
        <h2 className="text-xl font-bold text-white">Prediction Unavailable</h2>
        <p className="text-gray-400 text-sm">{prediction.disclaimer}</p>
        <p className="text-gray-500 text-xs">
          Run <code className="text-f1-red">python scripts/ingest_historical.py</code> then{' '}
          <code className="text-f1-red">python scripts/train_models.py</code> to enable forecasts.
        </p>
      </div>
    );
  }

  if (loading && !prediction) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-f1-red border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-semibold text-gray-400">Running 10,000 Monte Carlo Race Simulations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Race Header Banner */}
      {race && (
        <div className="bg-gradient-to-r from-gray-800 via-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6 relative overflow-hidden">
          <div className="absolute right-0 top-0 bottom-0 w-64 bg-f1-red/10 blur-3xl rounded-full -mr-20 pointer-events-none" />
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2 text-xs font-bold text-f1-red tracking-wider uppercase mb-1">
                <span>ROUND {race.round_number}</span>
                <span>•</span>
                <span>{race.season_year} SEASON</span>
              </div>
              <h1 className="text-3xl font-black text-white tracking-tight">{race.name}</h1>
              <p className="text-sm text-gray-400 mt-1">
                {race.circuit?.name || 'Circuit'}, {race.circuit?.country || 'Grand Prix'}
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <span className="bg-green-500/10 text-green-400 border border-green-500/20 text-xs px-3 py-1.5 rounded-full font-semibold">
                ● SIMULATION ACTIVE ({prediction?.model.simulation_count.toLocaleString()} SIMS)
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Simulation Controls Bar */}
      <SimulationControls
        simCount={simCount}
        onSimCountChange={(c) => setSimCount(c)}
        onRun={loadData}
        loading={loading}
      />

      {/* Probability Cards Grid */}
      {prediction && (
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Trophy className="w-5 h-5 text-yellow-400" />
            <h2 className="text-lg font-bold text-white tracking-wide">
              DRIVER RACE FINISHING PROBABILITIES
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {prediction.drivers.map((driver) => (
              <DriverCard
                key={driver.driver_id}
                driver={driver}
                selected={selectedDriver?.driver_id === driver.driver_id}
                onClick={() => setSelectedDriver(driver)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Layout Grid: Heatmap + Details */}
      {prediction && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <PositionHeatmap drivers={prediction.drivers} />
            <QualifyingGrid grid={prediction.qualifying_prediction} />
          </div>

          <div className="space-y-6">
            <WeatherWidget weather={prediction.weather} />
            <ScenarioPanel onRunScenario={handleRunScenario} loading={loading} />
            <ExplanationPanel
              driverCode={selectedDriver?.code || 'NOR'}
              explanation={selectedDriver ? prediction.explanations[selectedDriver.driver_id] : undefined}
            />
          </div>
        </div>
      )}

      {/* Disclaimer Notice */}
      <div className="bg-gray-800/60 border border-gray-700/50 rounded-lg p-3 flex items-start space-x-2.5 text-xs text-gray-400">
        <AlertCircle className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
        <p>{prediction?.disclaimer}</p>
      </div>
    </div>
  );
};
