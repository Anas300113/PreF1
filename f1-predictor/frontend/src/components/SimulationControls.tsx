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
    <div className="panel px-3 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
      <div className="flex items-center gap-2 min-w-0">
        <Cpu className="w-4 h-4 text-[#E10600] shrink-0" />
        <span className="font-bold text-[#9BA1AA] tracking-wide">SAMPLE SIZE</span>
        <div className="flex gap-1" role="group" aria-label="Simulation count">
          {[10000, 50000, 100000, 500000].map((c) => (
            <button
              key={c}
              onClick={() => onSimCountChange(c)}
              aria-pressed={simCount === c}
              className={`px-2.5 py-1.5 rounded-md font-mono text-[11px] font-bold transition-colors min-h-[32px] ${
                simCount === c
                  ? 'bg-[#E10600] text-white'
                  : 'bg-white/[0.05] text-[#9BA1AA] hover:bg-white/[0.09] hover:text-white'
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
        className="btn-ghost flex items-center gap-1.5 disabled:opacity-50 min-h-[36px]"
      >
        <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        <span>Refresh</span>
      </button>
    </div>
  );
};
