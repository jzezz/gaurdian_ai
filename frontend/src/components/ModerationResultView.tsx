import React from 'react';
import { ModerationResult } from '../lib/api';
import { AlertCircle, CheckCircle, ShieldAlert } from 'lucide-react';

interface Props {
  result: ModerationResult;
}

export const ModerationResultView: React.FC<Props> = ({ result }) => {
  const getStatusStyle = () => {
    if (result.safe) return "bg-green-50 border-green-200 text-green-800";
    if (result.action === "reject") return "bg-red-50 border-red-200 text-red-800";
    return "bg-yellow-50 border-yellow-200 text-yellow-800";
  };

  return (
    <div className={`p-6 border rounded-xl ${getStatusStyle()}`}>
      <div className="flex items-center gap-3 mb-4">
        {result.safe ? <CheckCircle /> : !result.flagged_categories.length ? <AlertCircle /> : <ShieldAlert />}
        <h2 className="text-xl font-bold">{result.safe ? "Approved" : result.action.toUpperCase()}</h2>
      </div>

      <p className="mb-4 font-mono whitespace-pre-line">{result.explanation}</p>

      {result.flagged_categories.length > 0 && (
        <div className="mt-4">
          <h3 className="font-semibold mb-2">Flagged Categories:</h3>
          <div className="flex flex-wrap gap-2">
            {result.flagged_categories.map(cat => (
              <span key={cat} className="px-2 py-1 bg-white rounded-full text-sm font-medium border border-current">
                {cat}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
