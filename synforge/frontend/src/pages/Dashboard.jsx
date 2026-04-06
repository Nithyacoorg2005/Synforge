import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
    Upload, Activity, Download, Settings, 
    FileText, ShieldAlert, ShieldCheck 
} from 'lucide-react';
import { uploadDataset } from '../services/api';

// Global Production URL with Local Fallback
const API_BASE_URL = process.env.REACT_APP_API_URL || "https://synforge.onrender.com";

const StatusBadge = ({ risk }) => {
    const isLow = risk < 0.3;
    const isMed = risk >= 0.3 && risk < 0.7;
    return (
        <div className={`flex items-center gap-2 text-[10px] px-3 py-1 rounded-full border shadow-sm transition-all ${
            isLow ? 'bg-emerald-900/20 text-emerald-400 border-emerald-800/50' : 
            isMed ? 'bg-amber-900/20 text-amber-400 border-amber-800/50' : 
            'bg-rose-900/20 text-rose-400 border-rose-800/50'
        }`}>
            {isLow ? <ShieldCheck size={12} /> : <ShieldAlert size={12} />}
            <span className="font-bold tracking-widest uppercase text-[9px]">
                {isLow ? 'Production Ready' : isMed ? 'Internal Use Only' : 'High Leakage Risk'}
            </span>
        </div>
    );
};

const MetricCard = ({ title, value, sub, color, border = "border-slate-800" }) => (
    <div className={`bg-slate-900/50 p-6 rounded-lg border ${border} backdrop-blur-sm transition-all hover:bg-slate-900 hover:border-slate-700`}>
        <h3 className="text-slate-400 text-[10px] uppercase tracking-[0.2em] mb-1">{title}</h3>
        <p className={`text-4xl font-bold my-2 tracking-tighter ${color}`}>{value}</p>
        <p className="text-[10px] text-slate-500 uppercase tracking-tight">{sub}</p>
    </div>
);

