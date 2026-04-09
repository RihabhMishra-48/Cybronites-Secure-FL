import React, { useState, useRef, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Cpu, ShieldCheck, Zap, Settings2, Lock, 
  Server, Download, PanelRightClose, PanelRightOpen,
  Terminal, Activity, ChevronRight, Code, Layers,
  Search, Plus, Minus, X, Link, Trash2, BookOpen
} from 'lucide-react';

/* ═══════════════════════════════════════════
   DRAGGABLE NODE
═══════════════════════════════════════════ */
const LayerNode = ({ id, type, name, active, onSelect, metadata, position, onDragEnd, onPortClick, onDelete, isConnecting }) => (
  <motion.div
    drag
    dragMomentum={false}
    onDragEnd={(e, info) => onDragEnd(id, info)}
    onClick={onSelect}
    initial={position}
    animate={position}
    className="arch-node-wrap"
    style={{ position: 'absolute', left: position.x, top: position.y, zIndex: active ? 20 : 10 }}
  >
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      {/* Input Port */}
      <button 
        onClick={(e) => { e.stopPropagation(); onPortClick(id, 'input'); }}
        className={`arch-port ${isConnecting && isConnecting.to === id ? 'arch-port-active' : ''}`}
      />
      
      <div className={`arch-node ${active ? 'arch-node-selected' : ''}`}>
        <div className={`arch-node-header ${active ? 'arch-node-header-active' : ''}`}>
          <span className="arch-node-type">{type}</span>
          {active && onDelete && (
            <button onClick={(e) => { e.stopPropagation(); onDelete(id); }} className="arch-node-delete">
              <Trash2 size={10} />
            </button>
          )}
        </div>
        <div className="arch-node-body">
          <h4 className="arch-node-name">{name}</h4>
          {metadata && metadata.length > 0 && (
            <div className="arch-node-meta">
              {metadata.map((m, i) => (
                <div key={i} className="arch-meta-row">
                  <span className="arch-meta-label">{m.label}:</span>
                  <span className={`arch-meta-value ${active ? 'arch-meta-value-active' : ''}`}>{m.value}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        {active && <div className="arch-node-dot" />}
      </div>

      {/* Output Port */}
      <button 
        onClick={(e) => { e.stopPropagation(); onPortClick(id, 'output'); }}
        className={`arch-port ${isConnecting && isConnecting.from === id ? 'arch-port-active' : ''}`}
      />
    </div>
  </motion.div>
);

/* ═══════════════════════════════════════════
   BEZIER CONNECTION
═══════════════════════════════════════════ */
const ConnectionLine = ({ from, to, onDelete }) => {
  if (!from || !to) return null;
  const startX = from.x + 95, startY = from.y + 100;
  const endX = to.x + 95, endY = to.y;
  const cp = (startY + endY) / 2;
  const d = `M ${startX} ${startY} C ${startX} ${cp}, ${endX} ${cp}, ${endX} ${endY}`;
  const midX = (startX + endX) / 2, midY = (startY + endY) / 2;

  return (
    <g className="arch-edge-group">
      <motion.path d={d} className="arch-edge-path" fill="none" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} />
      <foreignObject x={midX - 10} y={midY - 10} width="20" height="20" className="arch-edge-delete-wrap">
        <button onClick={onDelete} className="arch-edge-delete"><X size={8} /></button>
      </foreignObject>
    </g>
  );
};

/* ═══════════════════════════════════════════
   MAIN COMPONENT
═══════════════════════════════════════════ */
export const ArchitectureBuilder = ({ onAction }) => {
  const [activeNode, setActiveNode] = useState('global');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [viewScale, setViewScale] = useState(0.85);
  const [isConnecting, setIsConnecting] = useState(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const [search, setSearch] = useState('');

  const [positions, setPositions] = useState({
    global: { x: 350, y: 40 },
    blockchain: { x: 160, y: 220 },
    security: { x: 540, y: 220 },
    aggregation: { x: 350, y: 400 }
  });

  const [nodes, setNodes] = useState({
    global: { title: 'Aggregation Hub', type: 'Core', metadata: [{ label: 'I/O', value: 'Unified' }] },
    blockchain: { title: 'Audit Ledger', type: 'Consensus', metadata: [{ label: 'Ledger', value: 'Active' }] },
    security: { title: 'Compliance Shard', type: 'Secure', metadata: [{ label: 'Privacy', value: 'DP' }] },
    aggregation: { title: 'Training Node', type: 'Compute', metadata: [{ label: 'GFLOPs', value: '1.2k' }] }
  });

  const [edges, setEdges] = useState([
    { id: 'e1', from: 'global', to: 'blockchain' },
    { id: 'e2', from: 'global', to: 'security' },
    { id: 'e3', from: 'blockchain', to: 'aggregation' },
    { id: 'e4', from: 'security', to: 'aggregation' }
  ]);

  const libraryTemplates = useMemo(() => ([
    {
      id: 'mnist-mlp', name: 'MNIST-MLP Base',
      nodes: {
        'in': { title: 'Input [28x28]', type: 'Inference', metadata: [{ label: 'Dim', value: '784' }] },
        'h1': { title: 'Hidden Layer 1', type: 'Dense', metadata: [{ label: 'Nodes', value: '128' }] },
        'h2': { title: 'Hidden Layer 2', type: 'Dense', metadata: [{ label: 'Nodes', value: '64' }] },
        'out': { title: 'Classifier', type: 'Output', metadata: [{ label: 'Classes', value: '10' }] }
      },
      edges: [{ id: 'l1', from: 'in', to: 'h1' }, { id: 'l2', from: 'h1', to: 'h2' }, { id: 'l3', from: 'h2', to: 'out' }],
      layout: { 'in': { x: 250, y: 60 }, 'h1': { x: 250, y: 230 }, 'h2': { x: 250, y: 400 }, 'out': { x: 250, y: 570 } }
    },
    {
      id: 'secure-resnet', name: 'Secure-ResNet Shard',
      nodes: {
        'r_in': { title: 'Res-Block V1', type: 'Core', metadata: [{ label: 'Filters', value: '64' }] },
        'r_sec': { title: 'TEE Encryption', type: 'Secure', metadata: [{ label: 'Level', value: 'Hardened' }] },
        'r_agg': { title: 'Aggregator', type: 'Sequential', metadata: [{ label: 'Strategy', value: 'FedAvg' }] }
      },
      edges: [{ id: 'rl1', from: 'r_in', to: 'r_sec' }, { id: 'rl2', from: 'r_sec', to: 'r_agg' }],
      layout: { 'r_in': { x: 250, y: 80 }, 'r_sec': { x: 250, y: 260 }, 'r_agg': { x: 250, y: 440 } }
    }
  ]), []);

  const addNodeFromPalette = (name, type) => {
    const id = `node-${Date.now()}`;
    setPositions(prev => ({ ...prev, [id]: { x: 280 + Math.random() * 80, y: 180 + Math.random() * 80 } }));
    setNodes(prev => ({ ...prev, [id]: { title: name, type: type || 'Dense', metadata: [{ label: 'Alloc', value: 'Auto' }] } }));
    setActiveNode(id);
    onAction?.(`Initialized ${name} shard.`);
  };

  const applyTemplate = (template) => {
    setPositions(template.layout);
    setNodes(template.nodes);
    setEdges(template.edges);
    setActiveNode(Object.keys(template.nodes)[0]);
    onAction?.(`Loaded Template: ${template.name}`);
  };

  const deleteNode = (id) => {
    if (['global', 'aggregation', 'blockchain', 'security'].includes(id)) {
      onAction?.(`Cannot delete core node: ${id}`, 'error');
      return;
    }
    setNodes(prev => { const n = { ...prev }; delete n[id]; return n; });
    setPositions(prev => { const p = { ...prev }; delete p[id]; return p; });
    setEdges(prev => prev.filter(e => e.from !== id && e.to !== id));
    setActiveNode('global');
  };

  const compileModel = () => {
    setIsCompiling(true);
    setTimeout(() => { setIsCompiling(false); onAction?.('Architecture Compiled & Deployed.', 'success'); }, 2000);
  };

  const handleDragEnd = (id, info) => {
    setPositions(prev => ({ ...prev, [id]: { x: prev[id].x + info.delta.x, y: prev[id].y + info.delta.y } }));
  };

  const handlePortClick = (id, type) => {
    if (!isConnecting) {
      if (type === 'output') setIsConnecting({ from: id });
      else setIsConnecting({ to: id });
    } else {
      if (type === 'input' && isConnecting.from && isConnecting.from !== id) {
        setEdges([...edges, { id: `edge-${Date.now()}`, from: isConnecting.from, to: id }]);
      } else if (type === 'output' && isConnecting.to && isConnecting.to !== id) {
        setEdges([...edges, { id: `edge-${Date.now()}`, from: id, to: isConnecting.to }]);
      }
      setIsConnecting(null);
    }
  };

  const current = nodes[activeNode] || nodes['global'];

  const paletteCategories = {
    "Neural Topology": ['Dense', 'Convolutional', 'Recurrent', 'Activation'],
    "Compliance Shards": ['Input', 'Security', 'Aggregation', 'Gateway'],
    "Secure Storage": ['Blockchain', 'TEE-Vault', 'HSM-Node']
  };

  return (
    <div className="arch-root">
      {/* ─── Left: Component Library ─── */}
      <aside className="arch-library">
        <div className="arch-lib-header">
          <BookOpen size={14} />
          <span>Model Library</span>
        </div>
        <div className="arch-lib-search-wrap">
          <input
            type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search components..." className="arch-lib-search"
          />
          <Search size={12} className="arch-lib-search-icon" />
        </div>

        <div className="arch-lib-scroll">
          {/* Presets */}
          <div className="arch-lib-section">
            <span className="arch-lib-section-title">Model Presets</span>
            {libraryTemplates.map(t => (
              <button key={t.id} onClick={() => applyTemplate(t)} className="arch-preset-btn">
                <span className="arch-preset-name">{t.name}</span>
                <span className="arch-preset-info">Nodes: {Object.keys(t.nodes).length}</span>
              </button>
            ))}
          </div>

          {/* Components */}
          {Object.entries(paletteCategories).map(([cat, items]) => (
            <div key={cat} className="arch-lib-section">
              <span className="arch-lib-section-title">{cat}</span>
              {items.filter(n => n.toLowerCase().includes(search.toLowerCase())).map(name => (
                <button key={name} onClick={() => addNodeFromPalette(name, name)} className="arch-component-btn">
                  <Layers size={11} />
                  <span>{name}</span>
                </button>
              ))}
            </div>
          ))}
        </div>
      </aside>

      {/* ─── Center: Canvas ─── */}
      <main className="arch-canvas-area" onClick={() => setIsConnecting(null)}>
        {/* Canvas Header Badges */}
        <div className="arch-canvas-badges">
          <div className="arch-badge">
            <div className="arch-badge-dot" />
            <span>Forge: Ready</span>
          </div>
          {isConnecting && (
            <div className="arch-badge arch-badge-connecting">
              <Link size={10} />
              <span>Connecting...</span>
            </div>
          )}
          <div className="arch-badge" style={{ marginLeft: 'auto' }}>
            <span>{Object.keys(nodes).length} nodes · {edges.length} edges</span>
          </div>
        </div>

        {/* Zoomable Canvas */}
        <div className="arch-canvas-scroll">
          <motion.div
            className="arch-canvas-inner"
            animate={{ scale: viewScale }}
            transition={{ type: 'spring', damping: 25, stiffness: 120 }}
            style={{ transformOrigin: '0 0' }}
          >
            <svg className="arch-svg-layer">
              {edges.map(edge => (
                <ConnectionLine
                  key={edge.id}
                  from={positions[edge.from]}
                  to={positions[edge.to]}
                  onDelete={() => setEdges(edges.filter(e => e.id !== edge.id))}
                />
              ))}
            </svg>

            {Object.keys(positions).map(key => (
              <LayerNode
                key={key} id={key}
                type={nodes[key]?.type} name={nodes[key]?.title}
                metadata={nodes[key]?.metadata} active={activeNode === key}
                position={positions[key]} isConnecting={isConnecting}
                onSelect={() => setActiveNode(key)}
                onDragEnd={handleDragEnd}
                onPortClick={handlePortClick}
                onDelete={deleteNode}
              />
            ))}
          </motion.div>
        </div>

        {/* Zoom Controls */}
        <div className="arch-zoom-controls">
          <button onClick={() => setViewScale(s => Math.max(0.4, s - 0.1))} className="arch-zoom-btn"><Minus size={14} /></button>
          <span className="arch-zoom-label">{Math.round(viewScale * 100)}%</span>
          <button onClick={() => setViewScale(s => Math.min(1.5, s + 0.1))} className="arch-zoom-btn"><Plus size={14} /></button>
        </div>
      </main>

      {/* ─── Right: Inspector ─── */}
      {!isSidebarOpen && (
        <button onClick={() => setIsSidebarOpen(true)} className="arch-inspector-toggle">
          <PanelRightOpen size={16} />
        </button>
      )}
      <AnimatePresence>
        {isSidebarOpen && (
          <motion.aside
            className="arch-inspector"
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 320, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="arch-insp-header">
              <div className="arch-insp-header-left">
                <Settings2 size={14} />
                <span>Inspector</span>
              </div>
              <button onClick={() => setIsSidebarOpen(false)} className="arch-insp-close">
                <PanelRightClose size={16} />
              </button>
            </div>

            {/* Node Info */}
            <div className="arch-insp-node-info">
              <div className="arch-insp-icon"><Layers size={18} /></div>
              <div className="arch-insp-node-text">
                <h3 className="arch-insp-node-title">{current?.title}</h3>
                <span className="arch-insp-node-type">{current?.type} module</span>
              </div>
            </div>

            {/* Config */}
            <div className="arch-insp-body">
              <div className="arch-insp-section">
                <span className="arch-insp-section-title">Configuration</span>
                {current?.metadata?.map((p, i) => (
                  <div key={i} className="arch-insp-field">
                    <label className="arch-insp-field-label">{p.label}</label>
                    <input readOnly value={p.value} className="arch-insp-field-input" />
                  </div>
                ))}
              </div>

              <div className="arch-insp-section">
                <span className="arch-insp-section-title">Calculus Basis</span>
                <div className="arch-insp-formula-box">
                  <div className="arch-insp-formula">
                    {current?.type === 'Dense' ? 'W^T x + b' : current?.type === 'Convolutional' ? 'f * g' : 'L = Σ(wᵢ · xᵢ)'}
                  </div>
                  <span className="arch-insp-formula-sub">Homomorphic Verification</span>
                </div>
              </div>
            </div>

            {/* Compile Button */}
            <div className="arch-insp-footer">
              <button onClick={compileModel} disabled={isCompiling} className="arch-compile-btn">
                {isCompiling ? (
                  <><div className="arch-spinner" /> Compiling...</>
                ) : (
                  <><Zap size={14} /> Compile Architecture</>
                )}
              </button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      <style>{`
        /* ═══════════════════════════════════════════
           ARCHITECTURE BUILDER — SCOPED STYLES
        ═══════════════════════════════════════════ */
        .arch-root {
          display: flex;
          height: 100%;
          overflow: hidden;
          background: var(--bg-main);
          font-family: var(--font-sans);
          position: relative;
        }

        /* ─── Left Library ─── */
        .arch-library {
          width: 240px;
          flex-shrink: 0;
          display: flex;
          flex-direction: column;
          background: var(--bg-surface);
          border-right: 1px solid var(--border);
          z-index: 10;
        }
        .arch-lib-header {
          padding: 16px 20px;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.15em;
          color: var(--primary);
          border-bottom: 1px solid var(--border);
        }
        .arch-lib-search-wrap {
          padding: 12px 16px;
          border-bottom: 1px solid var(--border);
          position: relative;
        }
        .arch-lib-search {
          width: 100%;
          height: 32px;
          padding: 0 32px 0 10px;
          font-size: 10px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          border: 1px solid var(--border);
          background: var(--bg-main);
          color: var(--text-main);
          outline: none;
          font-family: var(--font-sans);
          transition: border-color 0.15s;
        }
        .arch-lib-search:focus { border-color: var(--primary); }
        .arch-lib-search-icon {
          position: absolute;
          right: 26px;
          top: 50%;
          transform: translateY(-50%);
          color: var(--text-muted);
          opacity: 0.4;
        }
        .arch-lib-scroll {
          flex: 1;
          overflow-y: auto;
          padding: 12px 16px 60px;
        }
        .arch-lib-scroll::-webkit-scrollbar { width: 3px; }
        .arch-lib-scroll::-webkit-scrollbar-thumb { background: var(--border); }
        .arch-lib-section {
          margin-bottom: 20px;
        }
        .arch-lib-section-title {
          display: block;
          font-size: 9px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.15em;
          color: var(--text-muted);
          margin-bottom: 8px;
          padding-left: 2px;
        }
        .arch-preset-btn {
          display: flex;
          flex-direction: column;
          width: 100%;
          padding: 10px 12px;
          margin-bottom: 4px;
          background: var(--bg-main);
          border: 1px solid var(--border);
          cursor: pointer;
          transition: all 0.15s;
          text-align: left;
          font-family: var(--font-sans);
        }
        .arch-preset-btn:hover {
          border-color: var(--primary);
          background: var(--bg-surface);
        }
        .arch-preset-name {
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          color: var(--text-main);
          letter-spacing: 0.05em;
        }
        .arch-preset-info {
          font-size: 8px;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.08em;
          margin-top: 2px;
        }
        .arch-component-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          width: 100%;
          padding: 8px 10px;
          margin-bottom: 3px;
          background: var(--bg-surface);
          border: 1px solid var(--border);
          font-size: 9px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--text-muted);
          cursor: pointer;
          transition: all 0.15s;
          font-family: var(--font-sans);
        }
        .arch-component-btn:hover {
          border-color: var(--primary);
          color: var(--primary);
          background: var(--bg-main);
        }
        .arch-component-btn:active { transform: scale(0.97); }

        /* ─── Canvas ─── */
        .arch-canvas-area {
          flex: 1;
          position: relative;
          overflow: hidden;
          background-image: var(--bg-grid-pattern);
          background-size: var(--bg-grid-size);
          cursor: crosshair;
        }
        .arch-canvas-badges {
          position: absolute;
          top: 12px; left: 12px; right: 12px;
          display: flex;
          align-items: center;
          gap: 8px;
          z-index: 30;
          pointer-events: none;
        }
        .arch-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 14px;
          background: var(--bg-surface);
          border: 1px solid var(--border);
          box-shadow: 0 2px 8px rgba(0,0,0,0.06);
          font-size: 9px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--text-main);
          pointer-events: auto;
        }
        .arch-badge-dot {
          width: 6px; height: 6px;
          border-radius: 50%;
          background: var(--success);
          animation: arch-pulse 2s infinite;
        }
        @keyframes arch-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .arch-badge-connecting {
          background: var(--primary);
          color: #fff;
          border-color: var(--primary);
          animation: arch-pulse 1s infinite;
        }
        .arch-canvas-scroll {
          width: 100%; height: 100%;
          overflow: auto;
        }
        .arch-canvas-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
        .arch-canvas-scroll::-webkit-scrollbar-thumb { background: var(--border); }
        .arch-canvas-inner {
          position: relative;
          min-width: 2000px; min-height: 2000px;
        }
        .arch-svg-layer {
          position: absolute;
          inset: 0;
          width: 100%; height: 100%;
          pointer-events: none;
          overflow: visible;
          z-index: 0;
        }

        /* ─── Zoom ─── */
        .arch-zoom-controls {
          position: absolute;
          bottom: 14px; left: 14px;
          display: flex;
          align-items: center;
          background: var(--bg-surface);
          border: 1px solid var(--border);
          box-shadow: 0 4px 16px rgba(0,0,0,0.08);
          z-index: 50;
        }
        .arch-zoom-btn {
          width: 36px; height: 36px;
          display: flex; align-items: center; justify-content: center;
          background: none; border: none;
          color: var(--text-muted);
          cursor: pointer;
          transition: all 0.15s;
          font-family: var(--font-sans);
        }
        .arch-zoom-btn:hover { background: var(--bg-main); color: var(--text-main); }
        .arch-zoom-label {
          width: 48px;
          text-align: center;
          font-size: 10px;
          font-weight: 700;
          font-family: var(--font-mono);
          color: var(--text-main);
          border-left: 1px solid var(--border);
          border-right: 1px solid var(--border);
          height: 36px;
          line-height: 36px;
        }

        /* ─── Nodes ─── */
        .arch-node-wrap { cursor: grab; user-select: none; }
        .arch-node-wrap:active { cursor: grabbing; }
        .arch-node {
          width: 190px;
          border: 1.5px solid var(--border);
          background: var(--bg-surface);
          transition: all 0.15s;
          box-shadow: 0 1px 4px rgba(0,0,0,0.04);
          position: relative;
        }
        .arch-node:hover { border-color: var(--text-muted); }
        .arch-node-selected {
          border-color: var(--primary) !important;
          box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 8%, transparent), 0 4px 12px rgba(0,0,0,0.08);
        }
        .arch-node-header {
          padding: 4px 8px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid var(--border);
          background: var(--bg-main);
        }
        .arch-node-header-active {
          background: color-mix(in srgb, var(--primary) 6%, transparent);
          border-color: color-mix(in srgb, var(--primary) 15%, transparent);
        }
        .arch-node-type {
          font-size: 8px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.12em;
          color: var(--text-muted);
        }
        .arch-node-delete {
          background: none; border: none; cursor: pointer;
          color: var(--text-muted);
          padding: 2px;
          transition: color 0.15s;
        }
        .arch-node-delete:hover { color: var(--error); }
        .arch-node-body { padding: 10px 12px; }
        .arch-node-name {
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.02em;
          color: var(--text-main);
          line-height: 1.2;
          margin: 0;
        }
        .arch-node-meta { margin-top: 8px; }
        .arch-meta-row {
          display: flex;
          justify-content: space-between;
          font-size: 8px;
          font-family: var(--font-mono);
          line-height: 1.8;
        }
        .arch-meta-label { color: var(--text-muted); text-transform: uppercase; }
        .arch-meta-value { font-weight: 700; color: var(--text-muted); }
        .arch-meta-value-active { color: var(--primary); }
        .arch-node-dot {
          position: absolute;
          top: -4px; right: -4px;
          width: 8px; height: 8px;
          background: var(--primary);
          border-radius: 50%;
          border: 2px solid var(--bg-surface);
        }
        .arch-port {
          width: 12px; height: 12px;
          border: 2px solid var(--border);
          border-radius: 50%;
          background: var(--bg-surface);
          cursor: pointer;
          transition: all 0.15s;
          margin: 2px 0;
          display: block;
          padding: 0;
        }
        .arch-port:hover { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 10%, transparent); }
        .arch-port-active { border-color: var(--primary); background: var(--primary); transform: scale(1.3); }

        /* ─── Edges ─── */
        .arch-edge-path {
          stroke: var(--primary);
          stroke-width: 1.5;
          stroke-opacity: 0.2;
          transition: stroke-opacity 0.15s;
        }
        .arch-edge-group:hover .arch-edge-path { stroke-opacity: 0.8; }
        .arch-edge-delete-wrap { opacity: 0; transition: opacity 0.15s; }
        .arch-edge-group:hover .arch-edge-delete-wrap { opacity: 1; }
        .arch-edge-delete {
          width: 18px; height: 18px;
          display: flex; align-items: center; justify-content: center;
          background: var(--bg-surface);
          border: 1px solid var(--border);
          border-radius: 50%;
          cursor: pointer;
          transition: all 0.15s;
          color: var(--text-muted);
        }
        .arch-edge-delete:hover { background: #fef2f2; border-color: var(--error); color: var(--error); }

        /* ─── Inspector (Right Panel) ─── */
        .arch-inspector-toggle {
          position: absolute;
          top: 12px; right: 12px;
          width: 36px; height: 36px;
          display: flex; align-items: center; justify-content: center;
          background: var(--bg-surface);
          border: 1px solid var(--border);
          box-shadow: 0 2px 8px rgba(0,0,0,0.06);
          cursor: pointer; z-index: 40;
          color: var(--text-muted);
          transition: all 0.15s;
        }
        .arch-inspector-toggle:hover { color: var(--primary); border-color: var(--primary); }
        .arch-inspector {
          flex-shrink: 0;
          display: flex;
          flex-direction: column;
          background: var(--bg-surface);
          border-left: 1px solid var(--border);
          overflow: hidden;
          z-index: 40;
        }
        .arch-insp-header {
          padding: 14px 20px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-bottom: 1px solid var(--border);
        }
        .arch-insp-header-left {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.15em;
          color: var(--primary);
        }
        .arch-insp-close {
          background: none; border: none; cursor: pointer;
          color: var(--text-muted); padding: 4px;
          transition: color 0.15s;
        }
        .arch-insp-close:hover { color: var(--text-main); }
        .arch-insp-node-info {
          padding: 20px;
          display: flex;
          align-items: center;
          gap: 14px;
          border-bottom: 1px solid var(--border);
        }
        .arch-insp-icon {
          width: 40px; height: 40px;
          display: flex; align-items: center; justify-content: center;
          border: 1px solid var(--border);
          color: var(--primary);
          flex-shrink: 0;
        }
        .arch-insp-node-text { overflow: hidden; }
        .arch-insp-node-title {
          font-family: var(--font-serif);
          font-size: 16px;
          font-weight: 500;
          color: var(--text-main);
          margin: 0;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .arch-insp-node-type {
          font-size: 9px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.12em;
          color: var(--primary);
          opacity: 0.6;
        }
        .arch-insp-body {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
        }
        .arch-insp-body::-webkit-scrollbar { width: 3px; }
        .arch-insp-body::-webkit-scrollbar-thumb { background: var(--border); }
        .arch-insp-section { margin-bottom: 24px; }
        .arch-insp-section-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 9px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.15em;
          color: var(--text-muted);
          margin-bottom: 12px;
        }
        .arch-insp-section-title::after {
          content: '';
          flex: 1;
          height: 1px;
          background: var(--border);
        }
        .arch-insp-field { margin-bottom: 12px; }
        .arch-insp-field-label {
          display: block;
          font-size: 9px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.12em;
          color: var(--text-muted);
          margin-bottom: 6px;
        }
        .arch-insp-field-input {
          width: 100%;
          padding: 8px 12px;
          font-size: 12px;
          font-weight: 600;
          font-family: var(--font-mono);
          border: 1px solid var(--border);
          background: var(--bg-main);
          color: var(--text-main);
          outline: none;
          border-left: 3px solid color-mix(in srgb, var(--primary) 25%, transparent);
        }
        .arch-insp-field-input:focus {
          border-left-color: var(--primary);
        }
        .arch-insp-formula-box {
          background: #0f172a;
          padding: 24px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 100px;
        }
        .arch-insp-formula {
          font-size: 16px;
          font-weight: 700;
          font-family: var(--font-mono);
          color: var(--primary);
          letter-spacing: 0.05em;
        }
        .arch-insp-formula-sub {
          font-size: 8px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.12em;
          color: rgba(255,255,255,0.25);
          margin-top: 12px;
        }

        /* ─── Footer ─── */
        .arch-insp-footer {
          padding: 16px 20px;
          border-top: 1px solid var(--border);
          flex-shrink: 0;
        }
        .arch-compile-btn {
          width: 100%;
          height: 42px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          background: var(--primary);
          color: #fff;
          border: none;
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.15em;
          cursor: pointer;
          transition: all 0.15s;
          font-family: var(--font-sans);
        }
        .arch-compile-btn:hover:not(:disabled) { opacity: 0.9; }
        .arch-compile-btn:active:not(:disabled) { transform: scale(0.97); }
        .arch-compile-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .arch-spinner {
          width: 14px; height: 14px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: #fff;
          border-radius: 50%;
          animation: arch-spin 0.6s linear infinite;
        }
        @keyframes arch-spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};
