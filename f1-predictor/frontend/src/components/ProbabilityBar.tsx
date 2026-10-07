import React from 'react';

interface ProbabilityBarProps {
  win: number;
  podium: number;
  top5: number;
  points: number;
  dnf: number;
}

export const ProbabilityBar: React.FC<ProbabilityBarProps> = ({
  win,
  podium,
  top5,
  points,
  dnf,
}) => {
  const winPct = win * 100;
  const podiumNonWin = Math.max(0, (podium - win) * 100);
  const top5NonPodium = Math.max(0, (top5 - podium) * 100);
  const pointsNonTop5 = Math.max(0, (points - top5) * 100);
  const dnfPct = dnf * 100;

  return (
    <div className="w-full">
      <div className="h-[5px] w-full bg-black/40 rounded-full overflow-hidden flex border border-white/[0.05]">
        <div style={{ width: `${winPct}%` }} className="bg-[#E10600]" title={`Win: ${winPct.toFixed(1)}%`} />
        <div style={{ width: `${podiumNonWin}%` }} className="bg-[#F5B942]" title={`Podium: ${(podium * 100).toFixed(1)}%`} />
        <div style={{ width: `${top5NonPodium}%` }} className="bg-[#9BA1AA]" title={`Top 5: ${(top5 * 100).toFixed(1)}%`} />
        <div style={{ width: `${pointsNonTop5}%` }} className="bg-[#3a424d]" title={`Points: ${(points * 100).toFixed(1)}%`} />
        <div style={{ width: `${dnfPct}%` }} className="bg-[#5b2330]" title={`DNF: ${dnfPct.toFixed(1)}%`} />
      </div>
    </div>
  );
};
