import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { 
  Database, 
  Search, 
  Trophy, 
  Calendar, 
  MapPin, 
  ArrowRight,
  Filter
} from 'lucide-react';

export default function HistoricalVault() {
  const navigate = useNavigate();
  const [matches, setMatches] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [formatFilter, setFormatFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getVaultMatches()
      .then(res => {
        setMatches(res.matches || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filteredMatches = matches.filter(m => {
    const matchesSearch = 
      m.team1?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.team2?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.venue?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.winner?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.player_of_match?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesFormat = formatFilter === 'ALL' || m.match_type === formatFilter;

    return matchesSearch && matchesFormat;
  });

  const handleQueryAI = (match) => {
    navigate(`/chat?q=${encodeURIComponent(`Provide a deep tactical breakdown of the match between ${match.team1} and ${match.team2} at ${match.venue} in ${match.season}`)}`);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#050505] text-white max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      
      {/* Header */}
      <div className="pb-6 border-b border-zinc-800">
        <div className="flex items-center gap-2 mb-1">
          <Database className="w-4 h-4 text-white" />
          <span className="text-xs font-mono text-zinc-400 uppercase tracking-widest">
            HISTORICAL ARCHIVE
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight uppercase">
          Cricsheet Records Vault
        </h1>
        <p className="text-zinc-400 text-xs sm:text-sm mt-1">
          Indexed ball-by-ball matches from Cricsheet. Query deterministic statistics, margins, and match heroes.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="my-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        
        {/* Search */}
        <div className="relative w-full sm:w-96">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search team, venue, winner, or player..."
            className="w-full bg-[#0a0a0a] border border-zinc-800 text-white rounded-sm pl-9 pr-4 py-2 text-xs font-sans focus:outline-none focus:border-white"
          />
        </div>

        {/* Format Filter Tabs */}
        <div className="flex items-center gap-1.5 w-full sm:w-auto">
          {['ALL', 'T20', 'ODI'].map((fmt) => (
            <button
              key={fmt}
              onClick={() => setFormatFilter(fmt)}
              className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wider rounded-sm transition-all ${
                formatFilter === fmt
                  ? 'bg-white text-black font-bold'
                  : 'bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white'
              }`}
            >
              {fmt}
            </button>
          ))}
        </div>

      </div>

      {/* Match Cards Grid */}
      {loading ? (
        <div className="p-12 text-center text-zinc-500 font-mono text-xs">
          Loading historical match archive...
        </div>
      ) : filteredMatches.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMatches.map((m) => (
            <div
              key={m.id}
              className="p-6 rounded-sm border border-zinc-800 bg-[#0a0a0a] hover:border-zinc-500 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400 mb-2">
                  <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 uppercase">
                    {m.match_type} &bull; {m.season}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" /> {m.date}
                  </span>
                </div>

                <h3 className="text-base font-bold text-white mt-2">
                  {m.team1} vs {m.team2}
                </h3>

                <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-400 mt-1">
                  <MapPin className="w-3.5 h-3.5 text-zinc-400" />
                  <span className="truncate">{m.venue}</span>
                </div>

                <div className="mt-4 pt-4 border-t border-zinc-900 space-y-1.5 text-xs font-mono">
                  <div className="text-zinc-300">
                    Winner: <span className="font-bold text-white">{m.winner}</span>
                    {m.win_by_runs > 0 ? ` (by ${m.win_by_runs} runs)` : m.win_by_wickets > 0 ? ` (by ${m.win_by_wickets} wickets)` : ' (Super Over)'}
                  </div>
                  <div className="text-zinc-400 flex items-center gap-1.5">
                    <Trophy className="w-3.5 h-3.5 text-zinc-300" />
                    POTM: <span className="text-zinc-200">{m.player_of_match}</span>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-zinc-900">
                <button
                  onClick={() => handleQueryAI(m)}
                  className="w-full py-2 bg-zinc-950 border border-zinc-800 hover:border-white text-zinc-300 hover:text-white text-xs font-mono uppercase tracking-wider rounded-sm transition-all flex items-center justify-center gap-1.5"
                >
                  Analyze in AI
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-12 text-center text-zinc-500 font-mono text-xs">
          No historical matches matched your filter criteria.
        </div>
      )}

    </div>
  );
}

