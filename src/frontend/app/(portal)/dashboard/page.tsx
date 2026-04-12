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

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  getMe,
  getAlerts,
  getChatrooms,
  getScheduled,
  createChatroom,
} from '@/lib/api-client';
import type { User, Alert, Chatroom, ScheduledQuery } from '@/lib/api-client';

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [chatrooms, setChatrooms] = useState<Chatroom[]>([]);
  const [scheduled, setScheduled] = useState<ScheduledQuery[]>([]);
  const [loading, setLoading] = useState(true);
  const [quickAsk, setQuickAsk] = useState('');
  const [askLoading, setAskLoading] = useState(false);

  useEffect(() => {
    getMe()
      .then((u) => {
        setUser(u);
        // Fire all fetches in parallel
        Promise.allSettled([
          getAlerts().then((a) => setAlerts(Array.isArray(a) ? a : [])),
          getChatrooms().then((c) => setChatrooms(Array.isArray(c) ? c : [])),
          getScheduled().then((s) => setScheduled(Array.isArray(s) ? s : [])),
        ]).finally(() => setLoading(false));
      })
      .catch(() => router.push('/login'));
  }, [router]);

  const handleQuickAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickAsk.trim() || askLoading) return;
    setAskLoading(true);
    try {
      const room = await createChatroom(quickAsk.trim().slice(0, 60));
      router.push(`/chat/${room.id}?q=${encodeURIComponent(quickAsk.trim())}`);
    } catch {
      setAskLoading(false);
    }
  };

  // Derived stats
  const unreadAlerts = alerts.filter((a) => !a.is_read);
  const highAlerts = alerts.filter((a) => a.severity === 'HIGH' && !a.is_read);
  const activeScheduled = scheduled.filter((s) => s.is_active);
  const nextScheduled = activeScheduled
    .filter((s) => s.next_run_at)
    .sort(
      (a, b) =>
        new Date(a.next_run_at!).getTime() - new Date(b.next_run_at!).getTime(),
    )[0];

  const teamCount = user?.accessible_teams?.length || 0;

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto w-full">
        <div className="mb-8 h-10 bg-gray-200 rounded w-64 animate-pulse" />
        {/* Skeleton KPI row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="bg-white rounded-xl p-6 border border-gray-100 h-40 animate-pulse"
            >
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-3" />
              <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />
              <div className="h-16 bg-gray-100 rounded" />
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="bg-white rounded-xl p-6 border border-gray-100 h-64 animate-pulse"
              />
            ))}
          </div>
          <div className="space-y-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="bg-white rounded-xl p-6 border border-gray-100 h-48 animate-pulse"
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="p-8 max-w-7xl mx-auto w-full">
      {/* ── Dashboard Header ── */}
      <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1
              className="text-3xl font-extrabold tracking-tight text-gray-900"
              style={{ fontFamily: 'Manrope, sans-serif' }}
            >
              Overview
            </h1>
            <span
              className={`px-3 py-1 text-[10px] font-bold tracking-widest rounded-full uppercase ${user.persona === 'EXECUTIVE'
                  ? 'bg-indigo-100/60 text-indigo-700'
                  : 'bg-gray-900 text-white'
                }`}
            >
              {user.persona}
            </span>
          </div>
          <p className="text-gray-500 text-sm">
            Welcome back, {user.name}. Here&apos;s your latest data overview.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push('/scheduled')}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg transition-all hover:bg-gray-200"
          >
            <span className="material-symbols-outlined text-lg">schedule</span>
            Scheduled
          </button>
          <button
            onClick={() => router.push('/alerts')}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg transition-all hover:bg-gray-200 relative"
          >
            <span className="material-symbols-outlined text-lg">
              notifications
            </span>
            Alerts
            {unreadAlerts.length > 0 && (
              <span className="ml-1 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                {unreadAlerts.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* ── 1. QUICK ASK — Global Input ── */}
      <div className="mb-8">
        <form onSubmit={handleQuickAsk} className="relative group">
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-500 transition-colors">
            <span className="material-symbols-outlined text-xl">
              auto_awesome
            </span>
          </div>
          <input
            type="text"
            value={quickAsk}
            onChange={(e) => setQuickAsk(e.target.value)}
            placeholder='Ask your data anything — e.g. "What was the failure rate last week?"'
            className="w-full bg-white border border-gray-200 rounded-xl py-4 pl-12 pr-32 text-sm text-gray-900 placeholder-gray-400 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-400 transition-all"
          />
          <button
            type="submit"
            disabled={askLoading || !quickAsk.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg font-semibold text-sm shadow-lg shadow-indigo-500/20 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="material-symbols-outlined text-sm">send</span>
            {askLoading ? 'Opening…' : 'Ask Scout'}
          </button>
        </form>
      </div>

      {/* ── KPI Grid (3 columns) ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Chat Sessions */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100/80 group hover:shadow-md transition-all">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-xs font-semibold text-gray-400 tracking-wider uppercase mb-1">
                Chat Sessions
              </p>
              <h3
                className="text-2xl font-bold"
                style={{ fontFamily: 'Manrope, sans-serif' }}
              >
                {chatrooms.length}
              </h3>
            </div>
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
              <span className="material-symbols-outlined">chat_bubble</span>
            </div>
          </div>
          <div className="h-12 flex items-center">
            <div className="w-full bg-emerald-50 rounded-lg h-2 relative overflow-hidden">
              <div
                className="absolute inset-0 bg-emerald-500 rounded-lg transition-all"
                style={{ width: `${Math.min(chatrooms.length * 10, 100)}%` }}
              />
            </div>
          </div>
          <div className="mt-3 flex items-center text-xs font-medium text-emerald-600">
            <span className="material-symbols-outlined text-sm mr-1">
              trending_up
            </span>
            {
              chatrooms.filter(
                (r) => Date.now() - new Date(r.created_at).getTime() < 86400000,
              ).length
            }{' '}
            today
          </div>
        </div>

        {/* Active Automations */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100/80 group hover:shadow-md transition-all">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-xs font-semibold text-gray-400 tracking-wider uppercase mb-1">
                Scheduled Tasks
              </p>
              <h3
                className="text-2xl font-bold"
                style={{ fontFamily: 'Manrope, sans-serif' }}
              >
                {activeScheduled.length}
              </h3>
            </div>
            <div className="p-2 bg-amber-50 rounded-lg text-amber-600">
              <span className="material-symbols-outlined">schedule</span>
            </div>
          </div>
          <div className="flex items-center gap-2 mb-2">
            <div className="flex -space-x-2">
              {activeScheduled.slice(0, 3).map((_, i) => (
                <div
                  key={i}
                  className="w-6 h-6 rounded-full bg-amber-100 border-2 border-white flex items-center justify-center text-[10px] font-bold text-amber-700"
                >
                  {i + 1}
                </div>
              ))}
            </div>
            {activeScheduled.length > 3 && (
              <span className="text-[10px] text-gray-400 font-medium">
                +{activeScheduled.length - 3} more
              </span>
            )}
          </div>
          <div className="mt-3 flex items-center text-xs font-medium text-amber-600">
            <span className="material-symbols-outlined text-sm mr-1">
              play_circle
            </span>
            {scheduled.filter((s) => !s.is_active).length} paused
          </div>
        </div>

        {/* Alerts Pulse */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100/80 group hover:shadow-md transition-all">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-xs font-semibold text-gray-400 tracking-wider uppercase mb-1">
                Alerts
              </p>
              <h3
                className="text-2xl font-bold"
                style={{ fontFamily: 'Manrope, sans-serif' }}
              >
                {unreadAlerts.length}
              </h3>
            </div>
            <div
              className={`p-2 rounded-lg ${highAlerts.length > 0 ? 'bg-red-50 text-red-500' : 'bg-green-50 text-green-600'}`}
            >
              <span className="material-symbols-outlined">
                {highAlerts.length > 0 ? 'warning' : 'verified'}
              </span>
            </div>
          </div>
          <div className="h-12 relative overflow-hidden rounded-lg">
            <svg
              className="absolute bottom-0 w-full h-full"
              preserveAspectRatio="none"
              viewBox="0 0 100 40"
            >
              <defs>
                <linearGradient
                  id="alertGrad"
                  x1="0%"
                  y1="0%"
                  x2="0%"
                  y2="100%"
                >
                  <stop
                    offset="0%"
                    style={{
                      stopColor:
                        highAlerts.length > 0
                          ? 'rgba(239,68,68,0.4)'
                          : 'rgba(16,185,129,0.4)',
                    }}
                  />
                  <stop
                    offset="100%"
                    style={{
                      stopColor:
                        highAlerts.length > 0
                          ? 'rgba(239,68,68,0)'
                          : 'rgba(16,185,129,0)',
                    }}
                  />
                </linearGradient>
              </defs>
              <path
                d="M0 40 L0 30 Q 15 25, 30 28 T 60 15 T 100 10 L 100 40 Z"
                fill="url(#alertGrad)"
              />
              <path
                d="M0 30 Q 15 25, 30 28 T 60 15 T 100 10"
                fill="none"
                stroke={highAlerts.length > 0 ? '#ef4444' : '#10b981'}
                strokeWidth="2"
              />
            </svg>
          </div>
          <div
            className={`mt-3 flex items-center text-xs font-medium ${highAlerts.length > 0 ? 'text-red-600' : 'text-green-600'}`}
          >
            <span className="material-symbols-outlined text-sm mr-1">
              {highAlerts.length > 0 ? 'priority_high' : 'check_circle'}
            </span>
            {highAlerts.length > 0
              ? `${highAlerts.length} critical`
              : 'All systems healthy'}
          </div>
        </div>
      </div>

      {/* ── High-Density Main Layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* ── LEFT 2/3 Column ── */}
        <div className="lg:col-span-2 space-y-8">
          {/* ── 3. Recent Chat History ── */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100/80 overflow-hidden">
            <div className="px-8 py-6 border-b border-gray-100 flex justify-between items-center">
              <h2
                className="text-base font-bold text-gray-900"
                style={{ fontFamily: 'Manrope, sans-serif' }}
              >
                Recent Conversations
              </h2>
              <button
                onClick={() => router.push('/chat')}
                className="text-indigo-600 text-sm font-semibold hover:underline"
              >
                View All
              </button>
            </div>
            {chatrooms.length === 0 ? (
              <div className="p-12 text-center">
                <div className="w-12 h-12 mx-auto bg-gray-50 rounded-full flex items-center justify-center mb-3">
                  <span className="material-symbols-outlined text-gray-300 text-2xl">
                    chat_bubble_outline
                  </span>
                </div>
                <p className="text-gray-400 text-sm font-medium">
                  No conversations yet
                </p>
                <p className="text-xs text-gray-300 mt-1">
                  Use the Quick Ask bar above to start
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="bg-gray-50/80">
                      <th className="px-8 py-3 text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                        Session
                      </th>
                      <th className="px-8 py-3 text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                        Preview
                      </th>
                      <th className="px-8 py-3 text-[10px] font-bold text-gray-400 uppercase tracking-widest text-right">
                        Last Active
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {chatrooms.slice(0, 5).map((room, i) => {
                      const colors = [
                        {
                          bg: 'bg-indigo-50',
                          text: 'text-indigo-600',
                          icon: '📊',
                        },
                        {
                          bg: 'bg-emerald-50',
                          text: 'text-emerald-600',
                          icon: '🔍',
                        },
                        {
                          bg: 'bg-orange-50',
                          text: 'text-orange-600',
                          icon: '📈',
                        },
                        {
                          bg: 'bg-purple-50',
                          text: 'text-purple-600',
                          icon: '🧠',
                        },
                        { bg: 'bg-rose-50', text: 'text-rose-600', icon: '💡' },
                      ];
                      const accent = colors[i % colors.length];
                      return (
                        <tr
                          key={room.id}
                          onClick={() => router.push(`/chat/${room.id}`)}
                          className="hover:bg-gray-50/80 transition-colors cursor-pointer group"
                        >
                          <td className="px-8 py-4">
                            <div className="flex items-center gap-3">
                              <div
                                className={`w-8 h-8 rounded-lg ${accent.bg} ${accent.text} flex items-center justify-center text-sm`}
                              >
                                {accent.icon}
                              </div>
                              <span className="text-sm font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors truncate max-w-[200px]">
                                {room.name}
                              </span>
                            </div>
                          </td>
                          <td className="px-8 py-4 text-xs text-gray-400 truncate max-w-[250px]">
                            {room.last_message_preview || 'Start exploring…'}
                          </td>
                          <td className="px-8 py-4 text-right text-xs text-gray-400">
                            {timeAgo(room.created_at)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* ── RIGHT 1/3 Column ── */}
        <div className="space-y-8">
          {/* ── 2. Alert Monitoring Widget ── */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100/80">
            <div className="flex items-center justify-between mb-5">
              <h2
                className="text-base font-bold text-gray-900"
                style={{ fontFamily: 'Manrope, sans-serif' }}
              >
                Alert Monitor
              </h2>
              <span
                className={`px-2.5 py-0.5 text-xs font-bold rounded-full ${unreadAlerts.length > 0
                    ? 'bg-red-100 text-red-700'
                    : 'bg-green-100 text-green-700'
                  }`}
              >
                {unreadAlerts.length > 0
                  ? `${unreadAlerts.length} Unread`
                  : 'All clear'}
              </span>
            </div>
            {unreadAlerts.length === 0 ? (
              <div className="text-center py-6">
                <div className="w-12 h-12 mx-auto bg-green-50 rounded-full flex items-center justify-center mb-3">
                  <span className="material-symbols-outlined text-green-500">
                    verified
                  </span>
                </div>
                <p className="text-sm text-gray-500 font-medium">
                  No active alerts
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  All systems operating normally
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {unreadAlerts.slice(0, 1).map((alert) => {
                  const sev = alert.severity;
                  const stripColor =
                    sev === 'HIGH'
                      ? 'bg-red-500'
                      : sev === 'MEDIUM'
                        ? 'bg-amber-500'
                        : 'bg-gray-300';
                  const iconColor =
                    sev === 'HIGH'
                      ? 'text-red-500'
                      : sev === 'MEDIUM'
                        ? 'text-amber-600'
                        : 'text-indigo-500';
                  const iconName =
                    sev === 'HIGH'
                      ? 'trending_down'
                      : sev === 'MEDIUM'
                        ? 'sync_problem'
                        : 'info';
                  return (
                    <div
                      key={alert.id}
                      onClick={() => router.push('/alerts')}
                      className="relative flex items-start gap-3 p-3 rounded-lg bg-gray-50/60 hover:bg-gray-100/80 transition-all cursor-pointer overflow-hidden group"
                    >
                      <div
                        className={`absolute left-0 top-0 bottom-0 w-1 ${stripColor}`}
                      />
                      <div
                        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-white shadow-sm ${iconColor}`}
                      >
                        <span className="material-symbols-outlined text-sm">
                          {iconName}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-gray-900 truncate">
                          {alert.title}
                        </p>
                        <p className="text-xs text-gray-400 truncate">
                          {alert.description}
                        </p>
                        <span className="text-[10px] text-gray-400 mt-1 inline-block">
                          {timeAgo(alert.created_at)}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            <button
              onClick={() => router.push('/alerts')}
              className="w-full mt-5 py-2.5 border border-gray-200/60 text-gray-600 rounded-xl font-semibold text-xs hover:bg-gray-50 transition-all"
            >
              View All Alerts
            </button>
          </div>

          {/* ── 4. Scheduled Queries / Data Pipelines ── */}
          <div className="relative overflow-hidden bg-indigo-600 p-6 rounded-xl text-white shadow-lg shadow-indigo-500/20">
            {/* Glassmorphism overlay */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl" />
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/5 rounded-full -ml-12 -mb-12 blur-xl" />
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-4 opacity-80">
                <span className="material-symbols-outlined text-sm">
                  auto_awesome
                </span>
                <span className="text-[10px] font-bold tracking-widest uppercase">
                  Data Pipelines
                </span>
              </div>
              <h3
                className="text-xl font-bold mb-2"
                style={{ fontFamily: 'Manrope, sans-serif' }}
              >
                {activeScheduled.length} Scheduled Task
                {activeScheduled.length !== 1 ? 's' : ''}
              </h3>
              <p className="text-sm text-indigo-100 leading-relaxed mb-5">
                {nextScheduled
                  ? `Next run: "${nextScheduled.query_text.slice(0, 50)}${nextScheduled.query_text.length > 50 ? '…' : ''}" ${nextScheduled.next_run_at ? timeAgo(nextScheduled.next_run_at) : ''}`
                  : 'No upcoming executions. Schedule a query to get automated insights.'}
              </p>
              <div className="flex items-center justify-between">
                <div className="flex -space-x-2">
                  {activeScheduled.slice(0, 4).map((s, i) => (
                    <div
                      key={s.id}
                      className="w-8 h-8 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center text-[10px] font-bold border border-white/20"
                    >
                      {s.delivery === 'EMAIL' ? '📧' : '📊'}
                    </div>
                  ))}
                </div>
                <button
                  onClick={() => router.push('/scheduled')}
                  className="bg-white text-indigo-700 px-4 py-2 rounded-lg font-bold text-xs shadow-sm hover:bg-gray-50 transition-all"
                >
                  Manage
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
