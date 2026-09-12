import React from 'react';
import { DriverPrediction } from '../types';
import { ProbabilityBar } from './ProbabilityBar';

interface DriverCardProps {
  driver: DriverPrediction;
  onClick?: () => void;
  selected?: boolean;
}

export const DriverCard: React.FC<DriverCardProps> = ({ driver, onClick, selected }) => {
  return (
    <div
      onClick={onClick}
      className={`bg-gray-800 border ${
        selected ? 'border-f1-red shadow-lg shadow-f1-red/20' : 'border-gray-700 hover:border-gray-600'
      } rounded-lg p-4 transition-all cursor-pointer relative overflow-hidden`}
    >
      <div
        className="absolute top-0 left-0 bottom-0 w-1.5"
        style={{ backgroundColor: driver.team_color }}
      />
      <div className="pl-2">
        <div className="flex justify-between items-start mb-2">
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-black text-xl text-white">{driver.code}</span>
              <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-300 font-medium">
                {driver.team}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">{driver.full_name}</p>
          </div>
          <div className="text-right">
            <span className="text-2xl font-black text-yellow-400">
              {(driver.win_probability * 100).toFixed(1)}%
            </span>
            <p className="text-[10px] text-gray-400 font-medium uppercase tracking-wider">Win Prob</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 my-3 text-xs bg-gray-900/60 p-2 rounded border border-gray-700/50">
          <div>
            <span className="text-gray-400 block text-[10px]">EXPECTED POS</span>
            <span className="font-bold text-white text-sm">P{driver.expected_position.toFixed(1)}</span>
          </div>
          <div>
            <span className="text-gray-400 block text-[10px]">EXP POINTS</span>
            <span className="font-bold text-white text-sm">{driver.expected_points.toFixed(1)} pts</span>
          </div>
        </div>

        <ProbabilityBar
          win={driver.win_probability}
          podium={driver.podium_probability}
          top5={driver.top5_probability}
          points={driver.points_probability}
          dnf={driver.dnf_probability}
        />
      </div>
    </div>
  );
};
