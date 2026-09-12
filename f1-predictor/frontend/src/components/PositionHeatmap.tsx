import React from 'react';
import { DriverPrediction } from '../types';

interface PositionHeatmapProps {
  drivers: DriverPrediction[];
}

export const PositionHeatmap: React.FC<PositionHeatmapProps> = ({ drivers }) => {
  const positions = Array.from({ length: 20 }, (_, i) => i + 1);

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 overflow-x-auto">
      <h3 className="text-sm font-bold text-gray-200 mb-3 tracking-wide uppercase">
        Finishing Position Probability Heatmap
      </h3>
      <table className="w-full text-xs text-left">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="py-2 px-2 text-gray-400 font-semibold sticky left-0 bg-gray-800">Driver</th>
            {positions.map((p) => (
              <th key={p} className="py-2 px-1 text-center text-gray-400 font-semibold min-w-[28px]">
                P{p}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {drivers.map((d) => (
            <tr key={d.driver_id} className="border-b border-gray-700/50 hover:bg-gray-750">
              <td className="py-1.5 px-2 font-bold text-white sticky left-0 bg-gray-800 flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.team_color }} />
                <span>{d.code}</span>
              </td>
              {positions.map((p) => {
                const prob = d.position_distribution[p.toString()] || 0;
                const alpha = Math.min(1.0, prob * 2.5);
                return (
                  <td
                    key={p}
                    className="py-1.5 px-1 text-center font-mono text-[10px] text-white/90 transition-colors"
                    style={{
                      backgroundColor: prob > 0.01 ? `rgba(225, 6, 0, ${alpha})` : 'transparent',
                    }}
                    title={`${d.code} P${p}: ${(prob * 100).toFixed(1)}%`}
                  >
                    {prob > 0.02 ? (prob * 100).toFixed(0) : ''}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
