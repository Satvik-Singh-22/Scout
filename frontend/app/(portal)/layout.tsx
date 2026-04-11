'use client'
import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { getMe, logout } from '@/lib/api-client'
import type { User } from '@/lib/api-client'
import { getAlerts } from '@/lib/api-client'

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<User | null>(null)
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    getMe()
      .then(u => {
        setUser(u)
        // Fetch unread alert count
        getAlerts().then(alerts => {
          setUnreadCount(alerts.filter(a => !a.is_read).length)
        }).catch(() => {})
      })
      .catch(() => router.replace('/login'))
  }, [router])

  const handleLogout = () => {
    logout()
    router.replace('/login')
  }

  const navItems = [
    ...(user?.role !== 'PLATFORM_ADMIN' ? [{ href: '/chat', label: 'Chat', icon: 'chat' }] : []),
    ...(user?.role !== 'PLATFORM_ADMIN' ? [{ href: '/dashboard', label: 'Dashboard', icon: 'dashboard' }] : []),
    ...(user?.role !== 'PLATFORM_ADMIN' ? [{ href: '/alerts', label: 'Alerts', icon: 'notifications', badge: unreadCount }] : []),
    ...(user?.role !== 'PLATFORM_ADMIN' ? [{ href: '/scheduled', label: 'Scheduled', icon: 'schedule' }] : []),
    ...(user?.role === 'DATA_OWNER' ? [{ href: '/onboarding', label: 'Data Config', icon: 'database' }] : []),
    ...(user?.role === 'PLATFORM_ADMIN' ? [{ href: '/admin', label: 'Governance', icon: 'shield_locked' }] : []),
    { href: '/settings', label: 'Settings', icon: 'settings' },
  ]

  const topNavLinks = [
    ...(user?.role !== 'PLATFORM_ADMIN' ? [{ href: '/chat', label: 'Chat' }] : []),
    ...(user?.role !== 'PLATFORM_ADMIN' ? [{ href: '/dashboard', label: 'Dashboard' }] : []),
    ...(user?.role === 'PLATFORM_ADMIN' ? [{ href: '/admin', label: 'Admin' }] : []),
    ...(user?.role === 'DATA_OWNER' ? [{ href: '/onboarding', label: 'Onboarding' }] : []),
  ]

  // Generate user initials for avatar
  const userInitials = user?.name
    ? user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : '?'

  return (
    <div className="flex flex-col min-h-screen bg-background text-on-surface font-body antialiased">
      {/* TopNavBar */}
      <header className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl h-16 w-full fixed top-0 z-40 flex items-center justify-between px-6 shadow-sm border-b border-outline-variant/10 font-manrope">
        <div className="flex items-center gap-8">
          <Link href={user?.role === 'PLATFORM_ADMIN' ? '/admin' : '/chat'} className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white shadow-sm" style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}>
              <span className="font-bold text-sm">S</span>
            </div>
            <span className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">Scout</span>
          </Link>
          <nav className="hidden md:flex gap-6 items-center">
            {topNavLinks.map(link => (
              <Link 
                key={link.href} 
                href={link.href}
                className={`h-16 flex items-center px-1 transition-all duration-200 font-semibold text-sm ${pathname.startsWith(link.href) ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600' : 'text-gray-500 dark:text-gray-400 hover:text-gray-900'}`}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1">
            <Link href="/alerts" className="p-2 text-on-surface-variant hover:bg-gray-50 rounded-full transition-all relative">
              <span className="material-symbols-outlined">notifications</span>
              {unreadCount > 0 && <span className="absolute top-1 right-2 w-2 h-2 bg-red-500 rounded-full"></span>}
            </Link>
            <Link href="/chat" className="p-2 text-on-surface-variant hover:bg-gray-50 rounded-full transition-all">
              <span className="material-symbols-outlined">chat_bubble</span>
            </Link>
            <Link href="/settings" className="p-2 text-on-surface-variant hover:bg-gray-50 rounded-full transition-all">
              <span className="material-symbols-outlined">settings</span>
            </Link>
          </div>
          <div className="h-6 w-px bg-outline-variant/30 hidden sm:block mx-1"></div>
          {/* User avatar with initials */}
          <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold border border-indigo-200 ml-1">
            {userInitials}
          </div>
        </div>
      </header>

      <div className="flex pt-16 min-h-screen">
        {/* SideNavBar */}
        <aside className="bg-gray-50 dark:bg-gray-950 w-64 fixed left-0 top-16 bottom-0 hidden md:flex flex-col p-4 gap-2 border-r border-outline-variant/10 z-30 font-inter text-sm font-medium">
          <div className="flex items-center gap-3 px-2 py-3 mb-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white shadow-sm" style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}>
              <span className="font-bold font-manrope">S</span>
            </div>
            <div>
              <div className="text-lg font-bold font-manrope text-emerald-600 leading-tight">Scout</div>
              <div className="text-[10px] uppercase tracking-wider font-bold text-on-surface-variant">
                {user?.role ? user.role.replace('_', ' ') : 'Loading...'}
              </div>
            </div>
          </div>
          <nav className="flex flex-col flex-1 gap-1 mt-2">
            {navItems.map(item => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link 
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-transform duration-200 ${isActive ? 'bg-white dark:bg-gray-900 text-indigo-600 dark:text-indigo-400 shadow-sm text-sm font-semibold' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:translate-x-1'}`}
                >
                  <span className="material-symbols-outlined">{item.icon}</span>
                  {item.label}
                  {item.badge !== undefined && item.badge > 0 && (
                    <span className="ml-auto bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>
          
          <div className="mt-auto flex flex-col gap-2 pt-6 border-t border-gray-200/60">
            {/* User info card */}
            {user && (
              <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-xl mb-2 border border-indigo-100 dark:border-indigo-800">
                <div className="text-xs font-bold text-indigo-600 dark:text-indigo-400 mb-1">SIGNED IN AS</div>
                <div className="text-sm font-semibold text-gray-900 dark:text-white truncate">{user.name}</div>
                <div className="text-[10px] text-gray-500 truncate mt-0.5">{user.email}</div>
              </div>
            )}
            <button onClick={handleLogout} className="flex items-center gap-3 px-3 py-2.5 text-error hover:bg-red-50 rounded-lg text-sm font-medium transition-all w-full text-left">
              <span className="material-symbols-outlined text-[20px]">logout</span>
              Logout
            </button>
          </div>
        </aside>

        {/* Main Content Canvas */}
        <main className="flex-1 md:ml-64 relative flex flex-col min-h-[calc(100vh-4rem)]">
          {children}
        </main>
      </div>
    </div>
  )
}
