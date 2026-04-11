// frontend/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

const MOCK_USER = {
  id: 'user-1',
  email: 'demo@bank.com',
  name: 'Demo User',
  persona: 'MANAGER' as const,
  role: 'ANALYST' as const,
  team_id: 'team-a',
  accessible_teams: [{ team_id: 'team-a', team_name: 'Team A — Payments' }]
}

const MOCK_ADMIN_USER = {
  id: 'admin-1',
  email: 'admin@scout.dev',
  name: 'Platform Admin',
  persona: 'MANAGER' as const,
  role: 'PLATFORM_ADMIN' as const,
  team_id: null,
  accessible_teams: []
}

// Track logged-in user type for /users/me based on login email
let activeUser: {
  id: string
  email: string
  name: string
  persona: 'MANAGER' | 'DEVELOPER'
  role: string
  team_id: string | null
  accessible_teams: { team_id: string; team_name: string }[]
} = MOCK_USER

export const handlers = [
  // ─────────────────────────────────────────
  // AUTH
  // ─────────────────────────────────────────
  http.post('*/auth/login', async ({ request }) => {
    const body = await request.json() as { email?: string; password?: string }
    if (body.email === 'admin@scout.dev') {
      activeUser = MOCK_ADMIN_USER
      return HttpResponse.json({ access_token: 'mock-admin-token', user: MOCK_ADMIN_USER })
    }
    activeUser = MOCK_USER
    return HttpResponse.json({ access_token: 'mock-token', user: MOCK_USER })
  }),

  http.post('*/auth/register', async ({ request }) => {
    const body = await request.json() as Record<string, string>
    const newUser = {
      id: 'user-' + Date.now(),
      email: body.email || 'new@bank.com',
      name: body.name || 'New User',
      persona: (body.persona as 'MANAGER' | 'DEVELOPER') || 'MANAGER',
      role: (body.role as 'ANALYST' | 'DATA_OWNER' | 'ENTERPRISE_ANALYST') || 'ANALYST',
      team_id: 'team-a',
      accessible_teams: [{ team_id: 'team-a', team_name: body.team_name || 'Default Team' }]
    }
    activeUser = newUser
    return HttpResponse.json({ access_token: 'mock-token-new', user: newUser })
  }),

  // ─────────────────────────────────────────
  // USERS
  // ─────────────────────────────────────────
  http.get('*/users/me', () => HttpResponse.json(activeUser)),

  http.patch('*/users/me', async ({ request }) => {
    const body = await request.json() as Record<string, string>
    activeUser = { ...activeUser, ...body }
    return HttpResponse.json(activeUser)
  }),

  // ─────────────────────────────────────────
  // CHATROOMS
  // ─────────────────────────────────────────
  http.get('*/chatrooms', () =>
    HttpResponse.json([
      {
        id: 'room-1',
        name: 'Revenue Analysis',
        created_at: new Date(Date.now() - 86400000).toISOString(),
        last_message_preview: 'Show total payment volume this week'
      },
      {
        id: 'room-2',
        name: 'Risk Assessment Q4',
        created_at: new Date(Date.now() - 172800000).toISOString(),
        last_message_preview: 'Which regions have highest fraud rates?'
      }
    ])
  ),

  http.post('*/chatrooms', async ({ request }) => {
    const body = await request.json() as { name?: string }
    return HttpResponse.json({
      id: 'room-' + Date.now(),
      name: body.name || 'New Conversation',
      created_at: new Date().toISOString()
    })
  }),

  http.get('*/chatrooms/:id/messages', () => HttpResponse.json([])),

  // ─────────────────────────────────────────
  // SSE STREAMING
  // ─────────────────────────────────────────
  http.post('*/chatrooms/:id/message', () => {
    const stream = new ReadableStream({
      start(controller) {
        const chunks = [
          'Based on the data, ',
          'payment failures ',
          'spiked by **23%** ',
          'last Tuesday. ',
          'The primary driver was ',
          'the APAC region, ',
          'which saw a ',
          '3× increase ',
          'in declined transactions ',
          'due to gateway timeouts.'
        ]
        chunks.forEach((c, i) => {
          setTimeout(() => {
            controller.enqueue(new TextEncoder().encode(
              `data: ${JSON.stringify({ type: 'chunk', content: c })}\n\n`
            ))
            if (i === chunks.length - 1) {
              setTimeout(() => {
                controller.enqueue(new TextEncoder().encode(
                  `data: ${JSON.stringify({
                    type: 'done',
                    chain_of_thought: {
                      sources: ['mock_transactions', 'mock_api_gateway_logs'],
                      sql_executed: "SELECT COUNT(*) as failures, region, DATE(created_at) as day\nFROM mock_transactions\nWHERE status = 'FAILED'\n  AND created_at >= NOW() - INTERVAL '7 days'\nGROUP BY region, day\nORDER BY failures DESC",
                      rag_chunks_used: 0,
                      query_intent: 'SQL_ONLY',
                      confidence: 'high',
                      tables_searched: ['mock_transactions', 'mock_api_gateway_logs'],
                      tables_used: ['mock_transactions'],
                      agent_path: ['orchestrator', 'relevancy', 'sql_gen', 'execution', 'synthesis', 'persona'],
                      teams_accessed: ['Team A — Payments']
                    }
                  })}\n\n`
                ))
                controller.close()
              }, 80)
            }
          }, i * 100)
        })
      }
    })
    return new HttpResponse(stream, {
      headers: { 'Content-Type': 'text/event-stream' }
    })
  }),

  // ─────────────────────────────────────────
  // ALERTS
  // ─────────────────────────────────────────
  http.get('*/alerts', () =>
    HttpResponse.json([
      {
        id: 'a1',
        title: 'Transaction Failure Rate Spike',
        description: 'Failed rate reached 23%, exceeding the 15% threshold. Primary cause: APAC gateway timeouts.',
        severity: 'HIGH',
        data_snapshot: { rate: 0.23, threshold: 0.15, region: 'APAC' },
        is_read: false,
        created_at: new Date(Date.now() - 1800000).toISOString()
      },
      {
        id: 'a2',
        title: 'API Latency Elevated',
        description: 'P95 latency on /payments/process exceeded 2000ms for the last 30 minutes.',
        severity: 'MEDIUM',
        data_snapshot: { p95_ms: 2340, threshold_ms: 2000 },
        is_read: false,
        created_at: new Date(Date.now() - 3600000).toISOString()
      },
      {
        id: 'a3',
        title: 'New Schema Drift Detected',
        description: 'Column `settlement_currency` was added to mock_settlements. Review and update semantic definitions.',
        severity: 'LOW',
        data_snapshot: null,
        is_read: true,
        created_at: new Date(Date.now() - 86400000).toISOString()
      }
    ])
  ),

  http.patch('*/alerts/:id/read', ({ params }) =>
    HttpResponse.json({ id: params.id, is_read: true })
  ),

  // ─────────────────────────────────────────
  // SCHEDULED QUERIES
  // ─────────────────────────────────────────
  http.get('*/scheduled', () =>
    HttpResponse.json([
      {
        id: 'sq-1',
        query_text: 'What is the daily failure rate for the last 7 days?',
        cron_expression: '0 8 * * *',
        delivery: 'EMAIL',
        is_active: true,
        alert_condition: 'Alert me if the failure rate exceeds 5%',
        alert_severity: 'HIGH',
        last_run_at: new Date(Date.now() - 86400000).toISOString(),
        next_run_at: new Date(Date.now() + 43200000).toISOString()
      },
      {
        id: 'sq-2',
        query_text: 'Summarize top 5 customers by revenue this month',
        cron_expression: '0 9 * * 1',
        delivery: 'DASHBOARD',
        is_active: false,
        alert_condition: null,
        alert_severity: null,
        last_run_at: null,
        next_run_at: null
      }
    ])
  ),

  http.post('*/scheduled', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json({
      id: 'sq-' + Date.now(),
      ...body,
      is_active: true,
      next_run_at: new Date(Date.now() + 86400000).toISOString(),
      last_run_at: null
    })
  }),

  http.patch('*/scheduled/:id', async ({ params, request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json({ id: params.id, ...body })
  }),

  http.get('*/scheduled/:id/history', () =>
    HttpResponse.json([
      {
        id: 'run-1',
        executed_at: new Date(Date.now() - 86400000).toISOString(),
        result: { answer: 'Average failure rate was 4.2% over the past 7 days.' },
        status: 'SUCCESS'
      }
    ])
  ),

  // ─────────────────────────────────────────
  // DASHBOARD
  // ─────────────────────────────────────────
  http.get('*/dashboard/cards', () =>
    HttpResponse.json([
      {
        id: 'dc-1',
        title: 'Weekly Payment Volume',
        query_result: { answer: '$14.2M processed across 83,420 transactions' },
        chart_type: 'BAR',
        created_at: new Date().toISOString()
      },
      {
        id: 'dc-2',
        title: 'Failure Rate Trend',
        query_result: {
          answer: '4.2% average, trending down from 6.8% last week',
          sql_results: [
            { day: 'Mon', rate: 0.068 },
            { day: 'Tue', rate: 0.052 },
            { day: 'Wed', rate: 0.041 },
            { day: 'Thu', rate: 0.038 },
            { day: 'Fri', rate: 0.035 }
          ]
        },
        chart_type: 'LINE',
        created_at: new Date().toISOString()
      }
    ])
  ),

  // ─────────────────────────────────────────
  // ADMIN
  // ─────────────────────────────────────────
  http.get('*/admin/tables', () =>
    HttpResponse.json([
      { table_name: 'mock_transactions', column_count: 10, team_assignments: [{ config_id: 'mc-1', team_id: 'team-a', team_name: 'Team A — Payments', is_active: true }] },
      { table_name: 'mock_payment_methods', column_count: 6, team_assignments: [{ config_id: 'mc-2', team_id: 'team-a', team_name: 'Team A — Payments', is_active: true }] },
      { table_name: 'mock_settlements', column_count: 8, team_assignments: [{ config_id: 'mc-3', team_id: 'team-a', team_name: 'Team A — Payments', is_active: true }] },
      { table_name: 'mock_api_gateway_logs', column_count: 9, team_assignments: [{ config_id: 'mc-4', team_id: 'team-b', team_name: 'Team B — Operations', is_active: true }] },
      { table_name: 'mock_system_health', column_count: 7, team_assignments: [{ config_id: 'mc-5', team_id: 'team-b', team_name: 'Team B — Operations', is_active: true }] },
      { table_name: 'mock_fraud_flags', column_count: 11, team_assignments: [{ config_id: 'mc-6', team_id: 'team-c', team_name: 'Team C — Risk', is_active: true }] },
      { table_name: 'mock_risk_scores', column_count: 5, team_assignments: [{ config_id: 'mc-7', team_id: 'team-c', team_name: 'Team C — Risk', is_active: true }] },
      { table_name: 'mock_customers', column_count: 8, team_assignments: [{ config_id: 'mc-8', team_id: 'team-d', team_name: 'Team D — Customer', is_active: true }] },
      { table_name: 'mock_customer_feedback', column_count: 6, team_assignments: [{ config_id: 'mc-9', team_id: 'team-d', team_name: 'Team D — Customer', is_active: true }] },
      { table_name: 'mock_revenue_daily', column_count: 5, team_assignments: [{ config_id: 'mc-10', team_id: 'team-e', team_name: 'Team E — Finance', is_active: true }] },
      { table_name: 'mock_expense_reports', column_count: 7, team_assignments: [] },
      { table_name: 'mock_compliance_audits', column_count: 9, team_assignments: [] }
    ])
  ),

  http.get('*/admin/teams', () =>
    HttpResponse.json([
      { id: 'team-a', name: 'Team A — Payments', table_count: 12, member_count: 3 },
      { id: 'team-b', name: 'Team B — Operations', table_count: 10, member_count: 2 },
      { id: 'team-c', name: 'Team C — Risk', table_count: 6, member_count: 2 },
      { id: 'team-d', name: 'Team D — Customer', table_count: 6, member_count: 2 },
      { id: 'team-e', name: 'Team E — Finance', table_count: 6, member_count: 1 }
    ])
  ),

  http.get('*/admin/users', () =>
    HttpResponse.json([
      {
        id: 'u-1',
        name: 'Demo User',
        email: 'demo@bank.com',
        role: 'ANALYST',
        team_id: 'team-a',
        team_name: 'Team A — Payments',
        accessible_teams: [{ team_id: 'team-a', team_name: 'Team A — Payments' }]
      },
      {
        id: 'u-2',
        name: 'Enterprise User',
        email: 'enterprise@scout.dev',
        role: 'ENTERPRISE_ANALYST',
        team_id: 'team-a',
        team_name: 'Team A — Payments',
        accessible_teams: [
          { team_id: 'team-a', team_name: 'Team A — Payments' },
          { team_id: 'team-b', team_name: 'Team B — Operations' }
        ]
      },
      {
        id: 'u-3',
        name: 'Risk Analyst',
        email: 'risk@scout.dev',
        role: 'ANALYST',
        team_id: 'team-c',
        team_name: 'Team C — Risk',
        accessible_teams: [{ team_id: 'team-c', team_name: 'Team C — Risk' }]
      }
    ])
  ),

  http.post('*/admin/assign', () =>
    HttpResponse.json({ assigned_count: 5, team_id: 'team-a' })
  ),

  http.patch('*/admin/revoke/:id', ({ params }) =>
    HttpResponse.json({ id: params.id, is_active: false })
  ),

  http.post('*/admin/users/:id/access', () =>
    HttpResponse.json({ user_id: 'u-2', accessible_teams: [] })
  ),

  // ─────────────────────────────────────────
  // CONFIG (Data Owner)
  // ─────────────────────────────────────────
  http.post('*/config/connections', () =>
    HttpResponse.json({ id: 'conn-1', name: 'Primary PostgreSQL', status: 'CONNECTED' })
  ),

  http.get('*/config/scan/:id', () =>
    HttpResponse.json({
      tables: [
        { table_name: 'mock_transactions', column_count: 10 },
        { table_name: 'mock_customers', column_count: 8 },
        { table_name: 'mock_settlements', column_count: 8 }
      ]
    })
  ),

  http.post('*/config/tables', () =>
    HttpResponse.json({ id: 'tbl-1', status: 'REGISTERED' })
  ),

  http.get('*/config/tables', () =>
    HttpResponse.json([
      { table_name: 'mock_transactions', semantic_definition: 'Core transaction data', status: 'ACTIVE' },
      { table_name: 'mock_customers', semantic_definition: 'Customer profiles and demographics', status: 'ACTIVE' }
    ])
  )
]
