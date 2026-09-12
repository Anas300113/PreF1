import React, { useState, useEffect } from 'react';
import { fetchModelsInfo } from '../api/client';
import { Cpu, ShieldCheck, Layers, GitBranch } from 'lucide-react';

export const ModelInfo: React.FC = () => {
  const [info, setInfo] = useState<any>(null);

  useEffect(() => {
    fetchModelsInfo().then((data) => setInfo(data));
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <div className="flex items-center space-x-3">
        <Cpu className="w-6 h-6 text-f1-red" />
        <h1 className="text-2xl font-black text-white tracking-tight">
          PREF1 MACHINE LEARNING & SIMULATION ARCHITECTURE
        </h1>
      </div>

      {info && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 space-y-4">
          <div className="flex flex-wrap gap-4 text-xs font-mono">
            <span className="bg-f1-red/20 text-f1-red border border-f1-red/30 px-3 py-1.5 rounded font-bold">
              MODEL VERSION: {info.active_model_version}
            </span>
            <span className="bg-gray-700 text-gray-200 px-3 py-1.5 rounded font-bold">
              FEATURE VERSION: {info.feature_version}
            </span>
          </div>

          <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide pt-2">
            Modular Prediction Pipeline Architecture
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
            {info.components.map((c: any, i: number) => (
              <div key={i} className="bg-gray-900/60 border border-gray-700/50 rounded p-3 space-y-1">
                <span className="font-bold text-white block text-sm">{c.name}</span>
                <span className="text-gray-400 block font-mono">Type: {c.type}</span>
                <span className="text-gray-400 block font-mono">Target: {c.target || c.simulations}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 space-y-3 text-xs text-gray-300">
        <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-green-400" />
          <span>Statistically Honest Modelling Guarantees</span>
        </h3>
        <ul className="list-disc list-inside space-y-1.5 text-gray-400">
          <li>No giant single black-box driver-to-position model. Modular architecture separating driver, car, circuit, and strategy.</li>
          <li>Strict chronological validation. No temporal data leakage or lookahead bias during feature computation.</li>
          <li>Full probability calibration via isotonic regression. Measured via Brier score and Expected Calibration Error (ECE).</li>
          <li>High-performance vectorised Monte Carlo simulation using NumPy tensors over 10,000+ stochastic race runs.</li>
        </ul>
      </div>
    </div>
  );
};
