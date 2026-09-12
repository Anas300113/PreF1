import React from 'react';
import { CheckCircle2, AlertTriangle, Info } from 'lucide-react';
import { DriverExplanation } from '../types';

interface ExplanationPanelProps {
  driverCode: string;
  explanation?: DriverExplanation;
}

export const ExplanationPanel: React.FC<ExplanationPanelProps> = ({ driverCode, explanation }) => {
  if (!explanation) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 text-xs text-gray-400">
        Select a driver card to view model explanation and SHAP factors.
      </div>
    );
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <div className="flex items-center space-x-2 mb-3">
        <Info className="w-4 h-4 text-blue-400" />
        <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide">
          Model Explainability Factors: {driverCode}
        </h3>
      </div>

      <div className="space-y-3 text-xs">
        <div>
          <span className="text-green-400 font-bold block mb-1 flex items-center space-x-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>POSITIVE ADVANTAGE FACTORS</span>
          </span>
          <ul className="list-disc list-inside space-y-1 text-gray-300">
            {explanation.positive_factors.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </div>

        <div>
          <span className="text-red-400 font-bold block mb-1 flex items-center space-x-1">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>RISK / NEGATIVE FACTORS</span>
          </span>
          <ul className="list-disc list-inside space-y-1 text-gray-300">
            {explanation.negative_factors.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
