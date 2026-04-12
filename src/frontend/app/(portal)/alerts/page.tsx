'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import AlertCenter from '@/components/AlertCenter';

export default function AlertsPage() {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    const token = Cookies.get('access_token');
    if (!token) {
      router.push('/login');
      return;
    }
    setAuthorized(true);
  }, [router]);

  if (!authorized) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-500">Checking permissions...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <div className="px-6 py-8">
        <AlertCenter />
      </div>
    </div>
  );
}
