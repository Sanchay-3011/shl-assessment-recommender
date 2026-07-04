import React from 'react';
import type { ChatMessage, RecommendationItem } from '../../types';
import { User, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { RecommendationCard } from '../cards/RecommendationCard';
import { ComparisonTable } from '../cards/ComparisonTable';
import { motion } from 'framer-motion';

interface MessageItemProps {
  message: ChatMessage & {
    recommendations?: RecommendationItem[];
    comparisonTargets?: string[];
  };
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const timestamp = message.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <motion.div
      initial={{ y: 12, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`flex items-start space-x-4 py-6 px-4 ${
        isUser ? 'flex-row-reverse space-x-reverse bg-slate-50/50' : 'bg-white'
      }`}
    >
      {/* Icon Avatar */}
      <div
        className={`w-9 h-9 rounded-xl flex items-center justify-center shadow-sm shrink-0 border ${
          isUser
            ? 'bg-blue-600 border-blue-500 text-white'
            : 'bg-white border-slate-200 text-blue-600'
        }`}
      >
        {isUser ? <User className="w-5 h-5" /> : <Sparkles className="w-4 h-4 animate-pulse" />}
      </div>

      {/* Message Text and Metadata */}
      <div className="flex-1 space-y-2.5 max-w-3xl overflow-hidden">
        <div className="flex items-center space-x-2.5">
          <span className="text-sm font-semibold text-slate-800">
            {isUser ? 'Recruiter' : 'AI Hiring Copilot'}
          </span>
          <span className="text-[10px] font-medium text-slate-400">{timestamp}</span>
        </div>

        {/* Bubble Text (Supports Markdown) */}
        <div className="text-slate-700 text-sm leading-relaxed prose prose-slate max-w-none">
          {isUser ? (
            <p className="whitespace-pre-wrap font-medium">{message.content}</p>
          ) : (
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="mb-0.5">{children}</li>,
                strong: ({ children }) => <strong className="font-bold text-slate-900">{children}</strong>,
                code: ({ children }) => <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-xs">{children}</code>
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Dynamic Presentation Components (Recommendations or Comparison Tables) */}
        {!isUser && message.recommendations && message.recommendations.length > 0 && (
          <motion.div
            initial="hidden"
            animate="show"
            variants={{
              hidden: { opacity: 0 },
              show: {
                opacity: 1,
                transition: { staggerChildren: 0.1 }
              }
            }}
            className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4"
          >
            {message.recommendations.map((rec, idx) => (
              <RecommendationCard key={idx} item={rec} />
            ))}
          </motion.div>
        )}

        {!isUser && message.comparisonTargets && message.comparisonTargets.length > 0 && (
          <div className="pt-4 overflow-x-auto">
            <ComparisonTable targets={message.comparisonTargets} />
          </div>
        )}
      </div>
    </motion.div>
  );
};
