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
      <div className="h-2.5 w-full bg-gray-700 rounded-full overflow-hidden flex">
        <div style={{ width: `${winPct}%` }} className="bg-yellow-400" title={`Win: ${winPct.toFixed(1)}%`} />
        <div style={{ width: `${podiumNonWin}%` }} className="bg-blue-400" title={`Podium: ${(podium * 100).toFixed(1)}%`} />
        <div style={{ width: `${top5NonPodium}%` }} className="bg-green-400" title={`Top 5: ${(top5 * 100).toFixed(1)}%`} />
        <div style={{ width: `${pointsNonTop5}%` }} className="bg-purple-400" title={`Points: ${(points * 100).toFixed(1)}%`} />
        <div style={{ width: `${dnfPct}%` }} className="bg-red-500" title={`DNF: ${dnfPct.toFixed(1)}%`} />
      </div>
      <div className="flex justify-between text-[10px] text-gray-400 mt-1">
        <span>Win: {winPct.toFixed(1)}%</span>
        <span>Podium: {(podium * 100).toFixed(1)}%</span>
        <span>Top 5: {(top5 * 100).toFixed(1)}%</span>
        <span>DNF: {dnfPct.toFixed(1)}%</span>
      </div>
    </div>
  );
};
