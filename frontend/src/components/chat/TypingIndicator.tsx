import React, { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface TypingIndicatorProps {
  isLoading: boolean;
}

const ROTATING_STATES = [
  'Analyzing hiring requirements...',
  'Searching SHL catalog...',
  'Ranking assessments...',
  'Generating recommendations...'
];

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ isLoading }) => {
  const [stateIndex, setStateIndex] = useState(0);

  useEffect(() => {
    if (!isLoading) {
      setStateIndex(0);
      return;
    }

    const interval = setInterval(() => {
      setStateIndex((prev) => (prev + 1) % ROTATING_STATES.length);
    }, 1500);

    return () => clearInterval(interval);
  }, [isLoading]);

  if (!isLoading) return null;

  return (
    <div className="flex items-start space-x-4 py-6 px-4 mr-12 select-none">
      <div className="w-9 h-9 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center shrink-0">
        <Sparkles className="w-4 h-4 text-blue-600 animate-spin" style={{ animationDuration: '3s' }} />
      </div>

      <div className="space-y-2 mt-1">
        <div className="flex space-x-1.5 items-center">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>

        <div className="h-5 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.p
              key={stateIndex}
              initial={{ y: 8, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -8, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="text-xs font-semibold text-slate-500 uppercase tracking-wider"
            >
              {ROTATING_STATES[stateIndex]}
            </motion.p>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};
