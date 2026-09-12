import React from 'react';
import { Cpu, RefreshCw } from 'lucide-react';

interface SimulationControlsProps {
  simCount: number;
  onSimCountChange: (count: number) => void;
  onRun: () => void;
  loading?: boolean;
}

export const SimulationControls: React.FC<SimulationControlsProps> = ({
  simCount,
  onSimCountChange,
  onRun,
  loading,
}) => {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
      <div className="flex items-center space-x-2">
        <Cpu className="w-4 h-4 text-f1-red" />
        <span className="font-bold text-gray-300">MONTE CARLO SAMPLE SIZE:</span>
        <div className="flex space-x-1">
          {[10000, 50000, 100000, 500000].map((c) => (
            <button
              key={c}
              onClick={() => onSimCountChange(c)}
              className={`px-2.5 py-1 rounded font-mono text-[11px] font-semibold transition-colors ${
                simCount === c
                  ? 'bg-f1-red text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {c >= 1000 ? `${c / 1000}k` : c}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={onRun}
        disabled={loading}
        className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-1.5 px-3 rounded flex items-center space-x-1.5 transition-colors disabled:opacity-50"
      >
        <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        <span>Refresh Prediction</span>
      </button>
    </div>
  );
};
