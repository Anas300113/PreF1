export const formatProbability = (val: number): string => {
  return `${(val * 100).toFixed(1)}%`;
};

export const formatPosition = (pos: number): string => {
  const rounded = Math.round(pos);
  if (rounded === 1) return 'P1';
  if (rounded === 2) return 'P2';
  if (rounded === 3) return 'P3';
  return `P${rounded}`;
};

export const formatPoints = (pts: number): string => {
  return `${pts.toFixed(1)} pts`;
};
