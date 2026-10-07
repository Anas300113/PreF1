import { useState, useEffect } from 'react';
import { Race } from '../types';
import { fetchNextRace, fetchRaces } from '../api/client';

export const useNextRace = () => {
  const [race, setRace] = useState<Race | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNextRace()
      .then(setRace)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { race, loading, error };
};

export const useSeasonRaces = (season: number) => {
  const [races, setRaces] = useState<Race[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchRaces(season)
      .then(setRaces)
      .catch(() => setRaces([]))
      .finally(() => setLoading(false));
  }, [season]);

  return { races, loading };
};
