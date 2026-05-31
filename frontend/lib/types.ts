export type UserContext = {
  user_id: string;
  username: string;
  display_name?: string | null;
  email?: string | null;
  is_platform_admin?: boolean;
};

export type Subscription = {
  id: string;
  group_id?: string | null;
  name: string;
  service_url?: string | null;
  account_identifier_masked?: string | null;
  category_key?: string | null;
  status: string;
  billing_interval: string;
  amount_minor?: number | null;
  amount_model: string;
  estimate_strategy: string;
  estimate_confidence: string;
  currency: string;
  renewal_date?: string | null;
  trial_end_date?: string | null;
  calendar_event_id?: string | null;
  calendar_external_ref?: string | null;
  calendar_sync_status: string;
  calendar_sync_error?: string | null;
  monthly_minor?: number | null;
  yearly_minor?: number | null;
  is_estimated: boolean;
  notes?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type Group = {
  id: string;
  name: string;
  service_url?: string | null;
  status: string;
  billing_interval: string;
  amount_minor?: number | null;
  amount_model: string;
  estimate_strategy: string;
  estimate_confidence: string;
  currency: string;
  renewal_date?: string | null;
  calendar_event_id?: string | null;
  calendar_external_ref?: string | null;
  calendar_sync_status: string;
  calendar_sync_error?: string | null;
  monthly_minor?: number | null;
  yearly_minor?: number | null;
  is_estimated: boolean;
  notes?: string | null;
  subscriptions: Subscription[];
};

export type DashboardSummary = {
  month: string;
  due_this_month_minor: number;
  paid_this_month_minor: number;
  remaining_this_month_minor: number;
  next_month_due_minor: number;
  variable_estimated_minor: number;
  active_subscriptions: number;
  active_groups: number;
  recommendations_active: number;
  currency: string;
};

export type ForecastSummary = {
  monthly_total_minor: number;
  yearly_total_minor: number;
  estimated_minor: number;
  active_subscriptions: number;
  active_groups: number;
  currency: string;
  next_payment?: { date: string; amount_minor: number; source_type: string; source_id: string } | null;
};

export type MonthlyPoint = { month: string; amount_minor: number; paid_minor: number; estimated_minor: number; currency: string };
export type Recommendation = { id: string; target_type: string; target_id: string; type: string; severity: string; confidence: number; title: string; explanation: string; estimated_saving_minor?: number | null; status: string; created_at: string };
export type AuditItem = { id: string; action: string; target_type: string; target_id: string; payload: Record<string, unknown>; created_at: string };
export type IntegrationStatus = { planner_calendar_title: string; failed_sync_count: number; pending_sync_count: number; synced_count: number };
