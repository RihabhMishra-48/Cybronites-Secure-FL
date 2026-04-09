import React from 'react';
import { Database, ShieldCheck, Clock, Hash, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

const BlockchainLedger = ({ chain }) => {
  return (
    <div className="w-full overflow-x-auto pb-6 custom-scrollbar">
      <div className="flex items-center gap-6 min-w-max px-4">
        {chain.map((block, index) => (
          <React.Fragment key={block.index}>
            <motion.div 
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: index * 0.1 }}
              className={`glass-card p-4 rounded-xl border-l-4 ${
                index === 0 ? 'border-l-indigo-500' : 'border-l-cyan-500'
              } w-64 shadow-lg flex flex-col gap-3 group relative hover:neon-border transition-all`}
            >
              <div className="flex items-center justify-between border-b border-cyber-border pb-2">
                <div className="flex items-center gap-2">
                  <Database size={16} className="text-cyber-primary" />
                  <span className="font-mono text-zinc-400">BLOCK #{block.index}</span>
                </div>
                {index === 0 && (
                  <span className="bg-indigo-500/20 text-indigo-400 text-[10px] px-1.5 py-0.5 rounded border border-indigo-500/30">
                    GENESIS
                  </span>
                )}
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex items-center gap-2 text-zinc-500">
                  <Hash size={12} />
                  <span className="font-mono truncate">{block.hash.slice(0, 20)}...</span>
                </div>
                <div className="flex items-center gap-2 text-zinc-500">
                  <ShieldCheck size={12} />
                  <span>Updates: {block.transactions?.length || 0}</span>
                </div>
                <div className="flex items-center gap-2 text-zinc-500">
                  <Clock size={12} />
                  <span>{new Date(block.timestamp * 1000).toLocaleTimeString()}</span>
                </div>
              </div>
              
              <div className="mt-2 pt-2 border-t border-cyber-border/50">
                <p className="text-[10px] text-zinc-600 uppercase tracking-tighter">Previous Hash</p>
                <p className="text-[10px] font-mono text-zinc-500 truncate">
                  {block.previous_hash.slice(0, 24)}...
                </p>
              </div>
            </motion.div>
            
            {index < chain.length - 1 && (
              <ChevronRight className="text-cyber-primary/30 animate-pulse" />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default BlockchainLedger;
