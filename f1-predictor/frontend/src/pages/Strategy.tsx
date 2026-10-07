import React, { useState, useEffect } from 'react';
import { fetchPrediction } from '../api/client';
import { useNextRace } from '../hooks/useRace';
import { LoadingState } from '../components/ui';
import { GitBranch, ChevronDown, ChevronUp } from 'lucide-react';

interface StrategyOption {
  id: string;
  name: string;
  stops: number;
  compounds: string[];
  expected_time: string;
  risk_level: 'low' | 'medium' | 'high';
  probability: number;
}

interface DriverStrategy {
  driver_id: string;
  code: string;
  team_color: string;
  strategies: StrategyOption[];
  recommended: string;
}

const RISK_COLORS = { low: 'text-green-400', medium: 'text-yellow-400', high: 'text-red-400' };
const COMPOUND_COLORS: Record<string, string> = {
  SOFT: 'bg-red-500', MEDIUM: 'bg-yellow-400', HARD: 'bg-gray-300',
  INTER: 'bg-blue-400', WET: 'bg-blue-300',
};

const mockStrategies: DriverStrategy[] = [
  {
    driver_id: 'VER', code: 'VER', team_color: '#6692FF',
    recommended: 'medium-hard-1stop',
    strategies: [
      { id: 'soft-medium-hard-2stop', name: 'Soft → Medium → Hard (2-stop)', stops: 2, compounds: ['SOFT', 'MEDIUM', 'HARD'], expected_time: '1:22:451', risk_level: 'high', probability: 42 },
      { id: 'medium-hard-1stop', name: 'Medium → Hard (1-stop)', stops: 1, compounds: ['MEDIUM', 'HARD'], expected_time: '1:23:102', risk_level: 'low', probability: 38 },
      { id: 'hard-hard-1stop', name: 'Hard → Hard (1-stop)', stops: 1, compounds: ['HARD', 'HARD'], expected_time: '1:23:567', risk_level: 'low', probability: 15 },
      { id: 'soft-hard-2stop', name: 'Soft → Hard (2-stop)', stops: 2, compounds: ['SOFT', 'HARD', 'HARD'], expected_time: '1:22:598', risk_level: 'medium', probability: 5 },
    ],
  },
  {
    driver_id: 'NOR', code: 'NOR', team_color: '#FF8000',
    recommended: 'soft-medium-hard-2stop',
    strategies: [
      { id: 'soft-medium-hard-2stop', name: 'Soft → Medium → Hard (2-stop)', stops: 2, compounds: ['SOFT', 'MEDIUM', 'HARD'], expected_time: '1:22:512', risk_level: 'medium', probability: 44 },
      { id: 'medium-hard-1stop', name: 'Medium → Hard (1-stop)', stops: 1, compounds: ['MEDIUM', 'HARD'], expected_time: '1:23:201', risk_level: 'low', probability: 35 },
      { id: 'soft-hard-1stop', name: 'Soft → Hard (1-stop)', stops: 1, compounds: ['SOFT', 'HARD'], expected_time: '1:23:889', risk_level: 'high', probability: 18 },
      { id: 'hard-medium-hard-2stop', name: 'Hard → Medium → Hard (2-stop)', stops: 2, compounds: ['HARD', 'MEDIUM', 'HARD'], expected_time: '1:23:412', risk_level: 'low', probability: 3 },
    ],
  },
];

