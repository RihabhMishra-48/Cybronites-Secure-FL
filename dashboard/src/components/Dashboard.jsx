import React from 'react';
import { motion } from 'framer-motion';
import { Activity, ShieldCheck, Zap, Globe, Lock, Cpu, Server, TrendingUp, AlertCircle, Copy, Users, Radio, StopCircle } from 'lucide-react';
import { MetricsChart } from './MetricsChart';
import { BlockchainRibbon } from './BlockchainExplorer';

export const Dashboard = ({ 
  accuracyHistory = [], 
  isConnected, 
  isActive, 
  status, 
  startSimulation, 
  clearSimulation,
  blockchain = [],
  clients = [],
  rejectedCount = 0,
  round = 0,
  distributedStatus = {},
  startDistributed,
  stopDistributed,
  refreshDistributedStatus,
  nodeRegistry = {},
  apiBaseUrl = ''
}) => {
  const [distRounds, setDistRounds] = React.useState(5);
  const [distMinClients, setDistMinClients] = React.useState(1);
  const [copied, setCopied] = React.useState(false);

  const joinCommand = `python run_client.py --server ${apiBaseUrl} --name "My-Device"`;

  const handleCopy = () => {
    navigator.clipboard.writeText(joinCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleStartDistributed = async () => {
    await startDistributed(distRounds, distMinClients);
  };
  const currentAccuracy = accuracyHistory.length > 0 
    ? (accuracyHistory[accuracyHistory.length - 1] * 100).toFixed(2)
    : "0.00";

  return (
    <div className="dash-root section-fade">
      {/* ─── Header Section ─── */}
      <header className="dash-header">
        <div className="dash-header-info">
          <h2 className="dash-title">Global Orchestration Dashboard</h2>
          <div className="dash-meta">
            <div className="dash-meta-item">
              <span className="dash-meta-label">NODE_ID:</span>
              <span className="dash-meta-value">0x88F2_SECURE</span>
            </div>
            <div className="dash-meta-divider" />
            <div className="dash-meta-item">
              <span className="dash-meta-label">MODE:</span>
              <span className="dash-meta-value dash-meta-value-primary">Institutional Production</span>
            </div>
          </div>
        </div>

        <div className="dash-header-controls">
          <div className="dash-stat-group">
            <span className="dash-stat-label">Global Accuracy</span>
            <div className="dash-stat-value-wrap">
              <span className="dash-stat-value">{currentAccuracy}%</span>
              <div className={`dash-status-dot ${isConnected && isActive ? 'dash-status-active' : ''}`}>
                <Activity size={10} />
              </div>
            </div>
          </div>

          <div className="dash-actions">
            <button
              onClick={startSimulation}
              disabled={isActive || !isConnected}
              className={`dash-btn-primary ${(!isConnected || isActive) ? 'dash-btn-disabled' : ''}`}
            >
              <Zap size={12} fill="currentColor" />
              <span>{status === 'IDLE' ? 'Connect Sessions' : status === 'FINISHED' ? 'Report Complete' : 'Synchronized'}</span>
            </button>
            <button onClick={clearSimulation} className="dash-btn-icon">
              <TrendingUp size={14} />
            </button>
          </div>
        </div>
      </header>

      {/* ─── Top Metrics Grid ─── */}
      <div className="dash-grid">
        {/* Main Chart */}
        <div className="dash-card dash-card-main">
          <div className="dash-card-header">
            <div className="dash-card-title-wrap">
              <Activity size={14} className="dash-card-icon" />
              <span className="dash-card-title">Real-Time Model Convergence</span>
            </div>
            <div className="dash-card-legend">
              <div className="dash-legend-item">
                <div className="dash-legend-color" />
                <span>Converged Accuracy</span>
              </div>
            </div>
          </div>
          <div className="dash-card-body dash-chart-container">
            <MetricsChart data={accuracyHistory} isActive={isActive} />
          </div>
        </div>

        {/* Right Sidebar Stats */}
        <div className="dash-sidebar-stats">
          {/* Security Policy */}
          <div className="dash-card dash-card-accent">
            <ShieldCheck size={20} className="dash-accent-icon" />
            <h3 className="dash-accent-title">Security Policy Active</h3>
            <p className="dash-accent-text">Differential Privacy calibration enabled (L2-Clip=1.0, Noise=0.01). Coordination via Secure gRPC Tunnel.</p>
          </div>

          {/* Network Resilience */}
          <div className="dash-card">
            <div className="dash-card-header">
              <Activity size={12} className="dash-card-icon" />
              <span className="dash-card-title">Network Resilience</span>
            </div>
            <div className="dash-card-body dash-metrics-list">
              <div className="dash-metric-row">
                <span className="dash-metric-label">Active Shards</span>
                <span className="dash-metric-value">{clients.filter(c => c.status === 'ACTIVE' || c.status === 'BUSY').length} / 8</span>
              </div>
              <div className="dash-metric-row">
                <span className="dash-metric-label">Rounds Synced</span>
                <span className="dash-metric-value">{round}</span>
              </div>
              <div className="dash-metric-row">
                <span className="dash-metric-label">Integrity Alerts</span>
                <span className={`dash-metric-value ${rejectedCount > 0 ? 'dash-value-error' : 'dash-value-success'}`}>{rejectedCount}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── Blockchain Journal ─── */}
      <div className="dash-journal-section">
        <div className="dash-journal-header">
          <h3 className="dash-journal-title">Immutable Node Journal</h3>
          <div className="dash-journal-line" />
        </div>
        <div className="dash-journal-container">
          <BlockchainRibbon blockchain={blockchain} />
        </div>
      </div>

      {/* ─── Distributed Training Panel ─── */}
      <div className="dash-distributed-section">
        <div className="dash-journal-header">
          <h3 className="dash-journal-title">Distributed Training</h3>
          <div className="dash-journal-line" />
        </div>

        <div className="dash-distributed-grid">
          {/* Controls Card */}
          <div className="dash-card dash-dist-controls">
            <div className="dash-card-header">
              <div className="dash-card-title-wrap">
                <Globe size={14} className="dash-card-icon" />
                <span className="dash-card-title">Cross-Network Training</span>
              </div>
              <div className={`dash-dist-status-badge ${distributedStatus.status === 'WAITING' ? 'dash-dist-waiting' : distributedStatus.status === 'COMPLETE' ? 'dash-dist-complete' : ''}`}>
                <Radio size={8} />
                <span>{distributedStatus.status || 'IDLE'}</span>
              </div>
            </div>
            <div className="dash-card-body dash-dist-body">
              {distributedStatus.status === 'IDLE' || !distributedStatus.status ? (
                <>
                  <div className="dash-dist-config">
                    <div className="dash-dist-field">
                      <label>Rounds</label>
                      <input type="number" value={distRounds} onChange={e => setDistRounds(Number(e.target.value))} min={1} max={100} />
                    </div>
                    <div className="dash-dist-field">
                      <label>Min Clients</label>
                      <input type="number" value={distMinClients} onChange={e => setDistMinClients(Number(e.target.value))} min={1} max={10} />
                    </div>
                  </div>
                  <button className="dash-btn-primary dash-dist-start-btn" onClick={handleStartDistributed} disabled={!isConnected}>
                    <Globe size={12} />
                    <span>Start Distributed Session</span>
                  </button>
                </>
              ) : (
                <>
                  <div className="dash-dist-live">
                    <div className="dash-metric-row">
                      <span className="dash-metric-label">Round</span>
                      <span className="dash-metric-value">{distributedStatus.round} / {distributedStatus.totalRounds}</span>
                    </div>
                    <div className="dash-metric-row">
                      <span className="dash-metric-label">Connected Nodes</span>
                      <span className="dash-metric-value">{distributedStatus.registeredClients}</span>
                    </div>
                    <div className="dash-metric-row">
                      <span className="dash-metric-label">Updates This Round</span>
                      <span className="dash-metric-value">{distributedStatus.updatesReceived} / {distributedStatus.updatesNeeded}</span>
                    </div>
                  </div>
                  {distributedStatus.status !== 'COMPLETE' && (
                    <button className="dash-btn-stop" onClick={stopDistributed}>
                      <StopCircle size={12} />
                      <span>Stop Session</span>
                    </button>
                  )}
                  {distributedStatus.status === 'COMPLETE' && (
                    <button className="dash-btn-primary dash-dist-start-btn" onClick={handleStartDistributed} disabled={!isConnected}>
                      <Globe size={12} />
                      <span>Start New Session</span>
                    </button>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Join Command Card */}
          <div className="dash-card dash-dist-join">
            <div className="dash-card-header">
              <div className="dash-card-title-wrap">
                <Users size={14} className="dash-card-icon" />
                <span className="dash-card-title">Invite Devices</span>
              </div>
            </div>
            <div className="dash-card-body dash-dist-body">
              <p className="dash-dist-desc">Share this command with anyone to join training from any device, any network:</p>
              <div className="dash-dist-cmd-box">
                <code>{joinCommand}</code>
                <button className="dash-dist-copy-btn" onClick={handleCopy}>
                  <Copy size={12} />
                  <span>{copied ? 'Copied!' : 'Copy'}</span>
                </button>
              </div>
              <div className="dash-dist-steps">
                <div className="dash-dist-step"><span className="dash-dist-step-num">1</span> pip install torch torchvision requests</div>
                <div className="dash-dist-step"><span className="dash-dist-step-num">2</span> Run the command above</div>
                <div className="dash-dist-step"><span className="dash-dist-step-num">3</span> Client auto-joins the session</div>
              </div>

              {/* Live Node Registry */}
              {Object.keys(nodeRegistry).length > 0 && (
                <div className="dash-dist-nodes">
                  <div className="dash-dist-nodes-title">Connected Nodes</div>
                  {Object.entries(nodeRegistry).map(([id, node]) => (
                    <div key={id} className="dash-dist-node-row">
                      <div className={`dash-dist-node-dot ${node.status === 'VALID' ? 'dash-dot-valid' : 'dash-dot-connected'}`} />
                      <span className="dash-dist-node-name">{node.name || id.slice(0,8)}</span>
                      <span className="dash-dist-node-ip">{node.ip}</span>
                      <span className={`dash-dist-node-status ${node.status === 'VALID' ? 'dash-status-valid' : ''}`}>{node.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .dash-root {
          padding: 40px;
          display: flex;
          flex-direction: column;
          gap: 40px;
          background: var(--bg-main);
          min-height: 100%;
          font-family: var(--font-sans);
        }

        /* ─── Header ─── */
        .dash-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          padding-bottom: 32px;
          border-bottom: 1px solid var(--border);
        }
        .dash-title {
          font-family: var(--font-serif);
          font-size: 32px;
          font-weight: 500;
          color: var(--text-main);
          letter-spacing: -0.02em;
          margin: 0 0 16px 0;
        }
        .dash-meta {
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .dash-meta-item {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .dash-meta-label {
          font-size: 9px;
          font-weight: 500;
          color: var(--text-muted);
          opacity: 0.4;
          text-transform: uppercase;
          letter-spacing: 0.2em;
        }
        .dash-meta-value {
          font-size: 9px;
          font-weight: 700;
          color: var(--text-main);
          opacity: 0.8;
          text-transform: uppercase;
          letter-spacing: 0.15em;
        }
        .dash-meta-value-primary {
          color: var(--primary);
          opacity: 1;
        }
        .dash-meta-divider {
          width: 1px;
          height: 10px;
          background: var(--border);
          opacity: 0.6;
        }

        .dash-header-controls {
          display: flex;
          align-items: center;
          gap: 40px;
        }
        .dash-stat-group {
          text-align: right;
          padding-right: 40px;
          border-right: 1px solid var(--border);
          height: 44px;
          display: flex;
          flex-direction: column;
          justify-content: flex-end;
        }
        .dash-stat-label {
          font-size: 9px;
          font-weight: 700;
          color: var(--text-muted);
          opacity: 0.4;
          text-transform: uppercase;
          letter-spacing: 0.3em;
          margin-bottom: 6px;
        }
        .dash-stat-value-wrap {
          display: flex;
          align-items: baseline;
          justify-content: flex-end;
          gap: 12px;
        }
        .dash-stat-value {
          font-family: var(--font-serif);
          font-size: 28px;
          font-weight: 500;
          color: var(--text-main);
          line-height: 1;
        }
        .dash-status-dot {
          padding: 4px;
          border-radius: 50%;
          background: var(--bg-surface);
          color: var(--text-muted);
          display: flex;
          align-items: center;
          justify-content: center;
          transform: translateY(-2px);
        }
        .dash-status-active {
          background: color-mix(in srgb, var(--success) 10%, transparent);
          color: var(--success);
          animation: dash-pulse 2s infinite;
        }
        @keyframes dash-pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }

        .dash-actions {
          display: flex;
          align-items: center;
          gap: 12px;
          height: 44px;
        }
        .dash-btn-primary {
          height: 100%;
          background: var(--primary);
          color: #fff;
          border: none;
          padding: 0 32px;
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.25em;
          display: flex;
          align-items: center;
          gap: 16px;
          cursor: pointer;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .dash-btn-primary:hover:not(.dash-btn-disabled) { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.15); }
        .dash-btn-primary:active:not(.dash-btn-disabled) { transform: scale(0.98); }
        .dash-btn-disabled { opacity: 0.5; cursor: not-allowed; filter: grayscale(1); box-shadow: none; }
        
        .dash-btn-icon {
          width: 44px; height: 44px;
          display: flex; align-items: center; justify-content: center;
          border: 1px solid var(--border);
          background: transparent;
          color: var(--text-muted);
          cursor: pointer;
          transition: all 0.2s;
        }
        .dash-btn-icon:hover { background: var(--bg-surface); color: var(--text-main); border-color: var(--text-muted); }

        /* ─── Grid ─── */
        .dash-grid {
          display: grid;
          grid-template-columns: 1fr 320px;
          gap: 40px;
        }
        .dash-card {
          background: var(--bg-surface);
          border: 1px solid var(--border);
          display: flex;
          flex-direction: column;
        }
        .dash-card-header {
          padding: 16px 24px;
          border-bottom: 1px solid var(--border);
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: rgba(var(--bg-surface-rgb), 0.5);
        }
        .dash-card-title-wrap {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .dash-card-icon { color: var(--primary); opacity: 0.6; }
        .dash-card-title {
          font-size: 10px;
          font-weight: 700;
          color: var(--text-main);
          text-transform: uppercase;
          letter-spacing: 0.2em;
        }
        .dash-card-legend {
          font-size: 10px;
          font-weight: 700;
          color: var(--text-muted);
          opacity: 0.6;
          text-transform: uppercase;
          letter-spacing: 0.15em;
        }
        .dash-legend-item { display: flex; align-items: center; gap: 8px; }
        .dash-legend-color { width: 10px; height: 4px; background: var(--primary); }

        .dash-chart-container {
          padding: 32px;
          height: 380px;
          background: #fff;
        }

        .dash-sidebar-stats {
          display: flex;
          flex-direction: column;
          gap: 40px;
        }
        .dash-card-accent {
          background: var(--primary);
          color: #fff;
          border: none;
          padding: 32px;
          position: relative;
          overflow: hidden;
        }
        .dash-card-accent::after {
          content: '';
          position: absolute;
          top: -20%; right: -10%;
          width: 80%; height: 140%;
          background: linear-gradient(135deg, transparent, rgba(255,255,255,0.05));
          transform: rotate(15deg);
        }
        .dash-accent-icon { margin-bottom: 24px; opacity: 0.4; }
        .dash-accent-title {
          font-family: var(--font-serif);
          font-size: 20px;
          font-weight: 500;
          margin: 0 0 12px 0;
        }
        .dash-accent-text {
          font-size: 11px;
          line-height: 1.6;
          opacity: 0.8;
          text-transform: uppercase;
          letter-spacing: 0.02em;
          margin: 0;
        }

        .dash-metrics-list { padding: 32px; display: flex; flex-direction: column; gap: 24px; }
        .dash-metric-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-bottom: 24px;
          border-bottom: 1px solid var(--border);
        }
        .dash-metric-row:last-child { border-bottom: none; padding-bottom: 0; }
        .dash-metric-label {
          font-size: 10px;
          font-weight: 700;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.15em;
        }
        .dash-metric-value { font-size: 14px; font-weight: 700; color: var(--primary); }
        .dash-value-error { color: var(--error); }
        .dash-value-success { color: var(--success); }

        /* ─── Journal ─── */
        .dash-journal-section {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }
        .dash-journal-header {
          display: flex;
          align-items: center;
          gap: 16px;
          position: relative;
        }
        .dash-journal-title {
          font-family: var(--font-serif);
          font-size: 20px;
          font-weight: 500;
          color: var(--text-main);
          margin: 0;
          background: var(--bg-main);
          padding-right: 16px;
          z-index: 2;
        }
        .dash-journal-line {
          flex: 1;
          height: 1px;
          background: var(--border);
          opacity: 0.6;
        }
        .dash-journal-container {
          height: 320px;
          border: 1px solid var(--border);
          background: #000;
          display: flex;
          flex-direction: column;
        }

        /* ─── Distributed Panel ─── */
        .dash-distributed-section {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }
        .dash-distributed-grid {
          display: grid;
          grid-template-columns: 380px 1fr;
          gap: 24px;
        }
        .dash-dist-body {
          padding: 24px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .dash-dist-config {
          display: flex;
          gap: 16px;
        }
        .dash-dist-field {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .dash-dist-field label {
          font-size: 9px;
          font-weight: 700;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.15em;
        }
        .dash-dist-field input {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid var(--border);
          background: var(--bg-main);
          color: var(--text-main);
          font-size: 14px;
          font-weight: 600;
          font-family: var(--font-mono, monospace);
        }
        .dash-dist-start-btn {
          width: 100%;
          justify-content: center;
          height: 44px;
        }
        .dash-dist-live {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .dash-dist-status-badge {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 9px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.15em;
          color: var(--text-muted);
          padding: 4px 12px;
          border: 1px solid var(--border);
        }
        .dash-dist-waiting {
          color: var(--warning, #f59e0b);
          border-color: var(--warning, #f59e0b);
          animation: dash-pulse 2s infinite;
        }
        .dash-dist-complete {
          color: var(--success);
          border-color: var(--success);
        }
        .dash-btn-stop {
          width: 100%;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          background: transparent;
          border: 1px solid var(--error, #ef4444);
          color: var(--error, #ef4444);
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.15em;
          cursor: pointer;
          transition: all 0.2s;
        }
        .dash-btn-stop:hover {
          background: var(--error, #ef4444);
          color: #fff;
        }
        .dash-dist-desc {
          font-size: 12px;
          color: var(--text-muted);
          line-height: 1.5;
          margin: 0;
        }
        .dash-dist-cmd-box {
          display: flex;
          align-items: center;
          gap: 8px;
          background: var(--bg-main);
          border: 1px solid var(--border);
          padding: 10px 12px;
          overflow-x: auto;
        }
        .dash-dist-cmd-box code {
          flex: 1;
          font-size: 11px;
          font-family: var(--font-mono, monospace);
          color: var(--primary);
          white-space: nowrap;
        }
        .dash-dist-copy-btn {
          flex-shrink: 0;
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 4px 12px;
          border: 1px solid var(--border);
          background: transparent;
          color: var(--text-muted);
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          cursor: pointer;
          transition: all 0.2s;
        }
        .dash-dist-copy-btn:hover {
          border-color: var(--primary);
          color: var(--primary);
        }
        .dash-dist-steps {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .dash-dist-step {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 11px;
          color: var(--text-muted);
        }
        .dash-dist-step-num {
          width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--primary);
          color: #fff;
          font-size: 9px;
          font-weight: 800;
          flex-shrink: 0;
        }
        .dash-dist-nodes {
          border-top: 1px solid var(--border);
          padding-top: 16px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .dash-dist-nodes-title {
          font-size: 9px;
          font-weight: 700;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.2em;
          margin-bottom: 4px;
        }
        .dash-dist-node-row {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 6px 0;
          border-bottom: 1px solid color-mix(in srgb, var(--border) 40%, transparent);
        }
        .dash-dist-node-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          flex-shrink: 0;
        }
        .dash-dot-connected { background: var(--warning, #f59e0b); }
        .dash-dot-valid { background: var(--success); }
        .dash-dist-node-name {
          font-size: 11px;
          font-weight: 600;
          color: var(--text-main);
          flex: 1;
        }
        .dash-dist-node-ip {
          font-size: 10px;
          font-family: var(--font-mono, monospace);
          color: var(--text-muted);
          opacity: 0.6;
        }
        .dash-dist-node-status {
          font-size: 9px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--text-muted);
        }
        .dash-status-valid { color: var(--success); }

        @media (max-width: 1200px) {
          .dash-distributed-grid { grid-template-columns: 1fr; }
        }

        /* ─── Responsive ─── */
        @media (max-width: 1200px) {
          .dash-grid { grid-template-columns: 1fr; }
          .dash-sidebar-stats { flex-direction: row; }
          .dash-sidebar-stats > * { flex: 1; }
        }
      `}</style>
    </div>
  );
};
