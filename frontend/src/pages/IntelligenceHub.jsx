import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { 
  Send, 
  Cpu, 
  Database, 
  Activity, 
  Layers, 
  Users, 
  Code, 
  CheckCircle, 
  Sparkles,
  Terminal,
  RefreshCw
} from 'lucide-react';
import { 
  Radar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  ResponsiveContainer 
} from 'recharts';

export default function IntelligenceHub() {
  const [searchParams] = useSearchParams();
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `### Welcome to the Cricket Intelligence Analyst.
I am connected to:
- **Cricsheet Historical Database** (SQLite ball-by-ball indexed records)
- **ChromaDB Narrative Vector Archive** (Iconic match reports & rules)
- **Live Cricket Telemetry Feed** (Live scorecards & chase equations)
- **Head-to-Head Comparison Engine** (Multi-metric radar analytics)

Ask any historical, live, hybrid, or player comparison question to begin.`,
      intent: 'SYSTEM_READY',
      citations: ['SQLite Engine', 'ChromaDB Vector Store', 'Live Telemetry']
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSql, setShowSql] = useState({});
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Handle URL query parameter launch
  useEffect(() => {
    const q = searchParams.get('q');
    if (q && q.trim()) {
      handleSend(q);
    }
  }, [searchParams]);

  const handleSend = async (queryText = null) => {
    const query = (queryText || inputValue).trim();
    if (!query || isLoading) return;

    // Append user message
    const newMessages = [...messages, { role: 'user', content: query }];
    setMessages(newMessages);
    if (!queryText) setInputValue('');
    setIsLoading(true);

    try {
      const response = await api.askQuery(query);
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: response.final_answer,
          intent: response.intent,
          citations: response.citations,
          sql_query: response.sql_query,
          chart_payload: response.chart_payload,
          live_data: response.live_data
        }
      ]);
    } catch (err) {
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: `**Error**: ${err.message || 'Unable to process cricket query.'}`,
          intent: 'ERROR',
          citations: []
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const samplePills = [
    "Most sixes in death overs?",
    "What is the live score?",
    "Compare Virat Kohli and Babar Azam",
    "Can Kohli chase this down tonight?",
    "Tell me about the 2019 WC Super Over"
  ];

  const getIntentBadge = (intent) => {
    switch (intent) {
      case 'HISTORICAL_SQL':
        return { label: 'HISTORICAL SQL', icon: Database };
      case 'LIVE_MATCH':
        return { label: 'LIVE TELEMETRY', icon: Activity };
      case 'HYBRID':
        return { label: 'HYBRID AGENT', icon: Layers };
      case 'PLAYER_COMPARISON':
        return { label: 'PLAYER COMPARISON', icon: Users };
      case 'HISTORICAL_RAG':
        return { label: 'NARRATIVE RAG', icon: Cpu };
      default:
        return { label: intent || 'INTELLIGENCE', icon: Sparkles };
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#050505] text-white flex flex-col justify-between max-w-6xl mx-auto px-4 py-6">
      
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between pb-4 border-b border-zinc-800 gap-3">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-white" />
          <h2 className="text-base font-bold tracking-wider font-mono uppercase">
            AI Cricket Intelligence Terminal
          </h2>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          LANGGRAPH ACTIVE
        </div>
      </div>

      {/* Quick Suggestion Pills */}
      <div className="flex items-center gap-2 overflow-x-auto py-3 no-scrollbar border-b border-zinc-900">
        <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider shrink-0">
          PROMPTS:
        </span>
        {samplePills.map((pill, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(pill)}
            className="text-xs font-mono px-3 py-1 bg-zinc-900 border border-zinc-800 hover:border-zinc-400 text-zinc-300 hover:text-white rounded-full whitespace-nowrap transition-colors"
          >
            {pill}
          </button>
        ))}
      </div>

      {/* Chat Messages Feed */}
      <div className="flex-1 overflow-y-auto py-6 space-y-6">
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          const badge = !isUser && msg.intent ? getIntentBadge(msg.intent) : null;
          const BadgeIcon = badge?.icon;

          return (
            <div
              key={index}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
            >
              {/* Message Container */}
              <div
                className={`max-w-4xl p-5 rounded-sm border ${
                  isUser
                    ? 'bg-zinc-900 border-zinc-700 text-white'
                    : 'bg-[#0a0a0a] border-zinc-800 text-zinc-200'
                }`}
              >
                {/* Meta header for assistant responses */}
                {!isUser && badge && (
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-3 border-b border-zinc-900 text-xs font-mono">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-zinc-900 border border-zinc-700 text-zinc-300">
                      {BadgeIcon && <BadgeIcon className="w-3 h-3 text-white" />}
                      {badge.label}
                    </span>
                    {msg.citations && msg.citations.length > 0 && (
                      <span className="text-zinc-400 text-[11px]">
                        Sources: {msg.citations.join(' &bull; ')}
                      </span>
                    )}
                  </div>
                )}

                {/* Formatted Content */}
                <div className="prose prose-invert max-w-none text-xs sm:text-sm leading-relaxed whitespace-pre-wrap font-sans">
                  {msg.content}
                </div>

                {/* Radar Chart Display (When Intent is PLAYER_COMPARISON) */}
                {msg.chart_payload && msg.chart_payload.data && (
                  <div className="mt-6 pt-4 border-t border-zinc-800">
                    <h4 className="text-xs font-mono uppercase tracking-wider text-zinc-300 mb-2">
                      Radar Visualization Matrix
                    </h4>
                    <div className="h-64 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart data={msg.chart_payload.data}>
                          <PolarGrid stroke="#262626" />
                          <PolarAngleAxis dataKey="subject" stroke="#a1a1aa" tick={{ fontSize: 11 }} />
                          <Radar
                            name="Player 1"
                            dataKey="player1"
                            stroke="#ffffff"
                            fill="#ffffff"
                            fillOpacity={0.25}
                          />
                          <Radar
                            name="Player 2"
                            dataKey="player2"
                            stroke="#71717a"
                            fill="#71717a"
                            fillOpacity={0.25}
                          />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* SQL Query Inspector (When executed) */}
                {msg.sql_query && (
                  <div className="mt-4 pt-3 border-t border-zinc-800">
                    <button
                      onClick={() => setShowSql(prev => ({ ...prev, [index]: !prev[index] }))}
                      className="text-[11px] font-mono text-zinc-400 hover:text-white flex items-center gap-1"
                    >
                      <Code className="w-3 h-3" />
                      {showSql[index] ? 'Hide Executed SQL' : 'Inspect Executed SQL Query'}
                    </button>
                    {showSql[index] && (
                      <pre className="mt-2 p-3 bg-black border border-zinc-800 rounded text-[11px] font-mono text-emerald-400 overflow-x-auto">
                        {msg.sql_query}
                      </pre>
                    )}
                  </div>
                )}

              </div>
            </div>
          );
        })}

        {/* Loading Spinner Indicator */}
        {isLoading && (
          <div className="flex items-center gap-3 p-4 rounded-sm border border-zinc-800 bg-[#0a0a0a] max-w-md">
            <RefreshCw className="w-4 h-4 text-white animate-spin" />
            <div className="text-xs font-mono text-zinc-300 tracking-wider">
              LANGGRAPH ORCHESTRATING RETRIEVAL...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <div className="pt-4 border-t border-zinc-800">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything (e.g. 'Compare Bumrah and Starc in death overs' or 'What is the live score?')..."
            className="flex-1 bg-[#0a0a0a] border border-zinc-800 focus:border-white focus:outline-none rounded-sm px-4 py-3 text-sm text-white placeholder-zinc-500 font-sans"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="px-5 py-3 bg-white text-black font-mono font-bold text-xs uppercase tracking-wider rounded-sm hover:bg-zinc-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            <span>Execute</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
        <p className="text-[10px] font-mono text-zinc-400 mt-2 text-center">
          Pure deterministic SQL &bull; ChromaDB Semantic Vectors &bull; Live Telemetry Feed &bull; Hallucination-Guarded
        </p>
      </div>

    </div>
  );
}

