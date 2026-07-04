import React, { useEffect, useRef } from 'react';
import type { ChatMessage, RecommendationItem } from '../../types';
import { MessageItem } from './MessageItem';
import { TypingIndicator } from './TypingIndicator';

interface ChatHistoryProps {
  messages: (ChatMessage & {
    recommendations?: RecommendationItem[];
    comparisonTargets?: string[];
  })[];
  isLoading: boolean;
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ messages, isLoading }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto divide-y divide-slate-100 bg-slate-50/20"
    >
      <div className="flex flex-col min-h-full">
        {messages.map((msg, index) => (
          <MessageItem key={index} message={msg} />
        ))}
        <TypingIndicator isLoading={isLoading} />
      </div>
    </div>
  );
};
