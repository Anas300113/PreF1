import React, { useMemo } from 'react';

interface CircuitSVGProps {
  circuitId?: string;
  className?: string;
}

// Simplified circuit outlines (normalized coordinates)
// In production, these would be loaded from the racetrack-database CSVs
const CIRCUIT_OUTLINES: Record<string, { path: string; viewBox: string }> = {
  madring: {
    path: 'M 30,50 Q 30,20 60,20 Q 90,20 90,40 Q 90,60 70,65 Q 50,70 40,85 Q 30,100 50,110 Q 70,120 100,115 Q 130,110 140,90 Q 150,70 130,55 Q 110,40 100,30 Q 90,20 110,15 Q 140,10 160,25 Q 180,40 175,60 Q 170,80 150,90 Q 130,100 120,110',
    viewBox: '0 0 200 130',
  },
  monza: {
    path: 'M 20,60 L 40,30 L 80,25 L 120,20 L 160,30 L 180,50 L 170,70 L 140,80 L 100,85 L 60,90 L 30,80 Z',
    viewBox: '0 0 200 110',
  },
  spa: {
    path: 'M 20,70 Q 40,30 80,25 Q 120,20 140,40 Q 160,60 150,80 Q 140,100 110,105 Q 80,110 60,100 Q 40,90 20,70',
    viewBox: '0 0 170 130',
  },
  silverstone: {
    path: 'M 30,80 Q 50,40 90,30 Q 130,20 150,40 Q 170,60 160,80 Q 150,100 120,105 Q 90,110 70,100 Q 50,90 30,80',
    viewBox: '0 0 180 130',
  },
  suzuka: {
    path: 'M 40,30 Q 80,20 120,30 Q 160,40 170,60 Q 160,50 140,60 Q 120,70 100,65 Q 80,60 60,70 Q 40,80 30,60 Q 20,40 40,30',
    viewBox: '0 0 180 100',
  },
  default: {
    path: 'M 30,60 Q 60,20 100,25 Q 140,30 160,50 Q 170,70 150,85 Q 120,100 80,95 Q 40,90 30,60',
    viewBox: '0 0 180 120',
  },
};

export const CircuitSVG: React.FC<CircuitSVGProps> = ({ circuitId, className = '' }) => {
  const circuit = CIRCUIT_OUTLINES[circuitId || 'default'] || CIRCUIT_OUTLINES.default;

  return (
    <svg
      className={className}
      viewBox={circuit.viewBox}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Circuit map"
      preserveAspectRatio="xMidYMid meet"
    >
      {/* Track outline */}
      <path
        d={circuit.path}
        stroke="rgba(255,255,255,0.22)"
        strokeWidth="7"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <path
        d={circuit.path}
        stroke="#0B0E13"
        strokeWidth="4.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      {/* Racing line */}
      <path
        d={circuit.path}
        stroke="rgba(225,6,0,0.55)"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
        strokeDasharray="5 7"
      />
      {/* Start marker */}
      <circle cx="30" cy="60" r="3" fill="#F5F6F7" opacity="0.85" />
    </svg>
  );
};
