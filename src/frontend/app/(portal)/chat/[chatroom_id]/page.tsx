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
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { getMe, getChatrooms, renameChatroom, User, Chatroom as ChatroomType } from '@/lib/api-client';
import Chatroom from '@/components/Chatroom';
import { getAgentModeConfig } from '@/lib/agent-modes';
import { ArrowLeft, Edit2, Search } from 'lucide-react';

export default function ChatroomPage({
  params,
}: {
  params: { chatroom_id: string };
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const [user, setUser] = useState<User | null>(null);
  const [persona, setPersona] = useState<'EXECUTIVE' | 'TECHNICAL' | null>(null);
  const [loading, setLoading] = useState(true);
  const [chatroom, setChatroom] = useState<ChatroomType | null>(null);
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [u, rooms] = await Promise.all([getMe(), getChatrooms()]);
        setUser(u);
        setPersona(u.persona as 'EXECUTIVE' | 'TECHNICAL');
        
        const current = rooms.find(r => r.id === params.chatroom_id);
        if (current) {
          setChatroom(current);
          setNewName(current.name || '');
        }
        setLoading(false);
      } catch {
        router.push('/login');
      }
    };
    fetchData();
  }, [params.chatroom_id, router]);

  // Keyboard shortcut Cmd/Ctrl + K to focus search (demo only - navigates to chat list)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        router.push('/chat');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [router]);

  const handleRename = async () => {
    if (!newName.trim() || !chatroom) return;
    try {
      const updated = await renameChatroom(chatroom.id, newName.trim());
      setChatroom(updated);
      setIsRenaming(false);
    } catch {
      alert('Failed to rename chatroom');
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[calc(100vh-64px)] text-gray-500 bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm font-medium">Initializing encrypted session...</p>
        </div>
      </div>
    );
  }

  if (!user || !persona) return null;

  return (
    <div className="flex-1 bg-gray-50 flex flex-col h-[calc(100vh-64px)] relative">
      {/* Header */}
      <header className="h-16 border-b border-gray-200 bg-white shadow-sm flex items-center justify-between px-6 shrink-0 z-10 w-full relative">
        <div className="flex items-center gap-4 min-w-0">
          <Link
            href="/chat"
            className="p-2 text-gray-400 hover:text-indigo-600 rounded-xl hover:bg-indigo-50 transition-all shadow-sm border border-transparent hover:border-indigo-100"
          >
            <ArrowLeft size={18} />
          </Link>
          <div className="min-w-0">
            {isRenaming ? (
              <div className="flex items-center gap-2">
                <input
                  autoFocus
                  className="text-sm font-bold text-gray-900 border-b-2 border-indigo-500 focus:outline-none bg-transparent"
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleRename();
                    if (e.key === 'Escape') setIsRenaming(false);
                  }}
                />
                <button onClick={handleRename} className="text-[10px] font-bold text-indigo-600 uppercase">Save</button>
              </div>
            ) : (
              <div className="flex items-center gap-2 group">
                <h2 className="text-sm font-bold text-gray-900 truncate max-w-[200px] sm:max-w-md">
                  {chatroom?.name || `Chatroom: ${params.chatroom_id.slice(0, 8)}`}
                </h2>
                <button 
                  onClick={() => setIsRenaming(true)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-indigo-600 transition-all rounded-md hover:bg-gray-50"
                >
                  <Edit2 size={12} />
                </button>
              </div>
            )}
              <span className="text-[10px] text-emerald-600 font-bold uppercase tracking-widest flex items-center gap-1">
              <span className="w-1 h-1 bg-emerald-500 rounded-full animate-pulse"></span>
              {chatroom ? getAgentModeConfig(chatroom.agent_mode).headerSubtitle : 'Live Pipeline Active'}
            </span>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg text-gray-400 group cursor-pointer hover:bg-gray-200 transition-all" onClick={() => router.push('/chat')}>
            <Search size={14} />
            <span className="text-[10px] font-bold uppercase tracking-widest">Search Chats</span>
            <kbd className="text-[9px] bg-white border border-gray-300 px-1 rounded text-gray-500 shadow-sm ml-1 group-hover:border-indigo-300 group-hover:text-indigo-600 transition-colors capitalize">
              {navigator.platform.toUpperCase().includes('MAC') ? '⌘' : 'Ctrl'} K
            </kbd>
          </div>

          <div className="h-8 w-px bg-gray-100 mx-1"></div>

          <div className="flex items-center gap-3">
            {/* Mode badge */}
            {chatroom && (() => {
              const mc = getAgentModeConfig(chatroom.agent_mode);
              return (
                <div className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg ${mc.badgeBg} ${mc.badgeText}`}>
                  <span className="text-sm">{mc.icon}</span>
                  <span className="text-[10px] font-bold uppercase tracking-wider">{mc.shortLabel}</span>
                </div>
              );
            })()}
             <div className={`flex flex-col items-end`}>
               <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest leading-none mb-1">Perspective</span>
               <div
                 className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider shadow-sm border ${persona === 'EXECUTIVE'
                   ? 'bg-indigo-600 text-white border-indigo-700'
                   : 'bg-emerald-600 text-white border-emerald-700'
                   }`}
               >
                 {persona} Mode
               </div>
             </div>
          </div>
        </div>
      </header>

      {/* Body */}
      <Chatroom
        chatroomId={params.chatroom_id}
        userPersona={persona}
        agentMode={chatroom?.agent_mode || 'DATABASE'}
        onPersonaChange={(p) => setPersona(p)}
        initialQuery={initialQuery}
      />
    </div>
  );
}
