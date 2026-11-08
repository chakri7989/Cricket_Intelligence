import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { 
  Users, 
  ArrowRight, 
  CheckCircle, 
  TrendingUp, 
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { 
  Radar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  ResponsiveContainer 
} from 'recharts';

export default function PlayerComparePage() {
  const navigate = useNavigate();
  const [playerList, setPlayerList] = useState([]);
  const [player1, setPlayer1] = useState('Virat Kohli');
  const [player2, setPlayer2] = useState('Rohit Sharma');
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getPlayers()
      .then(res => {
        const list = res.players?.map(p => p.name) || [];
        setPlayerList(list);
      })
      .catch(console.error);

    fetchComparison('Virat Kohli', 'Rohit Sharma');
  }, []);

  const fetchComparison = async (p1, p2) => {
    setLoading(true);
    try {
      const data = await api.comparePlayers(p1, p2);
      setComparison(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = () => {
    fetchComparison(player1, player2);
  };

  const handleLaunchAI = () => {
    navigate(`/chat?q=${encodeURIComponent(`Compare ${player1} and ${player2} in high pressure games and death overs`)}`);
  };

  const s1 = comparison?.player1_stats || {};
  const s2 = comparison?.player2_stats || {};

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#050505] text-white max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      
      {/* Header */}
      <div className="pb-6 border-b border-zinc-800">
        <div className="flex items-center gap-2 mb-1">
          <Users className="w-4 h-4 text-white" />
          <span className="text-xs font-mono text-zinc-400 uppercase tracking-widest">
            ANALYTICAL STUDIO
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight uppercase">
          Head-to-Head Player Analytics
        </h1>
        <p className="text-zinc-400 text-xs sm:text-sm mt-1">
          Multidimensional statistical evaluation across career phases, death-over striking, and boundary velocity.
        </p>
      </div>

      {/* Selectors Bar */}
      <div className="my-8 p-6 rounded-sm border border-zinc-800 bg-[#0a0a0a] flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Player 1 Dropdown */}
        <div className="w-full md:w-1/3">
          <label className="block text-[11px] font-mono text-zinc-400 uppercase mb-2">
            Player A
          </label>
          <select
            value={player1}
            onChange={(e) => setPlayer1(e.target.value)}
            className="w-full bg-black border border-zinc-700 text-white rounded-sm px-4 py-2.5 text-sm font-sans focus:outline-none focus:border-white"
          >
            {playerList.map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </div>

        {/* VS Badge */}
        <div className="px-3 py-1 bg-zinc-900 border border-zinc-800 rounded-full text-xs font-mono font-bold text-zinc-400">
          VS
        </div>

        {/* Player 2 Dropdown */}
        <div className="w-full md:w-1/3">
          <label className="block text-[11px] font-mono text-zinc-400 uppercase mb-2">
            Player B
          </label>
          <select
            value={player2}
            onChange={(e) => setPlayer2(e.target.value)}
            className="w-full bg-black border border-zinc-700 text-white rounded-sm px-4 py-2.5 text-sm font-sans focus:outline-none focus:border-white"
          >
            {playerList.map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </div>

        {/* Execute Button */}
        <button
          onClick={handleCompare}
          disabled={loading}
          className="w-full md:w-auto px-6 py-2.5 bg-white text-black font-mono font-bold text-xs uppercase tracking-wider rounded-sm hover:bg-zinc-200 transition-colors disabled:opacity-50 self-end"
        >
          {loading ? 'Evaluating...' : 'Run Analytics'}
        </button>

      </div>

      {/* Comparison Body */}
      {comparison && (
        <div className="space-y-8">
          
          {/* Radar Chart + AI Verdict */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* High-Contrast Radar Card */}
            <div className="p-6 rounded-sm border border-zinc-800 bg-[#0a0a0a]">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-400">
                  Performance Radar Map
                </h3>
                <div className="flex items-center gap-4 text-xs font-mono">
                  <span className="flex items-center gap-1.5 text-white">
                    <span className="w-2.5 h-2.5 rounded-full bg-white"></span> {player1}
                  </span>
                  <span className="flex items-center gap-1.5 text-zinc-400">
                    <span className="w-2.5 h-2.5 rounded-full bg-zinc-600"></span> {player2}
                  </span>
                </div>
              </div>

              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={comparison.radar_data}>
                    <PolarGrid stroke="#262626" />
                    <PolarAngleAxis dataKey="subject" stroke="#a1a1aa" tick={{ fontSize: 11 }} />
                    <Radar
                      name={player1}
                      dataKey={player1}
                      stroke="#ffffff"
                      fill="#ffffff"
                      fillOpacity={0.3}
                    />
                    <Radar
                      name={player2}
                      dataKey={player2}
                      stroke="#71717a"
                      fill="#71717a"
                      fillOpacity={0.3}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* AI Analytical Verdict Card */}
            <div className="p-6 rounded-sm border border-zinc-800 bg-[#0a0a0a] flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-white" />
                  <span className="text-xs font-mono uppercase tracking-widest text-zinc-400">
                    ANALYTICAL VERDICT
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white mb-4">
                  {player1} vs {player2} Tactical Breakdown
                </h3>
                <p className="text-sm text-zinc-300 leading-relaxed font-sans">
                  {comparison.verdict}
                </p>
                <div className="mt-6 p-4 rounded bg-black border border-zinc-900 text-xs font-mono space-y-2 text-zinc-400">
                  <div>&bull; Normalized across Cricsheet match records.</div>
                  <div>&bull; Death-over metrics computed strictly for overs 16–20.</div>
                  <div>&bull; Dot-ball resistance reflects non-boundary rotational strike capability.</div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-zinc-900">
                <button
                  onClick={handleLaunchAI}
                  className="w-full py-2.5 bg-zinc-900 border border-zinc-700 hover:border-white text-white text-xs font-mono uppercase tracking-wider rounded-sm transition-all flex items-center justify-center gap-2"
                >
                  Deep Dive With AI Analyst
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

          </div>

          {/* Metric Matrix Table */}
          <div className="p-6 rounded-sm border border-zinc-800 bg-[#0a0a0a]">
            <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-400 mb-4">
              Side-by-Side Statistical Matrix
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-400">
                    <th className="pb-3">Performance Dimension</th>
                    <th className="pb-3 text-right">{player1}</th>
                    <th className="pb-3 text-right">{player2}</th>
                    <th className="pb-3 text-right">Advantage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900 text-zinc-200">
                  <tr className="hover:bg-zinc-900/40">
                    <td className="py-3 font-semibold text-white">Overall Strike Rate</td>
                    <td className="py-3 text-right font-bold">{s1.strike_rate}</td>
                    <td className="py-3 text-right font-bold">{s2.strike_rate}</td>
                    <td className="py-3 text-right text-emerald-400">
                      {s1.strike_rate > s2.strike_rate ? player1 : player2}
                    </td>
                  </tr>
                  <tr className="hover:bg-zinc-900/40">
                    <td className="py-3 font-semibold text-white">Death Overs SR (16–20)</td>
                    <td className="py-3 text-right font-bold">{s1.death_sr}</td>
                    <td className="py-3 text-right font-bold">{s2.death_sr}</td>
                    <td className="py-3 text-right text-emerald-400">
                      {s1.death_sr > s2.death_sr ? player1 : player2}
                    </td>
                  </tr>
                  <tr className="hover:bg-zinc-900/40">
                    <td className="py-3 font-semibold text-white">Boundary Frequency %</td>
                    <td className="py-3 text-right">{s1.boundary_pct}%</td>
                    <td className="py-3 text-right">{s2.boundary_pct}%</td>
                    <td className="py-3 text-right text-emerald-400">
                      {s1.boundary_pct > s2.boundary_pct ? player1 : player2}
                    </td>
                  </tr>
                  <tr className="hover:bg-zinc-900/40">
                    <td className="py-3 font-semibold text-white">Dot Ball Rate %</td>
                    <td className="py-3 text-right">{s1.dot_ball_pct}%</td>
                    <td className="py-3 text-right">{s2.dot_ball_pct}%</td>
                    <td className="py-3 text-right text-emerald-400">
                      {s1.dot_ball_pct < s2.dot_ball_pct ? player1 : player2} (Fewer dots)
                    </td>
                  </tr>
                  <tr className="hover:bg-zinc-900/40">
                    <td className="py-3 font-semibold text-white">Six Hitting Velocity</td>
                    <td className="py-3 text-right">{s1.sixes_per_100} / 100b</td>
                    <td className="py-3 text-right">{s2.sixes_per_100} / 100b</td>
                    <td className="py-3 text-right text-emerald-400">
                      {s1.sixes_per_100 > s2.sixes_per_100 ? player1 : player2}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </div>
      )}

    </div>
  );
}

