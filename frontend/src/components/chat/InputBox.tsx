import React, { useState, useRef } from 'react';
import { Send, Sparkles, AlertCircle } from 'lucide-react';

interface InputBoxProps {
  onSendMessage: (content: string) => void;
  isLoading: boolean;
  error: string | null;
}

export const InputBox: React.FC<InputBoxProps> = ({ onSendMessage, isLoading, error }) => {
  const [content, setContent] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!content.trim() || isLoading) return;
    onSendMessage(content.trim());
    setContent('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  };

  return (
    <div className="border-t border-slate-200 bg-white p-6 shrink-0 select-none">
      <div className="max-w-4xl mx-auto space-y-3">
        {/* Error warning bar */}
        {error && (
          <div className="flex items-center space-x-2.5 p-3 rounded-xl bg-rose-50 border border-rose-100 text-xs font-semibold text-rose-700">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Input box wrap */}
        <div className="relative flex items-end border border-slate-200 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100 rounded-2xl bg-white shadow-sm overflow-hidden transition-all duration-200">
          <textarea
            ref={textareaRef}
            rows={1}
            value={content}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Describe your hiring needs (e.g. 'I want to hire an entry-level Python developer for a 30-minute test')..."
            className="flex-1 w-full bg-transparent resize-none border-0 focus:ring-0 py-3.5 pl-4 pr-16 text-slate-800 text-sm leading-relaxed outline-none max-h-40 min-h-[50px]"
            style={{ height: 'auto' }}
          />

          <div className="absolute right-3.5 bottom-3.5 flex items-center space-x-2">
            <button
              onClick={handleSend}
              disabled={!content.trim() || isLoading}
              className={`p-2 rounded-xl flex items-center justify-center transition-all duration-200 ${
                content.trim() && !isLoading
                  ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:scale-[1.02] active:scale-[0.98]'
                  : 'bg-slate-100 text-slate-400 cursor-not-allowed'
              }`}
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Caption */}
        <div className="flex justify-between items-center px-1 text-[11px] font-medium text-slate-400">
          <span className="flex items-center space-x-1">
            <Sparkles className="w-3.5 h-3.5 text-blue-500" />
            <span>Press Enter to send, Shift + Enter for new line.</span>
          </span>
          <span>SHL assessment recommendations are validated.</span>
        </div>
      </div>
    </div>
  );
};
