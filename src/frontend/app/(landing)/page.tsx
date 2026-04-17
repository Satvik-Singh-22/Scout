/**
 * Copyright 2026 The SCOUT Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use client';
import Link from 'next/link';
import { useState, useEffect, useRef } from 'react';

// ── Animated counter hook ─────────────────────────────────────────
function useCounter(end: number, duration = 1800, start = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!start) return;
    let startTime: number | null = null;
    const step = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      setCount(Math.floor(progress * end));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [end, duration, start]);
  return count;
}

// ── Stats row data ────────────────────────────────────────────────
const stats = [
  { value: 99, suffix: '.9%', label: 'Uptime SLA' },
  { value: 100, suffix: 'K+', label: 'Queries Served' },
  { value: 3, suffix: 'x', label: 'Faster Insights' },
  { value: 0, suffix: ' PII Leaks', label: 'Security Record' },
];

// ── Feature cards data ────────────────────────────────────────────
const features = [
  {
    icon: 'chat_bubble',
    title: 'Natural Language Queries',
    desc: 'Ask questions about your data in plain English. Scout translates your intent into precise SQL — no technical expertise needed.',
    color: '#635bff',
    bg: 'rgba(99,91,255,0.06)',
    border: 'rgba(99,91,255,0.18)',
  },
  {
    icon: 'schema',
    title: 'Multi-Database Support',
    desc: 'Connect PostgreSQL, MySQL, BigQuery, and more. Scout understands your schema and generates optimized queries automatically.',
    color: '#0ea5e9',
    bg: 'rgba(14,165,233,0.06)',
    border: 'rgba(14,165,233,0.18)',
  },
  {
    icon: 'visibility',
    title: 'Chain-of-Thought Transparency',
    desc: 'Every answer comes with a full reasoning trace. See exactly how Scout interpreted your query and which tables it joined.',
    color: '#8b5cf6',
    bg: 'rgba(139,92,246,0.06)',
    border: 'rgba(139,92,246,0.18)',
  },
  {
    icon: 'bar_chart',
    title: 'Instant Visualizations',
    desc: 'Scout automatically selects the best chart type for your data — bar, line, pie, scatter — rendered beautifully in seconds.',
    color: '#10b981',
    bg: 'rgba(16,185,129,0.06)',
    border: 'rgba(16,185,129,0.18)',
  },
  {
    icon: 'schedule',
    title: 'Scheduled Reports',
    desc: 'Set up recurring queries and receive automated summaries on a schedule. Stay informed without lifting a finger.',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.06)',
    border: 'rgba(245,158,11,0.18)',
  },
  {
    icon: 'notifications_active',
    title: 'Intelligent Alerts',
    desc: 'Define thresholds and get notified when data anomalies occur. Scout monitors your metrics and fires alerts proactively.',
    color: '#ef4444',
    bg: 'rgba(239,68,68,0.06)',
    border: 'rgba(239,68,68,0.18)',
  },
  {
    icon: 'shield_locked',
    title: 'Role-Based Governance',
    desc: 'Platform Admins control which tables each team can access. Fine-grained permissions ensure data stays compliant.',
    color: '#6366f1',
    bg: 'rgba(99,102,241,0.06)',
    border: 'rgba(99,102,241,0.18)',
  },
  {
    icon: 'groups',
    title: 'Team Collaboration',
    desc: 'Invite teammates, share query results, and collaborate on data insights — all within a single secure workspace.',
    color: '#ec4899',
    bg: 'rgba(236,72,153,0.06)',
    border: 'rgba(236,72,153,0.18)',
  },
  {
    icon: 'manage_accounts',
    title: 'Admin Governance Console',
    desc: 'A dedicated interface for platform admins to manage users, configure data sources, and audit all query activity.',
    color: '#14b8a6',
    bg: 'rgba(20,184,166,0.06)',
    border: 'rgba(20,184,166,0.18)',
  },
];

// ── How it works steps ────────────────────────────────────────────
const steps = [
  {
    step: '01',
    title: 'Connect Your Data',
    desc: 'Data Owners onboard their databases through the guided setup wizard. Scout securely maps your schema and makes it queryable instantly.',
    icon: 'storage',
    color: '#635bff',
  },
  {
    step: '02',
    title: 'Ask in Plain English',
    desc: 'Type any business question — "What were last month\'s top 10 products by revenue?" — and Scout writes the SQL for you.',
    icon: 'edit_note',
    color: '#8b5cf6',
  },
  {
    step: '03',
    title: 'Verify the Reasoning',
    desc: 'Review the full chain-of-thought: which tables were selected, how filters were applied, and why Scout made each decision.',
    icon: 'account_tree',
    color: '#0ea5e9',
  },
  {
    step: '04',
    title: 'Visualize & Share',
    desc: 'Results render as interactive charts. Export, schedule recurring reports, or set live alerts — all from one dashboard.',
    icon: 'insights',
    color: '#10b981',
  },
];

// ── Roles data ────────────────────────────────────────────────────
const roles = [
  {
    icon: 'manage_accounts',
    title: 'Platform Admin',
    desc: 'Complete governance over the entire platform. Manage user roles, approve data source connections, and audit every query across all teams.',
    color: '#635bff',
    features: ['User & Role Management', 'Data Access Governance', 'Full Query Audit Trail', 'Platform Configuration'],
  },
  {
    icon: 'database',
    title: 'Data Owner',
    desc: 'Onboard and manage your team\'s data sources. Configure which tables are accessible and ensure data quality before it reaches analysts.',
    color: '#0ea5e9',
    features: ['Database Onboarding', 'Schema Configuration', 'Table-Level Permissions', 'Data Quality Controls'],
  },
  {
    icon: 'person_search',
    title: 'Data Analyst',
    desc: 'Query your data conversationally without writing SQL. Explore insights, create scheduled reports, and collaborate with your team seamlessly.',
    color: '#10b981',
    features: ['Natural Language Queries', 'Interactive Visualizations', 'Scheduled Reports', 'Alert Configuration'],
  },
];

// ── Testimonials ──────────────────────────────────────────────────
const testimonials = [
  {
    quote: 'Scout cut our reporting cycle from two weeks to two hours. Our analysts spend time on insights now, not writing SQL.',
    name: 'Priya Mehta',
    role: 'Head of Analytics, FinTech Corp',
    avatar: 'PM',
    color: '#635bff',
  },
  {
    quote: 'The chain-of-thought transparency was a game-changer for our compliance team. We can now audit every data access in seconds.',
    name: 'Daniel Osei',
    role: 'CTO, Logistics Ventures',
    avatar: 'DO',
    color: '#10b981',
  },
  {
    quote: 'Role-based governance means we sleep better. Data Owners control exactly what\'s exposed without slowing down the analysts.',
    name: 'Sarah Lin',
    role: 'VP Engineering, MedData Inc',
    avatar: 'SL',
    color: '#f59e0b',
  },
];

// ── Live Query Demo Component ─────────────────────────────────────
function QueryDemo() {
  const queries = [
    { q: 'What are the top 5 products by revenue this quarter?', tag: 'Revenue Analysis' },
    { q: 'Show me monthly active users over the last 12 months', tag: 'User Metrics' },
    { q: 'Which regions had the highest churn rate last month?', tag: 'Churn Analysis' },
    { q: 'Compare sales performance across all sales reps this week', tag: 'Sales Report' },
  ];
  const [active, setActive] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setActive(prev => (prev + 1) % queries.length);
        setVisible(true);
      }, 400);
    }, 3200);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid rgba(99,91,255,0.12)',
        borderRadius: '16px',
        padding: '24px',
        boxShadow: '0 8px 40px rgba(99,91,255,0.08)',
      }}
    >
      {/* Terminal header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444' }} />
        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b' }} />
        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#22c55e' }} />
        <span
          style={{
            marginLeft: '8px',
            fontSize: '11px',
            color: '#9ca3af',
            fontFamily: 'var(--font-inter)',
            letterSpacing: '0.05em',
          }}
        >
          SCOUT QUERY ENGINE
        </span>
        <span
          style={{
            marginLeft: 'auto',
            fontSize: '10px',
            color: '#635bff',
            background: 'rgba(99,91,255,0.08)',
            border: '1px solid rgba(99,91,255,0.2)',
            padding: '2px 8px',
            borderRadius: '20px',
            fontFamily: 'var(--font-inter)',
          }}
        >
          LIVE
        </span>
      </div>

      {/* Query input */}
      <div
        style={{
          background: '#f9f8ff',
          border: '1px solid rgba(99,91,255,0.15)',
          borderRadius: '10px',
          padding: '14px 16px',
          marginBottom: '16px',
          transition: 'opacity 0.3s ease',
          opacity: visible ? 1 : 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#635bff' }}>edit_note</span>
          <span style={{ fontSize: '12px', color: '#9ca3af', fontFamily: 'var(--font-inter)', fontWeight: 600, letterSpacing: '0.05em' }}>
            YOUR QUESTION
          </span>
        </div>
        <p style={{ margin: 0, fontSize: '14px', color: '#1f2937', fontFamily: 'var(--font-manrope)', fontWeight: 500, lineHeight: '1.5' }}>
          {queries[active].q}
        </p>
        <span
          style={{
            display: 'inline-block',
            marginTop: '8px',
            fontSize: '10px',
            color: '#635bff',
            background: 'rgba(99,91,255,0.08)',
            padding: '2px 8px',
            borderRadius: '10px',
            fontFamily: 'var(--font-inter)',
          }}
        >
          {queries[active].tag}
        </span>
      </div>

      {/* Reasoning trace */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {[
          { label: 'Schema Analysis', status: 'complete', color: '#10b981' },
          { label: 'SQL Generation', status: 'complete', color: '#10b981' },
          { label: 'Query Execution', status: 'complete', color: '#10b981' },
          { label: 'Chart Selection', status: 'processing', color: '#635bff' },
        ].map((item, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 12px',
              background: item.status === 'processing' ? 'rgba(99,91,255,0.04)' : 'transparent',
              border: item.status === 'processing' ? '1px solid rgba(99,91,255,0.12)' : '1px solid transparent',
              borderRadius: '8px',
            }}
          >
            <span
              className="material-symbols-outlined"
              style={{ fontSize: '16px', color: item.color }}
            >
              {item.status === 'complete' ? 'check_circle' : 'sync'}
            </span>
            <span style={{ fontSize: '12px', color: '#4b5563', fontFamily: 'var(--font-inter)', fontWeight: 500 }}>
              {item.label}
            </span>
            {item.status === 'processing' && (
              <span style={{ marginLeft: 'auto', display: 'flex', gap: '3px', alignItems: 'center' }}>
                {[0, 1, 2].map((d) => (
                  <span
                    key={d}
                    style={{
                      width: '4px',
                      height: '4px',
                      borderRadius: '50%',
                      background: '#635bff',
                      animation: `pulse 1.2s ${d * 0.2}s infinite`,
                    }}
                  />
                ))}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main Landing Page ─────────────────────────────────────────────
export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [statsVisible, setStatsVisible] = useState(false);
  const statsRef = useRef<HTMLDivElement>(null);
  const heroRef = useRef<HTMLDivElement>(null);

  // Navbar scroll effect
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Mouse parallax for hero
  useEffect(() => {
    const handleMouse = (e: MouseEvent) => {
      if (heroRef.current) {
        const rect = heroRef.current.getBoundingClientRect();
        setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
      }
    };
    window.addEventListener('mousemove', handleMouse);
    return () => window.removeEventListener('mousemove', handleMouse);
  }, []);

  // Intersection observer for stats counter
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setStatsVisible(true); },
      { threshold: 0.4 }
    );
    if (statsRef.current) observer.observe(statsRef.current);
    return () => observer.disconnect();
  }, []);

  const c0 = useCounter(stats[0].value, 1600, statsVisible);
  const c1 = useCounter(stats[1].value, 1600, statsVisible);
  const c2 = useCounter(stats[2].value, 1400, statsVisible);
  const c3 = useCounter(stats[3].value, 1000, statsVisible);
  const counterValues = [c0, c1, c2, c3];

  return (
    <div style={{ background: '#f8f9ff', minHeight: '100vh', color: '#191c1d', fontFamily: 'var(--font-manrope), sans-serif', overflowX: 'hidden' }}>

      {/* ── Inline keyframes ── */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.3; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1.2); }
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(24px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes floatY {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        @keyframes scrollBounce {
          0%, 100% { transform: translateX(-50%) translateY(0); }
          50% { transform: translateX(-50%) translateY(8px); }
        }
        @keyframes shimmer {
          0% { background-position: -200% center; }
          100% { background-position: 200% center; }
        }
        .fade-up { animation: fadeUp 0.7s ease both; }
        .fade-up-d1 { animation: fadeUp 0.7s 0.1s ease both; }
        .fade-up-d2 { animation: fadeUp 0.7s 0.2s ease both; }
        .fade-up-d3 { animation: fadeUp 0.7s 0.3s ease both; }
        .fade-up-d4 { animation: fadeUp 0.7s 0.4s ease both; }
        .feature-card:hover { transform: translateY(-5px) !important; box-shadow: 0 16px 48px rgba(99,91,255,0.1), 0 0 0 1px rgba(99,91,255,0.1) !important; }
        .feature-card { transition: transform 0.3s ease, box-shadow 0.3s ease; }
        .step-card:hover { transform: translateY(-3px); }
        .step-card { transition: transform 0.3s ease; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(99,91,255,0.4) !important; }
        .btn-primary { transition: all 0.2s ease; }
        .btn-secondary:hover { border-color: rgba(99,91,255,0.4) !important; color: #635bff !important; }
        .btn-secondary { transition: all 0.2s ease; }
        .role-card:hover { box-shadow: 0 12px 40px rgba(0,0,0,0.08) !important; transform: translateY(-3px); }
        .role-card { transition: all 0.3s ease; }
        .nav-link:hover { color: #635bff !important; }
        .nav-link { transition: color 0.2s; }
        .testimonial-card:hover { box-shadow: 0 12px 40px rgba(99,91,255,0.1) !important; }
        .testimonial-card { transition: box-shadow 0.3s ease; }
      `}</style>

      {/* ══════════════════════════════════════════════════════════ */}
      {/*  NAVBAR                                                    */}
      {/* ══════════════════════════════════════════════════════════ */}
      <nav
        style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
          background: scrolled ? 'rgba(255,255,255,0.92)' : 'rgba(255,255,255,0.6)',
          backdropFilter: 'blur(20px)',
          borderBottom: scrolled ? '1px solid rgba(99,91,255,0.12)' : '1px solid transparent',
          padding: '0 40px',
          height: '64px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          transition: 'all 0.3s ease',
          boxShadow: scrolled ? '0 4px 24px rgba(99,91,255,0.07)' : 'none',
        }}
      >
        {/* Logo */}
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', textDecoration: 'none' }}>
          <img src="/scout_icon.svg" alt="Scout Logo" style={{ width: '32px', height: '32px', objectFit: 'contain' }} />
          <span style={{ fontSize: '18px', fontWeight: 700, color: '#111827', letterSpacing: '-0.02em', fontFamily: 'var(--font-manrope)' }}>Scout</span>
          <span
            style={{
              fontSize: '10px', color: '#635bff',
              background: 'rgba(99,91,255,0.08)', border: '1px solid rgba(99,91,255,0.2)',
              padding: '2px 8px', borderRadius: '20px',
              fontFamily: 'var(--font-inter)', fontWeight: 600, letterSpacing: '0.06em',
            }}
          >
            ENTERPRISE
          </span>
        </Link>

        {/* Nav links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          {['Features', 'How It Works', 'Roles', 'Security'].map((label) => (
            <a
              key={label}
              href={`#${label.toLowerCase().replace(/\s+/g, '-')}`}
              className="nav-link"
              style={{ color: '#6b7280', fontSize: '14px', fontWeight: 500, textDecoration: 'none', fontFamily: 'var(--font-manrope)' }}
            >
              {label}
            </a>
          ))}
        </div>

        {/* CTAs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Link
            href="/login"
            style={{
              color: '#374151', fontSize: '14px', fontWeight: 500,
              textDecoration: 'none', padding: '8px 16px',
              border: '1px solid #e5e7eb', borderRadius: '8px',
              fontFamily: 'var(--font-manrope)', transition: 'all 0.2s',
            }}
            className="btn-secondary"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="btn-primary"
            style={{
              background: 'linear-gradient(135deg, #635bff 0%, #4f46e5 100%)',
              color: 'white', fontSize: '14px', fontWeight: 600,
              textDecoration: 'none', padding: '8px 20px',
              borderRadius: '8px', fontFamily: 'var(--font-manrope)',
              boxShadow: '0 4px 14px rgba(99,91,255,0.28)',
              display: 'flex', alignItems: 'center', gap: '6px',
            }}
          >
            Get Started
            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>arrow_forward</span>
          </Link>
        </div>
      </nav>

      {/* ══════════════════════════════════════════════════════════ */}
      {/*  HERO SECTION                                              */}
      {/* ══════════════════════════════════════════════════════════ */}
      <section
        ref={heroRef}
        style={{
          minHeight: '100vh', display: 'flex', alignItems: 'center',
          paddingTop: '64px', position: 'relative', overflow: 'hidden',
        }}
      >
        {/* Background grid */}
        <div
          style={{
            position: 'absolute', inset: 0, zIndex: 0,
            backgroundImage: 'linear-gradient(rgba(99,91,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(99,91,255,0.04) 1px, transparent 1px)',
            backgroundSize: '56px 56px',
          }}
        />
        {/* Gradient orbs */}
        <div style={{ position: 'absolute', top: '12%', left: '5%', width: '560px', height: '560px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(99,91,255,0.09) 0%, transparent 70%)', filter: 'blur(48px)', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: '5%', right: '10%', width: '440px', height: '440px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(79,70,229,0.07) 0%, transparent 70%)', filter: 'blur(48px)', pointerEvents: 'none' }} />
        {/* Mouse-follow glow */}
        <div style={{
          position: 'absolute', width: '320px', height: '320px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99,91,255,0.06) 0%, transparent 70%)',
          filter: 'blur(32px)', pointerEvents: 'none', zIndex: 0,
          transform: `translate(${mousePos.x - 160}px, ${mousePos.y - 160}px)`,
          transition: 'transform 0.4s ease',
        }} />

        <div
          style={{
            maxWidth: '1320px', margin: '0 auto', padding: '0 40px',
            width: '100%', display: 'grid', gridTemplateColumns: '1fr 1fr',
            gap: '80px', alignItems: 'center', position: 'relative', zIndex: 1,
          }}
        >
          {/* LEFT: Hero copy */}
          <div>
            {/* Badge */}
            <div
              className="fade-up"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '8px',
                background: 'rgba(99,91,255,0.07)', border: '1px solid rgba(99,91,255,0.18)',
                borderRadius: '20px', padding: '6px 14px', marginBottom: '28px',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '14px', color: '#635bff' }}>auto_awesome</span>
              <span style={{ fontSize: '12px', color: '#635bff', fontFamily: 'var(--font-inter)', fontWeight: 600 }}>
                Enterprise AI Data Intelligence
              </span>
            </div>

            {/* Heading */}
            <h1
              className="fade-up-d1"
              style={{
                fontSize: 'clamp(40px, 5vw, 60px)', fontWeight: 700,
                color: '#0f172a', lineHeight: '1.1', letterSpacing: '-0.03em',
                margin: '0 0 20px', fontFamily: 'var(--font-manrope)',
              }}
            >
              Query your data with{' '}
              <span
                style={{
                  background: 'linear-gradient(135deg, #635bff 0%, #4f46e5 40%, #7c3aed 100%)',
                  WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}
              >
                plain English
              </span>
            </h1>

            {/* Subheading */}
            <p
              className="fade-up-d2"
              style={{
                fontSize: '18px', color: '#6b7280', lineHeight: '1.75',
                margin: '0 0 40px', maxWidth: '500px', fontFamily: 'var(--font-manrope)',
              }}
            >
              Scout is an enterprise-grade AI platform that transforms natural language into precise SQL queries — with full transparency, role-based governance, and zero data leakage.
            </p>

            {/* CTAs */}
            <div className="fade-up-d3" style={{ display: 'flex', gap: '14px', alignItems: 'center', marginBottom: '48px' }}>
              <Link
                href="/register"
                className="btn-primary"
                style={{
                  background: 'linear-gradient(135deg, #635bff 0%, #4f46e5 100%)',
                  color: 'white', fontWeight: 600, padding: '14px 28px',
                  borderRadius: '10px', textDecoration: 'none',
                  display: 'flex', alignItems: 'center', gap: '8px',
                  fontFamily: 'var(--font-manrope)', fontSize: '15px',
                  boxShadow: '0 4px 24px rgba(99,91,255,0.32)',
                }}
              >
                Start for Free
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>arrow_forward</span>
              </Link>
              <Link
                href="/login"
                className="btn-secondary"
                style={{
                  background: '#ffffff', color: '#374151',
                  fontWeight: 500, padding: '14px 28px', borderRadius: '10px',
                  textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px',
                  fontFamily: 'var(--font-manrope)', fontSize: '15px',
                  border: '1px solid #e5e7eb',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                }}
              >
                Sign In to Dashboard
              </Link>
            </div>

            {/* Trust badges */}
            <div className="fade-up-d4" style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
              {['RBAC Governance', 'Audit Trail', 'Zero PII', 'SOC 2 Ready'].map((badge) => (
                <div key={badge} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '14px', color: '#059669' }}>check_circle</span>
                  <span style={{ fontSize: '12px', color: '#6b7280', fontFamily: 'var(--font-inter)', fontWeight: 500 }}>{badge}</span>
                </div>
              ))}
            </div>
          </div>

          {/* RIGHT: Live query demo */}
          <div className="fade-up-d2" style={{ animation: 'floatY 5s ease-in-out infinite' }}>
            <QueryDemo />

            {/* Mini stats under demo card */}
            <div
              style={{
                display: 'flex', gap: '12px', marginTop: '16px',
              }}
            >
              {[
                { icon: 'bolt', label: 'Avg. response', value: '<2s', color: '#f59e0b' },
                { icon: 'security', label: 'Queries encrypted', value: '100%', color: '#10b981' },
                { icon: 'speed', label: 'Query accuracy', value: '99.8%', color: '#635bff' },
              ].map((s) => (
                <div
                  key={s.label}
                  style={{
                    flex: 1, background: '#ffffff', border: '1px solid #f3f4f6',
                    borderRadius: '12px', padding: '12px 16px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                    display: 'flex', flexDirection: 'column', gap: '4px',
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '18px', color: s.color }}>{s.icon}</span>
                  <span style={{ fontSize: '16px', fontWeight: 700, color: '#111827', fontFamily: 'var(--font-manrope)' }}>{s.value}</span>
                  <span style={{ fontSize: '10px', color: '#9ca3af', fontFamily: 'var(--font-inter)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div
          style={{
            position: 'absolute', bottom: '32px', left: '50%',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px',
            animation: 'scrollBounce 2s ease-in-out infinite', zIndex: 1,
          }}
        >
          <span style={{ fontSize: '10px', color: '#9ca3af', letterSpacing: '0.12em', fontFamily: 'var(--font-inter)', fontWeight: 600 }}>SCROLL</span>
          <span className="material-symbols-outlined" style={{ fontSize: '20px', color: 'rgba(99,91,255,0.4)' }}>keyboard_arrow_down</span>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════ */}
      {/*  STATS STRIP                                               */}
      {/* ══════════════════════════════════════════════════════════ */}
      <section
        ref={statsRef}
        style={{
          background: '#ffffff', borderTop: '1px solid #f3f4f6',
          borderBottom: '1px solid #f3f4f6', padding: '60px 40px',
        }}
      >
        <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '32px' }}>
          {stats.map((s, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div
                style={{
                  fontSize: '40px', fontWeight: 700, color: '#0f172a',
                  fontFamily: 'var(--font-manrope)', lineHeight: 1,
                }}
              >
                {counterValues[i]}{s.suffix}
              </div>
              <div style={{ fontSize: '13px', color: '#9ca3af', marginTop: '6px', fontFamily: 'var(--font-inter)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                {s.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════ */}
      {/*  FEATURES GRID                                             */}
      {/* ══════════════════════════════════════════════════════════ */}
      <section id="features" style={{ padding: '100px 40px', background: '#f8f9ff' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>

          {/* Section header */}
          <div style={{ textAlign: 'center', marginBottom: '64px' }}>
            <div
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '8px',
                background: 'rgba(99,91,255,0.07)', border: '1px solid rgba(99,91,255,0.18)',
                borderRadius: '20px', padding: '5px 14px', marginBottom: '20px',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '13px', color: '#635bff' }}>layers</span>
              <span style={{ fontSize: '11px', color: '#635bff', fontFamily: 'var(--font-inter)', fontWeight: 600, letterSpacing: '0.06em' }}>THE PLATFORM</span>
            </div>
            <h2
              style={{
                fontSize: '42px', fontWeight: 700, color: '#0f172a',
                fontFamily: 'var(--font-manrope)', letterSpacing: '-0.02em',
                margin: '0 0 16px',
              }}
            >
              Everything you need for data intelligence
            </h2>
            <p style={{ fontSize: '17px', color: '#6b7280', maxWidth: '560px', margin: '0 auto', lineHeight: '1.7', fontFamily: 'var(--font-manrope)' }}>
              Scout brings together natural language processing, query generation, visualisation, and governance into one cohesive platform.
            </p>
          </div>

          {/* 3-column grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
            {features.map((f, i) => (
              <div
                key={i}
                className="feature-card"
                style={{
                  background: '#ffffff', border: '1px solid #f3f4f6',
                  borderRadius: '16px', padding: '28px 28px 32px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                }}
              >
                <div
                  style={{
                    width: '44px', height: '44px', borderRadius: '12px',
                    background: f.bg, border: `1px solid ${f.border}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginBottom: '18px',
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '22px', color: f.color }}>{f.icon}</span>
                </div>
                <h3
                  style={{
                    margin: '0 0 10px', fontSize: '16px', fontWeight: 600,
                    color: '#111827', fontFamily: 'var(--font-manrope)',
                  }}
                >
                  {f.title}
                </h3>
                <p style={{ margin: 0, fontSize: '14px', color: '#6b7280', lineHeight: '1.7', fontFamily: 'var(--font-manrope)' }}>
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════ */}
      {/*  HOW IT WORKS                                              */}
      {/* ══════════════════════════════════════════════════════════ */}
      <section id="how-it-works" style={{ padding: '100px 40px', background: '#ffffff' }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>

          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '72px' }}>
            <div
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '8px',
                background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)',
                borderRadius: '20px', padding: '5px 14px', marginBottom: '20px',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '13px', color: '#10b981' }}>route</span>
              <span style={{ fontSize: '11px', color: '#10b981', fontFamily: 'var(--font-inter)', fontWeight: 600, letterSpacing: '0.06em' }}>THE WORKFLOW</span>
            </div>
            <h2
              style={{
                fontSize: '42px', fontWeight: 700, color: '#0f172a',
                fontFamily: 'var(--font-manrope)', letterSpacing: '-0.02em', margin: '0 0 16px',
              }}
            >
              From question to insight in seconds
            </h2>
            <p style={{ fontSize: '17px', color: '#6b7280', maxWidth: '520px', margin: '0 auto', lineHeight: '1.7', fontFamily: 'var(--font-manrope)' }}>
              Scout's four-step pipeline is designed to be fast, transparent, and verifiable at every stage.
            </p>
          </div>

          {/* Steps */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px', position: 'relative' }}>
            {/* Connecting line */}
            <div
              style={{
                position: 'absolute', top: '40px', left: 'calc(12.5% + 22px)',
                right: 'calc(12.5% + 22px)', height: '2px',
                background: 'linear-gradient(90deg, #635bff, #4f46e5, #0ea5e9, #10b981)',
                pointerEvents: 'none', zIndex: 0, opacity: 0.25,
              }}
            />
            {steps.map((s, i) => (
              <div
                key={i}
                className="step-card"
                style={{
                  background: '#fafaff', border: '1px solid rgba(99,91,255,0.08)',
                  borderRadius: '16px', padding: '28px 24px',
                  textAlign: 'center', position: 'relative', zIndex: 1,
                  boxShadow: '0 4px 16px rgba(0,0,0,0.04)',
                }}
              >
                {/* Step number */}
                <div
                  style={{
                    width: '44px', height: '44px', borderRadius: '50%',
                    background: `${s.color}12`, border: `2px solid ${s.color}30`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 16px',
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '22px', color: s.color }}>{s.icon}</span>
                </div>
                <div
                  style={{
                    fontSize: '10px', color: s.color, fontFamily: 'var(--font-inter)',
                    fontWeight: 700, letterSpacing: '0.1em', marginBottom: '8px',
                  }}
                >
                  STEP {s.step}
                </div>
                <h3
                  style={{
                    margin: '0 0 10px', fontSize: '15px', fontWeight: 600,
                    color: '#111827', fontFamily: 'var(--font-manrope)',
                  }}
                >
                  {s.title}
                </h3>
                <p style={{ margin: 0, fontSize: '13px', color: '#6b7280', lineHeight: '1.65', fontFamily: 'var(--font-manrope)' }}>
                  {s.desc}
                </p>
              </div>
            ))}
          </div>

          {/* Bottom CTA */}
          <div style={{ textAlign: 'center', marginTop: '56px' }}>
            <Link
              href="/register"
              className="btn-primary"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '8px',
                background: 'linear-gradient(135deg, #635bff, #4f46e5)',
                color: 'white', padding: '14px 32px', borderRadius: '10px',
                textDecoration: 'none', fontFamily: 'var(--font-manrope)',
                fontWeight: 600, fontSize: '15px',
                boxShadow: '0 4px 20px rgba(99,91,255,0.3)',
              }}
            >
              Try It Now — Free
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>arrow_forward</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════ */}
      {/*  ROLES SECTION                                             */}
      {/* ══════════════════════════════════════════════════════════ */}
      <section id="roles" style={{ padding: '100px 40px', background: '#f8f9ff' }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>

          <div style={{ textAlign: 'center', marginBottom: '64px' }}>
            <div
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '8px',
                background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.2)',
                borderRadius: '20px', padding: '5px 14px', marginBottom: '20px',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '13px', color: '#f59e0b' }}>badge</span>
              <span style={{ fontSize: '11px', color: '#f59e0b', fontFamily: 'var(--font-inter)', fontWeight: 600, letterSpacing: '0.06em' }}>ROLE-BASED ACCESS</span>
            </div>
            <h2
              style={{
                fontSize: '42px', fontWeight: 700, color: '#0f172a',
                fontFamily: 'var(--font-manrope)', letterSpacing: '-0.02em', margin: '0 0 16px',
              }}
            >
              Built for every member of your team
            </h2>
            <p style={{ fontSize: '17px', color: '#6b7280', maxWidth: '540px', margin: '0 auto', lineHeight: '1.7', fontFamily: 'var(--font-manrope)' }}>
              Scout's three-tier role model ensures the right people have the right access — with zero overlap or data leakage.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
            {roles.map((role, i) => (
              <div
                key={i}
                className="role-card"
                style={{
                  background: '#ffffff', border: '1px solid #f3f4f6',
                  borderRadius: '20px', padding: '36px 32px',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.04)',
                }}
              >
                {/* Icon */}
                <div
                  style={{
                    width: '52px', height: '52px', borderRadius: '14px',
                    background: `${role.color}10`, border: `1px solid ${role.color}25`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginBottom: '20px',
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '26px', color: role.color }}>{role.icon}</span>
                </div>
                <h3
                  style={{
                    margin: '0 0 12px', fontSize: '18px', fontWeight: 700,
                    color: '#111827', fontFamily: 'var(--font-manrope)',
                  }}
                >
                  {role.title}
                </h3>
                <p style={{ margin: '0 0 24px', fontSize: '14px', color: '#6b7280', lineHeight: '1.7', fontFamily: 'var(--font-manrope)' }}>
                  {role.desc}
                </p>
                {/* Feature list */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {role.features.map((feat) => (
                    <div key={feat} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="material-symbols-outlined" style={{ fontSize: '16px', color: role.color }}>check_circle</span>
                      <span style={{ fontSize: '13px', color: '#374151', fontFamily: 'var(--font-manrope)', fontWeight: 500 }}>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════ */}
      {/*  SECURITY SECTION                                          */}
      {/* ══════════════════════════════════════════════════════════ */}
      <section id="security" style={{ padding: '100px 40px', background: '#ffffff' }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '80px', alignItems: 'center' }}>

          {/* Left copy */}
          <div>
            <div
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '8px',
                background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.18)',
                borderRadius: '20px', padding: '5px 14px', marginBottom: '20px',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '13px', color: '#ef4444' }}>security</span>
              <span style={{ fontSize: '11px', color: '#ef4444', fontFamily: 'var(--font-inter)', fontWeight: 600, letterSpacing: '0.06em' }}>ENTERPRISE SECURITY</span>
            </div>
            <h2
              style={{
                fontSize: '38px', fontWeight: 700, color: '#0f172a',
                fontFamily: 'var(--font-manrope)', letterSpacing: '-0.02em', margin: '0 0 16px',
              }}
            >
              Bank-grade security at every layer
            </h2>
            <p style={{ fontSize: '16px', color: '#6b7280', lineHeight: '1.75', margin: '0 0 32px', fontFamily: 'var(--font-manrope)' }}>
              Scout is built with enterprise compliance in mind. Every query is logged, every access is permissioned, and no PII ever reaches the AI layer.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {[
                { icon: 'lock', title: 'End-to-End Encryption', desc: 'All data in transit and at rest is encrypted using AES-256.', color: '#635bff' },
                { icon: 'gpp_good', title: 'Zero-PII Architecture', desc: 'Personally identifiable data is stripped before reaching the AI model.', color: '#10b981' },
                { icon: 'receipt_long', title: 'Immutable Audit Trail', desc: 'Every query, user action, and data access is logged and tamper-proof.', color: '#f59e0b' },
                { icon: 'admin_panel_settings', title: 'Granular RBAC', desc: 'Table-level permissions controlled by your Platform Admins.', color: '#0ea5e9' },
              ].map((item) => (
                <div
                  key={item.title}
                  style={{
                    display: 'flex', alignItems: 'flex-start', gap: '14px',
                    padding: '16px 18px', background: '#fafaff',
                    border: '1px solid rgba(99,91,255,0.08)', borderRadius: '12px',
                  }}
                >
                  <div
                    style={{
                      width: '36px', height: '36px', borderRadius: '10px',
                      background: `${item.color}12`, border: `1px solid ${item.color}25`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                    }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '18px', color: item.color }}>{item.icon}</span>
                  </div>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: 600, color: '#111827', marginBottom: '3px', fontFamily: 'var(--font-manrope)' }}>{item.title}</div>
                    <div style={{ fontSize: '13px', color: '#6b7280', fontFamily: 'var(--font-manrope)' }}>{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: visual card */}
          <div>
            <div
              style={{
                background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)',
                borderRadius: '20px', padding: '36px',
                boxShadow: '0 24px 64px rgba(99,91,255,0.2)',
                border: '1px solid rgba(99,91,255,0.2)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '28px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px rgba(16,185,129,0.6)' }} />
                <span style={{ fontSize: '11px', color: '#10b981', fontFamily: 'var(--font-inter)', fontWeight: 600, letterSpacing: '0.1em' }}>SECURITY MONITOR · LIVE</span>
              </div>

              {[
                { event: 'Query executed by analyst@company.com', time: '0s ago', status: 'allowed', color: '#10b981' },
                { event: 'Table `users_pii` access denied: insufficient role', time: '12s ago', status: 'blocked', color: '#ef4444' },
                { event: 'Schema change detected — cache invalidated', time: '45s ago', status: 'info', color: '#f59e0b' },
                { event: 'Admin granted access to `orders` table', time: '2m ago', status: 'allowed', color: '#10b981' },
                { event: 'PII filter applied: 3 fields stripped from result', time: '3m ago', status: 'info', color: '#0ea5e9' },
              ].map((log, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '12px',
                    padding: '10px 12px',
                    background: i === 0 ? 'rgba(255,255,255,0.05)' : 'transparent',
                    borderRadius: '8px', marginBottom: '4px',
                  }}
                >
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: log.color, flexShrink: 0, boxShadow: `0 0 6px ${log.color}` }} />
                  <span style={{ flex: 1, fontSize: '12px', color: '#d1d5db', fontFamily: 'var(--font-inter)', lineHeight: '1.4' }}>{log.event}</span>
                  <span style={{ fontSize: '10px', color: '#6b7280', fontFamily: 'var(--font-inter)', flexShrink: 0 }}>{log.time}</span>
                </div>
              ))}

              <div
                style={{
                  marginTop: '20px', padding: '12px 16px',
                  background: 'rgba(99,91,255,0.12)', border: '1px solid rgba(99,91,255,0.25)',
                  borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '10px',
                }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#a5b4fc' }}>verified_user</span>
                <span style={{ fontSize: '13px', color: '#c7d2fe', fontFamily: 'var(--font-inter)', fontWeight: 500 }}>All systems compliant · Last audit: 0 violations</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════ */}
      {/*  TESTIMONIALS                                              */}
      {/* ══════════════════════════════════════════════════════════ */}
      <section style={{ padding: '100px 40px', background: '#f8f9ff' }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>

          <div style={{ textAlign: 'center', marginBottom: '64px' }}>
            <div
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '8px',
                background: 'rgba(139,92,246,0.07)', border: '1px solid rgba(139,92,246,0.2)',
                borderRadius: '20px', padding: '5px 14px', marginBottom: '20px',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '13px', color: '#8b5cf6' }}>star</span>
              <span style={{ fontSize: '11px', color: '#8b5cf6', fontFamily: 'var(--font-inter)', fontWeight: 600, letterSpacing: '0.06em' }}>FROM OUR USERS</span>
            </div>
            <h2
              style={{
                fontSize: '42px', fontWeight: 700, color: '#0f172a',
                fontFamily: 'var(--font-manrope)', letterSpacing: '-0.02em', margin: 0,
              }}
            >
              Trusted by data-driven teams
            </h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
            {testimonials.map((t, i) => (
              <div
                key={i}
                className="testimonial-card"
                style={{
                  background: '#ffffff', border: '1px solid #f3f4f6',
                  borderRadius: '16px', padding: '32px',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.04)',
                }}
              >
                {/* Stars */}
                <div style={{ display: 'flex', gap: '3px', marginBottom: '16px' }}>
                  {[...Array(5)].map((_, s) => (
                    <span key={s} className="material-symbols-outlined" style={{ fontSize: '16px', color: '#f59e0b', fontVariationSettings: "'FILL' 1" }}>star</span>
                  ))}
                </div>
                <blockquote style={{ margin: '0 0 24px', fontSize: '15px', color: '#374151', lineHeight: '1.7', fontFamily: 'var(--font-manrope)', fontStyle: 'italic' }}>
                  "{t.quote}"
                </blockquote>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '40px', height: '40px', borderRadius: '50%',
                      background: `${t.color}15`, border: `2px solid ${t.color}30`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '13px', fontWeight: 700, color: t.color,
                      fontFamily: 'var(--font-manrope)',
                    }}
                  >
                    {t.avatar}
                  </div>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: 600, color: '#111827', fontFamily: 'var(--font-manrope)' }}>{t.name}</div>
                    <div style={{ fontSize: '12px', color: '#9ca3af', fontFamily: 'var(--font-inter)' }}>{t.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════ */}
      {/*  CTA SECTION                                               */}
      {/* ══════════════════════════════════════════════════════════ */}
      <section
        style={{
          padding: '120px 40px', background: '#ffffff',
          position: 'relative', overflow: 'hidden',
        }}
      >
        {/* Background glow */}
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: '700px', height: '400px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(99,91,255,0.06) 0%, transparent 70%)', filter: 'blur(60px)', pointerEvents: 'none' }} />

        <div style={{ maxWidth: '700px', margin: '0 auto', textAlign: 'center', position: 'relative' }}>
          <div
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '8px',
              background: 'rgba(99,91,255,0.07)', border: '1px solid rgba(99,91,255,0.18)',
              borderRadius: '20px', padding: '5px 14px', marginBottom: '24px',
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '13px', color: '#635bff' }}>rocket_launch</span>
            <span style={{ fontSize: '11px', color: '#635bff', fontFamily: 'var(--font-inter)', fontWeight: 600, letterSpacing: '0.06em' }}>GET STARTED TODAY</span>
          </div>

          <h2
            style={{
              fontSize: '52px', fontWeight: 700, color: '#0f172a',
              fontFamily: 'var(--font-manrope)', letterSpacing: '-0.03em',
              margin: '0 0 20px', lineHeight: '1.1',
            }}
          >
            Ready to unlock your<br />
            <span
              style={{
                background: 'linear-gradient(135deg, #635bff, #4f46e5, #7c3aed)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              data's potential?
            </span>
          </h2>
          <p style={{ fontSize: '17px', color: '#6b7280', margin: '0 0 44px', lineHeight: '1.75', fontFamily: 'var(--font-manrope)' }}>
            Join teams already using Scout to answer business questions in seconds — not days. Set up in minutes, no SQL expertise required.
          </p>

          <div style={{ display: 'flex', gap: '14px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link
              href="/register"
              className="btn-primary"
              style={{
                background: 'linear-gradient(135deg, #635bff, #4f46e5)',
                color: 'white', padding: '16px 36px', borderRadius: '12px',
                textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px',
                fontFamily: 'var(--font-manrope)', fontWeight: 600, fontSize: '16px',
                boxShadow: '0 4px 24px rgba(99,91,255,0.35)',
              }}
            >
              Create Free Account
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>arrow_forward</span>
            </Link>
            <Link
              href="/login"
              className="btn-secondary"
              style={{
                background: '#f8f9ff', color: '#374151',
                padding: '16px 28px', borderRadius: '12px',
                textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px',
                fontFamily: 'var(--font-manrope)', fontWeight: 500, fontSize: '16px',
                border: '1px solid #e5e7eb',
              }}
            >
              Sign In to Dashboard
            </Link>
          </div>

          {/* Social proof */}
          <p style={{ marginTop: '32px', fontSize: '13px', color: '#9ca3af', fontFamily: 'var(--font-inter)' }}>
            No credit card required · Free tier available · Cancel anytime
          </p>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════ */}
      {/*  FOOTER                                                    */}
      {/* ══════════════════════════════════════════════════════════ */}
      <footer
        style={{
          borderTop: '1px solid #f3f4f6', padding: '40px',
          background: '#fafaff',
        }}
      >
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr 1fr', gap: '48px', marginBottom: '48px' }}>

            {/* Brand */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <img src="/scout_icon.svg" alt="Scout Logo" style={{ width: '28px', height: '28px', objectFit: 'contain' }} />
                <span style={{ fontSize: '17px', fontWeight: 700, color: '#111827', fontFamily: 'var(--font-manrope)' }}>Scout</span>
                <span style={{ fontSize: '10px', color: '#635bff', background: 'rgba(99,91,255,0.08)', border: '1px solid rgba(99,91,255,0.18)', padding: '1px 7px', borderRadius: '12px', fontFamily: 'var(--font-inter)', fontWeight: 600 }}>ENTERPRISE</span>
              </div>
              <p style={{ margin: 0, fontSize: '14px', color: '#6b7280', lineHeight: '1.7', maxWidth: '260px', fontFamily: 'var(--font-manrope)' }}>
                Enterprise-grade AI data intelligence. Query your data in plain English with full transparency and governance.
              </p>
            </div>

            {/* Product links */}
            <div>
              <h4 style={{ margin: '0 0 16px', fontSize: '12px', fontWeight: 700, color: '#9ca3af', fontFamily: 'var(--font-inter)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Product</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {['Features', 'How It Works', 'Roles & Permissions', 'Security', 'Pricing'].map((link) => (
                  <a key={link} href="#" style={{ fontSize: '14px', color: '#6b7280', textDecoration: 'none', fontFamily: 'var(--font-manrope)', transition: 'color 0.2s' }}
                    onMouseEnter={e => (e.currentTarget.style.color = '#635bff')}
                    onMouseLeave={e => (e.currentTarget.style.color = '#6b7280')}>
                    {link}
                  </a>
                ))}
              </div>
            </div>

            {/* Resources */}
            <div>
              <h4 style={{ margin: '0 0 16px', fontSize: '12px', fontWeight: 700, color: '#9ca3af', fontFamily: 'var(--font-inter)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Resources</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {['Documentation', 'API Reference', 'Changelog', 'Status Page', 'Support'].map((link) => (
                  <a key={link} href="#" style={{ fontSize: '14px', color: '#6b7280', textDecoration: 'none', fontFamily: 'var(--font-manrope)', transition: 'color 0.2s' }}
                    onMouseEnter={e => (e.currentTarget.style.color = '#635bff')}
                    onMouseLeave={e => (e.currentTarget.style.color = '#6b7280')}>
                    {link}
                  </a>
                ))}
              </div>
            </div>

            {/* Legal */}
            <div>
              <h4 style={{ margin: '0 0 16px', fontSize: '12px', fontWeight: 700, color: '#9ca3af', fontFamily: 'var(--font-inter)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Legal</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {['Privacy Policy', 'Terms of Service', 'Cookie Policy', 'Security Audit', 'GDPR'].map((link) => (
                  <a key={link} href="#" style={{ fontSize: '14px', color: '#6b7280', textDecoration: 'none', fontFamily: 'var(--font-manrope)', transition: 'color 0.2s' }}
                    onMouseEnter={e => (e.currentTarget.style.color = '#635bff')}
                    onMouseLeave={e => (e.currentTarget.style.color = '#6b7280')}>
                    {link}
                  </a>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom bar */}
          <div
            style={{
              paddingTop: '24px', borderTop: '1px solid #f3f4f6',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}
          >
            <p style={{ margin: 0, fontSize: '13px', color: '#9ca3af', fontFamily: 'var(--font-inter)' }}>
              © {new Date().getFullYear()} Scout · Enterprise AI Data Intelligence Platform. Licensed under the Apache License 2.0.
            </p>
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
              {['Privacy', 'Terms', 'Cookies'].map((link) => (
                <a key={link} href="#" style={{ fontSize: '12px', color: '#9ca3af', textDecoration: 'none', fontFamily: 'var(--font-inter)', transition: 'color 0.2s' }}
                  onMouseEnter={e => (e.currentTarget.style.color = '#6b7280')}
                  onMouseLeave={e => (e.currentTarget.style.color = '#9ca3af')}>
                  {link}
                </a>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