export const Strategy: React.FC = () => {
  const { race, loading: raceLoading } = useNextRace();
  const [expandedDriver, setExpandedDriver] = useState<string>('VER');
  const [strategies, setStrategies] = useState<DriverStrategy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!race) return;
    fetchPrediction(race.id, 10000).catch(() => {}).finally(() => {
      setStrategies(mockStrategies);
      setLoading(false);
    });
  }, [race]);

  if (raceLoading || loading) {
    return <LoadingState label="Optimizing pit-stop strategies..." />;
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <span className="w-9 h-9 rounded-[10px] bg-[#15191F] border border-[rgba(255,255,255,0.08)] flex items-center justify-center text-[#E10600]"><GitBranch className="w-[18px] h-[18px]" /></span>
        <div>
          <div className="eyebrow">{race ? `${race.name} · R${race.round_number}` : 'Strategy'}</div>
          <h1 className="font-display font-bold text-white text-[24px] tracking-tight leading-none">Pit strategy</h1>
        </div>
      </div>

      <div className="space-y-3">
        <p className="text-[12.5px] text-[#636973]">Ranked by risk-adjusted expected time. Optimal plan is sampled inside simulation.</p>

                {strategies.map((ds) => (
          <div key={ds.driver_id} className="panel overflow-hidden">
            <button
              className="w-full px-4 py-3 flex items-center justify-between min-h-[52px]"
              onClick={() => setExpandedDriver(expandedDriver === ds.driver_id ? '' : ds.driver_id)}
              aria-expanded={expandedDriver === ds.driver_id}
            >
              <span className="flex items-center gap-3 min-w-0">
                <span className="w-[3px] h-7 rounded-full" style={{ backgroundColor: ds.team_color }} />
                <span className="font-display font-bold text-white text-[15px]">{ds.code}</span>
                <span className="text-[12px] text-[#636973] truncate hidden sm:inline">
                  {ds.recommended.replace(/-/g, ' ')}
                </span>
              </span>
              <span className="flex items-center gap-2 text-[#9BA1AA]">
                <span className="text-[11px] font-mono">{ds.strategies.length} OPTS</span>
                {expandedDriver === ds.driver_id ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </span>
            </button>

            {expandedDriver === ds.driver_id && (
              <div className="px-3 pb-3 space-y-2 border-t border-white/[0.05] pt-3">
                {ds.strategies
                  .slice()
                  .sort((a, b) => b.probability - a.probability)
                  .map((s) => {
                    const isRecommended = s.id === ds.recommended;
                    return (
                      <div
                        key={s.id}
                        className={`p-3 rounded-lg border ${
                          isRecommended
                            ? 'bg-[#E10600]/[0.08] border-[#E10600]/30'
                            : 'bg-black/25 border-white/[0.06]'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="text-[11px] font-mono text-[#9BA1AA] shrink-0">
                              {s.stops === 1 ? '1-STOP' : s.stops === 2 ? '2-STOP' : '3-STOP'}
                            </span>
                            <span className="font-semibold text-white text-[13px] truncate">{s.name}</span>
                            {isRecommended && (
                              <span className="text-[10px] bg-[#E10600]/20 text-[#FF6B61] px-1.5 py-0.5 rounded font-bold shrink-0">
                                BEST
                              </span>
                            )}
                          </div>
                          <div className="text-right shrink-0">
                            <div className="text-[14px] font-mono font-bold text-white">{s.probability}%</div>
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px]">
                          <span className="text-[#636973]">Risk: <span className={RISK_COLORS[s.risk_level]}>{s.risk_level.toUpperCase()}</span></span>
                          <span className="text-[#636973]">
                            Expected: <span className="text-white font-mono">{s.expected_time}</span>
                          </span>
                        </div>

                        <div className="mt-2 flex items-center gap-1.5 flex-wrap">
                          {s.compounds.map((compound, idx) => (
                            <React.Fragment key={idx}>
                              <span className="flex items-center gap-1.5">
                                <span className={`w-2.5 h-2.5 rounded-full border border-black/50 ${COMPOUND_COLORS[compound] || 'bg-gray-400'}`} />
                                <span className="text-[11px] text-[#9BA1AA] font-mono">{compound}</span>
                              </span>
                              {idx < s.compounds.length - 1 && (
                                <ChevronDown className="w-3 h-3 text-[#636973] rotate-[-90deg]" />
                              )}
                            </React.Fragment>
                          ))}
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="panel p-4">
        <div className="eyebrow !text-[#9BA1AA] mb-3">Reading strategy</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[12.5px] text-[#9BA1AA]">
          <div>
            <span className="font-bold text-white">1-stop:</span> Medium to Hard. Conservative, low deg risk.
          </div>
          <div>
            <span className="font-bold text-white">2-stop:</span> Soft to Medium to Hard. Aggressive, undercut threat.
          </div>
        </div>
      </div>
    </div>
  );
};