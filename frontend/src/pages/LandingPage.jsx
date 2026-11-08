import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { 
  Activity, 
  ArrowRight, 
  Cpu, 
  Database, 
  Flame, 
  Layers, 
  Search, 
  ShieldCheck, 
  Sparkles, 
  TrendingUp, 
  Users 
} from 'lucide-react';

export default function LandingPage() {
  const navigate = useNavigate();
  const [liveMatches, setLiveMatches] = useState([]);
  const [loadingLive, setLoadingLive] = useState(true);

  useEffect(() => {
    api.getLiveMatches()
      .then((data) => {
        setLiveMatches(data.matches || []);
        setLoadingLive(false);
      })
      .catch(() => setLoadingLive(false));
  }, []);

  const samplePrompts = [
    { title: "Death Over Sixes", query: "Who hit the most sixes in death overs (overs 16-20)?" },
    { title: "Live Equation", query: "What is the live score and equation in the India vs Australia match?" },
    { title: "Player Head-to-Head", query: "Compare Virat Kohli and Babar Azam across strike rate and boundaries" },
    { title: "Iconic Miracle", query: "Tell me about the 2022 MCG match between India and Pakistan and Kohli's sixes" },
    { title: "Hybrid Chase Analytics", query: "Can Kohli chase down this target given his historical career run-chase record in Australia?" },
  ];

  const handleLaunchPrompt = (query) => {
    navigate(`/chat?q=${encodeURIComponent(query)}`);
  };

  const currentLive = liveMatches.length > 0 ? liveMatches[0] : null;

  return (
    <div className="min-h-screen bg-[#050505] text-white bg-grid-pattern selection:bg-white selection:text-black">
      
      {/* Hero Section */}
      <section className="relative pt-20 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center border-b border-[#1f1f1f]">
        
        {/* Release Tag */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-zinc-700 bg-zinc-900/80 text-zinc-300 text-xs font-mono mb-8 tracking-wider">
          <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
          STATEFUL MULTI-AGENT CRICKET SYSTEM &bull; v1.0
        </div>

        {/* Main Title */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight max-w-5xl mx-auto leading-none uppercase">
          Precision Cricket <br />
          <span className="text-zinc-500 hover:text-white transition-colors duration-300">
            Intelligence Engine
          </span>
        </h1>

        {/* Subtitle */}
        <p className="mt-6 text-zinc-400 max-w-3xl mx-auto text-base sm:text-lg lg:text-xl font-normal leading-relaxed">
          Autonomous orchestration powered by <strong className="text-white">LangGraph</strong> and <strong className="text-white">Gemini</strong>. 
          Resolves historical ball-by-ball queries, live match situations, hybrid contextual chase evaluations, and radar player comparisons.
        </p>

        {/* CTA Buttons */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            to="/chat"
            className="px-8 py-3.5 rounded-sm bg-white text-black font-mono font-bold text-sm tracking-wider uppercase hover:bg-zinc-200 transition-all shadow-[0_0_20px_rgba(255,255,255,0.2)] flex items-center gap-2"
          >
            Launch AI Analyst
            <ArrowRight className="w-4 h-4" />
          </Link>
          
          <Link
            to="/live"
            className="px-8 py-3.5 rounded-sm border border-zinc-700 bg-zinc-900/60 text-white font-mono font-semibold text-sm tracking-wider uppercase hover:border-zinc-400 hover:bg-zinc-800 transition-all flex items-center gap-2"
          >
            <Activity className="w-4 h-4" />
            Live Match Center
          </Link>

          <Link
            to="/compare"
            className="px-8 py-3.5 rounded-sm border border-zinc-700 bg-zinc-900/60 text-white font-mono font-semibold text-sm tracking-wider uppercase hover:border-zinc-400 hover:bg-zinc-800 transition-all flex items-center gap-2"
          >
            <Users className="w-4 h-4" />
            Compare Players
          </Link>
        </div>

      </section>

      {/* Live Match Telemetry Ticker */}
      {currentLive && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6">
          <div className="p-4 sm:p-5 rounded-sm border border-zinc-800 bg-[#0a0a0a] shadow-xl flex flex-col md:flex-row items-center justify-between gap-4">
            
            <div className="flex items-center gap-4 w-full md:w-auto">
              <div className="px-2.5 py-1 rounded bg-white text-black text-[11px] font-mono font-bold uppercase tracking-wider flex items-center gap-1.5 shrink-0">
                <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse"></span>
                LIVE NOW
              </div>
              <div>
                <h4 className="text-white font-bold text-sm sm:text-base tracking-wide">
                  {currentLive.name}
                </h4>
                <p className="text-zinc-400 text-xs font-mono mt-0.5">
                  {currentLive.venue} &bull; <span className="text-zinc-200">{currentLive.status}</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 w-full md:w-auto justify-end">
              <div className="text-right">
                <div className="text-xs font-mono text-zinc-400">Target: 187</div>
                <div className="text-sm font-mono font-bold text-white">IND 143/3 (15.2 ov)</div>
              </div>
              <Link
                to="/live"
                className="px-4 py-2 bg-zinc-900 border border-zinc-700 hover:border-white text-white text-xs font-mono uppercase tracking-wider rounded-sm transition-all"
              >
                Full Scorecard &rarr;
              </Link>
            </div>

          </div>
        </section>
      )}

      {/* 4 Core Intelligence Portals */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-12">
          <h2 className="text-xs font-mono text-zinc-400 tracking-widest uppercase mb-2">
            INTELLIGENCE ARCHITECTURE
          </h2>
          <h3 className="text-2xl sm:text-3xl font-bold tracking-tight text-white uppercase">
            Four Specialized Analytical Portals
          </h3>
          <p className="text-zinc-400 text-sm max-w-xl mx-auto mt-2">
            Click any portal below to enter its specialized analytics workspace.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          {/* Portal 1 */}
          <Link
            to="/vault"
            className="group p-6 rounded-sm border border-zinc-800 bg-[#0a0a0a] hover:border-white transition-all flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-sm bg-zinc-900 border border-zinc-700 flex items-center justify-center mb-4 group-hover:bg-white group-hover:text-black transition-colors">
                <Database className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest">
                PORTAL 01 // RECORDS
              </span>
              <h4 className="text-lg font-bold text-white mt-1 group-hover:text-zinc-200">
                Historical Vault
              </h4>
              <p className="text-zinc-400 text-xs mt-2 leading-relaxed">
                Deterministic Text-to-SQL over Cricsheet ball-by-ball matches. Query death-over strike rates, boundary ratios, and tournament finals.
              </p>
            </div>
            <div className="mt-6 flex items-center text-xs font-mono text-zinc-400 group-hover:text-white uppercase tracking-wider">
              Enter Vault &rarr;
            </div>
          </Link>

          {/* Portal 2 */}
          <Link
            to="/live"
            className="group p-6 rounded-sm border border-zinc-800 bg-[#0a0a0a] hover:border-white transition-all flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-sm bg-zinc-900 border border-zinc-700 flex items-center justify-center mb-4 group-hover:bg-white group-hover:text-black transition-colors">
                <Activity className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest">
                PORTAL 02 // TELEMETRY
              </span>
              <h4 className="text-lg font-bold text-white mt-1 group-hover:text-zinc-200">
                Live Match Center
              </h4>
              <p className="text-zinc-400 text-xs mt-2 leading-relaxed">
                Real-time scorecard feeds with TTL caching, ball-by-ball commentary, current equation solver, and AI momentum evaluation.
              </p>
            </div>
            <div className="mt-6 flex items-center text-xs font-mono text-zinc-400 group-hover:text-white uppercase tracking-wider">
              View Matches &rarr;
            </div>
          </Link>

          {/* Portal 3 */}
          <Link
            to="/chat"
            className="group p-6 rounded-sm border border-zinc-800 bg-[#0a0a0a] hover:border-white transition-all flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-sm bg-zinc-900 border border-zinc-700 flex items-center justify-center mb-4 group-hover:bg-white group-hover:text-black transition-colors">
                <Layers className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest">
                PORTAL 03 // HYBRID AI
              </span>
              <h4 className="text-lg font-bold text-white mt-1 group-hover:text-zinc-200">
                Intelligence Analyst
              </h4>
              <p className="text-zinc-400 text-xs mt-2 leading-relaxed">
                Dual-retrieval engine synthesizing real-time match state with historical precedents. ChromaDB narrative RAG and LangGraph state graph.
              </p>
            </div>
            <div className="mt-6 flex items-center text-xs font-mono text-zinc-400 group-hover:text-white uppercase tracking-wider">
              Start Chat &rarr;
            </div>
          </Link>

          {/* Portal 4 */}
          <Link
            to="/compare"
            className="group p-6 rounded-sm border border-zinc-800 bg-[#0a0a0a] hover:border-white transition-all flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-sm bg-zinc-900 border border-zinc-700 flex items-center justify-center mb-4 group-hover:bg-white group-hover:text-black transition-colors">
                <Users className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-widest">
                PORTAL 04 // COMPARISON
              </span>
              <h4 className="text-lg font-bold text-white mt-1 group-hover:text-zinc-200">
                Player Comparison Studio
              </h4>
              <p className="text-zinc-400 text-xs mt-2 leading-relaxed">
                Side-by-side head-to-head metric matrices, death-over splits, dot-ball resistance, and dynamic high-contrast radar visualization.
              </p>
            </div>
            <div className="mt-6 flex items-center text-xs font-mono text-zinc-400 group-hover:text-white uppercase tracking-wider">
              Open Studio &rarr;
            </div>
          </Link>

        </div>
      </section>

      {/* Quick Launch Query Playground */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
        <div className="p-8 sm:p-10 rounded-sm border border-zinc-800 bg-[#080808]">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-white" />
            <span className="text-xs font-mono uppercase tracking-widest text-zinc-300">
              SAMPLE INTELLIGENCE QUERIES
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-white mb-6 uppercase">
            Test Real-Time Orchestration With One Click
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {samplePrompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleLaunchPrompt(p.query)}
                className="text-left p-4 rounded-sm border border-zinc-800 bg-zinc-950 hover:border-zinc-500 hover:bg-zinc-900/60 transition-all group flex flex-col justify-between"
              >
                <div>
                  <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider block mb-1">
                    {p.title}
                  </span>
                  <p className="text-xs text-zinc-300 group-hover:text-white line-clamp-2">
                    "{p.query}"
                  </p>
                </div>
                <div className="mt-3 text-[11px] font-mono text-zinc-400 group-hover:text-white flex items-center gap-1">
                  Run Query &rarr;
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

    </div>
  );
}

