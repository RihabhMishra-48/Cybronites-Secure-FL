import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, Eye, EyeOff, Lock, Mail, ChevronRight } from 'lucide-react';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(email, password);
            navigate('/');
        } catch (err) {
            setError(err.response?.data?.detail || 'Authentication failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#131315] flex flex-col items-center justify-center p-4 font-['Inter'] text-[#e5e1e4] selection:bg-[#00f2ff] selection:text-[#131315]">
            {/* Background Grid Effect */}
            <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none opacity-20">
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px]"></div>
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,#00f2ff05_0%,transparent_70%)]"></div>
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md z-10"
            >
                {/* Header */}
                <div className="mb-12 text-center">
                    <div className="inline-flex items-center gap-2 mb-6">
                        <Shield className="w-8 h-8 text-[#00f2ff]" />
                        <span className="font-['Space_Grotesk'] text-2xl font-bold tracking-tighter">MONOLITH_OS</span>
                    </div>
                    <h1 className="font-['Space_Grotesk'] text-4xl font-bold tracking-tight text-white mb-2 uppercase">AUTHENTICATION_REQUIRED</h1>
                    <p className="text-[#b9cacb] text-sm">Enter your secure credentials to access the node network.</p>
                </div>

                {/* Form Card */}
                <div className="bg-[#1c1b1d]/40 backdrop-blur-xl border border-[#3a494b]/20 p-8 shadow-2xl relative overflow-hidden">
                    {/* Top Accent Bar */}
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
                            <label className="block text-[#b9cacb] text-[10px] uppercase tracking-widest font-bold mb-2">SECURITY_IDENTIFIER (EMAIL)</label>
                            <div className="relative group">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#849495] group-focus-within:text-[#00f2ff] transition-colors" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full bg-[#131315]/50 border-b-2 border-[#3a494b] focus:border-[#00f2ff] p-3 pl-10 outline-none transition-all font-mono text-sm"
                                    placeholder="node@guardian.sys"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <label className="text-[#b9cacb] text-[10px] uppercase tracking-widest font-bold">ACCESS_KEY (PASSWORD)</label>
                                <Link to="/forgot-password" size="sm" className="text-[#00f2ff] text-[10px] hover:underline uppercase tracking-wider">RETRIEVE_KEY</Link>
                            </div>
                            <div className="relative group">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#849495] group-focus-within:text-[#00f2ff] transition-colors" />
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-[#131315]/50 border-b-2 border-[#3a494b] focus:border-[#00f2ff] p-3 pl-10 pr-10 outline-none transition-all font-mono text-sm"
                                    placeholder="••••••••"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#849495] hover:text-white"
                                >
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-[#00f2ff] text-[#131315] font-['Space_Grotesk'] font-bold py-4 hover:shadow-[0_0_20px_rgba(0,242,255,0.4)] active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-50 group"
                        >
                            {loading ? "INITIALIZING_ACCESS..." : "ACCESS_SYSTEM"}
                            {!loading && <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />}
                        </button>
                    </form>

                    <div className="mt-8 pt-6 border-t border-[#3a494b]/20 text-center">
                        <p className="text-sm text-[#849495]">New terminal detected?</p>
                        <Link to="/signup" className="text-[#00f2ff] text-sm font-bold hover:underline mt-1 inline-block">INITIALIZE_NEW_IDENTITY</Link>
                    </div>
                </div>

                {/* Footer Status */}
                <div className="mt-12 flex justify-center items-center gap-4 text-[#849495] text-[10px] uppercase tracking-[0.2em] font-mono">
                    <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 bg-[#00f2ff] rounded-full animate-pulse"></div>
                        E2E_ENCRYPTION_ACTIVE
                    </div>
                    <div className="w-1 h-3 border-l border-[#3a494b]"></div>
                    NODE_REGION: GLOBAL_01
                </div>
            </motion.div>
        </div>
    );
};

export default Login;
