# PERSON 3 — FRONTEND ENGINEER
## Read 00_MASTER_SHARED_CONTEXT.md first. Everything in that document applies to you.

---

## YOUR ROLE

You own the entire Next.js 14 application. You build every page, every component, every UI interaction. You use the API contracts from Master Shared Context section 7 to build against. From hour 2 to hour 24, you use MSW (Mock Service Worker) so you never wait for Person 2's backend to be live. At hour 24, you swap MSW for real API calls. You never touch backend files.

---

## YOUR FILES — COMPLETE LIST

```
frontend/app/layout.tsx
frontend/app/page.tsx                              ← redirect to /login or /chat
frontend/app/(auth)/login/page.tsx
frontend/app/(auth)/register/page.tsx
frontend/app/(portal)/layout.tsx                   ← sidebar navigation
frontend/app/(portal)/chat/page.tsx                ← chatroom list
frontend/app/(portal)/chat/[chatroom_id]/page.tsx  ← active chatroom
frontend/app/(portal)/dashboard/page.tsx           ← Manager dashboard + cards
frontend/app/(portal)/onboarding/page.tsx          ← 4-step Data Owner flow
frontend/app/(portal)/alerts/page.tsx              ← Alert Center
frontend/app/(portal)/scheduled/page.tsx           ← Scheduled queries list
frontend/app/(portal)/scheduled/[id]/history/page.tsx ← Past run history
frontend/app/(portal)/settings/page.tsx            ← Persona toggle + display name
frontend/components/Chatroom.tsx
frontend/components/ChainOfThought.tsx
frontend/components/ManagerDashboard.tsx
frontend/components/DeveloperView.tsx
frontend/components/MessageBubble.tsx
frontend/components/AlertCenter.tsx
frontend/components/ScheduledQueryForm.tsx
frontend/components/OnboardingFlow.tsx
frontend/components/DashboardCard.tsx
frontend/lib/api-client.ts
```

---

## HOUR-BY-HOUR PLAN

### Hour 0–2 (with team)
- Scaffold Next.js 14: `npx create-next-app@14 frontend --typescript --tailwind --app`
- Install dependencies: `npm install recharts lucide-react js-cookie eventsource-parser`
- Install shadcn/ui: `npx shadcn-ui@latest init`
- Install MSW: `npm install msw --save-dev`
- Copy API contracts from Master Shared Context into `/lib/api-client.ts` as typed interfaces.

### Hour 2–16 (build all pages and components against MSW)
Build in this order: `api-client.ts` → `login` → `register` → `chat list` → `chatroom` → `ChainOfThought` → `ManagerDashboard` → `DeveloperView` → `MessageBubble`

### Hour 16–24 (build secondary screens)
Build: `onboarding` (4 steps) → `alerts` → `scheduled` → `dashboard` → `settings` → `scheduled/[id]/history`

### Hour 24 (integration)
- Remove MSW handlers.
- Update `NEXT_PUBLIC_API_URL` in `.env.local` to Person 2's deployed backend URL.
- Test chatroom end-to-end: send query, see streaming answer, see CoT panel.

### Hour 24–36 (polish)
- Add loading states to every page that fetches data.
- Add error states.
- Add empty states (no chatrooms yet, no alerts).
- Test persona switching (change persona in settings, run same query, compare output).

### Hour 36–44 (final checks)
- Mobile responsiveness pass.
- Confirm CoT panel opens/closes correctly.
- Confirm Manager gets charts, Developer gets SQL code block.
- Record demo backup video.

---

## FILE 1: `lib/api-client.ts`

This is the single file all pages import. Never use `fetch` directly in a page component.

```typescript
import Cookies from 'js-cookie'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function getToken(): string {
  return Cookies.get('access_token') || ''
}

function authHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}`
  }
}

export interface User {
  id: string
  email: string
  name: string
  persona: 'MANAGER' | 'DEVELOPER'
  role: 'DATA_OWNER' | 'ANALYST'
}

export interface Message {
  id: string
  role: 'USER' | 'ASSISTANT'
  content: string
  chain_of_thought: ChainOfThought | null
  created_at: string
}

export interface ChainOfThought {
  sources: string[]
  sql_executed: string
  rag_chunks_used: number
  agent_path: string[]
  query_intent: string
  confidence: string
  tables_searched: string[]
  tables_used: string[]
}

export interface Chatroom {
  id: string
  name: string
  created_at: string
  last_message_preview?: string
}

export interface Alert {
  id: string
  title: string
  description: string
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
  data_snapshot: object | null
  is_read: boolean
  created_at: string
}

