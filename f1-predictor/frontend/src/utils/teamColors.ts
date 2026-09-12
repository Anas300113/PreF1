export const TEAM_COLORS: Record<string, string> = {
  mclaren: '#FF8000',
  red_bull: '#3671C6',
  ferrari: '#E8002D',
  mercedes: '#27F4D2',
  aston_martin: '#229971',
  alpine: '#FF87BC',
  haas: '#B6BABD',
  rb: '#6692FF',
  williams: '#64C4FF',
  sauber: '#52E252',
  cadillac: '#C9CDD1',
};

export const getTeamColor = (teamId: string): string =>
  TEAM_COLORS[teamId.toLowerCase()] ?? '#9CA3AF';
