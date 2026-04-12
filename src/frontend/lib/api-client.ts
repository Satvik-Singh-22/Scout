// frontend/lib/api-client.ts
import Cookies from 'js-cookie';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getToken(): string {
  return Cookies.get('access_token') || '';
}

function authHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${getToken()}`,
  };
}

// FIX: Central fetch wrapper — handles 401 globally, throws on auth failure
async function apiFetch(url: string, options?: RequestInit): Promise<Response> {
  const res = await fetch(url, options);
  if (res.status === 401) {
    Cookies.remove('access_token');
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Session expired. Redirecting to login.');
  }
  return res;
}

// ─────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  persona: 'EXECUTIVE' | 'TECHNICAL';
  role: 'DATA_OWNER' | 'ANALYST' | 'PLATFORM_ADMIN' | 'ENTERPRISE_ANALYST';
  team_id: string | null;
  accessible_teams: { team_id: string; team_name: string }[];
}

export interface ChainOfThought {
  sources: string[];
  sql_executed: string;
  sql_results: object[];
  rag_chunks_used: number;
  agent_path: string[];
  query_intent: string;
  confidence: 'high' | 'low';
  tables_searched: string[];
  tables_used: string[];
  teams_accessed: string[];
  chart_type: 'BAR' | 'LINE' | 'PIE' | 'TABLE';
}

export interface Message {
  id: string;
  role: 'USER' | 'ASSISTANT';
  content: string;
  chain_of_thought: ChainOfThought | null;
  created_at: string;
}

export interface Chatroom {
  id: string;
  name: string;
  created_at: string;
  last_message_preview?: string;
}

export interface Alert {
  id: string;
  title: string;
  description: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  data_snapshot: object | null;
  is_read: boolean;
  created_at: string;
}

export interface ScheduledQuery {
  id: string;
  query_text: string;
  cron_expression: string;
  delivery: 'EMAIL' | 'DASHBOARD';
  is_active: boolean;
  alert_condition?: string | null;
  alert_severity?: string | null;
  last_run_at: string | null;
  next_run_at: string | null;
}

export interface DashboardCard {
  id: string;
  title: string;
  query_result: { answer?: string; sql_results?: object[] };
  chart_type: 'BAR' | 'LINE' | 'PIE' | 'TABLE';
  created_at: string;
}

export interface AdminTable {
  table_name: string;
  column_count: number;
  team_assignments: {
    config_id: string;
    team_id: string;
    team_name: string;
    is_active: boolean;
  }[];
}

export interface AdminTeam {
  id: string;
  name: string;
  table_count: number;
  member_count: number;
}

export interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: string;
  team_id: string | null;
  team_name: string | null;
  accessible_teams: { team_id: string; team_name: string }[];
}

// ─────────────────────────────────────────────
// AUTH
// ─────────────────────────────────────────────

export async function login(email: string, password: string) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Login failed');
  Cookies.set('access_token', data.access_token, { expires: 1 });
  return data as { access_token: string; user: User };
}

export async function register(payload: {
  email: string;
  password: string;
  name: string;
  persona: string;
  role: string;
  team_id: string;
}) {
  const res = await fetch(`${BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Registration failed');
  Cookies.set('access_token', data.access_token, { expires: 1 });
  return data as { access_token: string; user: User };
}

export function logout() {
  Cookies.remove('access_token');
}

