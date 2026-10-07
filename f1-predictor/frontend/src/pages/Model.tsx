import React, { useState, useEffect } from 'react';
import { fetchModelsInfo } from '../api/client';
import { Cpu, ShieldCheck } from 'lucide-react';
import { LoadingState, EmptyState } from '../components/ui';

interface ModelInfo {
  active_model_version: string;
  feature_version: string;
  architecture: string;
  components: Array<{
    name: string;
    type: string;
    target?: string;
    simulations?: number;
  }>;
}

export const Model: React.FC = () => {
  const [info, setInfo] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchModelsInfo()
      .then(setInfo)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <LoadingState label="Loading model card..." />;
  }

  if (!info) {
    return <EmptyState title="Model unavailable" body="Model metadata could not be loaded." />;
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <span className="w-9 h-9 rounded-[10px] bg-[#15191F] border border-[rgba(255,255,255,0.08)] flex items-center justify-center text-[#E10600]"><Cpu className="w-[18px] h-[18px]" /></span>
        <div>
          <div className="eyebrow">ML system · {info.architecture}</div>
          <h1 className="font-display font-bold text-white text-[24px] tracking-tight leading-none">Model card</h1>
        </div>
      </div>

      <div className="panel p-5">
        <div className="flex flex-wrap gap-2 text-[11px] font-mono font-bold">
          <span className="bg-[#E10600]/12 text-[#FF6B61] border border-[#E10600]/30 px-3 py-1.5 rounded-md">MODEL {info.active_model_version}</span>
          <span className="bg-white/[0.04] text-white border border-white/10 px-3 py-1.5 rounded-md">FEATURES {info.feature_version}</span>
          <span className="bg-white/[0.04] text-[#9BA1AA] border border-white/10 px-3 py-1.5 rounded-md">{info.architecture}</span>
        </div>

        <h3 className="eyebrow !text-[#9BA1AA] mt-6 mb-3">Pipeline stages</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2.5">
          {info.components.map((c, i) => (
            <div key={i} className="bg-black/30 border border-white/[0.05] rounded-lg p-3.5">
              <div className="flex items-center gap-2.5">
                <span className="w-6 h-6 rounded-md bg-[#E10600]/15 text-[#FF6B61] font-mono font-bold text-[11px] flex items-center justify-center">{String(i + 1).padStart(2, '0')}</span>
                <span className="font-bold text-white text-[13.5px]">{c.name}</span>
              </div>
              <div className="text-[11.5px] text-[#636973] font-mono mt-2">TYPE {c.type}{c.target ? ` · ${c.target}` : ''}{c.simulations ? ` · ${c.simulations.toLocaleString()} SIMS` : ''}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="panel p-5 text-[12.5px] text-[#9BA1AA]">
        <h3 className="eyebrow !text-[#9BA1AA] mb-3 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-[#20C997]" />
          <span>Modelling guarantees</span>
        </h3>
        <ul className="space-y-2 leading-relaxed">
          <li>Modular pipeline. Driver, car, circuit, and strategy are separated.</li>
          <li>Chronological validation only. No lookahead bias in features.</li>
          <li>Calibrated probabilities via isotonic regression. Tracked with Brier score and ECE.</li>
          <li>Vectorised Monte Carlo over 10,000+ stochastic runs per race.</li>
        </ul>
      </div>
    </div>
  );
};