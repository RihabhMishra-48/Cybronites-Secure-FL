import React, { useEffect, useState } from 'react';
import { 
  ShieldCheck, Lock, Cpu, Database, Play, 
  Download, Activity, CheckCircle2, AlertCircle, RefreshCcw,
  Zap, Fingerprint, LockKeyhole
} from 'lucide-react';
import { useSecureTraining } from '../hooks/useSecureTraining';
import { motion, AnimatePresence } from 'framer-motion';

export const PrivacyVault = () => {
    const { 
        datasets, jobs, models, loading, error, 
        fetchDatasets, fetchJobs, fetchModels, submitJob 
    } = useSecureTraining();

    const [selectedDataset, setSelectedDataset] = useState(null);
    const [isLaunching, setIsLaunching] = useState(false);

    useEffect(() => {
        fetchDatasets();
        fetchJobs();
        fetchModels();
    }, [fetchDatasets, fetchJobs, fetchModels]);

    const handleLaunch = async () => {
        if (!selectedDataset) return;
        setIsLaunching(true);
        try {
            await submitJob(selectedDataset.id, "SimpleCNN", {
                epochs: 5,
                batch_size: 32,
                learning_rate: 0.001
            });
            setSelectedDataset(null);
        } catch (err) {
            console.error(err);
        } finally {
            setIsLaunching(false);
        }
    };

    return (
        <div className="vault-container p-10 space-y-12 section-fade bg-white min-h-full">
            {/* Header: Vault Intelligence */}
            <div className="flex items-end justify-between pb-8 border-b border-border">
                <div className="space-y-4">
                    <div className="flex items-center gap-3">
                        <LockKeyhole size={20} className="text-primary opacity-80" />
                        <h2 className="type-l2 serif text-text-main font-medium tracking-tight">Institutional Privacy Vault</h2>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <span className="text-[9px] font-medium text-text-muted/40 uppercase tracking-[0.2em]">VAULT_STATUS:</span>
                            <span className="text-[9px] font-bold text-emerald-600 uppercase tracking-widest flex items-center gap-1">
                                <span className="w-1 h-1 bg-emerald-500 rounded-full animate-pulse" /> Encrypted & Synchronized
                            </span>
                        </div>
                        <div className="w-[1px] h-2 bg-border/60" />
                        <div className="flex items-center gap-2">
                            <span className="text-[9px] font-medium text-text-muted/40 uppercase tracking-[0.2em]">MASTER_KEY:</span>
                            <span className="text-[9px] font-bold text-text-main/80 uppercase tracking-widest font-mono">AES-256-GCM_STP_CORE</span>
                        </div>
                    </div>
                </div>

                <div className="flex gap-10">
                    <div className="text-right pr-6 border-r border-border h-10 flex flex-col justify-end">
                        <div className="text-[9px] font-bold text-text-muted mb-1.5 uppercase tracking-[0.3em] opacity-40">Processed Entropy</div>
                        <span className="text-xl serif text-text-main font-medium tabular-nums leading-none">
                            {(Array.isArray(datasets) ? datasets.reduce((acc, d) => acc + (d.dataset_size || 0), 0) : 0 / (1024 * 1024)).toFixed(1)} MB
                        </span>
                    </div>
                    <button 
                        onClick={() => { fetchDatasets(); fetchJobs(); fetchModels(); }}
                        className="h-10 px-4 border border-border text-text-muted hover:text-primary transition-all flex items-center justify-center gap-2"
                    >
                        <RefreshCcw size={12} className={loading ? 'animate-spin' : ''} />
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-10">
                {/* Left: Resource Grid & Launchpad */}
                <div className="xl:col-span-2 space-y-10">
                    <section className="space-y-6">
                        <div className="flex items-center gap-3">
                            <Fingerprint size={14} className="text-primary" />
                            <span className="text-[10px] font-bold text-text-main uppercase tracking-[0.2em]">Encrypted Dataset Pool</span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {Array.isArray(datasets) && datasets.map(ds => (
                                <motion.div 
                                    key={ds.id}
                                    whileHover={{ y: -4 }}
                                    className={`institutional-card group cursor-pointer transition-all ${selectedDataset?.id === ds.id ? 'ring-2 ring-primary ring-offset-2' : ''}`}
                                    onClick={() => setSelectedDataset(ds)}
                                >
                                    <div className="p-6 space-y-4">
                                        <div className="flex justify-between items-start">
                                            <div className="p-2 bg-primary/5 rounded border border-primary/10 text-primary">
                                                <Database size={16} />
                                            </div>
                                            <div className="flex items-center gap-1.5 px-2 py-0.5 bg-emerald-50 border border-emerald-100 rounded-full">
                                                <ShieldCheck size={10} className="text-emerald-600" />
                                                <span className="text-[8px] font-extrabold text-emerald-700 uppercase tracking-widest">Protected</span>
                                            </div>
                                        </div>
                                        <div>
                                            <h4 className="text-xs font-bold text-text-main uppercase tracking-widest mb-1">{ds.name}</h4>
                                            <p className="text-[10px] text-text-muted line-clamp-2 leading-relaxed opacity-70 italic">{ds.description}</p>
                                        </div>
                                        <div className="flex items-center gap-4 pt-4 border-t border-border/50">
                                            <div className="flex flex-col">
                                                <span className="text-[8px] text-text-muted/60 font-bold uppercase tracking-wider">Samples</span>
                                                <span className="text-[10px] font-bold tabular-nums">{(ds.num_samples / 1000).toFixed(1)}k</span>
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-[8px] text-text-muted/60 font-bold uppercase tracking-wider">Dim</span>
                                                <span className="text-[10px] font-bold tabular-nums">{ds.input_shape.join('×')}</span>
                                            </div>
                                            <div className="flex flex-col ml-auto text-right">
                                                <span className="text-[8px] text-text-muted/60 font-bold uppercase tracking-wider">ID_Hash</span>
                                                <span className="text-[9px] font-mono text-text-muted/40">{ds.id.slice(0, 8)}...</span>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </section>

                    {/* Active Jobs Monitor */}
                    <section className="space-y-6">
                        <div className="flex items-center gap-3">
                            <Activity size={14} className="text-primary" />
                            <span className="text-[10px] font-bold text-text-main uppercase tracking-[0.2em]">Autonomous Training Synapses</span>
                        </div>

                        <div className="institutional-card overflow-hidden">
                            <div className="p-8 space-y-6">
                                {(!Array.isArray(jobs) || jobs.length === 0) ? (
                                    <div className="flex flex-col items-center justify-center py-12 text-text-muted/40 border-2 border-dashed border-border/40 rounded-sm">
                                        <Zap size={24} className="mb-4 opacity-20" />
                                        <span className="text-[10px] font-bold uppercase tracking-[0.25em]">No Active Training Jobs</span>
                                    </div>
                                ) : (
                                    <div className="space-y-8">
                                        {jobs.map(job => (
                                            <div key={job.id} className="space-y-3">
                                                <div className="flex justify-between items-end">
                                                    <div className="flex items-center gap-4">
                                                        <div className={`w-8 h-8 rounded-full border border-border flex items-center justify-center ${job.status === 'RUNNING' ? 'animate-spin' : ''}`}>
                                                            {job.status === 'COMPLETED' ? <CheckCircle2 size={12} className="text-emerald-500" /> : <RefreshCcw size={12} className="text-primary" />}
                                                        </div>
                                                        <div>
                                                            <div className="text-[10px] font-bold uppercase tracking-widest text-text-main flex items-center gap-2">
                                                                Job_{job.id.slice(0, 6)} 
                                                                <span className="text-[8px] font-normal text-text-muted opacity-60">| {job.model_type}</span>
                                                            </div>
                                                            <div className="text-[8px] text-text-muted font-mono">{job.dataset_id}</div>
                                                        </div>
                                                    </div>
                                                    <div className="text-right">
                                                        <span className="text-[10px] font-bold text-primary tabular-nums tracking-widest">{(job.progress * 100).toFixed(1)}%</span>
                                                        <div className="text-[8px] text-text-muted uppercase tracking-[0.1em]">{job.status}</div>
                                                    </div>
                                                </div>
                                                <div className="h-1 bg-border/20 rounded-full overflow-hidden">
                                                    <motion.div 
                                                        className="h-full bg-primary"
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${job.progress * 100}%` }}
                                                        transition={{ duration: 0.5 }}
                                                    />
                                                </div>
                                                {job.status === 'COMPLETED' && (
                                                    <div className="flex gap-4 px-2 py-1 bg-emerald-50/50 border border-emerald-100/50 rounded-sm">
                                                        <span className="text-[9px] font-bold text-emerald-700 uppercase tracking-widest">Acc: {job.accuracy}%</span>
                                                        <span className="text-[9px] font-bold text-emerald-700 uppercase tracking-widest">Loss: {job.loss}</span>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </section>
                </div>

                {/* Right: Security Control & Model Archive */}
                <div className="space-y-10">
                    {/* Launch Controller */}
                    <div className="institutional-card bg-primary text-white border-none overflow-hidden hover:shadow-2xl transition-all">
                        <div className="p-8 space-y-6 relative overflow-hidden">
                            <div className="absolute -right-8 -top-8 p-12 bg-white/5 rounded-full blur-2xl" />
                            <div className="relative z-10 space-y-6">
                                <div className="flex items-center gap-3">
                                    <Zap size={18} className="text-white/40" />
                                    <h3 className="type-l2 serif">Secure Orchestrator</h3>
                                </div>
                                <p className="text-[10px] leading-relaxed opacity-60 uppercase tracking-tight font-sans italic">
                                    Execute in-memory training on encrypted assets. Data decrypted ONLY in RAM via AES-256-GCM hardware acceleration.
                                </p>
                                
                                <div className="space-y-2">
                                    <div className="flex justify-between text-[9px] font-bold text-white/40 uppercase tracking-widest mb-4">
                                        <span>Target Dataset</span>
                                        <span className="text-white/80">{selectedDataset ? selectedDataset.name : 'NONE_SELECTED'}</span>
                                    </div>
                                    <button 
                                        onClick={handleLaunch}
                                        disabled={!selectedDataset || isLaunching}
                                        className={`w-full py-4 bg-white text-primary text-[10px] font-bold uppercase tracking-[0.3em] flex items-center justify-center gap-3 active:scale-95 transition-all ${(!selectedDataset || isLaunching) ? 'opacity-40 grayscale cursor-not-allowed' : ''}`}
                                    >
                                        {isLaunching ? <RefreshCcw size={12} className="animate-spin" /> : <Play size={12} fill="currentColor" />}
                                        Launch Secure Job
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Model Registry (Archive) */}
                    <section className="space-y-6">
                        <div className="flex items-center gap-3">
                            <Download size={14} className="text-primary" />
                            <span className="text-[10px] font-bold text-text-main uppercase tracking-[0.2em]">Trained Weights Hub</span>
                        </div>

                        <div className="space-y-4">
                            {(!Array.isArray(models) || models.length === 0) ? (
                                <div className="p-8 border border-border border-dashed text-text-muted/40 text-[9px] font-bold uppercase tracking-widest text-center">
                                    Registry Empty
                                </div>
                            ) : (
                                models.map(model => (
                                    <div key={model.id} className="institutional-card group">
                                        <div className="p-5 flex items-center justify-between">
                                            <div className="space-y-1">
                                                <div className="text-[10px] font-bold text-text-main uppercase tracking-widest">Weights_v{model.id.slice(0, 4)}</div>
                                                <div className="text-[8px] text-text-muted font-bold uppercase opacity-60">Acc: {model.accuracy}% | {model.model_type}</div>
                                            </div>
                                            <a 
                                                href={`http://localhost:8100/api/v1/models/download/${model.id}`}
                                                className="p-3 border border-border text-text-muted hover:bg-primary/5 hover:text-primary transition-all rounded-sm"
                                                title="Download Weights (.pt)"
                                            >
                                                <Download size={14} />
                                            </a>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </section>

                    {/* Security Ledger Summary */}
                    <div className="institutional-card bg-bg-surface/30">
                        <div className="p-6 space-y-4">
                            <div className="flex items-center gap-2">
                                <ShieldCheck size={12} className="text-emerald-600" />
                                <span className="text-[10px] font-bold text-text-main uppercase tracking-tight">Security Audit Ledger</span>
                            </div>
                            <div className="space-y-2">
                                <div className="flex items-center justify-between text-[8px] font-bold text-text-muted uppercase tracking-widest border-b border-border/40 pb-2">
                                    <span>RAM Decryption Pulse</span>
                                    <span className="text-text-main">256-bit</span>
                                </div>
                                <div className="flex items-center justify-between text-[8px] font-bold text-text-muted uppercase tracking-widest border-b border-border/40 pb-2">
                                    <span>Memory Wipe Signal</span>
                                    <span className="text-emerald-600 flex items-center gap-1">
                                        <div className="w-1 h-1 bg-emerald-500 rounded-full" /> Verified
                                    </span>
                                </div>
                                <div className="p-3 bg-red-50/30 rounded-sm mt-4">
                                    <p className="text-[8px] text-red-900 leading-relaxed font-bold uppercase tracking-tight">
                                        <AlertCircle size={8} className="inline mr-1" />
                                        Warning: Decrypted data never touches persistent storage. Ensure worker stable entropy.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <style>{`
                .section-fade {
                    animation: section-entry 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                }
                @keyframes section-entry {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .institutional-card {
                    background: #fff;
                    border: 1px solid var(--border);
                    border-radius: 2px;
                    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                }
                .institutional-card:hover {
                    border-color: var(--primary);
                    box-shadow: 0 10px 30px -5px rgba(0,0,0,0.05);
                }
            `}</style>
        </div>
    );
};
