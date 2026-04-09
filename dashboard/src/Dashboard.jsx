import { useState, useEffect, useCallback, useRef } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ArchitectureBuilder } from './components/ArchitectureBuilder';
import { MetricsChart } from './components/MetricsChart';
import { Terminal } from './components/Terminal';
import { BlockchainRibbon } from './components/BlockchainExplorer';
import { TrainingWorkspace } from './components/TrainingWorkspace';
import { DatasetExplorer } from './components/DatasetExplorer';
import { Laboratory } from './components/Laboratory';
import { useSecureFederated } from './hooks/useSecureFederated';
import { Play, RotateCcw, ShieldCheck, Activity, X, Globe, Zap, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from './context/AuthContext';
import { useNavigate } from 'react-router-dom';

function Dashboard() {
  const {
    round,
    isActive,
    blockchain,
    clients,
    accuracyHistory,
    lossHistory,
    rejectedCount,
    logs,
    clearLogs,
    runRound,
    setIsActive,
    clearSimulation,
    isConnected,
    status,
    lastSync,
    nodeRegistry,
    hyperparams,
    roundHistory,
    modelArchitecture,
    shards,
    clientsActive
  } = useSecureFederated();

  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const [currentView, setCurrentView] = useState('dashboard');
  const [toasts, setToasts] = useState([]);
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [footerHeight, setFooterHeight] = useState(280);
  const resizingRef = useRef(null);

  useEffect(() => {
    const onMouseMove = (e) => {
      if (!resizingRef.current) return;
      e.preventDefault();
      if (resizingRef.current === 'terminal') {
        const newH = window.innerHeight - e.clientY;
        if (newH >= 80 && newH <= window.innerHeight * 0.7) setFooterHeight(newH);
      } else if (resizingRef.current === 'sidebar') {
        if (e.clientX >= 160 && e.clientX <= 500) setSidebarWidth(e.clientX);
      }
    };
    const onMouseUp = () => { resizingRef.current = null; document.body.style.cursor = ''; };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => { window.removeEventListener('mousemove', onMouseMove); window.removeEventListener('mouseup', onMouseUp); };
  }, []);

  const startTerminalResize = useCallback((e) => { e.preventDefault(); resizingRef.current = 'terminal'; document.body.style.cursor = 'ns-resize'; }, []);
  const startSidebarResize = useCallback((e) => { e.preventDefault(); resizingRef.current = 'sidebar'; document.body.style.cursor = 'col-resize'; }, []);

  const addToast = (msg, type = 'success') => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, msg, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000);
  };

  const startSimulation = async () => {
    if (!user) { navigate('/login'); return; }
    if (!isConnected) { addToast('Backend connection offline.', 'error'); return; }
    addToast(status === 'IDLE' ? 'Monitoring external backend...' : 'Session already in progress.', 'info');
    await runRound();
  };

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return (
          <div className="flex-1 p-10 space-y-12 section-fade bg-white">
            <div className="flex items-end justify-between pb-8 border-b border-border">
              <div className="space-y-4">
                <h2 className="type-l2 serif text-text-main pr-10 font-medium tracking-tight">Global Orchestrator</h2>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-medium text-text-muted/40 uppercase tracking-[0.2em]">NODE_ID:</span>
                    <span className="text-[9px] font-bold text-text-main/80 uppercase tracking-widest">0x88F2_SECURE</span>
                  </div>
                  <div className="w-[1px] h-2 bg-border/60" />
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-medium text-text-muted/40 uppercase tracking-[0.2em]">USER:</span>
                    <span className="text-[9px] font-bold text-primary uppercase tracking-widest">{user?.username || 'ANONYMOUS'}</span>
                  </div>
                  <div className="w-[1px] h-2 bg-border/60" />
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-medium text-text-muted/40 uppercase tracking-[0.2em]">MODE:</span>
                    <span className="text-[9px] font-bold text-primary uppercase tracking-widest">Institutional Production</span>
                  </div>
                </div>
              </div>

              <div className="flex items-end gap-10">
                <div className="text-right pr-10 border-r border-border h-10 flex flex-col justify-end">
                  <div className="text-[9px] font-bold text-text-muted mb-1.5 uppercase tracking-[0.3em] opacity-40">Global Accuracy</div>
                  <div className="flex items-baseline justify-end gap-3">
                    <span className="text-2xl serif text-text-main font-medium tabular-nums leading-none">
                      {accuracyHistory && accuracyHistory.length > 0
                        ? (accuracyHistory[accuracyHistory.length - 1] * 100).toFixed(2)
                        : "0.00"}%
                    </span>
                    <div className="flex items-center gap-2 translate-y-[-2px]">
                      <div className={`p-1 rounded-full ${isConnected ? 'bg-emerald-50' : 'bg-red-50'}`}>
                        <Activity size={10} className={isConnected && isActive ? 'text-emerald-500 animate-pulse' : 'text-text-muted'} />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 h-10">
                  <button
                    onClick={() => user ? startSimulation() : navigate('/login')}
                    disabled={user && (isActive || !isConnected)}
                    className={`h-full bg-primary text-white flex items-center gap-4 shadow-lg active:scale-95 transition-all px-8 text-[11px] font-bold uppercase tracking-[0.25em] ${(user && (!isConnected || isActive)) ? 'opacity-50 cursor-not-allowed grayscale' : ''}`}
                  >
                    <Play size={12} fill="currentColor" className={isActive ? 'animate-pulse' : ''} />
                    <span>
                      {!user ? 'Login Required' : status === 'IDLE' ? 'Connect Sessions' : status === 'FINISHED' ? 'Report Complete' : 'Synchronized'}
                    </span>
                  </button>
                  {user ? (
                    <button
                      onClick={logout}
                      title="Logout"
                      className="h-full px-4 border border-border text-red-500 hover:bg-red-50 transition-all flex items-center justify-center"
                    >
                      <X size={14} />
                    </button>
                  ) : (
                    <button
                      onClick={() => navigate('/login')}
                      className="h-full px-6 border border-primary text-primary hover:bg-primary/10 transition-all flex items-center justify-center text-[10px] uppercase font-bold"
                    >
                      Sign In To Operate
                    </button>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-10">
              <div className="xl:col-span-2 space-y-10">
                <div className="institutional-card">
                  <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-bg-surface/50">
                    <div className="flex items-center gap-4">
                      <Activity size={14} className="text-primary opacity-60" />
                      <span className="text-[10px] font-bold text-text-main uppercase tracking-[0.2em] pr-10">Real-Time Model Convergence</span>
                    </div>
                    <div className="flex items-center gap-4 text-[10px] uppercase font-bold tracking-widest text-text-muted/60 font-sans">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-1 bg-primary" /> Converged Accuracy
                      </div>
                    </div>
                  </div>
                  <div className="p-8 h-[340px]">
                    <MetricsChart data={accuracyHistory} isActive={isActive} />
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="relative flex items-center">
                    <h3 className="type-l2 serif text-text-main pr-4 bg-white relative z-10">Immutable Node Journal</h3>
                    <div className="absolute inset-0 flex items-center" aria-hidden="true">
                      <div className="w-full border-t border-border/60"></div>
                    </div>
                  </div>
                  <div className="h-[240px] border border-border/60 rounded-sm overflow-hidden">
                    <BlockchainRibbon blockchain={blockchain} />
                  </div>
                </div>
              </div>

              <div className="space-y-10">
                <div className="institutional-card bg-primary text-white border-none overflow-hidden group">
                  <div className="p-8 relative z-10">
                    <ShieldCheck className="mb-6 opacity-40 group-hover:scale-110 transition-transform" size={24} />
                    <h3 className="type-l2 serif mb-4">Security Policy Active</h3>
                    <p className="text-[11px] leading-relaxed opacity-80 uppercase tracking-tight font-sans">
                      Differential Privacy calibration enabled (L2-Clip=1.0, Noise=0.01). Coordination via Secure gRPC Tunnel.
                    </p>
                  </div>
                </div>

                <div className="institutional-card">
                  <div className="px-6 py-4 border-b border-border flex items-center gap-3 bg-bg-surface/50">
                    <Activity size={14} className="text-primary" />
                    <span className="type-label text-text-main font-bold">Network Resilience</span>
                  </div>
                  <div className="p-8 space-y-6">
                    <div className="flex justify-between items-center pb-6 border-b border-border/50">
                      <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Active Shards</span>
                      <span className="type-label text-primary font-bold">{clients.filter(c => c.status === 'ACTIVE' || c.status === 'BUSY').length} / 8</span>
                    </div>
                    <div className="flex justify-between items-center pb-6 border-b border-border/50">
                      <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Rounds Synced</span>
                      <span className="type-label text-primary font-bold">{round}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Integrity Alerts</span>
                      <span className={`type-label font-bold ${rejectedCount > 0 ? 'text-red-600' : 'text-emerald-600'}`}>{rejectedCount}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      case 'architecture': return <ArchitectureBuilder onAction={addToast} />;
      case 'training': return <TrainingWorkspace clients={clients} logs={logs} accuracyHistory={accuracyHistory} lossHistory={lossHistory} hyperparams={hyperparams} roundHistory={roundHistory} modelArchitecture={modelArchitecture} />;
      case 'datasets': return <DatasetExplorer shards={shards} clientsActive={clientsActive} />;
      case 'laboratory': return <Laboratory onAction={addToast} />;
      default: return <div>View not found</div>;
    }
  };

  return (
    <div className={`shell-container selection:bg-primary/10 bg-white`}>
      <Header status={isConnected ? (isActive ? 'TRAINING' : status || 'CONNECTED') : 'OFFLINE'} />

      <div className="flex flex-1" style={{ overflow: 'hidden' }}>
        <Sidebar
          currentView={currentView}
          setView={setCurrentView}
          clients={clients}
          nodeRegistry={nodeRegistry}
          rejectedCount={rejectedCount}
          blockchain={blockchain}
          width={sidebarWidth}
          onResize={startSidebarResize}
        />

        <main className="flex-1 flex flex-col" style={{ minWidth: 0, overflow: 'hidden' }}>
          <div className="flex-1" style={{ overflowY: 'auto', minHeight: 0 }}>
            {renderView()}
          </div>

          <div style={{ height: footerHeight, flexShrink: 0 }}>
            <Terminal
              logs={logs}
              onResize={startTerminalResize}
              isResizing={!!resizingRef.current}
              nodeRegistry={nodeRegistry}
              accuracyHistory={accuracyHistory}
              lossHistory={lossHistory}
              roundHistory={roundHistory}
              onClear={clearLogs}
              onAction={(cmd) => {
                if (!user) { navigate('/login'); return; }
                addToast(`Terminal command executed: ${cmd}`, 'info');
              }}
            />
          </div>
        </main>
      </div>

      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 50, x: 20 }}
            animate={{ opacity: 1, y: 0, x: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className={`institutional-toast-enterprise fixed right-8 bottom-8 z-[200] ${toast.type === 'error' ? 'border-red-500 bg-red-50 text-red-700' : ''}`}
          >
            <div className="flex items-center gap-3">
              {toast.type === 'error' ? <X size={14} /> : <ShieldCheck size={14} />}
              <span className="type-label font-bold uppercase tracking-widest">{toast.msg}</span>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

export default Dashboard;
