import { useState, useEffect, useRef, useCallback } from 'react';

export const useWebSocket = (url) => {
    const [stats, setStats] = useState({ round: 0, total_blocks: 1, clients_active: 0, trust_score: 100, status: 'IDLE' });
    const [chain, setChain] = useState([]);
    const [logs, setLogs] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    
    const ws = useRef(null);

    const onMessage = useCallback((event) => {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
            case 'initial_state':
            case 'global_update':
                setStats(message.stats);
                setChain(message.chain);
                break;
            case 'status_update':
                setStats(prev => ({ ...prev, status: message.status }));
                break;
            case 'round_started':
                setStats(prev => ({ ...prev, round: message.round, status: message.status }));
                break;
            case 'log':
                setLogs(prev => [...prev, message.data]);
                break;
            case 'error':
                console.error("Server error:", message.message);
                break;
            default:
                break;
        }
    }, []);

    useEffect(() => {
        const connect = () => {
            ws.current = new WebSocket(url);

            ws.current.onopen = () => {
                setIsConnected(true);
                console.log("WebSocket Connected");
            };

            ws.current.onmessage = onMessage;

            ws.current.onclose = () => {
                setIsConnected(false);
                console.log("WebSocket Disconnected. Retrying in 3s...");
                setTimeout(connect, 3000);
            };

            ws.current.onerror = (err) => {
                console.error("WebSocket Error:", err);
                ws.current.close();
            };
        };

        connect();

        return () => {
            if (ws.current) ws.current.close();
        };
    }, [url, onMessage]);

    return { stats, chain, logs, isConnected };
};
