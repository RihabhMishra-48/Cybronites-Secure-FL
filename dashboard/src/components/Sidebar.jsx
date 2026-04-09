import React from 'react';
import {
  LayoutDashboard, Database, ShieldCheck, Terminal, Activity, Layers,
  History, Workflow, Cpu, BookOpen, PieChart, Server, ChevronRight, LogOut
} from 'lucide-react';

const MetricItem = ({ label, value, icon: Icon, color }) => (
  <div className="sb-metric-item group">
    <div className={`sb-metric-icon-wrap ${color ? `sb-icon-${color}` : ''}`}>
      {Icon && <Icon size={12} />}
    </div>
    <div className="sb-metric-content">
      <span className="sb-metric-label">{label}</span>
      <span className="sb-metric-value">{value}</span>
    </div>
    <div className="sb-metric-indicator" />
  </div>
);

export const Sidebar = ({ currentView, setView, clients = [], nodeRegistry = {}, rejectedCount = 0, blockchain = [], width, onResize, onLogout }) => {
  const activeCount = clients.filter(c => c.status === 'ACTIVE' || c.status === 'BUSY').length;
  const nodeCount = Object.keys(nodeRegistry).length || clients.length || 0;

  const yieldValue = blockchain && blockchain.length > 1
    ? (100 - (rejectedCount / (blockchain.length - 1) * 100)).toFixed(1)
    : "100.0";
  const powerValue = (activeCount * 0.4 + 0.2).toFixed(1);

  const navItems = [
    { id: 'dashboard', label: 'Academic Progress', num: '01', icon: LayoutDashboard },
    { id: 'training', label: 'Training Cluster', num: '02', icon: Activity },
    { id: 'datasets', label: 'Shard Registry', num: '03', icon: Database },
    { id: 'architecture', label: 'Model Library', num: '04', icon: Layers },
    { id: 'privacy_vault', label: 'Privacy Vault', num: '06', icon: ShieldCheck },
    { id: 'laboratory', label: 'Code Laboratory', num: '05', icon: Terminal },
  ];

  return (
    <aside className="sb-root" style={{ width: width || 260 }}>
      {/* Resize Handle */}
      <div onMouseDown={onResize} className="sb-resizer">
        <div className="sb-resizer-line" />
      </div>

      {/* Navigation Section */}
      <div className="sb-scroll">
        <div className="sb-section-header">
          <BookOpen size={12} />
          <span>Coursework</span>
        </div>

        <nav className="sb-nav">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setView(item.id)}
              className={`sb-nav-btn ${currentView === item.id ? 'sb-nav-active' : ''}`}
            >
              <span className="sb-nav-num">{item.num}</span>
              <span className="sb-nav-label">{item.label}</span>
              {currentView === item.id && <ChevronRight size={10} className="sb-nav-chevron" />}
            </button>
          ))}
        </nav>

        <div className="sb-section-header sb-section-stats">
          <Activity size={12} />
          <span>System Telemetry</span>
        </div>

        <div className="sb-metrics">
          <MetricItem
            label="Node Count"
            value={nodeCount}
            icon={Server}
            color="primary"
          />
          <MetricItem
            label="Verification Yield"
            value={`${yieldValue}%`}
            icon={ShieldCheck}
            color="success"
          />
          <MetricItem
            label="Computing Power"
            value={`${powerValue} GB/S`}
            icon={Cpu}
            color="accent"
          />
        </div>
      </div>

      {/* User Branding */}
      <footer className="sb-footer">
        <div className="sb-footer-inner">
          <div className="sb-user-avatar">
            <Server size={14} />
          </div>
          <div className="sb-user-info">
            <span className="sb-user-name">Research Node</span>
            <div className="sb-user-status">
              <div className="sb-status-dot" />
              <span>Operational</span>
            </div>
          </div>
          <button className="sb-logout-btn" onClick={onLogout} title="Terminate Session">
            <LogOut size={14} />
          </button>
        </div>
      </footer>

      <style>{`
        .sb-root {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: #fff;
          border-right: 1px solid var(--border);
          position: relative;
          flex-shrink: 0;
          font-family: var(--font-sans);
        }

        .sb-resizer {
          position: absolute; top: 0; right: -3px; bottom: 0; width: 6px;
          cursor: col-resize; z-index: 100;
        }
        .sb-resizer-line {
          position: absolute; top: 0; bottom: 0; left: 2px; width: 2px;
          background: transparent; transition: background 0.2s;
        }
        .sb-resizer:hover .sb-resizer-line { background: var(--primary); }

        .sb-scroll { flex: 1; overflow-y: auto; display: flex; flex-direction: column; }
        .sb-scroll::-webkit-scrollbar { width: 3px; }
        .sb-scroll::-webkit-scrollbar-thumb { background: var(--border); }

        .sb-section-header {
          padding: 32px 32px 16px;
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 10px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.15em;
          color: var(--text-muted);
          opacity: 0.5;
        }
        .sb-section-stats { margin-top: 16px; }

        .sb-nav { display: flex; flex-direction: column; }
        .sb-nav-btn {
          height: 48px;
          padding: 0 32px;
          display: flex;
          align-items: center;
          background: transparent;
          border: none;
          cursor: pointer;
          transition: all 0.2s;
          position: relative;
          text-align: left;
        }
        .sb-nav-btn:hover { background: var(--bg-main); }
        .sb-nav-active { background: color-mix(in srgb, var(--primary) 5%, transparent); }
        .sb-nav-active::before {
          content: '';
          position: absolute; left: 0; top: 12px; bottom: 12px; width: 3px;
          background: var(--primary);
        }

        .sb-nav-num {
          font-family: var(--font-mono);
          font-size: 9px;
          font-weight: 800;
          color: var(--primary);
          opacity: 0.4;
          width: 32px;
          letter-spacing: 0.1em;
        }
        .sb-nav-active .sb-nav-num { opacity: 1; }

        .sb-nav-label {
          font-size: 11px;
          font-weight: 700;
          color: var(--text-muted);
          transition: color 0.15s;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .sb-nav-active .sb-nav-label { color: var(--text-main); }
        .sb-nav-chevron { margin-left: auto; color: var(--primary); opacity: 0.5; }

        .sb-metrics { padding: 8px 24px 24px; display: flex; flex-direction: column; gap: 2px; }
        .sb-metric-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 0;
          border-bottom: 1px solid var(--border);
          position: relative;
          transition: all 0.2s;
        }
        .sb-metric-item:last-child { border-bottom: none; }
        .sb-metric-item:hover { transform: translateX(2px); }
        
        .sb-metric-icon-wrap {
          width: 28px; height: 28px;
          display: flex; align-items: center; justify-content: center;
          background: var(--bg-main);
          border: 1px solid var(--border);
          color: var(--text-muted);
          opacity: 0.6;
          transition: all 0.2s;
        }
        .sb-icon-primary { color: var(--primary); }
        .sb-icon-success { color: var(--success); }
        .sb-icon-accent { color: #f59e0b; }
        .sb-metric-item:hover .sb-metric-icon-wrap { border-color: var(--primary); opacity: 1; }

        .sb-metric-content { display: flex; flex-direction: column; gap: 2px; }
        .sb-metric-label { font-size: 9px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.6; }
        .sb-metric-value { font-family: var(--font-mono); font-size: 12px; font-weight: 800; color: var(--text-main); tabular-nums: true; }
        
        .sb-metric-indicator {
          position: absolute; right: 0; width: 0; height: 2px;
          background: var(--primary); opacity: 0; transition: all 0.2s;
        }
        .sb-metric-item:hover .sb-metric-indicator { width: 12px; opacity: 0.4; }

        .sb-footer {
          padding: 24px 32px; 
          background: #fff; 
          border-top: 1px solid var(--border);
          flex-shrink: 0;
        }
        .sb-footer-inner { display: flex; align-items: center; gap: 16px; }
        .sb-user-avatar {
          width: 36px; height: 36px;
          display: flex; align-items: center; justify-content: center;
          background: #0f172a;
          color: #fff;
          border-radius: 2px;
        }
        .sb-user-info { display: flex; flex-direction: column; gap: 2px; }
        .sb-user-name { font-size: 11px; font-weight: 800; color: var(--text-main); text-transform: uppercase; letter-spacing: 0.05em; }
        .sb-user-status { display: flex; align-items: center; gap: 8px; }
        .sb-status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--success); animation: sb-blink 2s infinite; }
        @keyframes sb-blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
        .sb-user-status span { font-size: 9px; font-weight: 700; color: var(--success); text-transform: uppercase; letter-spacing: 0.1em; }

        .sb-logout-btn {
          margin-left: auto;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: transparent;
          border: 1px solid var(--border);
          color: var(--text-muted);
          cursor: pointer;
          transition: all 0.2s;
        }
        .sb-logout-btn:hover {
          background: #fef2f2;
          border-color: #fecaca;
          color: #ef4444;
          box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
        }
      `}</style>
    </aside>
  );
};
