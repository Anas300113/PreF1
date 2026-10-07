import React, { useState, useEffect } from 'react';
import { Users, Search } from 'lucide-react';
import { fetchPrediction } from '../api/client';
import { useNextRace } from '../hooks/useRace';
import { DriverPrediction } from '../types';
import { DriverCard } from '../components/DriverCard';
import { LoadingState, EmptyState } from '../components/ui';

export const Drivers: React.FC = () => {
  const { race } = useNextRace();
  const [drivers, setDrivers] = useState<DriverPrediction[]>([]);
  const [filtered, setFiltered] = useState<DriverPrediction[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (race) {
      setLoading(true);
      fetchPrediction(race.id, 10000)
        .then((pred) => {
          setDrivers(pred.drivers);
          setFiltered(pred.drivers);
        })
        .finally(() => setLoading(false));
    }
  }, [race]);

  useEffect(() => {
    if (!search) {
      setFiltered(drivers);
    } else {
      const lower = search.toLowerCase();
      setFiltered(drivers.filter(d =>
        d.code.toLowerCase().includes(lower) ||
        d.full_name.toLowerCase().includes(lower) ||
        d.team.toLowerCase().includes(lower)
      ));
    }
  }, [search, drivers]);

  if (loading) {
    return <LoadingState label="Loading driver market..." />;
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="w-9 h-9 rounded-[10px] bg-[#15191F] border border-[rgba(255,255,255,0.08)] flex items-center justify-center text-[#E10600]"><Users className="w-[18px] h-[18px]" /></span>
          <div>
            <div className="eyebrow">Field · {filtered.length} drivers</div>
            <h1 className="font-display font-bold text-white text-[24px] tracking-tight leading-none">Driver market</h1>
          </div>
        </div>
        <div className="relative w-full sm:w-[240px]">
          <Search className="w-4 h-4 text-[#636973] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search code, name, team..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search drivers"
            className="field !pl-9"
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="No drivers match" body="Try a different code, name, or team." />
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 stagger">
        {filtered.map((driver) => (
          <DriverCard key={driver.driver_id} driver={driver} />
        ))}
      </div>
      )}
    </div>
  );
};
