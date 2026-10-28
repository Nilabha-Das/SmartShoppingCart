import React from 'react';

export const AudioWaveform = () => {
  return (
    <div className="absolute -inset-4 rounded-full flex items-center justify-center pointer-events-none">
      {/* Outer ripple rings */}
      <div className="absolute inset-0 rounded-full border border-purple-500/40 animate-ping opacity-75" />
      <div className="absolute -inset-2 rounded-full border border-blue-500/30 animate-pulse" />

      {/* Frequency Bar Waveform Simulation */}
      <div className="absolute -top-8 flex items-center gap-1 bg-slate-950/80 px-3 py-1.5 rounded-full border border-purple-500/30 backdrop-blur-md">
        <span className="text-[10px] text-purple-300 font-semibold uppercase tracking-wider mr-1">Listening</span>
        <span className="w-1 h-3 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-1 h-6 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-1 h-4 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        <span className="w-1 h-7 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '100ms' }} />
        <span className="w-1 h-3 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '200ms' }} />
      </div>
    </div>
  );
};