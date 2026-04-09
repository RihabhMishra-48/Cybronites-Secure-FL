import { useState, useCallback, useEffect } from 'react';

const isProd = import.meta.env.PROD;
const SECURE_BASE_URL = isProd 
    ? `${window.location.origin}/api/secure`
    : `http://localhost:${import.meta.env.VITE_SECURE_PORT || '8100'}`;

export const useSecureTraining = () => {
    const [datasets, setDatasets] = useState([]);
    const [jobs, setJobs] = useState([]);
    const [models, setModels] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchDatasets = useCallback(async () => {
        setLoading(true);
        try {
            const res = await fetch(`${SECURE_BASE_URL}/api/v1/datasets`);
            if (!res.ok) throw new Error('Failed to fetch datasets');
            const data = await res.json();
            // Backend returns { count: X, datasets: [...] }
            setDatasets(Array.isArray(data.datasets) ? data.datasets : []);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchJobs = useCallback(async () => {
        try {
            const res = await fetch(`${SECURE_BASE_URL}/api/v1/training_jobs`);
            if (!res.ok) throw new Error('Failed to fetch jobs');
            const data = await res.json();
             // Backend returns { count: X, jobs: [...] }
            setJobs(Array.isArray(data.jobs) ? data.jobs : []);
        } catch (err) {
            console.error(err);
        }
    }, []);

    const fetchModels = useCallback(async () => {
        try {
            const res = await fetch(`${SECURE_BASE_URL}/api/v1/models`);
            if (!res.ok) throw new Error('Failed to fetch models');
            const data = await res.json();
            // Backend returns list directly for models
            setModels(Array.isArray(data) ? data : (data.models || []));
        } catch (err) {
            console.error(err);
        }
    }, []);

    const submitJob = async (datasetId, modelType, hyperparams) => {
        try {
            const res = await fetch(`${SECURE_BASE_URL}/api/v1/train`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    dataset_id: datasetId, 
                    model_type: modelType, 
                    ...hyperparams 
                })
            });
            if (!res.ok) throw new Error('Failed to submit job');
            const data = await res.json();
            fetchJobs();
            return data;
        } catch (err) {
            setError(err.message);
            throw err;
        }
    };

    // Auto-poll for jobs if any are active
    useEffect(() => {
        const active = Array.isArray(jobs) && jobs.some(j => j.status === 'QUEUED' || j.status === 'RUNNING');
        if (active) {
            const interval = setInterval(fetchJobs, 2000);
            return () => clearInterval(interval);
        }
    }, [jobs, fetchJobs]);

    return {
        datasets,
        jobs,
        models,
        loading,
        error,
        fetchDatasets,
        fetchJobs,
        fetchModels,
        submitJob
    };
};
