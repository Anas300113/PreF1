import React from 'react';

export const SectionHeader: React.FC<{ eyebrow: string; title: string; right?: React.ReactNode; icon?: React.ReactNode }> = ({ eyebrow, title, right, icon }) => (
  <div className="flex items-end justify-between gap-4">
    <div className="flex items-center gap-3 min-w-0">
      {icon && <span className="w-9 h-9 rounded-[10px] bg-[#15191F] border border-[rgba(255,255,255,0.08)] flex items-center justify-center text-[#E10600] shrink-0">{icon}</span>}
      <div className="min-w-0">
        <div className="eyebrow">{eyebrow}</div>
        <h2 className="font-display font-bold text-white text-lg leading-tight tracking-tight truncate">{title}</h2>
      </div>
    </div>
    {right && <div className="shrink-0">{right}</div>}
  </div>
);

export const StatusPill: React.FC<{ tone?: 'live' | 'ok' | 'warn' | 'muted'; children: React.ReactNode }> = ({ tone = 'muted', children }) => {
  const map: Record<string, string> = {
    live: 'bg-[#E10600]/10 text-[#FF6B61] border-[#E10600]/30',
    ok: 'bg-[#20C997]/10 text-[#20C997] border-[#20C997]/25',
    warn: 'bg-[#F5B942]/10 text-[#F5B942] border-[#F5B942]/25',
    muted: 'bg-white/[0.04] text-[#9BA1AA] border-white/10',
  };
  return <span className={`inline-flex items-center gap-1.5 text-[11px] font-bold tracking-wide px-2.5 py-1 rounded-full border ${map[tone]}`}>{tone === 'live' && <span className="live-dot" />}{children}</span>;
};

export const LoadingState: React.FC<{ label?: string }> = ({ label = 'Loading timing data...' }) => (
  <div className="flex items-center justify-center min-h-[40vh]" role="status" aria-live="polite">
    <div className="text-center space-y-4 animate-fade-in">
      <div className="w-10 h-10 border-[3px] border-[#E10600] border-t-transparent rounded-full animate-spin mx-auto" />
      <p className="text-[13px] text-[#9BA1AA] font-medium">{label}</p>
    </div>
  </div>
);

export const EmptyState: React.FC<{ title: string; body: string }> = ({ title, body }) => (
  <div className="panel p-10 text-center space-y-2">
    <p className="text-white font-bold">{title}</p>
    <p className="text-[13px] text-[#9BA1AA] max-w-md mx-auto">{body}</p>
  </div>
);
