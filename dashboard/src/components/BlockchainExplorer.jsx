import React, { useRef, useEffect } from 'react';
import { Box, Layers, History, ShieldCheck, Activity, Archive, Landmark, Database } from 'lucide-react';
import { motion } from 'framer-motion';

export const BlockchainRibbon = ({ blockchain }) => {
  const ribbonRef = useRef(null);

  useEffect(() => {
    if (ribbonRef.current) {
      ribbonRef.current.scrollLeft = ribbonRef.current.scrollWidth;
    }
  }, [blockchain]);

  return (
    <div className="flex flex-col grounded-dark h-full overflow-hidden relative">
      {/* Ribbon Header: Institutional Audit Ledger */}
      <div className="px-10 py-3 border-b border-white/10 flex items-center justify-between shrink-0 bg-white/[0.02]">
        <div className="flex items-center gap-4">
          <Landmark size={12} className="text-primary" />
          <span className="text-[9px] font-bold text-white/30 uppercase tracking-[0.25em] font-mono leading-none">
            Audit Ledger
          </span>
        </div>
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Database size={13} className="text-primary/70" />
              <h3 className="type-l3 text-white">Blockchain Ledger</h3>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="type-label text-emerald-400">Ledger Synchronized</span>
            </div>
          </div>
        </div>
      </div>

      {/* Ledger Column Headers */}
      <div 
        className="px-8 py-2 border-b border-white/5 bg-black/40 text-[8px] font-bold text-white/20 uppercase tracking-[0.2em] sticky top-0 z-10 font-mono"
        style={{
          display: 'grid',
          gridTemplateColumns: '120px 1fr 100px 120px',
          alignItems: 'center'
        }}
      >
        <div>Block ID</div>
        <div className="px-4">Checksum (Signature)</div>
        <div className="text-center">Node Load</div>
        <div className="text-right">Integrity Status</div>
      </div>

      {/* Ledger Rows Viewport */}
      <div
        ref={ribbonRef}
        className="flex-1 overflow-y-auto bg-black custom-scrollbar-ribbon"
      >
        {blockchain?.map((block) => (
          <motion.div
            key={`${block.index}-${block.hash}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`px-8 py-3 border-b border-white/5 hover:bg-white/[0.02] transition-all group ${block.index === 0 ? 'bg-primary/5' : ''
              }`}
            style={{
              display: 'grid',
              gridTemplateColumns: '120px 1fr 100px 120px',
              alignItems: 'center'
            }}
          >
            {/* Block ID */}
            <div className="flex items-center gap-3">
              <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${block.index === 0 ? 'bg-primary shadow-[0_0_8px_var(--primary-glow)]' : 'bg-white/20'}`} />
              <span className="text-[10px] font-bold text-white tracking-widest uppercase serif whitespace-nowrap">
                {block.index === 0 ? 'Genesis' : `Block ${block.index.toString().padStart(4, '0')}`}
              </span>
            </div>

            {/* Signature Hash */}
            <div className="px-4 overflow-hidden min-w-0 flex items-center">
              <div className="font-mono text-[9px] text-white/30 tracking-tighter truncate opacity-60 group-hover:opacity-100 transition-opacity">
                {block.hash !== 'null' && block.hash.length > 16
                  ? `${block.hash.substring(0, 10)}...${block.hash.substring(block.hash.length - 8)}`
                  : block.hash === 'null' ? '0x00000000_SEED_PROTOCOL' : block.hash}
              </div>
            </div>

            {/* Metrics/Load */}
            <div className="flex items-center justify-center gap-2">
              <span className="text-[9px] text-white/20 uppercase font-bold whitespace-nowrap tabular-nums">{block.transactions.length} LRD</span>
              <div className="flex gap-0.5">
                {[...Array(Math.min(block.transactions.length, 3))].map((_, idx) => (
                  <div key={idx} className="w-0.5 h-2.5 bg-primary/30" />
                ))}
              </div>
            </div>

            {/* Integrity Status */}
            <div className="text-right flex justify-end">
              <span className={`text-[8px] font-bold uppercase tracking-widest px-2.5 py-1 border ${block.index === 0 ? 'text-primary border-primary/20 bg-primary/5' : 'text-emerald-500 border-emerald-500/10 bg-emerald-500/5'
                } whitespace-nowrap`}>
                {block.index === 0 ? 'Authorized' : 'Verified'}
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      <style>{`
        .custom-scrollbar-ribbon::-webkit-scrollbar { width: 5px; }
        .custom-scrollbar-ribbon::-webkit-scrollbar-track { background: #000; }
        .custom-scrollbar-ribbon::-webkit-scrollbar-thumb { background: #111; border: 1px solid #222; border-radius: 2px; }
      `}</style>
    </div>
  );
};
