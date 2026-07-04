import { useState } from 'react';
import { HomePage } from './pages/Home/HomePage';
import { ChatPage } from './pages/Chat/ChatPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false
    }
  }
});

function App() {
  const [view, setView] = useState<'home' | 'chat'>('home');
  const [initialPrompt, setInitialPrompt] = useState<string | undefined>(undefined);

  const handleStartChat = (prompt?: string) => {
    setInitialPrompt(prompt);
    setView('chat');
  };

  const handleBackToHome = () => {
    setView('home');
    setInitialPrompt(undefined);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-slate-50 flex flex-col overflow-hidden">
        {view === 'home' ? (
          <HomePage onStartChat={handleStartChat} />
        ) : (
          <ChatPage onBackToHome={handleBackToHome} initialPrompt={initialPrompt} />
        )}
      </div>
    </QueryClientProvider>
  );
}

export default App;