const SynForgeDashboard = () => {
    const [file, setFile] = useState(null);
    const [jobId, setJobId] = useState(null);
    const [status, setStatus] = useState('idle');
    const [metrics, setMetrics] = useState(null);
    const [epsilon, setEpsilon] = useState(0.5);

    const handleUpload = async () => {
        if (!file) return;
        setStatus('processing');
        try {
            const response = await uploadDataset(file, epsilon);
            setJobId(response.job_id);
        } catch (error) {
            console.error("Upload failed", error);
            setStatus('idle');
            alert(`Connection Error: Ensure the synthesis engine is awake at ${API_BASE_URL}`);
        }
    };

    useEffect(() => {
        if (jobId && status === 'processing') {
            const interval = setInterval(async () => {
                try {
                    const res = await axios.get(`${API_BASE_URL}/status/${jobId}`);
                    if (res.data.status === 'completed') {
                        setMetrics(res.data);
                        setStatus('completed');
                        clearInterval(interval);
                    }
                } catch (error) {
                    console.error("Polling Error:", error);
                }
            }, 3000);
            return () => clearInterval(interval);
        }
    }, [jobId, status]);

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-mono">
            <header className="border-b border-slate-800 pb-6 mb-10 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-black tracking-tighter italic uppercase">SynForge // v1.0</h1>
                    <p className="text-slate-500 text-xs mt-1 uppercase tracking-widest">Adversarial Privacy & Synthetic Data Engine</p>
                </div>
                {status === 'completed' && metrics && <StatusBadge risk={metrics.privacy_risk} />}
            </header>

            {status === 'idle' && (
                <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-top-4 duration-500">
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl">
                        <div className="flex items-center gap-3 mb-6 text-blue-400">
                            <Settings size={20} className="animate-pulse" />
                            <h2 className="text-xs font-black uppercase tracking-[0.3em]">Privacy Configuration</h2>
                        </div>
                        <label className="text-xs text-slate-400 flex justify-between mb-2 uppercase tracking-tighter font-bold">
                            <span>Differential Privacy Budget (ε)</span>
                            <span className="font-bold text-blue-400 text-sm bg-blue-400/10 px-2 py-0.5 rounded italic">{epsilon.toFixed(1)}</span>
                        </label>
                        <input type="range" min="0.1" max="5" step="0.1" value={epsilon} onChange={(e) => setEpsilon(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500" />
                    </div>

                    <div className="border-2 border-dashed border-slate-800 rounded-xl p-16 text-center bg-slate-900/20 hover:border-blue-500/50 transition-all group">
                        <input type="file" onChange={(e) => setFile(e.target.files[0])} className="hidden" id="fileInput" />
                        <label htmlFor="fileInput" className="cursor-pointer flex flex-col items-center">
                            <div className="p-5 bg-slate-800 rounded-full mb-6 group-hover:scale-110 transition-transform">
                                <Upload className="text-blue-500" size={32} />
                            </div>
                            <span className="text-xl font-bold tracking-tight mb-1 text-slate-300">Upload Sensitive Dataset</span>
                        </label>
                        {file && (
                            <div className="mt-8 animate-in zoom-in-95">
                                <p className="mb-6 text-[10px] bg-slate-800 py-1.5 px-4 rounded-full text-slate-300 uppercase inline-block">{file.name}</p><br/>
                                <button onClick={handleUpload} className="bg-blue-600 hover:bg-blue-500 transition-all px-12 py-4 rounded text-xs font-black uppercase tracking-[0.2em]">Execute Synthesis</button>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {status === 'processing' && (
                <div className="flex flex-col items-center justify-center py-32 space-y-6">
                    <Activity className="animate-spin text-blue-500" size={64} />
                    <p className="text-xl font-black tracking-[0.3em] uppercase italic">Initializing GAN Engine</p>
                </div>
            )}

            {status === 'completed' && metrics && (
                <div className="space-y-8 animate-in slide-in-from-bottom-8 duration-700">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <MetricCard title="Statistical Fidelity" value={`${(metrics.fidelity * 100).toFixed(1)}%`} sub="Distribution Accuracy" color="text-emerald-400" />
                        <MetricCard title="Privacy Risk" value={metrics.privacy_risk < 0.3 ? "LOW" : "HIGH"} sub={`MIA Score: ${metrics.privacy_risk}`} color={metrics.privacy_risk < 0.3 ? "text-blue-400" : "text-rose-400"} />
                        <MetricCard title="Utility Retention" value={metrics.tstr_results?.tstr_score ? `${(metrics.tstr_results.tstr_score * 100).toFixed(1)}%` : "N/A"} sub="Task Performance" color="text-indigo-400" />
                        
                        <div className="bg-slate-900 p-6 rounded-lg border border-slate-800 flex flex-col gap-3 justify-center shadow-lg">
                            <a href={`${API_BASE_URL}/download/${jobId}`} target="_blank" rel="noreferrer" className="w-full bg-blue-600 hover:bg-blue-500 transition-all py-3 rounded flex items-center justify-center gap-2 font-black no-underline text-white uppercase tracking-widest text-[10px]">
                                <Download size={14} /> Synthetic CSV
                            </a>
                            <a href={`${API_BASE_URL}/audit-report/${jobId}`} target="_blank" rel="noreferrer" className="w-full bg-transparent border border-slate-700 hover:border-slate-500 transition-all py-3 rounded flex items-center justify-center gap-2 font-black no-underline text-slate-300 uppercase tracking-widest text-[10px]">
                                <FileText size={14} /> Audit Report
                            </a>
                        </div>
                    </div>
                    <footer className="text-[10px] text-slate-600 text-center uppercase tracking-[0.4em] py-6 border-t border-slate-900/50">
                        Privacy Budget ε: {epsilon.toFixed(1)} | Alpha-Signal Validation
                    </footer>
                </div>
            )}
        </div>
    );
};

export default SynForgeDashboard;