export async function getTeams(): Promise<{ id: string; name: string }[]> {
  const res = await apiFetch(`${BASE_URL}/auth/teams`);
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

// ─────────────────────────────────────────────
// USERS
// ─────────────────────────────────────────────

export async function getMe(): Promise<User> {
  const res = await apiFetch(`${BASE_URL}/users/me`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Not authenticated');
  return res.json();
}

export async function updateMe(payload: { persona?: string; name?: string; team_id?: string }) {
  const res = await apiFetch(`${BASE_URL}/users/me`, {
    method: 'PATCH',
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update profile');
  return res.json();
}

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  persona: 'EXECUTIVE' | 'TECHNICAL';
  role: string;
  created_at: string;
}

export interface TeamInfo {
  team_id: string;
  team_name: string;
  members: TeamMember[];
}

export async function getTeamMembers(): Promise<TeamInfo> {
  const res = await apiFetch(`${BASE_URL}/users/team`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch team members');
  return res.json();
}

// ─────────────────────────────────────────────
// CHATROOMS
// ─────────────────────────────────────────────

export async function getChatrooms(): Promise<Chatroom[]> {
  const res = await apiFetch(`${BASE_URL}/chatrooms`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch chatrooms');
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function createChatroom(name: string): Promise<Chatroom> {
  const res = await apiFetch(`${BASE_URL}/chatrooms`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error('Failed to create chatroom');
  return res.json();
}

export async function renameChatroom(chatroomId: string, name: string): Promise<Chatroom> {
  const res = await apiFetch(`${BASE_URL}/chatrooms/${chatroomId}`, {
    method: 'PATCH',
    headers: authHeaders(),
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error('Failed to rename chatroom');
  return res.json();
}

export async function getMessages(chatroomId: string): Promise<Message[]> {
  const res = await apiFetch(`${BASE_URL}/chatrooms/${chatroomId}/messages`, {
    headers: authHeaders(),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

// SSE streaming — uses raw fetch (cannot stream through apiFetch)
export function streamMessage(
  chatroomId: string,
  query: string,
  persona: 'EXECUTIVE' | 'TECHNICAL',
  onChunk: (text: string) => void,
  onDone: (cot: ChainOfThought) => void,
  onError: (err: string) => void,
): () => void {
  const controller = new AbortController();

  fetch(`${BASE_URL}/chatrooms/${chatroomId}/message`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ query, persona }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (res.status === 401) {
        Cookies.remove('access_token');
        window.location.href = '/login';
        return;
      }
      if (!res.ok) {
        const err = await res
          .json()
          .catch(() => ({ detail: 'Request failed' }));
        onError(err.detail || 'Request failed');
        return;
      }
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(line.slice(6));
              if (parsed.type === 'chunk') onChunk(parsed.content);
              else if (parsed.type === 'done') onDone(parsed.chain_of_thought);
              else if (parsed.type === 'error') onError(parsed.message);
            } catch {
              // Ignore malformed SSE lines
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError(err.message || 'Connection error');
    });

  return () => controller.abort();
}

// ─────────────────────────────────────────────
// ALERTS
// ─────────────────────────────────────────────

export async function getAlerts(): Promise<Alert[]> {
  const res = await apiFetch(`${BASE_URL}/alerts`, { headers: authHeaders() });
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function markAlertRead(alertId: string): Promise<void> {
  await apiFetch(`${BASE_URL}/alerts/${alertId}/read`, {
    method: 'PATCH',
    headers: authHeaders(),
  });
}

// ─────────────────────────────────────────────
// SCHEDULED QUERIES
// ─────────────────────────────────────────────

export async function getScheduled(): Promise<ScheduledQuery[]> {
  const res = await apiFetch(`${BASE_URL}/scheduled`, {
    headers: authHeaders(),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function createScheduled(payload: {
  query_text: string;
  cron_expression: string;
  delivery: string;
  delivery_email?: string;
  alert_condition?: string;
  alert_severity?: string;
}): Promise<ScheduledQuery> {
  const res = await apiFetch(`${BASE_URL}/scheduled`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create scheduled query');
  return res.json();
}

export async function updateScheduled(
  id: string,
  payload: {
    query_text?: string;
    cron_expression?: string;
    delivery?: string;
    delivery_email?: string;
    is_active?: boolean;
    alert_condition?: string;
    alert_severity?: string;
  },
): Promise<ScheduledQuery> {
  const res = await apiFetch(`${BASE_URL}/scheduled/${id}`, {
    method: 'PATCH',
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update scheduled query');
  return res.json();
}

export async function toggleScheduled(id: string, is_active: boolean) {
  return updateScheduled(id, { is_active });
}

export async function getScheduledHistory(id: string) {
  const res = await apiFetch(`${BASE_URL}/scheduled/${id}/history`, {
    headers: authHeaders(),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function deleteScheduled(id: string): Promise<void> {
  const res = await apiFetch(`${BASE_URL}/scheduled/${id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Failed to delete scheduled query');
}

// ─────────────────────────────────────────────
// DASHBOARD CARDS
// ─────────────────────────────────────────────

export async function getDashboardCards(): Promise<DashboardCard[]> {
  const res = await apiFetch(`${BASE_URL}/dashboard/cards`, {
    headers: authHeaders(),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

// ─────────────────────────────────────────────
// ADMIN (PLATFORM_ADMIN only)
// ─────────────────────────────────────────────

export async function adminGetTables(): Promise<AdminTable[]> {
  const res = await apiFetch(`${BASE_URL}/admin/tables`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Unauthorized or failed to fetch tables');
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function adminGetTeams(): Promise<AdminTeam[]> {
  const res = await apiFetch(`${BASE_URL}/admin/teams`, {
    headers: authHeaders(),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function adminGetUsers(): Promise<AdminUser[]> {
  const res = await apiFetch(`${BASE_URL}/admin/users`, {
    headers: authHeaders(),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function adminAssignTables(payload: {
  team_id: string;
  table_assignments: {
    table_name: string;
    semantic_definition: string;
    columns_metadata: object[];
  }[];
}) {
  const res = await apiFetch(`${BASE_URL}/admin/assign`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to assign tables');
  return res.json();
}

export async function adminRevokeTable(masterConfigId: string) {
  const res = await apiFetch(`${BASE_URL}/admin/revoke/${masterConfigId}`, {
    method: 'PATCH',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Failed to revoke table');
  return res.json();
}

export async function adminUpdateUserAccess(userId: string, teamIds: string[]) {
  const res = await apiFetch(`${BASE_URL}/admin/users/${userId}/access`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ team_ids: teamIds }),
  });
  if (!res.ok) throw new Error('Failed to update user access');
  return res.json();
}

// ─────────────────────────────────────────────
// CONFIG (Data Owner)
// ─────────────────────────────────────────────

export async function createConnection(payload: {
  name: string;
  db_type: string;
  connection_string: string;
}) {
  const res = await apiFetch(`${BASE_URL}/config/connections`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create connection');
  return res.json();
}

export async function scanDatabase(connectionId: string) {
  const res = await apiFetch(`${BASE_URL}/config/scan/${connectionId}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Failed to scan database');
  return res.json();
}

export async function registerTable(payload: {
  db_connection_id: string;
  table_name: string;
  semantic_definition: string;
  columns_metadata: object[];
}) {
  const res = await apiFetch(`${BASE_URL}/config/tables`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to register table');
  return res.json();
}

export async function getConfigTables() {
  const res = await apiFetch(`${BASE_URL}/config/tables`, {
    headers: authHeaders(),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}
