import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { 
  Activity, 
  Flame, 
  RefreshCw, 
  Target, 
  TrendingUp, 
  Clock, 
  MapPin, 
  Sparkles,
  ArrowRight
} from 'lucide-react';

export default function LiveCenter() {
  const navigate = useNavigate();
  const [matches, setMatches] = useState([]);
  const [selectedMatchId, setSelectedMatchId] = useState('');
  const [scorecard, setScorecard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMatches();
  }, []);

  const loadMatches = async () => {
    setLoading(true);
    try {
      const data = await api.getLiveMatches();
      const list = data.matches || [];
      setMatches(list);
      if (list.length > 0) {
        setSelectedMatchId(list[0].id);
        loadScorecard(list[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadScorecard = async (id) => {
    try {
      const sc = await api.getMatchScorecard(id);
      setScorecard(sc);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSelectMatch = (id) => {
    setSelectedMatchId(id);
    loadScorecard(id);
  };

  const handleAskAI = (contextQuery) => {
    navigate(`/chat?q=${encodeURIComponent(contextQuery)}`);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#050505] text-white max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-zinc-800 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse"></span>
            <span className="text-xs font-mono text-zinc-400 uppercase tracking-widest">
              TELEMETRY CENTER
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight uppercase">
            Live Cricket Operations Hub
          </h1>
        </div>

        <button
          onClick={loadMatches}
          className="self-start sm:self-auto px-4 py-2 border border-zinc-700 bg-zinc-900 text-xs font-mono uppercase tracking-wider rounded-sm hover:border-white transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Live Feeds
        </button>
      </div>

      {/* Match Selector Tabs */}
      <div className="flex items-center gap-3 overflow-x-auto py-6 border-b border-zinc-900">
        {matches.map((m) => (
          <button
            key={m.id}
            onClick={() => handleSelectMatch(m.id)}
            className={`px-5 py-3 rounded-sm border text-left shrink-0 transition-all ${
              selectedMatchId === m.id
                ? 'bg-zinc-900 border-white text-white shadow-sm'
                : 'bg-[#0a0a0a] border-zinc-800 text-zinc-400 hover:border-zinc-600'
            }`}
          >
            <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 mb-1">
              {m.matchType?.toUpperCase()} &bull; {m.teams?.join(' vs ')}
            </div>
            <div className="text-sm font-bold text-white">
              {m.name}
            </div>
          </button>
        ))}
      </div>

      {/* Detailed Live State */}
      {scorecard ? (
        <div className="mt-8 space-y-8">
          
          {/* Hero Match Status Banner */}
          <div className="p-6 sm:p-8 rounded-sm border border-zinc-800 bg-[#0a0a0a]">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              
              <div>
                <span className="px-2.5 py-0.5 rounded bg-zinc-800 text-zinc-300 text-[10px] font-mono tracking-wider uppercase">
                  ACTIVE INNINGS
                </span>
                <h2 className="text-xl sm:text-2xl font-bold mt-2 text-white">
                  {scorecard.name}
                </h2>
                <div className="flex items-center gap-4 mt-2 text-xs font-mono text-zinc-400">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" /> {scorecard.venue}
                  </span>
                </div>
                <p className="mt-3 text-sm text-zinc-300 font-medium">
                  {scorecard.status}
                </p>
              </div>

              {/* Equation Box (if chasing) */}
              {scorecard.required_runs && (
                <div className="p-4 rounded-sm border border-zinc-800 bg-black text-right shrink-0">
                  <div className="text-[11px] font-mono text-zinc-400 uppercase">Equation</div>
                  <div className="text-2xl font-mono font-bold text-white mt-1">
                    {scorecard.required_runs} <span className="text-xs text-zinc-400 font-normal">runs needed</span>
                  </div>
                  <div className="text-xs font-mono text-zinc-400 mt-1">
                    {scorecard.remaining_balls} balls left &bull; RRR: <span className="text-white font-bold">{scorecard.required_run_rate}</span>
                  </div>
                </div>
              )}

            </div>

            {/* AI Action Pill */}
            <div className="mt-6 pt-6 border-t border-zinc-800 flex flex-wrap items-center justify-between gap-4">
              <span className="text-xs text-zinc-400">
                Want deeper tactical win probabilities and historical chase analytics?
              </span>
              <button
                onClick={() => handleAskAI(`Given the live match situation in ${scorecard.name} (${scorecard.status}), evaluate win probability and career records under these conditions.`)}
                className="px-4 py-2 bg-white text-black text-xs font-mono font-bold uppercase tracking-wider rounded-sm hover:bg-zinc-200 transition-colors flex items-center gap-2"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Analyze With AI Agent
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

          </div>

          {/* Batters & Bowler Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Batting Card */}
            <div className="lg:col-span-2 p-6 rounded-sm border border-zinc-800 bg-[#0a0a0a]">
              <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-400 mb-4">
                Current Batters on Crease
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-400">
                      <th className="pb-2">Batter</th>
                      <th className="pb-2 text-right">Runs</th>
                      <th className="pb-2 text-right">Balls</th>
                      <th className="pb-2 text-right">4s</th>
                      <th className="pb-2 text-right">6s</th>
                      <th className="pb-2 text-right">SR</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-900 text-zinc-200">
                    {scorecard.current_batters?.map((b, idx) => (
                      <tr key={idx} className="hover:bg-zinc-900/40">
                        <td className="py-3 font-semibold text-white flex items-center gap-1.5">
                          {b.name} <span className="text-[10px] text-zinc-400">*</span>
                        </td>
                        <td className="py-3 text-right font-bold text-white">{b.runs}</td>
                        <td className="py-3 text-right text-zinc-400">{b.balls}</td>
                        <td className="py-3 text-right text-zinc-400">{b.fours}</td>
                        <td className="py-3 text-right text-zinc-400">{b.sixes}</td>
                        <td className="py-3 text-right text-white">{b.strike_rate}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Bowling Card */}
            {scorecard.current_bowler && (
              <div className="p-6 rounded-sm border border-zinc-800 bg-[#0a0a0a] flex flex-col justify-between">
                <div>
                  <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-400 mb-4">
                    Current Bowler Spell
                  </h3>
                  <div className="text-lg font-bold text-white mb-2">
                    {scorecard.current_bowler.name}
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs font-mono mt-4">
                    <div className="p-2.5 rounded bg-black border border-zinc-900">
                      <span className="text-zinc-500 block text-[10px]">OVERS</span>
                      <span className="text-white font-bold text-sm">{scorecard.current_bowler.overs}</span>
                    </div>
                    <div className="p-2.5 rounded bg-black border border-zinc-900">
                      <span className="text-zinc-500 block text-[10px]">FIGURES</span>
                      <span className="text-white font-bold text-sm">{scorecard.current_bowler.wickets}/{scorecard.current_bowler.runs}</span>
                    </div>
                    <div className="p-2.5 rounded bg-black border border-zinc-900">
                      <span className="text-zinc-500 block text-[10px]">ECONOMY</span>
                      <span className="text-white font-bold text-sm">{scorecard.current_bowler.economy}</span>
                    </div>
                    <div className="p-2.5 rounded bg-black border border-zinc-900">
                      <span className="text-zinc-500 block text-[10px]">MAIDENS</span>
                      <span className="text-white font-bold text-sm">{scorecard.current_bowler.maidens}</span>
                    </div>
                  </div>
                </div>

                {scorecard.recent_balls && (
                  <div className="mt-6 pt-4 border-t border-zinc-900">
                    <span className="text-[10px] font-mono text-zinc-500 uppercase block mb-2">Recent Over Deliveries</span>
                    <div className="flex items-center gap-2">
                      {scorecard.recent_balls.map((ball, i) => (
                        <span
                          key={i}
                          className={`w-7 h-7 rounded flex items-center justify-center font-mono text-xs font-bold ${
                            ball === '6'
                              ? 'bg-white text-black'
                              : ball === '4'
                              ? 'bg-zinc-200 text-black'
                              : ball === 'W'
                              ? 'bg-red-600 text-white'
                              : 'bg-zinc-900 border border-zinc-800 text-zinc-300'
                          }`}
                        >
                          {ball}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

          </div>

          {/* Commentary Timeline */}
          {scorecard.commentary_highlights && (
            <div className="p-6 rounded-sm border border-zinc-800 bg-[#0a0a0a]">
              <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-400 mb-4">
                Ball-by-Ball Key Moments
              </h3>
              <div className="space-y-3">
                {scorecard.commentary_highlights.map((c, i) => (
                  <div key={i} className="p-3 rounded bg-zinc-950 border border-zinc-900 text-xs font-mono text-zinc-300">
                    {c}
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      ) : (
        <div className="p-12 text-center text-zinc-500 font-mono text-xs">
          Loading live match scorecard...
        </div>
      )}

    </div>
  );
}

