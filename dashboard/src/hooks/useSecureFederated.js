import { useState, useEffect, useRef, useCallback } from 'react';

const isProd = import.meta.env.PROD;
export const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT || '7861';
export const BACKEND_IP = import.meta.env.VITE_BACKEND_IP || '127.0.0.1';
export const API_BASE_URL = isProd ? window.location.origin : `http://${BACKEND_IP}:${BACKEND_PORT}`;
export const WS_URL = isProd 
  ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws` 
  : `ws://${BACKEND_IP}:${BACKEND_PORT}/ws`;

export function useSecureFederated() {
  const [round, setRound] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const [clientsActive, setClientsActive] = useState(0); 
  const [blockchain, setBlockchain] = useState([
    { index: 0, hash: '0x0000_GENESIS', transactions: [] }
  ]);
  const [clients, setClients] = useState([]);
  const [accuracyHistory, setAccuracyHistory] = useState([]);
  const [lossHistory, setLossHistory] = useState([]);
  const [rejectedCount, setRejectedCount] = useState(0);
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState('IDLE');
  const [lastSync, setLastSync] = useState(null);
  const [nodeRegistry, setNodeRegistry] = useState({});
  const [hyperparams, setHyperparams] = useState({
    learning_rate: 0.01,
    batch_size: 32,
    epochs: 1
  });
  const [roundHistory, setRoundHistory] = useState([]);
  const [shards, setShards] = useState([]); // NEW STATE
  const [modelArchitecture, setModelArchitecture] = useState('# Loading Model source...'); 
  const [labState, setLabState] = useState({ status: 'IDLE', progress: 0, epoch: 0, loss: 0, accuracy: 0, ptPath: null, onnxPath: null });

  const ws = useRef(null);

  const updateClientStatus = useCallback((currentStatus, numActive = 2) => {
    setClients(Array.from({ length: 8 }, (_, i) => ({
      id: `NODE-${i}`,
      org: ['Hospital', 'FinTech', 'AutoDrive', 'Retail', 'Logistics', 'HealthAI', 'EdTech', 'GovNet'][i % 8],
      status: i < numActive ? (['TRAINING', 'AGGREGATING'].includes(currentStatus) ? 'BUSY' : 'ACTIVE') : 'IDLE',
      reputation: 100
    })));
    setClientsActive(numActive);
  }, []);

  const onMessage = useCallback((event) => {
    try {
        const message = JSON.parse(event.data);
        const { type, payload } = message;
        setLastSync(new Date());

        switch (type) {
          case 'INITIAL_SYNC': {
            console.log("INITIAL_SYNC", payload);
            const { state, logs: initialLogs } = payload;
            setRound(state.round || 0);
            setStatus(state.status || 'IDLE');
            setAccuracyHistory(state.accuracy_history || []);
            setLossHistory(state.loss_history || []);
            setLogs(initialLogs.map(l => ({ msg: `${l}`, color: '#64748b' })));
            if (state.chain) setBlockchain(state.chain);
            if (state.node_registry) setNodeRegistry(state.node_registry);
            if (state.hyperparams) setHyperparams(state.hyperparams);
            if (state.round_history) setRoundHistory(state.round_history);
            if (state.shards) setShards(state.shards);
            if (state.model_architecture) setModelArchitecture(state.model_architecture);
            updateClientStatus(state.status, state.clients_active);
            break;
          }

          case 'STAT_UPDATE': {
            console.log("STAT_UPDATE", payload);
            if (payload.round !== undefined) setRound(payload.round);
            if (payload.status !== undefined) {
                setStatus(payload.status);
                setIsActive(['TRAINING', 'AGGREGATING', 'MINING'].includes(payload.status));
                updateClientStatus(payload.status, payload.clients_active);
            }
            if (payload.accuracy_history !== undefined) setAccuracyHistory(payload.accuracy_history);
            if (payload.loss_history !== undefined) setLossHistory(payload.loss_history);
            if (payload.chain !== undefined) setBlockchain(payload.chain);
            if (payload.node_registry !== undefined) setNodeRegistry(payload.node_registry);
            if (payload.hyperparams) setHyperparams(payload.hyperparams);
            if (payload.round_history) setRoundHistory(payload.round_history);
            if (payload.shards) setShards(payload.shards);
            if (payload.model_architecture) setModelArchitecture(payload.model_architecture);
            break;
          }

          case 'LOG': {
            const isError = payload.includes('ERROR') || payload.includes('CRITICAL');
            setLogs(prev => [...prev.slice(-199), { msg: `${payload}`, color: isError ? '#ef4444' : '#64748b' }]);
            break;
          }

          case 'LAB_PROGRESS': {
            setLabState(prev => ({ 
              ...prev, 
              status: 'TRAINING',
              progress: payload.progress,
              epoch: payload.epoch,
              loss: payload.loss,
              accuracy: payload.accuracy
            }));
            break;
          }

          case 'LAB_COMPLETE': {
            setLabState(prev => ({ 
              ...prev, 
              status: 'COMPLETE',
              progress: 100,
              ptPath: payload.pt_path,
              onnxPath: payload.onnx_path
            }));
            break;
          }

          case 'LAB_ERROR': {
            setLabState(prev => ({ ...prev, status: 'ERROR', error: payload.error }));
            break;
          }

          default:
            break;
        }
    } catch (err) {
        console.error("Hook Message Error:", err);
    }
  }, [updateClientStatus]);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  useEffect(() => {
    let isMounted = true;
    let reconnectTimeout = null;

    const connect = () => {
      if (ws.current) {
        ws.current.onclose = null;
        ws.current.close();
      }

      console.log("Connecting to Secure Bridge:", WS_URL);
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => {
        setIsConnected(true);
        console.log("Bridge Connected");
      };

      ws.current.onmessage = onMessage;

      ws.current.onclose = () => {
        setIsConnected(false);
        if (isMounted) reconnectTimeout = setTimeout(connect, 3000);
      };

      ws.current.onerror = (err) => console.error("WS Error:", err);
    };

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws.current) {
        ws.current.onclose = null;
        ws.current.close();
      }
    };
  }, [onMessage]);

  const runRound = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/federated/start`, { method: 'POST' });
      if (!response.ok) throw new Error('Backend Offline');
      const data = await response.json();
      return data.success;
    } catch (err) {
      console.error("Round Execution Error:", err);
      return false;
    }
  };

  return {
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
  };
}
