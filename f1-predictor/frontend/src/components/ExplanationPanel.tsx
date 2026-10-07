import React from 'react';
import { CheckCircle2, AlertTriangle } from 'lucide-react';
import { DriverExplanation } from '../types';

interface ExplanationPanelProps {
  driverCode: string;
  explanation?: DriverExplanation;
}

export const ExplanationPanel: React.FC<ExplanationPanelProps> = ({ driverCode, explanation }) => {
  if (!explanation) {
    return (
      <div className="panel p-4 text-[12.5px] text-[#636973]">
        Select a driver row to view model factors.
      </div>
    );
  }

  return (
    <div className="panel p-4">
      <div className="eyebrow !text-[#9BA1AA] mb-3">Why {driverCode} · model factors</div>

      <div className="space-y-3 text-[12.5px]">
        <div>
          <span className="text-[#20C997] font-bold block mb-1.5 text-[11px] tracking-wide">STRENGTHS</span>
          <ul className="space-y-1.5 text-[#c7ccd2]">
            {explanation.positive_factors.map((f, i) => (
              <li key={i} className="flex gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-[#20C997] shrink-0 mt-0.5" /><span>{f}</span></li>
            ))}
          </ul>
        </div>

        <div>
          <span className="text-[#FF6B61] font-bold block mb-1.5 text-[11px] tracking-wide">RISKS</span>
          <ul className="space-y-1.5 text-[#c7ccd2]">
            {explanation.negative_factors.map((f, i) => (
              <li key={i} className="flex gap-2"><AlertTriangle className="w-3.5 h-3.5 text-[#FF6B61] shrink-0 mt-0.5" /><span>{f}</span></li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
