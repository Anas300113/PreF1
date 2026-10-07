import React from 'react';

interface QualifyingGridProps {
  grid: Array<{ driver_id: string; code: string; expected_position: number }>;
}

export const QualifyingGrid: React.FC<QualifyingGridProps> = ({ grid }) => {
  const sorted = [...grid].sort((a, b) => a.expected_position - b.expected_position);
  return (
    <div className="panel overflow-hidden">
      <div className="px-4 py-3 border-b border-white/[0.05] flex items-center justify-between">
        <h3 className="eyebrow !text-[#9BA1AA]">Qualifying · Q3 pace</h3>
        <span className="text-[11px] font-mono text-[#636973]">GAP TO POLE</span>
      </div>
      <div className="overflow-x-auto">
        <table className="timing-table min-w-[420px]">
          <thead><tr><th className="!text-center w-14">Grid</th><th>Driver</th><th className="!text-right">Gap</th></tr></thead>
          <tbody>
            {sorted.map((item, idx) => (
              <tr key={item.driver_id}>
                <td className="!text-center"><span className={`inline-flex w-8 h-7 items-center justify-center rounded-md font-mono font-bold text-[12px] ${idx === 0 ? 'bg-[#E10600]/15 text-[#FF6B61]' : 'bg-white/[0.05] text-white'}`}>P{idx + 1}</span></td>
                <td className="font-bold text-white text-[13.5px]">{item.code}</td>
                <td className="num text-[#9BA1AA]">{idx === 0 ? 'POLE' : `+${(idx * 0.12).toFixed(3)}`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
