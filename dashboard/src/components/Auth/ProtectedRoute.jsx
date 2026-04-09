import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Loader2 } from 'lucide-react';

const ProtectedRoute = () => {
    const { user, loading, token } = useAuth();

    if (loading) {
        return (
            <div className="min-h-screen bg-[#131315] flex flex-col items-center justify-center text-[#00f2ff]">
                <Loader2 className="w-12 h-12 animate-spin mb-4" />
                <span className="font-['Space_Grotesk'] text-sm tracking-widest uppercase">SYNCHRONIZING_NODE...</span>
            </div>
        );
    }

    if (!token) {
        return <Navigate to="/login" replace />;
    }

    return <Outlet />;
};

export default ProtectedRoute;
