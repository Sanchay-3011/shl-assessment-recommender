import React from 'react';
import { Compass, Sparkles, MessageCircle, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

interface HomePageProps {
  onStartChat: (initialPrompt?: string) => void;
}

const LANDING_CHIPS = [
  { text: 'Hire Graduate Software Engineers', category: 'Engineering' },
  { text: 'Python Developer Assessment', category: 'Technical' },
  { text: 'Leadership Hiring Options', category: 'Management' },
  { text: 'Sales Executive Screening', category: 'Sales' },
  { text: 'Customer Support Simulation', category: 'Support' },
  { text: 'Compare OPQ and Verify tests', category: 'Comparison' }
];

export const HomePage: React.FC<HomePageProps> = ({ onStartChat }) => {
  return (
    <div className="flex-1 bg-slate-50 flex flex-col justify-center items-center p-6 md:p-12 overflow-y-auto select-none">
      <div className="max-w-3xl w-full text-center space-y-8">
        
        {/* Animated badge header */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="inline-flex items-center space-x-2 bg-blue-50 border border-blue-100 rounded-full px-4 py-1.5 text-xs font-bold text-blue-700 shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>SHL AI HIRING COPILOT FOR RECRUITERS</span>
        </motion.div>

        {/* Hero title */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="space-y-4"
        >
          <h2 className="text-4xl md:text-5xl font-black text-slate-900 tracking-tight leading-none">
            SHL AI Assessment <span className="text-blue-600">Recommender</span>
          </h2>
          <p className="text-slate-500 text-base md:text-lg max-w-xl mx-auto font-medium leading-relaxed">
            Quickly navigate the official SHL catalog. Leverage hybrid semantic search to match candidate requirements, seniority levels, and languages.
          </p>
        </motion.div>

        {/* Call to Action */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="flex justify-center"
        >
          <button
            onClick={() => onStartChat()}
            className="group flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-8 rounded-2xl shadow-md hover:shadow-lg transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98]"
          >
            <MessageCircle className="w-5 h-5" />
            <span>Start Conversation</span>
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </button>
        </motion.div>

        {/* Template Prompt Chips */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="space-y-4 pt-6 border-t border-slate-200"
        >
          <div className="flex justify-center items-center space-x-2 text-xs font-bold text-slate-400 uppercase tracking-widest">
            <Compass className="w-4 h-4" />
            <span>Select a template to start</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 max-w-2xl mx-auto">
            {LANDING_CHIPS.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => onStartChat(chip.text)}
                className="text-left bg-white border border-slate-100 hover:border-slate-200/80 shadow-sm hover:shadow-md p-3.5 rounded-xl transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 text-slate-700 group hover:bg-slate-50/50"
              >
                <span className="text-[10px] font-bold text-blue-600 block uppercase tracking-wider mb-1">
                  {chip.category}
                </span>
                <span className="text-xs font-bold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1">
                  {chip.text}
                </span>
              </button>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};
