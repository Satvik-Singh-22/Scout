'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getMe, getTeamMembers } from '@/lib/api-client';
import type { User, TeamInfo, TeamMember } from '@/lib/api-client';

function timeAgo(dateStr: string): string {
  if (!dateStr) return '—';
  const diff = Date.now() - new Date(dateStr).getTime();
  const days = Math.floor(diff / 86400000);
  if (days > 365) return `${Math.floor(days / 365)}y ago`;
  if (days > 30) return `${Math.floor(days / 30)}mo ago`;
  if (days > 0) return `${days}d ago`;
  const hours = Math.floor(diff / 3600000);
  if (hours > 0) return `${hours}h ago`;
  return 'Just now';
}

const ROLE_BADGES: Record<string, { bg: string; text: string; label: string }> =
{
  DATA_OWNER: {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    label: 'Data Owner',
  },
  ANALYST: { bg: 'bg-indigo-50', text: 'text-indigo-700', label: 'Analyst' },
  ENTERPRISE_ANALYST: {
    bg: 'bg-purple-50',
    text: 'text-purple-700',
    label: 'Enterprise',
  },
  PLATFORM_ADMIN: { bg: 'bg-rose-50', text: 'text-rose-700', label: 'Admin' },
};

const PERSONA_ICONS: Record<string, { icon: string; color: string }> = {
  EXECUTIVE: { icon: 'business_center', color: 'text-violet-500' },
  TECHNICAL: { icon: 'terminal', color: 'text-emerald-500' },
};

const AVATAR_COLORS = [
  'from-indigo-500 to-blue-500',
  'from-emerald-500 to-teal-500',
  'from-violet-500 to-purple-500',
  'from-orange-500 to-amber-500',
  'from-rose-500 to-pink-500',
  'from-cyan-500 to-sky-500',
  'from-fuchsia-500 to-pink-500',
  'from-lime-500 to-green-500',
];

