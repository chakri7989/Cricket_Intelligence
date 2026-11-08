import React, { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Activity, Cpu, Database, Flame, Menu, X, Users, Compass } from 'lucide-react';

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { name: 'Overview', path: '/' },
    { name: 'AI Analyst', path: '/chat', icon: Cpu },
    { name: 'Live Center', path: '/live', icon: Activity, live: true },
    { name: 'Player Studio', path: '/compare', icon: Users },
    { name: 'Historical Vault', path: '/vault', icon: Database },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#080808]/90 backdrop-blur-md border-b border-[#262626]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Brand Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-8 h-8 rounded-sm bg-white text-black flex items-center justify-center font-black tracking-tighter text-sm transition-transform group-hover:scale-105">
              CI
            </div>
            <div className="flex flex-col">
              <span className="text-white font-bold tracking-wider text-sm sm:text-base">
                CRICKET INTELLIGENCE
              </span>
              <span className="text-[10px] text-zinc-400 font-mono tracking-widest uppercase">
                AI Analytics Engine
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              return (
                <NavLink
                  key={link.path}
                  to={link.path}
                  end={link.path === '/'}
                  className={({ isActive }) =>
                    `px-3.5 py-1.5 rounded-sm text-xs font-mono uppercase tracking-wider transition-all flex items-center gap-1.5 ${
                      isActive
                        ? 'bg-white text-black font-semibold shadow-sm'
                        : 'text-zinc-400 hover:text-white hover:bg-zinc-900/60'
                    }`
                  }
                >
                  {Icon && <Icon className="w-3.5 h-3.5" />}
                  {link.name}
                  {link.live && (
                    <span className="flex h-2 w-2 relative ml-1">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>

          {/* Action CTA */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              to="/chat"
              className="px-4 py-1.5 rounded-sm bg-white text-black text-xs font-mono font-bold tracking-wider uppercase hover:bg-zinc-200 transition-colors shadow-sm"
            >
              Ask AI &rarr;
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-900 rounded-sm"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#262626] bg-[#0c0c0c] px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              end={link.path === '/'}
              onClick={() => setMobileMenuOpen(false)}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-sm text-xs font-mono uppercase tracking-wider ${
                  isActive
                    ? 'bg-white text-black font-semibold'
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
                }`
              }
            >
              <div className="flex items-center justify-between">
                <span>{link.name}</span>
                {link.live && (
                  <span className="px-1.5 py-0.5 text-[9px] bg-zinc-800 text-white rounded font-mono">LIVE</span>
                )}
              </div>
            </NavLink>
          ))}
          <div className="pt-2">
            <Link
              to="/chat"
              onClick={() => setMobileMenuOpen(false)}
              className="block w-full text-center py-2 bg-white text-black text-xs font-mono font-bold tracking-wider uppercase rounded-sm"
            >
              Launch AI Analyst
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}