export interface ScheduledQuery {
  id: string
  query_text: string
  cron_expression: string
  delivery: 'EMAIL' | 'DASHBOARD'
  is_active: boolean
  last_run_at: string | null
  next_run_at: string | null
}

export interface DashboardCard {
  id: string
  title: string
  query_result: object
  chart_type: 'BAR' | 'LINE' | 'PIE' | 'TABLE'
  created_at: string
}

// Auth
export async function login(email: string, password: string) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Login failed')
  Cookies.set('access_token', data.access_token, { expires: 1 })
  return data as { access_token: string; user: User }
}

export async function register(payload: {
  email: string; password: string; name: string;
  persona: string; role: string; team_name: string
}) {
  const res = await fetch(`${BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Registration failed')
  Cookies.set('access_token', data.access_token, { expires: 1 })
  return data as { access_token: string; user: User }
}

export function logout() {
  Cookies.remove('access_token')
}

// Chatrooms
export async function getChatrooms(): Promise<Chatroom[]> {
  const res = await fetch(`${BASE_URL}/chatrooms`, { headers: authHeaders() })
  if (!res.ok) throw new Error('Failed to fetch chatrooms')
  return res.json()
}

export async function createChatroom(name: string): Promise<Chatroom> {
  const res = await fetch(`${BASE_URL}/chatrooms`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ name })
  })
  return res.json()
}

export async function getMessages(chatroomId: string): Promise<Message[]> {
  const res = await fetch(`${BASE_URL}/chatrooms/${chatroomId}/messages`, { headers: authHeaders() })
  return res.json()
}

// SSE streaming for chat
export function streamMessage(
  chatroomId: string,
  query: string,
  onChunk: (text: string) => void,
  onDone: (cot: ChainOfThought) => void,
  onError: (err: string) => void
): () => void {
  const controller = new AbortController()

  fetch(`${BASE_URL}/chatrooms/${chatroomId}/message`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ query }),
    signal: controller.signal
  }).then(async (res) => {
    const reader = res.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'chunk') onChunk(event.content)
            if (event.type === 'done') onDone(event.chain_of_thought)
            if (event.type === 'error') onError(event.message)
          } catch {}
        }
      }
    }
  }).catch((err) => {
    if (err.name !== 'AbortError') onError(err.message)
  })

  return () => controller.abort()
}

// Alerts
export async function getAlerts(): Promise<Alert[]> {
  const res = await fetch(`${BASE_URL}/alerts`, { headers: authHeaders() })
  return res.json()
}

export async function markAlertRead(alertId: string): Promise<void> {
  await fetch(`${BASE_URL}/alerts/${alertId}/read`, { method: 'PATCH', headers: authHeaders() })
}

// Config
export async function scanDatabase(connectionId: string) {
  const res = await fetch(`${BASE_URL}/config/scan/${connectionId}`, { headers: authHeaders() })
  return res.json()
}

export async function saveTableConfig(payload: object) {
  const res = await fetch(`${BASE_URL}/config/tables`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(payload)
  })
  return res.json()
}

export async function getConfigTables() {
  const res = await fetch(`${BASE_URL}/config/tables`, { headers: authHeaders() })
  return res.json()
}

// Scheduled
export async function getScheduledQueries(): Promise<ScheduledQuery[]> {
  const res = await fetch(`${BASE_URL}/scheduled`, { headers: authHeaders() })
  return res.json()
}

export async function createScheduledQuery(payload: object): Promise<ScheduledQuery> {
  const res = await fetch(`${BASE_URL}/scheduled`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(payload)
  })
  return res.json()
}

export async function getScheduleHistory(id: string) {
  const res = await fetch(`${BASE_URL}/scheduled/${id}/history`, { headers: authHeaders() })
  return res.json()
}

// Dashboard
export async function getDashboardCards(): Promise<DashboardCard[]> {
  const res = await fetch(`${BASE_URL}/dashboard/cards`, { headers: authHeaders() })
  return res.json()
}

// User
export async function getMe(): Promise<User> {
  const res = await fetch(`${BASE_URL}/users/me`, { headers: authHeaders() })
  return res.json()
}

export async function updateMe(payload: { persona?: string; name?: string }): Promise<User> {
  const res = await fetch(`${BASE_URL}/users/me`, {
    method: 'PATCH', headers: authHeaders(), body: JSON.stringify(payload)
  })
  return res.json()
}
```

---

## COMPONENT: `Chatroom.tsx`

**What it does:** Renders a full chatroom. Shows message history. Has an input at the bottom. On submit, calls `streamMessage()` and renders chunks as they arrive. Below each assistant message, shows the `ChainOfThought` expandable panel.

**State it manages:**
- `messages: Message[]` — loaded from `getMessages()` on mount
- `streamingText: string` — accumulates as SSE chunks arrive
- `isStreaming: boolean` — true while pipeline is running
- `inputValue: string` — current input field value

**Persona rendering:**
- If `user.persona === 'MANAGER'`: render `<ManagerDashboard />` with any chart data from message content
- If `user.persona === 'DEVELOPER'`: render `<DeveloperView />` with SQL block

**Key behavior:**
- When streaming starts: append empty assistant message with `isStreaming: true`
- As chunks arrive: update that message's content
- When done event arrives: update message with final content + chain_of_thought, set `isStreaming: false`
- Auto-scroll to bottom after every new chunk

---

## COMPONENT: `ChainOfThought.tsx`

**What it does:** Collapsible panel shown below every assistant message. Shows the full CoT JSON in a readable format.

**Props:** `cot: ChainOfThought | null`

**Rendered sections (only if data exists):**
1. **Sources used** — badge list of table names from `cot.sources`
2. **SQL executed** — code block with syntax highlighting (gray background, monospace font). Only shown if `cot.sql_executed` is non-empty.
3. **Text sources** — "Searched customer reviews (N excerpts used)" if `cot.rag_chunks_used > 0`
4. **Agent path** — horizontal pill chain showing each agent name
5. **Confidence** — badge: HIGH (green), MEDIUM (amber), LOW (red)

**Toggle behavior:** Collapsed by default. Click "Show reasoning" to expand.

---

## COMPONENT: `ManagerDashboard.tsx`

**What it does:** Renders the Manager persona answer as a visual card. Used inside the chatroom for Manager users.

**Props:** `answer: string`, `sqlResults: object[]`, `chatroomId: string`

**Chart logic:**
- If `sqlResults` has 2 columns where one is a string/category and one is a number: render `BarChart`
- If `sqlResults` has a timestamp/date column and a number column: render `LineChart`
- If `sqlResults` has 3+ rows and percentages: render `PieChart`
- Otherwise: render the answer as styled text with no chart

**Recharts implementation:**
```tsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'

// Always wrap in: <ResponsiveContainer width="100%" height={300}>
// Colors: use ["#7F77DD", "#1D9E75", "#D85A30"] for multi-series
```

---

## COMPONENT: `DeveloperView.tsx`

**What it does:** Renders the Developer persona answer with technical detail. Used inside the chatroom for Developer users.

**Props:** `answer: string`, `chainOfThought: ChainOfThought | null`

**Layout:**
1. Answer text (full, technical)
2. If `cot.sql_executed`: SQL code block in `<pre><code>` with gray background
3. Tables referenced as monospace badges
4. "RAG sources used: N customer review excerpts" if `rag_chunks_used > 0`

---

## COMPONENT: `OnboardingFlow.tsx`

**What it does:** 4-step wizard for Data Owners to register their database and configure table access.

**Step 1 — Connect database:**
- Form fields: Connection Name (text), Database Type (select: POSTGRES/MYSQL), Connection String (password input)
- Submit calls `POST /config/connections`
- On success: save `connection_id` to local state, advance to Step 2

**Step 2 — Select tables:**
- Calls `GET /config/scan/{connection_id}` to load table list
- Render checklist of table names with column counts
- All checked by default
- User can uncheck sensitive tables
- "Next" button advances to Step 3 with the checked table list

**Step 3 — Define table semantics:**
- For each checked table: show a text area labeled "What does this table contain? What does 'revenue' mean here?"
- This is the `semantic_definition` field
- Also show the columns list and allow the user to add descriptions per column
- "Save All" calls `POST /config/tables` for each table

**Step 4 — Confirmation:**
- Show summary: "X tables registered for your team"
- Show the registered tables with their definitions
- Button: "Go to Dashboard"

---

## PAGE: `app/(portal)/dashboard/page.tsx`

**Two sections:**
1. **Ask a question** — links to chatroom with a prominent CTA
2. **Saved dashboard cards** — grid of `DashboardCard` components from `GET /dashboard/cards`

Each `DashboardCard` shows: title, timestamp, chart (rendered from `query_result` + `chart_type`), "View in Chat" link.

---

## PAGE: `app/(portal)/alerts/page.tsx`

**Renders `AlertCenter` component.**

Alert list sorted by `created_at` descending. Each alert card:
- Severity badge: HIGH = red background, MEDIUM = amber, LOW = blue
- Title (bold)
- Description text
- Timestamp
- Data snapshot: collapsible pre/code block showing the triggering data
- "Mark as read" button (calls `PATCH /alerts/{id}/read`, fades the card)

Unread alerts have a solid left border accent. Read alerts are slightly dimmed.

---

## PAGE: `app/(portal)/scheduled/page.tsx`

**Two sections:**
1. **Create new scheduled query** — renders `ScheduledQueryForm`
2. **Your schedules** — list of saved `ScheduledQuery` records with toggle active/inactive and link to history

**`ScheduledQueryForm` fields:**
- Query text (large textarea)
- Frequency (select: Daily at 6pm / Weekly Monday 9am / Hourly / Custom cron)
- Delivery: Radio buttons — "Dashboard card" or "Email"
- Email address (shown only if delivery=EMAIL)
- Submit calls `POST /scheduled`

**Cron expressions for preset frequencies:**
- Daily at 6pm: `"0 18 * * *"`
- Weekly Monday 9am: `"0 9 * * 1"`
- Hourly: `"0 * * * *"`

---

## PAGE: `app/(portal)/settings/page.tsx`

**Three sections:**

1. **Display name** — text input, shows current name, save button calls `PATCH /users/me`
2. **Persona** — two large radio cards side by side:
   - Manager card: icon, "Business insights, simplified answers, charts" description
   - Developer card: icon, "SQL queries, technical details, full data context"
   - On select + save: calls `PATCH /users/me` with `{persona: "MANAGER"|"DEVELOPER"}`
3. **Account info** — read-only: email, role, team

---

## PORTAL LAYOUT: `app/(portal)/layout.tsx`

**Sidebar navigation with links:**
- Chat (icon: MessageSquare)
- Dashboard (icon: BarChart)
- Alerts (icon: Bell) — shows unread count badge
- Scheduled (icon: Clock)
- Onboarding (icon: Database) — only visible if `user.role === 'DATA_OWNER'`
- Settings (icon: Settings)
- Logout button at bottom

**Auth check:** If no token in cookie, redirect to `/login`.

---

## MSW MOCK SETUP (use until hour 24)

Create `/mocks/handlers.ts` with mock responses matching API contracts exactly:

```typescript
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.post('/auth/login', () =>
    HttpResponse.json({
      access_token: 'mock-token',
      user: { id: '1', email: 'demo@bank.com', name: 'Demo User', persona: 'MANAGER', role: 'ANALYST' }
    })
  ),
  http.get('/chatrooms', () =>
    HttpResponse.json([
      { id: '1', name: 'Revenue Analysis', created_at: new Date().toISOString() }
    ])
  ),
  http.post('/chatrooms/:id/message', async ({ request }) => {
    // Return mock SSE stream
    const stream = new ReadableStream({
      start(controller) {
        const chunks = ['Revenue ', 'dropped ', '11% ', 'in ', 'February.']
        chunks.forEach((c, i) => {
          setTimeout(() => {
            controller.enqueue(new TextEncoder().encode(
              `data: ${JSON.stringify({ type: 'chunk', content: c })}\n\n`
            ))
            if (i === chunks.length - 1) {
              controller.enqueue(new TextEncoder().encode(
                `data: ${JSON.stringify({ type: 'done', chain_of_thought: {
                  sources: ['mock_transactions'],
                  sql_executed: 'SELECT SUM(amount) FROM mock_transactions...',
                  rag_chunks_used: 0,
                  query_intent: 'SQL_ONLY',
                  confidence: 'high',
                  tables_searched: ['mock_transactions'],
                  tables_used: ['mock_transactions'],
                  agent_path: ['orchestrator','relevancy','sql_gen','execution','synthesis','persona']
                }})}\n\n`
              ))
              controller.close()
            }
          }, i * 100)
        })
      }
    })
    return new HttpResponse(stream, {
      headers: { 'Content-Type': 'text/event-stream' }
    })
  }),
  http.get('/alerts', () =>
    HttpResponse.json([
      { id: '1', title: 'Transaction Failure Rate Spike', description: 'Failed transaction rate reached 23% in the past hour, exceeding the 15% threshold.', severity: 'HIGH', data_snapshot: { rate: 0.23, threshold: 0.15 }, is_read: false, created_at: new Date().toISOString() },
      { id: '2', title: 'API Latency Elevated', description: 'P95 latency on /payments/process exceeded 2000ms.', severity: 'MEDIUM', data_snapshot: null, is_read: false, created_at: new Date().toISOString() }
    ])
  )
]
```

At hour 24: delete the MSW setup, update `.env.local` `NEXT_PUBLIC_API_URL` to real backend.

---

## `.env.local.example`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Banquoite
```
