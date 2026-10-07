import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Flag, Trophy, Users, GitBranch, Cloud, Cpu, History, Crown, Menu, X } from 'lucide-react';

const PRIMARY = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/race', label: 'Race', icon: Flag },
  { path: '/prediction', label: 'Timing', icon: Trophy },
  { path: '/drivers', label: 'Drivers', icon: Users },
  { path: '/championship', label: 'Title', icon: Crown },
];
const SECONDARY = [
  { path: '/simulation', label: 'Simulator', icon: Trophy },
  { path: '/strategy', label: 'Strategy', icon: GitBranch },
  { path: '/weather', label: 'Weather', icon: Cloud },
  { path: '/model', label: 'Model', icon: Cpu },
  { path: '/backtesting', label: 'History', icon: History },
];

export const NavigationRail: React.FC = () => {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const isActive = (path: string) => (path === '/' ? location.pathname === '/' : location.pathname.startsWith(path));
  const linkCls = (active: boolean) => `relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13.5px] font-semibold transition-colors ${active ? 'bg-[#E10600]/10 text-white' : 'text-[#9BA1AA] hover:text-white hover:bg-white/[0.04]'}`;

  return (
    <>
      <nav aria-label="Primary" className="hidden lg:flex fixed left-0 top-0 bottom-0 w-[224px] flex-col bg-[#0B0E13] border-r border-[rgba(255,255,255,0.07)] z-50">
        <div className="px-5 pt-6 pb-4 border-b border-[rgba(255,255,255,0.06)]">
          <Link to="/" className="flex items-center gap-3">
            <span className="w-9 h-9 bg-[#E10600] rounded-[8px] flex items-center justify-center"><Flag className="w-4 h-4 text-white" /></span>
            <span>
              <span className="block text-white font-display font-bold text-[15px] leading-none">PreF1</span>
              <span className="block text-[10px] text-[#636973] uppercase tracking-[0.18em] mt-1">Race Intelligence</span>
            </span>
          </Link>
        </div>
        <div className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
          <div>
            <div className="px-2 mb-2 text-[10px] font-bold tracking-[0.16em] text-[#636973]">RACE WEEKEND</div>
            <div className="space-y-1">
              {PRIMARY.map((item) => {
                const active = isActive(item.path);
                const Icon = item.icon;
                return <Link key={item.path} to={item.path} aria-current={active ? 'page' : undefined} className={linkCls(active)}>{active && <span className="absolute left-0 top-2 bottom-2 w-[3px] rounded-full bg-[#E10600]" />}<Icon className="w-[18px] h-[18px]" /><span>{item.label}</span></Link>;
              })}
            </div>
          </div>
          <div>
            <div className="px-2 mb-2 text-[10px] font-bold tracking-[0.16em] text-[#636973]">ANALYSIS</div>
            <div className="space-y-1">
              {SECONDARY.map((item) => {
                const active = isActive(item.path);
                const Icon = item.icon;
                return <Link key={item.path} to={item.path} aria-current={active ? 'page' : undefined} className={linkCls(active)}>{active && <span className="absolute left-0 top-2 bottom-2 w-[3px] rounded-full bg-[#E10600]" />}<Icon className="w-4 h-4" /><span>{item.label}</span></Link>;
              })}
            </div>
          </div>
        </div>
        <div className="px-5 py-4 border-t border-[rgba(255,255,255,0.06)]">
          <div className="flex items-center gap-2"><span className="live-dot" /><span className="text-[11px] font-mono text-[#9BA1AA]">MODEL xgb-mc-v1</span></div>
          <div className="text-[11px] font-mono text-[#636973] mt-1">100K SIMS / RACE</div>
        </div>
      </nav>

      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-[#0B0E13]/95 backdrop-blur-md border-b border-[rgba(255,255,255,0.07)]">
        <div className="flex items-center justify-between px-4 h-[56px]">
          <Link to="/" className="flex items-center gap-2">
            <span className="w-7 h-7 bg-[#E10600] rounded-md flex items-center justify-center"><Flag className="w-3.5 h-3.5 text-white" /></span>
            <span className="text-white font-display font-bold text-[15px]">PreF1</span>
          </Link>
          <button onClick={() => setOpen(!open)} aria-label="Menu" className="w-10 h-10 flex items-center justify-center rounded-lg border border-white/10 text-white">{open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}</button>
        </div>
        {open && (
          <div className="px-3 pb-4 grid grid-cols-2 gap-1.5 animate-fade-in">
            {[...PRIMARY, ...SECONDARY].map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return <Link key={item.path} to={item.path} onClick={() => setOpen(false)} className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-[13px] font-semibold ${active ? 'bg-[#E10600]/15 text-white' : 'bg-white/[0.03] text-[#9BA1AA]'}`}><Icon className="w-4 h-4" />{item.label}</Link>;
            })}
          </div>
        )}
      </header>
      <nav aria-label="Mobile" className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#0B0E13]/95 backdrop-blur-xl border-t border-[rgba(255,255,255,0.08)] safe-bottom">
        <div className="grid grid-cols-5 px-1 py-1.5">
          {PRIMARY.map((item) => {
            const active = isActive(item.path);
            const Icon = item.icon;
            return <Link key={item.path} to={item.path} aria-current={active ? 'page' : undefined} className={`flex flex-col items-center gap-0.5 py-1.5 rounded-lg min-h-[52px] justify-center ${active ? 'text-[#FF6B61]' : 'text-[#636973]'}`}><Icon className="w-[22px] h-[22px]" /><span className="text-[10px] font-semibold">{item.label}</span>{active && <span className="w-6 h-[2px] rounded-full bg-[#E10600] mt-0.5" />}</Link>;
          })}
        </div>
      </nav>
    </>
  );
};
