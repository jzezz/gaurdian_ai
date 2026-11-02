import React from 'react';
import { ModerationResult } from '../lib/api';
import { Card } from './ui/Card';
import { AlertCircle, CheckCircle, ShieldAlert } from 'lucide-react';
import { motion } from 'framer-motion';

interface Props {
  result: ModerationResult;
}

export const ModerationResultCard: React.FC<Props> = ({ result }) => {
  const isApproved = result.action === 'approve';
  const isReject = result.action === 'reject';

  const accentColor = isApproved ? "text-emerald-500" : isReject ? "text-rose-500" : "text-amber-500";
  const Icon = isApproved ? CheckCircle : isReject ? ShieldAlert : AlertCircle;

  // Render risk bars for different scores
  const renderRiskBar = (label: string, score: number) => (
    <div className="mb-3">
      <div className="flex justify-between text-xs text-neutral-400 mb-1">
        <span>{label}</span>
        <span>{(score * 100).toFixed(0)}%</span>
      </div>
      <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score * 100}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={`h-full ${isApproved ? "bg-emerald-500" : "bg-rose-500"}`}
        />
      </div>
    </div>
  );

  return (
    <Card className="max-w-2xl border-neutral-800">
      <div className="flex items-center gap-4 mb-8">
        <div className={`p-4 rounded-2xl bg-neutral-950 border border-neutral-800 ${accentColor}`}>
          <Icon size={32} />
        </div>
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight capitalize">{result.action}</h2>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-neutral-400 font-medium"
          >
            Confidence: {(result.confidence * 100).toFixed(1)}%
          </motion.p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
           <h3 className="text-sm font-semibold text-neutral-300 mb-4 uppercase tracking-wider">Analysis Breakdown</h3>
           {Object.entries((result.scores.vision || result.scores) as Record<string, number>)
             .filter(([, value]) => typeof value === "number")
             .slice(0, 6)
             .map(([key, value]) => renderRiskBar(key.replace('_score', '').replace('_', ' '), value))}
        </div>

        <div>
          <h3 className="text-sm font-semibold text-neutral-300 mb-4 uppercase tracking-wider">Explanation</h3>
          <p className="text-neutral-400 leading-relaxed font-light text-sm bg-neutral-950 p-4 rounded-xl border border-neutral-800">
            {result.explanation}
          </p>
        </div>
      </div>

      {result.flagged_categories.length > 0 && (
        <div className="mt-8 pt-6 border-t border-neutral-800">
          <h3 className="text-sm font-semibold text-neutral-300 mb-4 uppercase tracking-wider">Flagged Concerns</h3>
          <div className="flex flex-wrap gap-2">
            {result.flagged_categories.map(cat => (
              <motion.span
                key={cat}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="px-4 py-1.5 bg-neutral-950 text-neutral-300 rounded-full text-xs uppercase tracking-wide font-medium border border-neutral-700"
              >
                {cat}
              </motion.span>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};
