import React from 'react';
import { DriverPrediction } from '../types';
import { ProbabilityBar } from './ProbabilityBar';

export const DriverCard: React.FC<{ driver: DriverPrediction; onClick?: () => void; selected?: boolean }> = ({ driver, onClick, selected }) => {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={!!selected}
      className={`w-full text-left panel p-4 transition-all cursor-pointer relative overflow-hidden hover:border-[rgba(255,255,255,0.14)] ${selected ? 'border-[#E10600]/50 shadow-[0_0_24px_rgba(225,6,0,0.18)]' : ''}`}
    >
      <div className="flex gap-3">
        <span aria-hidden className="w-[3px] rounded-full shrink-0" style={{ backgroundColor: driver.team_color }} />
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start gap-2">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-display font-bold text-[17px] text-white tracking-tight">{driver.code}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.06] text-[#9BA1AA] font-semibold uppercase tracking-wide truncate max-w-[110px]">{driver.team}</span>
              </div>
              <p className="text-[12px] text-[#636973] truncate">{driver.full_name}</p>
            </div>
            <div className="text-right shrink-0">
              <div className="text-[22px] leading-none font-display font-bold text-white tnum">{(driver.win_probability * 100).toFixed(1)}<span className="text-[13px] text-[#9BA1AA]">%</span></div>
              <p className="text-[10px] text-[#636973] font-semibold uppercase tracking-wider mt-1">Win</p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2 my-3 text-center">
            <div className="bg-black/30 rounded-md py-1.5 border border-white/[0.04]"><div className="text-[10px] text-[#636973] font-semibold">EXP POS</div><div className="font-mono font-bold text-white text-[13px]">P{driver.expected_position.toFixed(1)}</div></div>
            <div className="bg-black/30 rounded-md py-1.5 border border-white/[0.04]"><div className="text-[10px] text-[#636973] font-semibold">EXP PTS</div><div className="font-mono font-bold text-white text-[13px]">{driver.expected_points.toFixed(1)}</div></div>
            <div className="bg-black/30 rounded-md py-1.5 border border-white/[0.04]"><div className="text-[10px] text-[#636973] font-semibold">PODIUM</div><div className="font-mono font-bold text-white text-[13px]">{(driver.podium_probability * 100).toFixed(0)}%</div></div>
          </div>
          <ProbabilityBar win={driver.win_probability} podium={driver.podium_probability} top5={driver.top5_probability} points={driver.points_probability} dnf={driver.dnf_probability} />
        </div>
      </div>
    </button>
  );
};

