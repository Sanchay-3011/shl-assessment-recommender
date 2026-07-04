import React from 'react';
import type { RecommendationItem } from '../../types';
import { Clock, Shield, ExternalLink, Globe, Layers } from 'lucide-react';
import { motion } from 'framer-motion';

interface RecommendationCardProps {
  item: RecommendationItem;
}


const mapCategory = (type?: string): string => {
  if (!type) return "Knowledge & Skills";
  switch (type.toUpperCase()) {
    case 'K': return "Knowledge & Skills";
    case 'P': return "Personality & Behavior";
    case 'S': return "Simulations";
    case 'A': return "Ability & Aptitude";
    default: return "Hiring Solution";
  }
};

export const RecommendationCard: React.FC<RecommendationCardProps> = ({ item }) => {
  const category = mapCategory(item.test_type);
  const duration = item.duration || "Approx. 20-30 minutes";
  const adaptive = item.adaptive ?? true;
  const remote = item.remote ?? true;
  const languages = item.languages && item.languages.length > 0 ? item.languages : ["English (USA)"];
  const levels = item.job_levels && item.job_levels.length > 0 ? item.job_levels : ["Mid-Professional"];
  const reason = item.description || "Retrieved assessment matching your hiring requirements and seniority levels.";

  return (
    <motion.div
      variants={{
        hidden: { y: 15, opacity: 0 },
        show: { y: 0, opacity: 1 }
      }}
      className="bg-white rounded-2xl border border-slate-100 hover:border-slate-200/80 shadow-glass hover:shadow-glass-hover p-5 flex flex-col h-full transition-all duration-200"
    >
      {/* Category and Title */}
      <div className="flex-1">
        <div className="flex justify-between items-start mb-3">
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-600 border border-slate-200">
            {category}
          </span>
          {remote && (
            <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded uppercase tracking-wider">
              Remote
            </span>
          )}
        </div>

        <h4 className="font-bold text-slate-900 text-base leading-tight tracking-tight mb-2">
          {item.name}
        </h4>

        <p className="text-xs text-slate-500 leading-relaxed mb-4 line-clamp-3">
          {reason}
        </p>

        {/* Info Grid */}
        <div className="grid grid-cols-2 gap-y-2.5 gap-x-2 border-t border-slate-50 pt-3.5 mb-4 text-xs font-medium text-slate-500">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-slate-400 shrink-0" />
            <span>{duration}</span>
          </div>
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-slate-400 shrink-0" />
            <span>{adaptive ? 'Adaptive Engine' : 'Fixed Form'}</span>
          </div>
          <div className="flex items-center space-x-2 col-span-2">
            <Globe className="w-4 h-4 text-slate-400 shrink-0" />
            <span className="truncate">{languages.join(', ')}</span>
          </div>
          <div className="flex items-center space-x-2 col-span-2">
            <Layers className="w-4 h-4 text-slate-400 shrink-0" />
            <span className="truncate">{levels.join(', ')}</span>
          </div>
        </div>
      </div>

      {/* Action Button */}
      <a
        href={item.url}
        target="_blank"
        rel="noopener noreferrer"
        className="w-full inline-flex items-center justify-center space-x-2 bg-slate-50 hover:bg-blue-600 text-slate-700 hover:text-white font-semibold py-2.5 px-4 rounded-xl border border-slate-100 hover:border-blue-600 transition-all duration-200 text-xs active:scale-[0.98]"
      >
        <span>View SHL Catalog</span>
        <ExternalLink className="w-3.5 h-3.5" />
      </a>
    </motion.div>
  );
};
