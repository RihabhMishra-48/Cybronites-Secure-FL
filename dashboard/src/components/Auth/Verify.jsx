import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Shield, CheckCircle, XCircle, Loader2 } from 'lucide-react';

const Verify = () => {
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token');
    const [status, setStatus] = useState('verifying'); // verifying, success, error
    const [message, setMessage] = useState('');

    useEffect(() => {
        const verify = async () => {
            if (!token) {
                setStatus('error');
                setMessage('Verification token is missing.');
                return;
            }

            try {
                const response = await axios.get(`http://localhost:7861/api/auth/verify?token=${token}`);
                setStatus('success');
                setMessage(response.data.message);
            } catch (err) {
                setStatus('error');
                setMessage(err.response?.data?.detail || 'Verification failed. The token may be expired or invalid.');
            }
        };

        verify();
    }, [token]);

    return (
        <div className="min-h-screen bg-[#131315] flex flex-col items-center justify-center p-4 font-['Inter'] text-[#e5e1e4]">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-md bg-[#1c1b1d]/40 backdrop-blur-xl border border-[#3a494b]/20 p-12 text-center shadow-2xl relative overflow-hidden"
            >
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-right from-[#00f2ff] to-[#bc13fe]"></div>

                {status === 'verifying' && (
                    <>
                        <Loader2 className="w-16 h-16 text-[#00f2ff] mx-auto mb-6 animate-spin" />
                        <h2 className="font-['Space_Grotesk'] text-2xl font-bold text-white mb-4 uppercase tracking-tighter">VERIFYING_IDENTITY...</h2>
                        <p className="text-[#849495] text-sm">Synchronizing your node with the central authority.</p>
                    </>
                )}

                {status === 'success' && (
                    <>
                        <CheckCircle className="w-16 h-16 text-[#00f2ff] mx-auto mb-6" />
                        <h2 className="font-['Space_Grotesk'] text-3xl font-bold text-white mb-4 uppercase tracking-tighter">IDENTITY_VERIFIED</h2>
                        <p className="text-[#b9cacb] mb-8 text-sm">{message}</p>
                        <Link
                            to="/login"
                            className="inline-flex items-center gap-2 bg-[#00f2ff] text-[#131315] font-['Space_Grotesk'] font-bold px-10 py-4 hover:shadow-[0_0_20px_rgba(0,242,255,0.4)] transition-all"
                        >
                            ACCESS_DASHBOARD
                        </Link>
                    </>
                )}

                {status === 'error' && (
                    <>
                        <XCircle className="w-16 h-16 text-red-500 mx-auto mb-6" />
                        <h2 className="font-['Space_Grotesk'] text-3xl font-bold text-white mb-4 uppercase tracking-tighter">VERIFICATION_FAILURE</h2>
                        <p className="text-red-400 mb-8 text-sm font-mono">[ERROR]: {message}</p>
                        <div className="flex flex-col gap-4">
                            <Link
                                to="/signup"
                                className="bg-white text-[#131315] font-['Space_Grotesk'] font-bold px-8 py-3 transition-all hover:bg-[#00f2ff]"
                            >
                                RETRY_ONBOARDING
                            </Link>
                            <Link to="/login" className="text-[#00f2ff] text-sm hover:underline">RETURN_TO_LOGIN</Link>
                        </div>
                    </>
                )}
            </motion.div>
        </div>
    );
};

export default Verify;
