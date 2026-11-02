import React from 'react';
import { motion } from 'framer-motion';

export const Card = ({ children, className = '' }: { children: React.ReactNode, className?: string }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl ${className}`}
    >
      {children}
    </motion.div>
  );
};
