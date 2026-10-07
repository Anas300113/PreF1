import os

# Write hooks/useRace.ts
hook_code = """import { useState, useEffect } from 'react';
import { Race } from '../types';
import { fetchNextRace } from '../api/client';

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
"""
with open('src/hooks/useRace.ts', 'w') as f:
    f.write(hook_code)
print("useRace.ts: OK")
