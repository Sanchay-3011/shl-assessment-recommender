import React from 'react';
import type { HiringConstraints } from '../../types';
import { Clock, Globe, Cpu, Check, X, Award, Code, HelpCircle } from 'lucide-react';

interface RightSidebarProps {
  constraints: HiringConstraints;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({ constraints }) => {
  const hasConstraints =
    constraints.role ||
    constraints.job_level ||
    constraints.duration ||
    constraints.language ||
    constraints.adaptive ||
    constraints.remote ||
    constraints.skills.length > 0 ||
    constraints.assessment_keys.length > 0;

  const renderBadge = (value: string | null) => {
    if (!value) return <span className="text-xs text-slate-400 italic">Unspecified</span>;
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-100">
        {value}
      </span>
    );
  };

  const renderYesNo = (value: string | null) => {
    if (!value) return <span className="text-xs text-slate-400 italic">Unspecified</span>;
    const isYes = value.toLowerCase() === 'yes';
    return (
      <span
        className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
          isYes ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : 'bg-rose-50 text-rose-700 border border-rose-100'
        }`}
      >
        {isYes ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
        <span>{isYes ? 'Required' : 'No'}</span>
      </span>
    );
  };

  return (
    <aside className="w-80 bg-white border-l border-slate-200 flex flex-col h-full shrink-0 select-none">
      <div className="p-6 border-b border-slate-100 flex items-center space-x-2">
        <Cpu className="w-5 h-5 text-blue-600 animate-pulse" />
        <h2 className="font-bold text-slate-900 text-base">Hiring Context</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {!hasConstraints ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-4">
            <div className="bg-slate-50 p-4 rounded-full border border-slate-100 mb-3 text-slate-300">
              <HelpCircle className="w-8 h-8" />
            </div>
            <p className="text-sm font-semibold text-slate-500">No constraints extracted yet</p>
            <p className="text-xs text-slate-400 mt-1 max-w-[200px]">
              Chat with the Copilot to clarify roles, levels, and requirements.
            </p>
          </div>
        ) : (
          <div className="space-y-5">
            {/* Core Target Info */}
            <div className="space-y-4">
              <div className="flex justify-between items-start border-b border-slate-50 pb-3.5">
                <span className="text-sm font-medium text-slate-500 flex items-center space-x-2">
                  <Award className="w-4 h-4 text-slate-400" />
                  <span>Target Role</span>
                </span>
                <span className="font-semibold text-slate-900 text-sm max-w-[150px] truncate text-right">
                  {constraints.role || <span className="text-slate-400 italic font-normal">None</span>}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-slate-50 pb-3.5">
                <span className="text-sm font-medium text-slate-500 flex items-center space-x-2">
                  <Code className="w-4 h-4 text-slate-400" />
                  <span>Job Level</span>
                </span>
                {renderBadge(constraints.job_level)}
              </div>

              <div className="flex justify-between items-start border-b border-slate-50 pb-3.5">
                <span className="text-sm font-medium text-slate-500 flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-slate-400" />
                  <span>Max Duration</span>
                </span>
                <span className="font-semibold text-slate-900 text-sm">
                  {constraints.duration ? `${constraints.duration} min` : <span className="text-slate-400 italic font-normal">Unlimited</span>}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-slate-50 pb-3.5">
                <span className="text-sm font-medium text-slate-500 flex items-center space-x-2">
                  <Globe className="w-4 h-4 text-slate-400" />
                  <span>Language</span>
                </span>
                {renderBadge(constraints.language)}
              </div>

              <div className="flex justify-between items-start border-b border-slate-50 pb-3.5">
                <span className="text-sm font-medium text-slate-500 flex items-center space-x-2">
                  <Cpu className="w-4 h-4 text-slate-400" />
                  <span>Adaptive</span>
                </span>
                {renderYesNo(constraints.adaptive)}
              </div>

              <div className="flex justify-between items-start border-b border-slate-50 pb-3.5">
                <span className="text-sm font-medium text-slate-500 flex items-center space-x-2">
                  <Globe className="w-4 h-4 text-slate-400" />
                  <span>Remote Proctor</span>
                </span>
                {renderYesNo(constraints.remote)}
              </div>
            </div>

            {/* Extracted Skills */}
            {constraints.skills.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Technologies & Skills</h4>
                <div className="flex flex-wrap gap-1.5">
                  {constraints.skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-xs font-medium border border-slate-200"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Assessment Types */}
            {constraints.assessment_keys.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Assessment Categories</h4>
                <div className="flex flex-wrap gap-1.5">
                  {constraints.assessment_keys.map((cat, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded bg-slate-50 text-slate-800 text-xs font-semibold border border-slate-100"
                    >
                      {cat}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Safety status block */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-center space-x-2.5 text-xs text-slate-600">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping shrink-0" />
          <span className="font-semibold text-slate-800">Agent Status: Active and Safe</span>
        </div>
      </div>
    </aside>
  );
};
