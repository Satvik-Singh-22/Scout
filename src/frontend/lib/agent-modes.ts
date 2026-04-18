/**
 * Agent Mode Configuration
 *
 * Central config for agent mode labels, descriptions, and styling.
 * Change names here and they update everywhere in the UI.
 */

export type AgentMode = 'DATABASE' | 'SLACK_JIRA';

export interface AgentModeConfig {
  key: AgentMode;
  label: string;
  shortLabel: string;
  description: string;
  icon: string;
  accentColor: string;      // Tailwind text-* class
  bgColor: string;           // Tailwind bg-* class
  badgeBg: string;           // Tailwind badge background
  badgeText: string;         // Tailwind badge text color
  borderColor: string;       // Tailwind border-* class
  placeholder: string;       // Chat input placeholder
  emptyStateTitle: string;
  emptyStateDescription: string;
  suggestedQueries: string[];
  headerSubtitle: string;
}

export const AGENT_MODES: Record<AgentMode, AgentModeConfig> = {
  DATABASE: {
    key: 'DATABASE',
    label: 'Data Intelligence Agent',
    shortLabel: 'Data Intelligence',
    description: 'Query your enterprise databases with natural language',
    icon: '📊',
    accentColor: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
    badgeBg: 'bg-indigo-100',
    badgeText: 'text-indigo-700',
    borderColor: 'border-indigo-200',
    placeholder: 'Ask a question about your data...',
    emptyStateTitle: 'Scout Intelligence Portal',
    emptyStateDescription: 'Ask anything about your processed data and customer insights.',
    suggestedQueries: [
      "Which API endpoints have an average response_time_ms higher than average?",
      "Is there a correlation between latency_ms in the Tyk gateway and specific api_name values?",
      "Which services have reported cpu_usage_pct exceeding 80% in the last hour?",
      "Show the share of transactions by region",
      "Which customers have unusually high refund-to-transaction ratios?",
    ],
    headerSubtitle: 'Data Pipeline Active',
  },
  SLACK_JIRA: {
    key: 'SLACK_JIRA',
    label: 'Workflow Agent',
    shortLabel: 'Workflow',
    description: 'Search Slack conversations and Jira tickets',
    icon: '🔗',
    accentColor: 'text-violet-600',
    bgColor: 'bg-violet-50',
    badgeBg: 'bg-violet-100',
    badgeText: 'text-violet-700',
    borderColor: 'border-violet-200',
    placeholder: 'Ask about Slack messages or Jira tickets...',
    emptyStateTitle: 'Workflow Intelligence Portal',
    emptyStateDescription: 'Ask about your Slack conversations, Jira tickets, and team workflows.',
    suggestedQueries: [
      "What payment failures happened recently in Slack?",
      "Show me high priority open bugs in Jira",
      "What did the team discuss about the backend errors?",
      "Any recent deployment messages?",
      "What's the latest standup update?",
    ],
    headerSubtitle: 'Slack & Jira Pipeline Active',
  },
};

/** Helper — get config for a mode string, falling back to DATABASE */
export function getAgentModeConfig(mode?: string): AgentModeConfig {
  if (mode && mode in AGENT_MODES) {
    return AGENT_MODES[mode as AgentMode];
  }
  return AGENT_MODES.DATABASE;
}
