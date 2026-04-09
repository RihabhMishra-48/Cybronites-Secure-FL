import React from 'react';
import { Network, ShieldCheck, Activity, GraduationCap } from 'lucide-react';

export const Header = ({ status }) => {
  return (
    <header className="shell-header flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="w-8 h-8 bg-primary rounded-sm flex items-center justify-center text-white font-serif text-lg">FL</div>
        <h1 className="type-l2 serif text-text-main leading-tight tracking-tight">
          AI Guardian Professional Dashboard
        </h1>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 bg-emerald-50 border border-emerald-100 rounded-sm">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]" />
          <span className="type-label text-emerald-700">{status}</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 bg-slate-50 border border-slate-200 rounded-sm">
          <ShieldCheck size={12} className="text-slate-400" />
          <span className="type-label text-slate-500 italic">Secure Node</span>
        </div>
      </div>
    </header>
  );
};
