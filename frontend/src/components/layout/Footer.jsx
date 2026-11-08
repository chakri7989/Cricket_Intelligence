import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Database, ShieldCheck, Cpu } from 'lucide-react';

export default function Footer() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    api.getSystemStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  return (
    <footer className="border-t border-[#222222] bg-[#070707] text-zinc-400 text-xs py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-white font-mono text-[11px] uppercase tracking-wider">
              ALL SYSTEMS ONLINE
            </span>
          </div>
          <span className="text-zinc-600">|</span>
          <span className="font-mono text-zinc-500 text-[11px]">
            FastAPI + LangGraph + ChromaDB + SQLite
          </span>
        </div>

        {status && (
          <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-zinc-400">
            <span className="flex items-center gap-1.5">
              <Database className="w-3 h-3 text-zinc-300" />
              SQLite: <span className="text-white">{status.sqlite?.deliveries || 0} balls</span>
            </span>
            <span className="flex items-center gap-1.5">
              <Cpu className="w-3 h-3 text-zinc-300" />
              ChromaDB: <span className="text-white">{status.chromadb?.document_count || 0} narratives</span>
            </span>
          </div>
        )}

        <div className="text-zinc-400 text-[11px] font-mono">
          &copy; {new Date().getFullYear()} AI-Powered Cricket Intelligence. Built for high performance.
        </div>

      </div>
    </footer>
  );
}

