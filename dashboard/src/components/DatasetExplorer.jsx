import React from 'react';
import { 
  Database, ShieldCheck, Share2, Box, PieChart, 
  Activity, HardDrive, Search, Filter, Info, 
  FileText, Download, ChevronRight, Server
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const DatasetExplorer = ({ shards = [], clientsActive = 0 }) => {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [filterType, setFilterType] = React.useState('All');
  
  const fragments = shards.slice(0, clientsActive);
  const types = ['All', ...new Set(fragments.map(f => f.type))];

  const filteredFragments = fragments.filter(frag => {
    const matchesSearch = frag.org.toLowerCase().includes(searchQuery.toLowerCase()) || 
                         frag.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterType === 'All' || frag.type === filterType;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="ds-root section-fade">
      {/* ─── Header ─── */}
      <header className="ds-header">
        <div className="ds-header-left">
          <div className="ds-module-badge">
            <span className="ds-badge-num">03</span>
            <span className="ds-badge-sep" />
            <span className="ds-badge-text">Shard Registry</span>
          </div>
          <h2 className="ds-title">Distributed Data Inventory</h2>
          <p className="ds-subtitle">
            Cryptographic registry of institutional shards currently indexed for federated synchronization. 
            All fragments are hashed and verified against the global audit ledger height.
          </p>
        </div>
        
        <div className="ds-header-right">
          <div className="ds-total-card">
            <Database size={14} className="ds-total-icon" />
            <div className="ds-total-info">
              <span className="ds-total-label">Indexed Capacity</span>
              <span className="ds-total-value">12.4 TB</span>
            </div>
          </div>
        </div>
      </header>

      {/* ─── Controls ─── */}
      <div className="ds-controls">
        <div className="ds-search-group">
          <Search size={14} className={`ds-control-icon ${searchQuery ? 'ds-active' : ''}`} />
          <input 
            type="text"
            placeholder="FILTER FRAGMENTS..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="ds-search-input"
          />
        </div>
        
        <div className="ds-filter-group">
          <Filter size={14} className={`ds-control-icon ${filterType !== 'All' ? 'ds-active' : ''}`} />
          <select 
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="ds-filter-select"
          >
            {types.map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}
          </select>
        </div>

        <div className="ds-ledger-status">
          <ShieldCheck size={12} className="ds-status-icon" />
          <span>Ledger Height: 48,291</span>
        </div>
      </div>

      {/* ─── Registry Grid ─── */}
      <div className="ds-grid">
        <AnimatePresence mode="popLayout">
          {filteredFragments.length > 0 ? filteredFragments.map((frag, idx) => (
            <motion.div
              key={frag.id}
              layout
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2, delay: idx * 0.05 }}
              className="ds-card group"
            >
              <div className="ds-card-header">
                <div className="ds-card-tag">FRAG-{frag.id}</div>
                <h3 className="ds-card-org">{frag.org}</h3>
                <div className="ds-card-icon-wrap">
                  <FileText size={16} />
                </div>
              </div>

              <div className="ds-card-body">
                <div className="ds-metric-group">
                  <div className="ds-metric-header">
                    <span className="ds-metric-label">Shard Density</span>
                    <span className="ds-metric-value">{frag.density}%</span>
                  </div>
                  <div className="ds-progress-track">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${frag.density}%` }}
                      className="ds-progress-fill"
                    />
                  </div>
                </div>

                <div className="ds-stats-row">
                  <div className="ds-stat">
                    <span className="ds-stat-label">Samples</span>
                    <span className="ds-stat-value">{(frag.size || 0).toLocaleString()}</span>
                  </div>
                  <div className="ds-stat-divider" />
                  <div className="ds-stat">
                    <span className="ds-stat-label">Protocol</span>
                    <span className="ds-stat-value">{frag.type}</span>
                  </div>
                </div>
              </div>
              
              <div className="ds-card-footer">
                <span className="ds-footer-date">{frag.date}</span>
                <button className="ds-footer-btn">
                  <span>METADATA</span>
                  <Download size={10} />
                </button>
              </div>
            </motion.div>
          )) : (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="ds-empty"
            >
              <div className="ds-empty-box">
                <Box size={32} className="ds-empty-icon" />
                <h4 className="ds-empty-title">Registry Empty</h4>
                <p className="ds-empty-text">No institutional shards detected matching selected criteria.</p>
                <button className="ds-empty-btn" onClick={() => { setSearchQuery(''); setFilterType('All'); }}>
                  Reset Filters
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <style>{`
        .ds-root {
          padding: 40px;
          display: flex;
          flex-direction: column;
          gap: 40px;
          background: var(--bg-main);
          min-height: 100%;
          font-family: var(--font-sans);
          padding-bottom: 120px;
        }

        /* ─── Header ─── */
        .ds-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
        }
        .ds-module-badge {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
        }
        .ds-badge-num { font-size: 10px; font-weight: 800; color: var(--primary); letter-spacing: 0.1em; }
        .ds-badge-sep { width: 24px; height: 1px; background: var(--primary); opacity: 0.2; }
        .ds-badge-text { font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.2em; }
        
        .ds-title { font-family: var(--font-serif); font-size: 32px; font-weight: 500; color: var(--text-main); margin: 0 0 12px 0; letter-spacing: -0.01em; }
        .ds-subtitle { font-size: 13px; color: var(--text-muted); line-height: 1.6; max-width: 600px; margin: 0; }

        .ds-total-card {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 16px 24px;
          background: var(--bg-surface);
          border: 1px solid var(--border);
        }
        .ds-total-icon { color: var(--primary); opacity: 0.4; }
        .ds-total-info { display: flex; flex-direction: column; gap: 4px; }
        .ds-total-label { font-size: 9px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.15em; }
        .ds-total-value { font-size: 14px; font-weight: 800; color: var(--text-main); font-family: var(--font-mono); }

        /* ─── Controls ─── */
        .ds-controls {
          display: flex;
          align-items: center;
          gap: 40px;
          padding-bottom: 24px;
          border-bottom: 1px solid var(--border);
        }
        .ds-search-group, .ds-filter-group {
          display: flex;
          align-items: center;
          gap: 12px;
          position: relative;
        }
        .ds-control-icon { color: var(--text-muted); opacity: 0.4; transition: all 0.2s; }
        .ds-control-icon.ds-active { color: var(--primary); opacity: 1; }
        
        .ds-search-input {
          background: none; border: none; outline: none;
          font-size: 11px; font-weight: 700; color: var(--text-main);
          text-transform: uppercase; letter-spacing: 0.15em;
          width: 180px; padding: 4px 0;
        }
        .ds-search-input::placeholder { color: var(--text-muted); opacity: 0.3; }

        .ds-filter-select {
          background: none; border: none; outline: none;
          font-size: 11px; font-weight: 700; color: var(--text-main);
          text-transform: uppercase; letter-spacing: 0.15em;
          cursor: pointer; appearance: none;
          padding: 4px 24px 4px 0;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right center;
        }

        .ds-ledger-status {
          margin-left: auto;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 10px;
          font-weight: 700;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.1em;
          opacity: 0.5;
        }

        /* ─── Grid ─── */
        .ds-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 32px;
        }
        .ds-card {
          background: var(--bg-surface);
          border: 1px solid var(--border);
          display: flex;
          flex-direction: column;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .ds-card:hover { border-color: var(--primary); transform: translateY(-4px); box-shadow: 0 12px 32px rgba(0,0,0,0.06); }
        
        .ds-card-header {
          padding: 24px 32px;
          border-bottom: 1px solid var(--border);
          position: relative;
        }
        .ds-card-tag {
          font-size: 9px; font-weight: 800; color: var(--primary);
          text-transform: uppercase; letter-spacing: 0.2em;
          margin-bottom: 12px;
        }
        .ds-card-org {
          font-family: var(--font-serif); font-size: 18px; font-weight: 500;
          color: var(--text-main); margin: 0; text-transform: uppercase;
          letter-spacing: -0.01em;
        }
        .ds-card-icon-wrap {
          position: absolute; top: 24px; right: 24px;
          color: var(--border); transition: color 0.2s;
        }
        .ds-card:hover .ds-card-icon-wrap { color: var(--primary); opacity: 0.3; }

        .ds-card-body { padding: 32px; display: flex; flex-direction: column; gap: 32px; }
        .ds-metric-group { display: flex; flex-direction: column; gap: 12px; }
        .ds-metric-header { display: flex; justify-content: space-between; align-items: flex-end; }
        .ds-metric-label { font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; }
        .ds-metric-value { font-size: 12px; font-weight: 800; color: var(--text-main); font-family: var(--font-mono); }
        
        .ds-progress-track { height: 4px; background: var(--bg-main); overflow: hidden; }
        .ds-progress-fill { height: 100%; background: var(--primary); }

        .ds-stats-row { display: flex; align-items: center; margin: 0 -32px -32px; border-top: 1px solid var(--border); background: #fff; }
        .ds-stat { flex: 1; padding: 20px 32px; display: flex; flex-direction: column; gap: 4px; }
        .ds-stat-label { font-size: 9px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.5; }
        .ds-stat-value { font-size: 12px; font-weight: 700; color: var(--text-main); font-family: var(--font-mono); }
        .ds-stat-divider { width: 1px; height: 32px; background: var(--border); }

        .ds-card-footer {
          margin-top: auto;
          padding: 16px 32px;
          border-top: 1px solid var(--border);
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: rgba(var(--bg-main-rgb), 0.1);
          opacity: 0.4; transition: opacity 0.2s;
        }
        .ds-card:hover .ds-card-footer { opacity: 1; }
        .ds-footer-date { font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; }
        .ds-footer-btn {
          background: none; border: none; cursor: pointer;
          font-size: 10px; font-weight: 800; color: var(--primary);
          display: flex; align-items: center; gap: 8px;
          text-transform: uppercase; letter-spacing: 0.1em;
        }

        /* ─── Empty state ─── */
        .ds-empty { grid-column: 1 / -1; display: flex; justify-content: center; padding: 80px 0; }
        .ds-empty-box {
          max-width: 400px; text-align: center; display: flex; flex-direction: column; align-items: center;
          padding: 60px; border: 2px dashed var(--border); background: var(--bg-surface);
        }
        .ds-empty-icon { color: var(--border); margin-bottom: 24px; }
        .ds-empty-title { font-family: var(--font-serif); font-size: 18px; color: var(--text-main); margin: 0 0 12px 0; }
        .ds-empty-text { font-size: 13px; color: var(--text-muted); line-height: 1.6; margin: 0 0 32px 0; }
        .ds-empty-btn {
          height: 36px; padding: 0 20px; background: var(--primary); color: #fff;
          border: none; font-size: 10px; font-weight: 700; text-transform: uppercase;
          letter-spacing: 0.15em; cursor: pointer;
        }
      `}</style>
    </div>
  );
};
