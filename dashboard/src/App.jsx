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
import { PrivacyVault } from './components/PrivacyVault';
import { Dashboard } from './components/Dashboard';
import { Login } from './components/Login';
import { useSecureFederated } from './hooks/useSecureFederated';
import { Play, RotateCcw, ShieldCheck, Info, X, Zap, Activity, Globe } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
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
    clientsActive,
    labState
  } = useSecureFederated();

  const [currentView, setCurrentView] = useState('dashboard');
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('federated_token') !== null;
  });
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('federated_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [toasts, setToasts] = useState([]);
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [footerHeight, setFooterHeight] = useState(280);
  const [isTerminalMinimized, setIsTerminalMinimized] = useState(false);
  const resizingRef = useRef(null); // 'terminal' | 'sidebar' | null

  // Universal resize handler using refs (no stale closures)
  useEffect(() => {
    const onMouseMove = (e) => {
      if (!resizingRef.current) return;
      e.preventDefault();
      if (resizingRef.current === 'terminal') {
        const newH = window.innerHeight - e.clientY;
        if (newH >= 80 && newH <= window.innerHeight * 0.7) {
          setFooterHeight(newH);
        }
      } else if (resizingRef.current === 'sidebar') {
        if (e.clientX >= 160 && e.clientX <= 500) {
          setSidebarWidth(e.clientX);
        }
      }
    };
    const onMouseUp = () => {
      resizingRef.current = null;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, []);

  const startTerminalResize = useCallback((e) => {
    e.preventDefault();
    resizingRef.current = 'terminal';
    document.body.style.cursor = 'ns-resize';
    document.body.style.userSelect = 'none';
  }, []);

  const startSidebarResize = useCallback((e) => {
    e.preventDefault();
    resizingRef.current = 'sidebar';
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, []);


  // Session Recovery
  useEffect(() => {
    const recoverSession = async () => {
      const token = localStorage.getItem('federated_token');
      if (!token) return;

      try {
        const baseUrl = import.meta.env.PROD ? window.location.origin : `http://localhost:${import.meta.env.VITE_BACKEND_PORT || '7880'}`;
        const response = await fetch(`${baseUrl}/api/auth/me?token=${token}`);
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
          setIsAuthenticated(true);
        } else {
          handleLogout();
        }
      } catch (err) {
        console.error("Session recovery failed:", err);
      }
    };
    recoverSession();
  }, []);

  const addToast = (msg, type = 'success') => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, msg, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3000);
  };

  const startSimulation = async () => {
    if (!isConnected) {
      addToast('Backend connection offline.', 'error');
      return;
    }

    addToast(status === 'IDLE' ? 'Initiating Federated Session...' : 'Session already in progress.', 'info');
    // In our new architecture, run_backend.py starts the rounds. 
    // The button acts as a "Synchonize/Monitor" state.
    await runRound();
  };

  const handleLogin = (data) => {
    const { access_token, user: userData } = data;
    setIsAuthenticated(true);
    setUser(userData);
    localStorage.setItem('federated_token', access_token);
    localStorage.setItem('federated_user', JSON.stringify(userData));
    addToast(`Access Granted: Welcome ${userData.username || userData.id}`, 'success');
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('federated_token');
    localStorage.removeItem('federated_user');
    addToast('Session Terminated.', 'info');
  };

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return (
          <Dashboard 
            accuracyHistory={accuracyHistory}
            isConnected={isConnected}
            isActive={isActive}
            status={status}
            startSimulation={startSimulation}
            clearSimulation={clearSimulation}
            blockchain={blockchain}
            clients={clients}
            rejectedCount={rejectedCount}
            round={round}
          />
        );
      case 'architecture':
        return <ArchitectureBuilder onAction={addToast} />;
      case 'training':
        return (
          <TrainingWorkspace 
            clients={clients} 
            logs={logs} 
            accuracyHistory={accuracyHistory} 
            lossHistory={lossHistory} 
            hyperparams={hyperparams} 
            roundHistory={roundHistory} 
            modelArchitecture={modelArchitecture} 
            onClear={clearLogs} 
            onInitiate={startSimulation}
            isActive={isActive}
          />
        );
      case 'datasets':
        return <DatasetExplorer shards={shards} clientsActive={clientsActive} />;
      case 'laboratory':
        return <Laboratory onAction={addToast} labState={labState} />;
      case 'privacy_vault':
        return <PrivacyVault />;
      default:
        return <div>View not found</div>;
    }
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

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
          onLogout={handleLogout}
        />

        <main className="flex-1 flex flex-col" style={{ minWidth: 0, overflow: 'hidden' }}>
          <div className="flex-1" style={{ overflowY: 'auto', minHeight: 0 }}>
            {renderView()}
          </div>

          <div 
            className="transition-all duration-300 ease-in-out"
            style={{ 
              height: (currentView === 'training' || currentView === 'laboratory') 
                ? 0 
                : (isTerminalMinimized ? 36 : footerHeight), 
              flexShrink: 0,
              overflow: 'hidden'
            }}
          >
            <Terminal
              logs={logs}
              onResize={startTerminalResize}
              isResizing={!!resizingRef.current}
              nodeRegistry={nodeRegistry}
              accuracyHistory={accuracyHistory}
              lossHistory={lossHistory}
              roundHistory={roundHistory}
              onClear={clearLogs}
              onAction={(cmd) => addToast(`Terminal command executed: ${cmd}`, 'info')}
              isMinimized={isTerminalMinimized}
              onToggleMinimize={() => setIsTerminalMinimized(!isTerminalMinimized)}
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

export default App;
