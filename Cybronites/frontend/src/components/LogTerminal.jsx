import React, { useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';

const LogTerminal = ({ logs }) => {
  const logEndRef = useRef(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="glass-card rounded-lg overflow-hidden border border-cyber-border/50 h-[300px] flex flex-col font-mono text-sm">
      <div className="bg-cyber-bg px-4 py-2 border-b border-cyber-border flex items-center gap-2">
        <Terminal size={14} className="text-cyber-primary" />
        <span className="text-cyber-primary font-semibold tracking-wider">SECURE_LOGS_v1.0</span>
        <div className="ml-auto flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
          <div className="w-2.5 h-2.5 rounded-full bg-green-500/50" />
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-2 cyber-grid">
        {logs.map((log, i) => (
          <div key={i} className="flex gap-2 animate-in fade-in slide-in-from-left-2 transition-all">
            <span className="text-zinc-600">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
            <span className={`font-bold ${log.status === 'REJECTED' ? 'text-cyber-accent' : 'text-emerald-500'}`}>
              [{log.status}]
            </span>
            <span className="text-zinc-300">
              {log.status === 'REJECTED' 
                ? `Malicious intent detected from ${log.client_id}. Update quarrantined.`
                : `Verified model segment received from ${log.client_id}. Hash: ${log.hash}`}
            </span>
          </div>
        ))}
        <div ref={logEndRef} />
      </div>
    </div>
  );
};

export default LogTerminal;
