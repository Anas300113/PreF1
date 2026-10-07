import React from 'react';
import { DriverPrediction } from '../types';

interface PositionHeatmapProps {
  drivers: DriverPrediction[];
}

export const PositionHeatmap: React.FC<PositionHeatmapProps> = ({ drivers }) => {
  const positions = Array.from({ length: 20 }, (_, i) => i + 1);

  return (
    <div className="panel overflow-hidden">
      <div className="px-4 py-3 border-b border-white/[0.05] flex items-center justify-between">
        <h3 className="eyebrow !text-[#9BA1AA]">Position distribution</h3>
        <span className="text-[11px] font-mono text-[#636973]">P1–P20</span>
      </div>
      <div className="overflow-x-auto">
      <table className="w-full text-xs text-left min-w-[640px]">
        <thead>
          <tr className="border-b border-white/[0.06]">
            <th className="py-2 px-2 text-[#636973] font-bold sticky left-0 bg-[#0E1116] text-[10px] tracking-[0.12em]">DRIVER</th>
            {positions.map((p) => (
              <th key={p} className="py-2 px-1 text-center text-[#636973] font-mono font-semibold min-w-[30px] text-[10px]">
                {p}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {drivers.map((d) => (
            <tr key={d.driver_id} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
              <td className="py-1.5 px-2 font-bold text-white sticky left-0 bg-[#0E1116]">
                <span className="flex items-center gap-1.5">
                <span className="w-[3px] h-5 rounded-full" style={{ backgroundColor: d.team_color }} />
                <span className="text-[12px]">{d.code}</span>
                </span>
              </td>
              {positions.map((p) => {
                const prob = d.position_distribution[p.toString()] || 0;
                const alpha = Math.min(1.0, prob * 2.5);
                return (
                  <td
                    key={p}
                    className="py-1.5 px-1 text-center font-mono text-[10px] text-white/90"
                    style={{
                      backgroundColor: prob > 0.01 ? `rgba(225, 6, 0, ${alpha})` : 'transparent',
                    }}
                    title={`${d.code} P${p}: ${(prob * 100).toFixed(1)}%`}
                  >
                    {prob > 0.03 ? (prob * 100).toFixed(0) : ''}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
};
