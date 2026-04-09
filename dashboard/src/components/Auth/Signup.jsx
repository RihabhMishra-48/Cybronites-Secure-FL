import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, User, Lock, Mail, ChevronRight, CheckCircle } from 'lucide-react';

const Signup = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await register(email, username, password);
            setSuccess(true);
        } catch (err) {
            setError(err.response?.data?.detail || 'Identity creation failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="min-h-screen bg-[#131315] flex flex-col items-center justify-center p-4 font-['Inter'] text-[#e5e1e4]">
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="w-full max-w-md bg-[#1c1b1d]/40 backdrop-blur-xl border border-[#00f2ff]/30 p-12 text-center shadow-2xl relative"
                >
                    <div className="absolute top-0 left-0 right-0 h-[2px] bg-[#00f2ff]"></div>
                    <CheckCircle className="w-16 h-16 text-[#00f2ff] mx-auto mb-6" />
                    <h2 className="font-['Space_Grotesk'] text-3xl font-bold text-white mb-4 uppercase">IDENTITY_INITIALIZED</h2>
                    <p className="text-[#b9cacb] mb-8 text-sm">
                        A verification packet has been dispatched to <span className="text-white font-mono">{email}</span>.
                        Please confirm your identity to activate your node status.
                    </p>
                    <Link
                        to="/login"
                        className="inline-flex items-center gap-2 bg-[#00f2ff] text-[#131315] font-['Space_Grotesk'] font-bold px-8 py-3 hover:shadow-[0_0_15px_rgba(0,242,255,0.4)] transition-all"
                    >
                        RETURN_TO_LOGIN
                    </Link>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#131315] flex flex-col items-center justify-center p-4 font-['Inter'] text-[#e5e1e4] selection:bg-[#00f2ff] selection:text-[#131315]">
            <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none opacity-20">
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]"></div>
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md z-10"
            >
                <div className="mb-10 text-center">
                    <div className="inline-flex items-center gap-2 mb-4 text-[#00f2ff]">
                        <Shield className="w-8 h-8" />
                        <span className="font-['Space_Grotesk'] text-xl font-bold tracking-tighter">SECURE_ONBOARDING</span>
                    </div>
                    <h1 className="font-['Space_Grotesk'] text-4xl font-bold tracking-tight text-white mb-2 uppercase">CREATE_IDENTITY</h1>
                    <p className="text-[#b9cacb] text-sm italic">Synchronizing new node with the neural network...</p>
                </div>

                <div className="bg-[#1c1b1d]/40 backdrop-blur-xl border border-[#3a494b]/20 p-8 shadow-2xl relative">
                    <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-right from-[#00f2ff] to-[#bc13fe]"></div>

                    {error && (
                        <motion.div
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="bg-red-500/10 border-l-2 border-red-500 p-4 mb-6 text-red-400 text-xs font-mono"
                        >
                            [ERROR]: {error}
                        </motion.div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-[#b9cacb] text-[10px] uppercase tracking-widest font-bold mb-2">IDENTIFIER_NAME (USERNAME)</label>
                            <div className="relative group">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#849495] group-focus-within:text-[#00f2ff] transition-colors" />
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full bg-[#131315]/50 border-b-2 border-[#3a494b] focus:border-[#00f2ff] p-3 pl-10 outline-none transition-all font-mono text-sm"
                                    placeholder="node_alfa_01"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-[#b9cacb] text-[10px] uppercase tracking-widest font-bold mb-2">COMM_CHANNEL (EMAIL)</label>
                            <div className="relative group">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#849495] group-focus-within:text-[#00f2ff] transition-colors" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full bg-[#131315]/50 border-b-2 border-[#3a494b] focus:border-[#00f2ff] p-3 pl-10 outline-none transition-all font-mono text-sm"
                                    placeholder="verified@guardian.sys"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-[#b9cacb] text-[10px] uppercase tracking-widest font-bold mb-2">ACCESS_KEY (PASSWORD)</label>
                            <div className="relative group">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#849495] group-focus-within:text-[#00f2ff] transition-colors" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-[#131315]/50 border-b-2 border-[#3a494b] focus:border-[#00f2ff] p-3 pl-10 outline-none transition-all font-mono text-sm"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        <div className="text-[10px] text-[#849495] p-3 bg-[#131315]/50 border border-[#3a494b]/30">
                            [SECURITY_NOTICE]: Identity creation triggers an automated email verification packet. Please ensure your communication channel is active.
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-white text-[#131315] font-['Space_Grotesk'] font-bold py-4 hover:bg-[#00f2ff] hover:shadow-[0_0_20px_rgba(0,242,255,0.4)] active:scale-[0.98] transition-all flex items-center justify-center gap-2 group"
                        >
                            {loading ? "PROCESSING_IDENTITY..." : "INITIALIZE_ID"}
                            {!loading && <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />}
                        </button>
                    </form>

                    <div className="mt-8 pt-6 border-t border-[#3a494b]/20 text-center">
                        <p className="text-sm text-[#849495]">Existing node detected?</p>
                        <Link to="/login" className="text-[#00f2ff] text-sm font-bold hover:underline mt-1 inline-block">AUTHENTICATE_IDENTITY</Link>
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

export default Signup;
