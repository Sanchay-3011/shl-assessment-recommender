import React from 'react';
import { PlusCircle, MessageSquare, Compass, Info, Briefcase } from 'lucide-react';

interface LeftSidebarProps {
  onSelectPrompt: (prompt: string) => void;
  onNewConversation: () => void;
}

const EXAMPLE_PROMPTS = [
  'Hire Graduate Software Engineers',
  'Python Developer Assessment',
  'Leadership Hiring Options',
  'Sales Executive Screening',
  'Customer Support Simulation',
  'Compare OPQ and Verify tests'
];

const MOCK_HISTORY = [
  { id: '1', title: 'Python Junior Developer' },
  { id: '2', title: 'Sales Force Coordinator' },
  { id: '3', title: 'Director of HR Candidates' }
];

export const LeftSidebar: React.FC<LeftSidebarProps> = ({
  onSelectPrompt,
  onNewConversation
}) => {
  return (
    <aside className="w-80 bg-white border-r border-slate-200 flex flex-col h-full shrink-0 select-none">
      {/* Header / Logo */}
      <div className="p-6 border-b border-slate-100 flex items-center space-x-3">
        <div className="bg-blue-600 p-2 rounded-xl text-white shadow-sm flex items-center justify-center">
          <Briefcase className="w-6 h-6" />
        </div>
        <div>
          <h1 className="font-bold text-slate-900 text-lg tracking-tight leading-none">SHL Hiring</h1>
          <span className="text-xs font-semibold text-blue-600 tracking-wider uppercase">AI Copilot</span>
        </div>
      </div>

      {/* Primary Action */}
      <div className="p-4">
        <button
          onClick={onNewConversation}
          className="w-full flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-xl shadow-sm transition-all duration-200 active:scale-[0.98]"
        >
          <PlusCircle className="w-5 h-5" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* Navigation / Scrollable Area */}
      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-6">
        {/* Recruiter Examples */}
        <div>
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center space-x-2">
            <Compass className="w-3.5 h-3.5" />
            <span>Recruiter Templates</span>
          </h3>
          <div className="space-y-1.5">
            {EXAMPLE_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => onSelectPrompt(prompt)}
                className="w-full text-left text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 py-2.5 px-3 rounded-lg border border-transparent hover:border-slate-100 transition-all truncate"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* History Log */}
        <div>
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center space-x-2">
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Search History</span>
          </h3>
          <div className="space-y-1">
            {MOCK_HISTORY.map((item) => (
              <div
                key={item.id}
                className="flex items-center space-x-3 text-sm text-slate-500 hover:text-slate-900 py-2.5 px-3 rounded-lg cursor-pointer hover:bg-slate-50/50 group"
              >
                <MessageSquare className="w-4 h-4 text-slate-400 group-hover:text-blue-500 shrink-0" />
                <span className="truncate">{item.title}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* About Box */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-start space-x-3 p-3 rounded-xl bg-white border border-slate-100 shadow-sm">
          <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
          <div className="text-xs text-slate-600 leading-normal">
            <p className="font-semibold text-slate-900 mb-0.5">SHL Catalog Search</p>
            Powered by keyword BM25 & FAISS vector embeddings. Response generation is 100% catalog-grounded.
          </div>
        </div>
      </div>
    </aside>
  );
};