export default function TeamPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [team, setTeam] = useState<TeamInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getMe()
      .then((u) => {
        setUser(u);
        return getTeamMembers();
      })
      .then((t) => {
        setTeam(t);
        setLoading(false);
      })
      .catch((err) => {
        if (err.message?.includes('not assigned')) {
          setError('You are not assigned to any team.');
        } else if (err.message?.includes('Not authenticated')) {
          router.push('/login');
          return;
        } else {
          setError(err.message || 'Failed to load team');
        }
        setLoading(false);
      });
  }, [router]);

  if (loading) {
    return (
      <div className="p-8 max-w-5xl mx-auto w-full">
        <div className="mb-8">
          <div className="h-8 bg-gray-200 rounded w-48 animate-pulse mb-2" />
          <div className="h-4 bg-gray-100 rounded w-72 animate-pulse" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-gray-100 p-6 h-44 animate-pulse"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-11 h-11 rounded-full bg-gray-200" />
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-28 mb-2" />
                  <div className="h-3 bg-gray-100 rounded w-36" />
                </div>
              </div>
              <div className="h-3 bg-gray-100 rounded w-20 mt-4" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-5xl mx-auto w-full">
        <div className="py-24 text-center">
          <div className="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="material-symbols-outlined text-gray-300 text-3xl">
              group_off
            </span>
          </div>
          <h2 className="text-lg font-bold text-gray-600 mb-1">
            No Team Found
          </h2>
          <p className="text-sm text-gray-400 max-w-sm mx-auto">{error}</p>
        </div>
      </div>
    );
  }

  if (!user || !team) return null;

  // Stat calculations
  const EXECUTIVECount = team.members.filter(
    (m) => m.persona === 'EXECUTIVE',
  ).length;
  const TECHNICALCount = team.members.filter(
    (m) => m.persona === 'TECHNICAL',
  ).length;
  const roleDistribution = team.members.reduce(
    (acc, m) => {
      acc[m.role] = (acc[m.role] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  return (
    <div className="p-8 max-w-5xl mx-auto w-full">
      {/* ── Header ── */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-1">
          <div className="p-2 bg-indigo-50 rounded-lg">
            <span className="material-symbols-outlined text-indigo-600">
              groups
            </span>
          </div>
          <div>
            <h1
              className="text-2xl font-extrabold text-gray-900"
              style={{ fontFamily: 'Manrope, sans-serif' }}
            >
              {team.team_name}
            </h1>
            <p className="text-sm text-gray-400">
              {team.members.length} member{team.members.length !== 1 ? 's' : ''}{' '}
              · Your workspace team
            </p>
          </div>
        </div>
      </div>

      {/* ── Summary Stats ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
            Total
          </p>
          <p
            className="text-2xl font-extrabold text-gray-900"
            style={{ fontFamily: 'Manrope, sans-serif' }}
          >
            {team.members.length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
            EXECUTIVEs
          </p>
          <p
            className="text-2xl font-extrabold text-violet-600"
            style={{ fontFamily: 'Manrope, sans-serif' }}
          >
            {EXECUTIVECount}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
            TECHNICALs
          </p>
          <p
            className="text-2xl font-extrabold text-emerald-600"
            style={{ fontFamily: 'Manrope, sans-serif' }}
          >
            {TECHNICALCount}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">
            Roles
          </p>
          <div className="flex flex-wrap gap-1 mt-1">
            {Object.entries(roleDistribution).map(([role, count]) => {
              const badge = ROLE_BADGES[role] || {
                bg: 'bg-gray-50',
                text: 'text-gray-600',
                label: role,
              };
              return (
                <span
                  key={role}
                  className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${badge.bg} ${badge.text}`}
                >
                  {count} {badge.label}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Members Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {team.members.map((member, idx) => {
          const isYou = member.id === user.id;
          const initials = member.name
            .split(' ')
            .map((w) => w[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
          const gradientClass = AVATAR_COLORS[idx % AVATAR_COLORS.length];
          const roleBadge = ROLE_BADGES[member.role] || {
            bg: 'bg-gray-50',
            text: 'text-gray-600',
            label: member.role,
          };
          const personaInfo = PERSONA_ICONS[member.persona] || {
            icon: 'person',
            color: 'text-gray-400',
          };

          return (
            <div
              key={member.id}
              className={`bg-white rounded-xl border shadow-sm p-5 relative group hover:shadow-md transition-all ${isYou
                ? 'border-indigo-200 ring-1 ring-indigo-100'
                : 'border-gray-100'
                }`}
            >
              {/* "You" indicator */}
              {isYou && (
                <div className="absolute top-3 right-3 px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded text-[9px] font-bold uppercase tracking-wider">
                  You
                </div>
              )}

              {/* Avatar + Name */}
              <div className="flex items-center gap-3 mb-4">
                <div
                  className={`w-11 h-11 rounded-full bg-gradient-to-br ${gradientClass} flex items-center justify-center text-white text-sm font-bold shadow-sm`}
                >
                  {initials}
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-bold text-gray-900 truncate group-hover:text-indigo-600 transition-colors">
                    {member.name}
                  </h3>
                  <p className="text-xs text-gray-400 truncate">
                    {member.email}
                  </p>
                </div>
              </div>

              {/* Role + Persona badges */}
              <div className="flex items-center gap-2 mb-3">
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${roleBadge.bg} ${roleBadge.text}`}
                >
                  {roleBadge.label}
                </span>
                <span className="flex items-center gap-1 text-[10px] text-gray-400">
                  <span
                    className={`material-symbols-outlined text-xs ${personaInfo.color}`}
                  >
                    {personaInfo.icon}
                  </span>
                  {member.persona === 'EXECUTIVE' ? 'EXECUTIVE' : 'TECHNICAL'}
                </span>
              </div>

              {/* Joined date */}
              <div className="flex items-center gap-1 text-[10px] text-gray-300">
                <span className="material-symbols-outlined text-xs">
                  calendar_today
                </span>
                Joined {timeAgo(member.created_at)}
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty state */}
      {team.members.length === 0 && (
        <div className="py-24 text-center">
          <div className="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="material-symbols-outlined text-gray-300 text-3xl">
              person_add
            </span>
          </div>
          <h2 className="text-lg font-bold text-gray-600 mb-1">
            No team members yet
          </h2>
          <p className="text-sm text-gray-400">
            Invite colleagues to join your team
          </p>
        </div>
      )}
    </div>
  );
}
