import React from 'react';
import { Flag, Calendar, MapPin, Timer, Trophy } from 'lucide-react';
import { useNextRace, useSeasonRaces } from '../hooks/useRace';
import { CircuitSVG } from '../components/CircuitSVG';
import { LoadingState, EmptyState, StatusPill } from '../components/ui';

export const Race: React.FC = () => {
  const { race, loading } = useNextRace();
  const { races: seasonRaces, loading: calLoading } = useSeasonRaces(2026);

  if (loading) {
    return <LoadingState label="Loading weekend brief..." />;
  }

  if (!race) {
    return <EmptyState title="No race scheduled" body="Next race data is unavailable right now." />;
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <section className="panel-strong overflow-hidden">
        <div className="h-[3px] bg-gradient-to-r from-[#E10600] via-[#E10600]/40 to-transparent" />
        <div className="p-5 sm:p-7 flex flex-col lg:flex-row gap-6">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <StatusPill tone="live">Next up · Round {race.round_number}</StatusPill>
              <span className="text-[11px] font-mono text-[#636973]">{race.season_year} SEASON</span>
              {race.is_sprint_weekend && <StatusPill tone="warn">Sprint</StatusPill>}
              <StatusPill tone="muted">{race.status}</StatusPill>
            </div>
            <h1 className="font-display font-bold text-white text-[30px] sm:text-[38px] tracking-tight leading-none mt-3">{race.name}</h1>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 mt-5 text-[13px]">
              <div className="panel px-3 py-2.5 flex items-center gap-2"><Calendar className="w-4 h-4 text-[#636973]" /><div><div className="text-[10px] font-bold text-[#636973] tracking-wide">DATE</div><div className="text-white font-semibold">{race.race_date || 'TBD'}</div></div></div>
              <div className="panel px-3 py-2.5 flex items-center gap-2"><MapPin className="w-4 h-4 text-[#636973]" /><div><div className="text-[10px] font-bold text-[#636973] tracking-wide">CIRCUIT</div><div className="text-white font-semibold truncate">{race.circuit?.name || 'TBD'}</div></div></div>
              <div className="panel px-3 py-2.5 flex items-center gap-2"><Flag className="w-4 h-4 text-[#636973]" /><div><div className="text-[10px] font-bold text-[#636973] tracking-wide">VENUE</div><div className="text-white font-semibold truncate">{race.circuit?.locality || ''}{race.circuit?.country ? `, ${race.circuit.country}` : 'TBD'}</div></div></div>
            </div>
          </div>
          <div className="w-full lg:w-[300px] shrink-0 panel p-3">
            <CircuitSVG circuitId={race.circuit?.id} className="w-full h-[130px]" />
            <div className="flex items-center gap-1.5 mt-2 px-1 text-[11px] font-mono text-[#636973]"><Timer className="w-3.5 h-3.5" />TRACK MAP · NOT TO SCALE</div>
          </div>
        </div>
      </section>

      <section className="panel p-5">
        <h2 className="eyebrow !text-[#9BA1AA] mb-4">Circuit characteristics</h2>
        {race.circuit ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 text-[13px]">
            <div className="bg-black/30 rounded-lg border border-white/[0.05] p-3"><div className="text-[10px] font-bold text-[#636973] tracking-wide">TYPE</div><div className="text-white font-mono font-semibold mt-1">{race.circuit.circuit_type || '—'}</div></div>
            <div className="bg-black/30 rounded-lg border border-white/[0.05] p-3"><div className="text-[10px] font-bold text-[#636973] tracking-wide">OVERTAKING</div><div className="text-white font-mono font-semibold mt-1">{race.circuit.overtaking_difficulty ?? '—'}</div></div>
            <div className="bg-black/30 rounded-lg border border-white/[0.05] p-3"><div className="text-[10px] font-bold text-[#636973] tracking-wide">LAT</div><div className="text-white font-mono font-semibold mt-1">{race.circuit.latitude ?? '—'}</div></div>
            <div className="bg-black/30 rounded-lg border border-white/[0.05] p-3"><div className="text-[10px] font-bold text-[#636973] tracking-wide">LON</div><div className="text-white font-mono font-semibold mt-1">{race.circuit.longitude ?? '—'}</div></div>
          </div>
        ) : (
          <p className="text-[13px] text-[#636973]">Circuit telemetry unavailable.</p>
        )}
      </section>

      <section className="panel overflow-hidden">
        <div className="px-4 sm:px-5 py-3.5 border-b border-white/[0.05] flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Trophy className="w-4 h-4 text-[#E10600]" />
            <h2 className="eyebrow !text-[#9BA1AA]">Race calendar</h2>
          </div>
          <span className="text-[11px] font-mono text-[#636973]">{seasonRaces.filter((r) => r.status === 'completed').length}/{seasonRaces.length || '—'} COMPLETE</span>
        </div>
        {calLoading ? (
          <div className="p-6 text-center text-[13px] text-[#636973]">Loading calendar...</div>
        ) : seasonRaces.length === 0 ? (
          <div className="p-6 text-center text-[13px] text-[#636973]">No races found for this season.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="timing-table min-w-[560px]">
              <thead><tr><th className="!text-center w-14">Rnd</th><th>Grand Prix</th><th>Venue</th><th className="!text-right">Date</th><th className="!text-right">Format</th><th className="!text-right">Status</th></tr></thead>
              <tbody>
                {seasonRaces.map((r) => {
                  const isNext = r.id === race.id;
                  return (
                    <tr key={r.id} className={isNext ? 'bg-[#E10600]/[0.07]' : ''}>
                      <td className="!text-center"><span className={`inline-flex w-7 h-7 items-center justify-center rounded-md font-display font-bold text-[13px] ${isNext ? 'bg-[#E10600]/15 text-[#FF6B61]' : r.status === 'completed' ? 'bg-white/[0.05] text-[#9BA1AA]' : 'bg-white/[0.03] text-[#636973]'}`}>{r.round_number}</span></td>
                      <td><div className="flex items-center gap-2.5"><span className="w-[3px] h-7 rounded-full" style={{ backgroundColor: isNext ? '#E10600' : r.status === 'completed' ? '#3a424d' : '#232a33' }} /><span className={`font-bold text-[14px] ${isNext ? 'text-white' : 'text-[#c7ccd2]'}`}>{r.name}</span>{isNext && <span className="text-[10px] bg-[#E10600]/20 text-[#FF6B61] px-1.5 py-0.5 rounded font-bold">NEXT</span>}</div></td>
                      <td className="text-[#636973]">{r.circuit?.country || '—'}</td>
                      <td className="num text-[#9BA1AA]">{r.race_date || 'TBD'}</td>
                      <td className="!text-right">{r.is_sprint_weekend ? <span className="text-[10px] font-bold text-[#F5B942] border border-[#F5B942]/25 bg-[#F5B942]/10 px-1.5 py-0.5 rounded-full">SPRINT</span> : <span className="text-[10px] font-bold text-[#636973] border border-white/10 bg-white/[0.03] px-1.5 py-0.5 rounded-full">GP</span>}</td>
                      <td className="!text-right">{r.status === 'completed' ? <span className="text-[11px] font-bold text-[#636973]">DONE</span> : isNext ? <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-[#FF6B61]"><span className="live-dot" />NEXT</span> : <span className="text-[11px] font-bold text-[#9BA1AA]">UPCOMING</span>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};
