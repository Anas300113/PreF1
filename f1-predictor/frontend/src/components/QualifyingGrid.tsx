import React from 'react';

interface QualifyingGridProps {
  grid: Array<{ driver_id: string; code: string; expected_position: number }>;
}

export const QualifyingGrid: React.FC<QualifyingGridProps> = ({ grid }) => {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-bold text-gray-200 mb-3 tracking-wide uppercase">
        Predicted Qualifying Grid (Q3 Pace Model)
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {grid.map((item, idx) => (
          <div
            key={item.driver_id}
            className="flex items-center justify-between bg-gray-900/60 p-2.5 rounded border border-gray-700/50"
          >
            <div className="flex items-center space-x-2.5">
              <span className="font-extrabold text-f1-red text-sm w-6">P{idx + 1}</span>
              <span className="font-bold text-white text-sm">{item.code}</span>
            </div>
            <span className="text-xs text-gray-400 font-mono">
              {idx === 0 ? 'POLE' : `+${(idx * 0.12).toFixed(3)}s`}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
