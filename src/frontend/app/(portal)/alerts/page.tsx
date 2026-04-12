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
