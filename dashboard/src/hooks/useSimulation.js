import { useState, useEffect, useCallback } from 'react';

const DEFAULT_CONFIG = {
  clients: 8,
  rounds: 6,
  maliciousRatio: 0.25,
  repInitial: 100,
  repThreshold: 30,
  repReward: 10,
  repPenalty: 25
};

export function useSimulation() {
  const [round, setRound] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const [blockchain, setBlockchain] = useState([
    { index: 0, hash: '0x0000_GENESIS', transactions: [] }
  ]);
  const [clients, setClients] = useState([]);
  const [accuracyHistory, setAccuracyHistory] = useState([0.12]);
  const [rejectedCount, setRejectedCount] = useState(0);
  const [logs, setLogs] = useState([]);

  const addLog = useCallback((msg, color = 'gray') => {
    setLogs(prev => [...prev.slice(-99), { msg: `> ${msg}`, color }]);
  }, []);

  const initClients = useCallback(() => {
    const types = ['Hospital', 'FinTech', 'AutoDrive', 'Retail', 'Logistics', 'HealthAI', 'EdTech', 'GovNet'];
    const numMal = Math.floor(DEFAULT_CONFIG.clients * DEFAULT_CONFIG.maliciousRatio);
    const newClients = Array.from({ length: DEFAULT_CONFIG.clients }, (_, i) => ({
      id: `P-${i.toString().padStart(2, '0')}`,
      org: types[i % types.length],
      isMalicious: i < numMal,
      reputation: DEFAULT_CONFIG.repInitial,
      status: 'ACTIVE',
      validCount: 0
    }));
    setClients(newClients);
    addLog('[INIT] Secure Federated Learning Engine v3.0 (Enterprise)', '#4f46e5');
    addLog('[AUTH] Federated identity synchronization complete.', '#64748b');
  }, [addLog]);

  useEffect(() => {
    const saved = localStorage.getItem('bcfl_state_corp');
    if (saved) {
      const parsed = JSON.parse(saved);
      setRound(parsed.round);
      setBlockchain(parsed.blockchain);
      setClients(parsed.clients);
      setAccuracyHistory(parsed.accuracyHistory);
      setRejectedCount(parsed.rejectedCount);
    } else {
      initClients();
    }
  }, [initClients]);

  useEffect(() => {
    if (clients.length > 0) {
      localStorage.setItem('bcfl_state_corp', JSON.stringify({
        round, blockchain, clients, accuracyHistory, rejectedCount
      }));
    }
  }, [round, blockchain, clients, accuracyHistory, rejectedCount]);

  const runRound = useCallback(async () => {
    setRound(prev => {
      const nextRound = prev + 1;
      addLog(`[CYCLE ${nextRound}] Global aggregation sequence initiated.`, '#4f46e5');
      
      let acceptedThisRound = 0;
      const txs = [];

      setClients(currentClients => {
        return currentClients.map(c => {
          if (c.status === 'BLOCKED') return c;
          
          let newRep = c.reputation;
          let newStatus = c.status;
          let newValidCount = c.validCount;

          if (c.isMalicious) {
            newRep = Math.max(0, c.reputation - DEFAULT_CONFIG.repPenalty);
            setRejectedCount(rc => rc + 1);
            addLog(`  [-] ${c.id}: Integrity check failed. Local update discarded.`, '#ef4444');
            txs.push({ peer: c.id, status: 'RED', action: 'PENALTY' });
          } else {
            newRep = Math.min(100, c.reputation + DEFAULT_CONFIG.repReward);
            newValidCount++;
            acceptedThisRound++;
            addLog(`  [+] ${c.id}: Gradient verified. Merging parameters.`, '#10b981');
            txs.push({ peer: c.id, status: 'GREEN', action: 'REWARD' });
          }

          if (newRep < DEFAULT_CONFIG.repThreshold) {
            newStatus = 'BLOCKED';
            addLog(`  [!] NODE ${c.id} DECOMMISSIONED. Trust threshold violation.`, '#ef4444');
          }

          return { ...c, reputation: newRep, status: newStatus, validCount: newValidCount };
        });
      });

      const hash = '0x' + Math.random().toString(16).substr(2, 12).toUpperCase();
      setBlockchain(prevChain => [...prevChain, { index: nextRound, hash, transactions: txs }]);

      setAccuracyHistory(prevAccHistory => {
        const prevAcc = prevAccHistory[prevAccHistory.length - 1];
        const boost = acceptedThisRound > 2 ? (0.05 + Math.random() * 0.08) : -0.02;
        return [...prevAccHistory, Math.min(0.99, Math.max(0.1, prevAcc + boost))];
      });

      return nextRound;
    });
  }, [addLog]);

  const clearSimulation = useCallback(() => {
    localStorage.removeItem('bcfl_state_corp');
    window.location.reload();
  }, []);

  return {
    round,
    isActive,
    blockchain,
    clients,
    accuracyHistory,
    rejectedCount,
    logs,
    runRound,
    clearSimulation,
    setIsActive
  };
}
