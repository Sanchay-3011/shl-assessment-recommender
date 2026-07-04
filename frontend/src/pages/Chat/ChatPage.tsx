import React from 'react';
import { LeftSidebar } from '../../components/sidebar/LeftSidebar';
import { RightSidebar } from '../../components/sidebar/RightSidebar';
import { ChatHistory } from '../../components/chat/ChatHistory';
import { InputBox } from '../../components/chat/InputBox';
import { useChat } from '../../hooks/useChat';
import { ArrowLeft, RefreshCw, AlertTriangle, Cpu, WifiOff } from 'lucide-react';

interface ChatPageProps {
  onBackToHome: () => void;
  initialPrompt?: string;
}

export const ChatPage: React.FC<ChatPageProps> = ({ onBackToHome, initialPrompt }) => {
  const {
    messages,
    isLoading,
    error,
    constraints,
    connectionStatus,
    backendError,
    retryCountdown,
    sendMessage,
    resetConversation,
    forceCheckConnection
  } = useChat();

  // Send initial prompt if provided and conversation is empty
  React.useEffect(() => {
    if (initialPrompt && messages.length === 0 && connectionStatus === 'connected' && !isLoading) {
      sendMessage(initialPrompt);
    }
  }, [initialPrompt, connectionStatus]);

  const showReconnectOverlay = connectionStatus !== 'connected' && connectionStatus !== 'connecting' && messages.length === 0;
  const isConnecting = connectionStatus === 'connecting';
  const isDisconnected = connectionStatus === 'disconnected' || connectionStatus === 'offline';

  return (
    <div className="flex h-screen w-screen bg-slate-50 overflow-hidden font-sans">
      
      {/* 1. Left Navigation Sidebar */}
      <LeftSidebar
        onSelectPrompt={sendMessage}
        onNewConversation={resetConversation}
      />

      {/* 2. Main Center Dialogue Panel */}
      <div className="flex-1 flex flex-col h-full bg-slate-50/20 relative min-w-0">
        
        {/* Central Header */}
        <header className="h-16 border-b border-slate-200 bg-white px-6 flex items-center justify-between shrink-0 select-none">
          <div className="flex items-center space-x-4">
            <button
              onClick={onBackToHome}
              className="p-2 -ml-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-50 transition-all duration-200"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h2 className="font-bold text-slate-900 text-sm leading-tight">Assessment Copilot Workspace</h2>
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Hiring screening advisor</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Top-Right Status System Badge indicators */}
            <div className="flex items-center space-x-2">
              {connectionStatus === 'connected' && (
                <>
                  <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded bg-emerald-50 text-[10px] font-bold text-emerald-700 border border-emerald-100 uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
                    Backend Connected
                  </span>
                  <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded bg-emerald-50 text-[10px] font-bold text-emerald-700 border border-emerald-100 uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
                    Catalog Loaded
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-emerald-50 text-[10px] font-bold text-emerald-700 border border-emerald-100 uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
                    AI Ready
                  </span>
                </>
              )}
              {isConnecting && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-100">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5 animate-ping" />
                  <span>Connecting...</span>
                </span>
              )}
              {connectionStatus === 'disconnected' && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-100">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 mr-1.5 animate-pulse" />
                  <span>Backend Offline</span>
                </span>
              )}
              {connectionStatus === 'offline' && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-100">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 mr-1.5 animate-pulse" />
                  <span>Network Offline</span>
                </span>
              )}
            </div>
            
            {/* Restart button */}
            <button
              onClick={resetConversation}
              className="p-2 rounded-xl border border-slate-200 text-slate-500 hover:text-slate-900 hover:bg-slate-50 transition-all duration-200 active:scale-[0.96]"
              title="Clear Active Chat"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Central Area: Empty / History / Reconnect Panels */}
        {showReconnectOverlay ? (
          <div className="flex-1 flex flex-col items-center justify-center p-6 text-center bg-slate-50/30 select-none">
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-glass max-w-sm w-full space-y-6">
              <div className="mx-auto w-14 h-14 rounded-2xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600 animate-bounce">
                {connectionStatus === 'offline' ? <WifiOff className="w-7 h-7" /> : <AlertTriangle className="w-7 h-7" />}
              </div>
              
              <div className="space-y-1.5">
                <h3 className="font-extrabold text-slate-900 text-base leading-tight">
                  {connectionStatus === 'offline' ? 'Network Offline' : 'Cannot Connect to Backend'}
                </h3>
                <p className="text-xs text-slate-500 leading-relaxed font-medium">
                  {backendError?.message || 'The SHL Recommendation API is currently unreachable.'}
                </p>
              </div>

              {retryCountdown > 0 && (
                <div className="bg-slate-50 rounded-xl py-2 px-3 border border-slate-100 text-[11px] font-bold text-slate-500 flex items-center justify-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-ping" />
                  <span>Retrying automatically in {retryCountdown}s...</span>
                </div>
              )}

              <button
                onClick={forceCheckConnection}
                disabled={isConnecting}
                className="w-full flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-xl shadow-sm hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50 text-xs"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isConnecting ? 'animate-spin' : ''}`} />
                <span>{isConnecting ? 'Reconnecting...' : 'Retry Now'}</span>
              </button>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-6 text-center select-none">
            <div className="bg-blue-50 p-5 rounded-2xl border border-blue-100 mb-4 text-blue-600 shadow-sm animate-bounce" style={{ animationDuration: '3s' }}>
              <Cpu className="w-8 h-8" />
            </div>
            <h3 className="font-bold text-slate-800 text-lg">Define Assessment Needs</h3>
            <p className="text-slate-500 text-sm max-w-sm mt-1.5 leading-relaxed font-medium">
              Start by typing requirements in the box below. Specify target role, seniorities, or languages.
            </p>
          </div>
        ) : (
          <ChatHistory messages={messages} isLoading={isLoading} />
        )}

        {/* Reconnect Banner when history exists and connection is offline */}
        {isDisconnected && messages.length > 0 && (
          <div className="px-6 py-3 border-t border-rose-100 bg-rose-50/80 flex flex-col sm:flex-row items-center justify-between space-y-2 sm:space-y-0 text-xs font-semibold text-rose-700">
            <div className="flex items-center space-x-2.5">
              <AlertTriangle className="w-4 h-4 text-rose-500 animate-pulse shrink-0" />
              <span>
                {connectionStatus === 'offline' ? 'Network Offline' : 'Backend connection dropped.'}{' '}
                {retryCountdown > 0 ? `Auto-retry in ${retryCountdown}s...` : 'Connecting...'}
              </span>
            </div>
            <button
              onClick={forceCheckConnection}
              disabled={isConnecting}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white border border-rose-200 text-rose-800 hover:bg-rose-50 text-[11px] font-bold active:scale-[0.98] transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 ${isConnecting ? 'animate-spin' : ''}`} />
              <span>Retry</span>
            </button>
          </div>
        )}

        {/* Central Input Box - disabled during offline status to prevent duplicate loops */}
        <InputBox 
          onSendMessage={sendMessage} 
          isLoading={isLoading || isDisconnected} 
          error={error} 
        />
      </div>

      {/* 3. Right Hiring Context Sidebar */}
      <RightSidebar constraints={constraints} />
    </div>
  );
};
