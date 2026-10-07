import React from 'react';
import { Link } from 'react-router-dom';
import { Play, Cpu, Zap, ArrowRight } from 'lucide-react';

export const Simulation: React.FC = () => {
  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <span className="w-9 h-9 rounded-[10px] bg-[#15191F] border border-[rgba(255,255,255,0.08)] flex items-center justify-center text-[#E10600]"><Play className="w-[18px] h-[18px]" /></span>
        <div>
          <div className="eyebrow">Monte Carlo engine</div>
          <h1 className="font-display font-bold text-white text-[24px] tracking-tight leading-none">Race simulator</h1>
        </div>
      </div>

      <div className="panel-strong p-6 sm:p-8 text-center space-y-5">
        <div className="flex items-center justify-center gap-4">
          <span className="w-11 h-11 rounded-xl bg-[#E10600]/12 border border-[#E10600]/25 flex items-center justify-center"><Cpu className="w-5 h-5 text-[#E10600]" /></span>
          <span className="w-11 h-11 rounded-xl bg-white/[0.04] border border-white/10 flex items-center justify-center"><Zap className="w-5 h-5 text-[#F5B942]" /></span>
        </div>
        <p className="text-[13.5px] text-[#9BA1AA] max-w-2xl mx-auto leading-relaxed">
          Vectorised Monte Carlo engine. Run 10k to 500k stochastic races across weather, safety-car, and tyre scenarios.
        </p>
        <div className="flex flex-wrap justify-center gap-2.5">
          <Link to="/prediction" className="btn-primary inline-flex items-center gap-2">Run race forecast <ArrowRight className="w-4 h-4" /></Link>
          <Link to="/championship" className="btn-ghost">Season run-out</Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 max-w-3xl mx-auto text-left">
          <div className="bg-black/30 border border-white/[0.05] rounded-lg p-3.5"><div className="text-[10px] font-bold text-[#636973] tracking-wide">ENGINE</div><div className="text-white font-bold mt-1 text-[14px]">Vectorised NumPy</div></div>
          <div className="bg-black/30 border border-white/[0.05] rounded-lg p-3.5"><div className="text-[10px] font-bold text-[#636973] tracking-wide">MAX SAMPLE</div><div className="text-white font-bold mt-1 text-[14px] font-mono">500,000</div></div>
          <div className="bg-black/30 border border-white/[0.05] rounded-lg p-3.5"><div className="text-[10px] font-bold text-[#636973] tracking-wide">CONVERGENCE</div><div className="text-white font-bold mt-1 text-[14px] font-mono">Δ &lt; 0.1%</div></div>
        </div>
      </div>
    </div>
  );
};
