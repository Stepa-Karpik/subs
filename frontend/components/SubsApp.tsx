"use client";

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import { amountFromMonthly, amountFromYearly, formatMoney, fromMinor, toMinor } from '@/lib/money';
import type { AuditItem, DashboardSummary, ForecastSummary, Group, IntegrationStatus, MonthlyPoint, Recommendation, Subscription, UserContext } from '@/lib/types';

type Tab = 'overview' | 'subscriptions' | 'groups' | 'forecast' | 'recommendations' | 'integrations' | 'history';
type Lang = 'ru' | 'en';
type Theme = 'dark' | 'light';

type Labels = typeof labels.ru;

type SubForm = {
  name: string;
  service_url: string;
  account_identifier: string;
  category_key: string;
  status: string;
  billing_interval: string;
  amount_model: string;
  amount_minor: number;
  monthly: string;
  yearly: string;
  renewal_date: string;
  trial_end_date: string;
  group_id: string;
  notes: string;
};

type GroupForm = {
  name: string;
  service_url: string;
  status: string;
  billing_interval: string;
  amount_model: string;
  amount_minor: number;
  monthly: string;
  yearly: string;
  renewal_date: string;
  notes: string;
};

const tabs: { key: Tab; href: string; ru: string; en: string }[] = [
  { key: 'overview', href: '/', ru: 'Обзор', en: 'Overview' },
  { key: 'subscriptions', href: '/subscriptions', ru: 'Подписки', en: 'Subscriptions' },
  { key: 'groups', href: '/groups', ru: 'Группы', en: 'Groups' },
  { key: 'forecast', href: '/forecast', ru: 'Прогноз', en: 'Forecast' },
  { key: 'recommendations', href: '/recommendations', ru: 'AI рекомендации', en: 'AI insights' },
  { key: 'integrations', href: '/integrations', ru: 'Интеграции', en: 'Integrations' },
  { key: 'history', href: '/history', ru: 'История', en: 'History' }
];

const labels = {
  ru: {
    addSub: 'Добавить подписку', editSub: 'Редактировать подписку', addGroup: 'Создать группу', editGroup: 'Редактировать группу', paid: 'Оплачено', runAi: 'Запустить анализ',
    due: 'К оплате в этом месяце', alreadyPaid: 'Уже оплачено', remaining: 'Осталось оплатить', nextMonth: 'Следующий месяц',
    activeSubs: 'Активные подписки', activeGroups: 'Группы', recommendations: 'Рекомендации', forecast12: 'Прогноз на 12 месяцев',
    name: 'Название', account: 'Аккаунт', group: 'Группа', renewal: 'Дата оплаты', interval: 'Интервал', amount: 'Сумма', type: 'Тип суммы', status: 'Статус', calendar: 'Календарь',
    save: 'Сохранить', cancel: 'Отмена', delete: 'Удалить', url: 'Ссылка', category: 'Категория', month: 'руб/мес', year: 'руб/год', history: 'История', sync: 'Синхронизация', noData: 'Данных пока нет',
    search: 'Поиск по названию, сервису, аккаунту', allStatuses: 'Все статусы', allIntervals: 'Все интервалы', allCategories: 'Все категории', allGroups: 'Все группы', standalone: 'Без группы', notes: 'Заметки', trialEnd: 'Конец пробного периода',
    upcoming: 'Ближайшие оплаты', attention: 'Требуют внимания', composition: 'Состав', syncNow: 'Обновить синхронизацию', planner: 'Planner', logout: 'Выйти', admin: 'Админ панель', light: 'Светлая тема', dark: 'Тёмная тема',
    fixed: 'Фиксированная', variable: 'Переменная', custom: 'Своя сумма', free: 'Бесплатная', unknown: 'Неизвестна', group_child: 'Входит в группу', empty: 'Создайте первую подписку, чтобы увидеть прогноз и календарные события.'
  },
  en: {
    addSub: 'Add subscription', editSub: 'Edit subscription', addGroup: 'Create group', editGroup: 'Edit group', paid: 'Paid', runAi: 'Run analysis',
    due: 'Due this month', alreadyPaid: 'Paid', remaining: 'Remaining', nextMonth: 'Next month',
    activeSubs: 'Active subscriptions', activeGroups: 'Groups', recommendations: 'Recommendations', forecast12: '12 month forecast',
    name: 'Name', account: 'Account', group: 'Group', renewal: 'Payment date', interval: 'Interval', amount: 'Amount', type: 'Amount type', status: 'Status', calendar: 'Calendar',
    save: 'Save', cancel: 'Cancel', delete: 'Delete', url: 'URL', category: 'Category', month: 'RUB/mo', year: 'RUB/yr', history: 'History', sync: 'Sync', noData: 'No data yet',
    search: 'Search by name, service, account', allStatuses: 'All statuses', allIntervals: 'All intervals', allCategories: 'All categories', allGroups: 'All groups', standalone: 'No group', notes: 'Notes', trialEnd: 'Trial end',
    upcoming: 'Upcoming payments', attention: 'Needs attention', composition: 'Composition', syncNow: 'Sync now', planner: 'Planner', logout: 'Logout', admin: 'Admin panel', light: 'Light theme', dark: 'Dark theme',
    fixed: 'Fixed', variable: 'Variable', custom: 'Custom', free: 'Free', unknown: 'Unknown', group_child: 'Group child', empty: 'Create your first subscription to see forecast and calendar events.'
  }
};

const intervalLabels = {
  ru: { weekly: 'неделя', monthly: 'месяц', semi_annual: 'полгода', annual: 'год' },
  en: { weekly: 'week', monthly: 'month', semi_annual: 'half-year', annual: 'year' }
};
const intervals = ['weekly', 'monthly', 'semi_annual', 'annual'];
const amountModels = ['fixed', 'variable', 'custom', 'free', 'unknown'];
const statuses = ['active', 'trial', 'paused', 'cancelled', 'expired', 'archived'];
const categories = ['ai', 'media', 'cloud', 'mobile', 'software', 'finance', 'education', 'gaming', 'business', 'utilities', 'electricity', 'water', 'heating', 'gas', 'transport', 'other'];
const variableCategories = new Set(['utilities', 'electricity', 'water', 'heating', 'gas']);

function statusLabel(status: string, lang: Lang) {
  const ru: Record<string, string> = { active: 'Активна', trial: 'Пробная', paused: 'Пауза', cancelled: 'Отменена', expired: 'Истекла', archived: 'Архив', synced: 'Синхронизировано', failed: 'Ошибка', not_synced: 'Не синхронизировано', pending: 'Ожидает', deleted: 'Удалено' };
  const en: Record<string, string> = { active: 'Active', trial: 'Trial', paused: 'Paused', cancelled: 'Cancelled', expired: 'Expired', archived: 'Archived', synced: 'Synced', failed: 'Failed', not_synced: 'Not synced', pending: 'Pending', deleted: 'Deleted' };
  return (lang === 'ru' ? ru : en)[status] || status;
}

function badgeClass(value: string) {
  if (['active', 'synced', 'checked'].includes(value)) return 'green';
  if (['trial', 'pending', 'not_synced', 'warning', 'important'].includes(value)) return 'amber';
  if (['failed', 'cancelled', 'expired', 'archived'].includes(value)) return 'red';
  return '';
}

function makeSubForm(initial?: Subscription): SubForm {
  return {
    name: initial?.name || '',
    service_url: initial?.service_url || '',
    account_identifier: '',
    category_key: initial?.category_key || 'software',
    status: initial?.status || 'active',
    billing_interval: initial?.billing_interval || 'monthly',
    amount_model: initial?.amount_model === 'group_child' ? 'fixed' : initial?.amount_model || 'fixed',
    amount_minor: initial?.amount_minor || 0,
    monthly: fromMinor(initial?.monthly_minor),
    yearly: fromMinor(initial?.yearly_minor),
    renewal_date: initial?.renewal_date || '',
    trial_end_date: initial?.trial_end_date || '',
    group_id: initial?.group_id || '',
    notes: initial?.notes || '',
  };
}

function makeGroupForm(initial?: Group): GroupForm {
  return {
    name: initial?.name || '',
    service_url: initial?.service_url || '',
    status: initial?.status || 'active',
    billing_interval: initial?.billing_interval || 'monthly',
    amount_model: initial?.amount_model || 'fixed',
    amount_minor: initial?.amount_minor || 0,
    monthly: fromMinor(initial?.monthly_minor),
    yearly: fromMinor(initial?.yearly_minor),
    renewal_date: initial?.renewal_date || '',
    notes: initial?.notes || '',
  };
}

export default function SubsApp({ initialTab }: { initialTab: Tab }) {
  const [tab, setTab] = useState<Tab>(initialTab);
  const [lang, setLang] = useState<Lang>('ru');
  const [theme, setTheme] = useState<Theme>('dark');
  const [user, setUser] = useState<UserContext | null>(null);
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [forecast, setForecast] = useState<ForecastSummary | null>(null);
  const [subs, setSubs] = useState<Subscription[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [monthly, setMonthly] = useState<MonthlyPoint[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [audit, setAudit] = useState<AuditItem[]>([]);
  const [integration, setIntegration] = useState<IntegrationStatus | null>(null);
  const [modal, setModal] = useState<{ type: 'sub'; item?: Subscription } | { type: 'group'; item?: Group } | null>(null);
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [intervalFilter, setIntervalFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [groupFilter, setGroupFilter] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const t = labels[lang];

  useEffect(() => {
    const savedTheme = localStorage.getItem('subs-theme') as Theme | null;
    const savedLang = localStorage.getItem('subs-lang') as Lang | null;
    if (savedTheme) setTheme(savedTheme);
    if (savedLang) setLang(savedLang);
  }, []);

  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem('subs-theme', theme); }, [theme]);
  useEffect(() => { document.documentElement.lang = lang; localStorage.setItem('subs-lang', lang); }, [lang]);
  useEffect(() => { setTab(initialTab); }, [initialTab]);
  useEffect(() => { void loadAll(); }, []);
  useEffect(() => { void loadSubscriptions(); }, [q, statusFilter, intervalFilter, categoryFilter, groupFilter]);

  const groupById = useMemo(() => new Map(groups.map(g => [g.id, g])), [groups]);
  const groupOptions = useMemo(() => groups.map(g => ({ value: g.id, label: g.name })), [groups]);
  const upcoming = useMemo(() => [...subs].filter(s => s.renewal_date && s.status !== 'archived').sort((a, b) => String(a.renewal_date).localeCompare(String(b.renewal_date))).slice(0, 6), [subs]);

  async function loadAll() {
    setBusy(true);
    setError(null);
    try {
      const [me, dash, forecastSummary, g, f, r, a, i] = await Promise.all([
        api<UserContext>('/me'),
        api<DashboardSummary>('/dashboard/summary'),
        api<ForecastSummary>('/forecast/summary'),
        api<Group[]>('/groups'),
        api<{ months: MonthlyPoint[] }>('/forecast/monthly'),
        api<Recommendation[]>('/recommendations'),
        api<AuditItem[]>('/audit'),
        api<IntegrationStatus>('/integrations/status'),
      ]);
      setUser(me); setDashboard(dash); setForecast(forecastSummary); setGroups(g); setMonthly(f.months); setRecommendations(r); setAudit(a); setIntegration(i);
      await loadSubscriptions();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setBusy(false);
    }
  }

  async function loadSubscriptions() {
    const params = new URLSearchParams();
    if (q.trim()) params.set('q', q.trim());
    if (statusFilter) params.set('status', statusFilter);
    if (intervalFilter) params.set('interval', intervalFilter);
    if (categoryFilter) params.set('category', categoryFilter);
    if (groupFilter === 'standalone') params.set('standalone', 'true');
    if (groupFilter && groupFilter !== 'standalone') params.set('group_id', groupFilter);
    const query = params.toString();
    try {
      setSubs(await api<Subscription[]>(`/subscriptions${query ? `?${query}` : ''}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed');
    }
  }

  async function refreshAfterMutation() {
    setModal(null);
    await loadAll();
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">NS</span><div><strong>Nerior Subs</strong><small>subscriptions</small></div></div>
      <nav className="nav">{tabs.map(item => <a key={item.key} href={item.href} className={tab === item.key ? 'active' : ''} onClick={(e) => { e.preventDefault(); window.history.pushState(null, '', item.href); setTab(item.key); }}>{item[lang]}</a>)}</nav>
      <div className="sidebar-bottom">
        <button className="ghost" onClick={() => setLang(lang === 'ru' ? 'en' : 'ru')}>{lang.toUpperCase()}</button>
        <button className="ghost" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>{theme === 'dark' ? t.light : t.dark}</button>
        {user?.is_platform_admin && <a className="ghost" href={`${process.env.NEXT_PUBLIC_ADMIN_URL || 'https://admin.nerior.ru'}?service=subs`}>{t.admin}</a>}
        <div className="user-pill">{user?.display_name || user?.username || '—'}</div>
        <a className="ghost" href="https://auth.nerior.ru/logout">{t.logout}</a>
      </div>
    </aside>
    <main className="content">
      <header className="topbar">
        <div className="title-stack"><h1>{tabs.find(x => x.key === tab)?.[lang]}</h1>{busy && <span className="muted">loading</span>}</div>
        <div className="actions"><button className="secondary" onClick={() => setModal({ type: 'group' })}>{t.addGroup}</button><button className="primary" onClick={() => setModal({ type: 'sub' })}>{t.addSub}</button></div>
      </header>
      {error && <div className="error-box">{error}</div>}
      {tab === 'overview' && <Overview dashboard={dashboard} forecast={forecast} monthly={monthly} subs={upcoming} recommendations={recommendations} t={t} />}
      {tab === 'subscriptions' && <Subscriptions subs={subs} groups={groups} t={t} lang={lang} groupById={groupById} q={q} setQ={setQ} statusFilter={statusFilter} setStatusFilter={setStatusFilter} intervalFilter={intervalFilter} setIntervalFilter={setIntervalFilter} categoryFilter={categoryFilter} setCategoryFilter={setCategoryFilter} groupFilter={groupFilter} setGroupFilter={setGroupFilter} onEdit={(item) => setModal({ type: 'sub', item })} onPaid={markPaidSubscription} />}
      {tab === 'groups' && <Groups groups={groups} subs={subs} t={t} lang={lang} onEdit={(item) => setModal({ type: 'group', item })} onAddChild={addChildToGroup} onRemoveChild={removeChildFromGroup} onPaid={markPaidGroup} />}
      {tab === 'forecast' && <ForecastView monthly={monthly} forecast={forecast} subs={subs} groups={groups} t={t} />}
      {tab === 'recommendations' && <Recommendations items={recommendations} t={t} onRun={runRecommendations} onAction={recommendationAction} />}
      {tab === 'integrations' && <Integrations status={integration} t={t} onSync={syncNow} />}
      {tab === 'history' && <History items={audit} t={t} />}
    </main>
    {modal?.type === 'sub' && <SubscriptionModal initial={modal.item} groups={groups} t={t} lang={lang} onClose={() => setModal(null)} onSaved={refreshAfterMutation} />}
    {modal?.type === 'group' && <GroupModal initial={modal.item} t={t} lang={lang} onClose={() => setModal(null)} onSaved={refreshAfterMutation} />}
  </div>;

  async function markPaidSubscription(id: string) {
    const amount = window.prompt(lang === 'ru' ? 'Сумма оплаты в рублях' : 'Paid amount in RUB');
    if (!amount) return;
    await api(`/subscriptions/${id}/payments`, { method: 'POST', body: JSON.stringify({ amount_minor: toMinor(amount) }) });
    await loadAll();
  }

  async function markPaidGroup(id: string) {
    const amount = window.prompt(lang === 'ru' ? 'Сумма оплаты группы в рублях' : 'Group paid amount in RUB');
    if (!amount) return;
    await api(`/groups/${id}/payments`, { method: 'POST', body: JSON.stringify({ amount_minor: toMinor(amount) }) });
    await loadAll();
  }

  async function addChildToGroup(groupId: string) {
    const candidates = subs.filter(s => !s.group_id);
    const name = window.prompt(lang === 'ru' ? 'Введите точное название подписки для добавления в группу' : 'Enter exact subscription name to add');
    if (!name) return;
    const match = candidates.find(s => s.name.toLowerCase() === name.toLowerCase());
    if (!match) { setError(lang === 'ru' ? 'Подписка не найдена среди подписок без группы' : 'Subscription was not found among standalone subscriptions'); return; }
    await api(`/groups/${groupId}/add-subscription`, { method: 'POST', body: JSON.stringify({ subscription_id: match.id }) });
    await loadAll();
  }

  async function removeChildFromGroup(groupId: string, sub: Subscription) {
    const amount = window.prompt(lang === 'ru' ? 'Введите новую самостоятельную цену в рублях' : 'Enter new standalone price in RUB');
    if (!amount) return;
    await api(`/groups/${groupId}/remove-subscription/${sub.id}`, { method: 'POST', body: JSON.stringify({ amount_minor: toMinor(amount), amount_model: 'fixed', billing_interval: sub.billing_interval, renewal_date: sub.renewal_date }) });
    await loadAll();
  }

  async function runRecommendations() {
    setRecommendations(await api<Recommendation[]>('/recommendations/run', { method: 'POST' }));
    await loadAll();
  }

  async function recommendationAction(id: string, action: 'dismiss' | 'mark-checked') {
    await api(`/recommendations/${id}/${action}`, { method: 'POST' });
    await loadAll();
  }

  async function syncNow() {
    await api('/integrations/sync-now', { method: 'POST' });
    await loadAll();
  }
}

function Metric({ label, value, muted }: { label: string; value: string; muted?: string }) { return <div className="metric"><span>{label}</span><strong>{value}</strong>{muted && <small>{muted}</small>}</div>; }
function Panel({ title, children }: { title: string; children: React.ReactNode }) { return <div className="panel"><h2>{title}</h2><div>{children}</div></div>; }
function Row({ title, meta, action }: { title: string; meta: string; action?: React.ReactNode }) { return <div className="row"><strong>{title}</strong><span>{meta}</span>{action}</div>; }
function Badge({ children, tone = '' }: { children: React.ReactNode; tone?: string }) { return <span className={`badge ${tone}`}>{children}</span>; }

function Overview({ dashboard, forecast, monthly, subs, recommendations, t }: { dashboard: DashboardSummary | null; forecast: ForecastSummary | null; monthly: MonthlyPoint[]; subs: Subscription[]; recommendations: Recommendation[]; t: Labels }) {
  return <section className="stack">
    <div className="metric-grid">
      <Metric label={t.due} value={formatMoney(dashboard?.due_this_month_minor)} muted={dashboard?.variable_estimated_minor ? `${formatMoney(dashboard.variable_estimated_minor, true)}` : undefined} />
      <Metric label={t.alreadyPaid} value={formatMoney(dashboard?.paid_this_month_minor)} />
      <Metric label={t.remaining} value={formatMoney(dashboard?.remaining_this_month_minor)} />
      <Metric label={t.nextMonth} value={formatMoney(dashboard?.next_month_due_minor)} />
    </div>
    <div className="metric-grid">
      <Metric label={t.activeSubs} value={String(dashboard?.active_subscriptions ?? 0)} />
      <Metric label={t.activeGroups} value={String(dashboard?.active_groups ?? 0)} />
      <Metric label={t.recommendations} value={String(dashboard?.recommendations_active ?? 0)} />
      <Metric label={t.year} value={formatMoney(forecast?.yearly_total_minor)} muted={forecast?.next_payment ? `${forecast.next_payment.date} · ${formatMoney(forecast.next_payment.amount_minor)}` : undefined} />
    </div>
    <ForecastChart monthly={monthly} t={t} compact />
    <div className="two-col"><Panel title={t.upcoming}>{subs.length ? subs.map(s => <Row key={s.id} title={s.name} meta={`${s.renewal_date || '—'} · ${formatMoney(s.amount_minor, s.is_estimated)}`} />) : <Empty text={t.empty} />}</Panel><Panel title={t.attention}>{recommendations.slice(0, 5).length ? recommendations.slice(0, 5).map(r => <Row key={r.id} title={r.title} meta={r.explanation} />) : <Empty text={t.noData} />}</Panel></div>
  </section>;
}

function Subscriptions(props: { subs: Subscription[]; groups: Group[]; groupById: Map<string, Group>; t: Labels; lang: Lang; q: string; setQ: (value: string) => void; statusFilter: string; setStatusFilter: (value: string) => void; intervalFilter: string; setIntervalFilter: (value: string) => void; categoryFilter: string; setCategoryFilter: (value: string) => void; groupFilter: string; setGroupFilter: (value: string) => void; onEdit: (item: Subscription) => void; onPaid: (id: string) => void }) {
  const { subs, groups, groupById, t, lang } = props;
  return <section className="stack">
    <div className="panel"><div className="filter-row"><input value={props.q} onChange={e => props.setQ(e.target.value)} placeholder={t.search} /><select value={props.statusFilter} onChange={e => props.setStatusFilter(e.target.value)}><option value="">{t.allStatuses}</option>{statuses.map(status => <option key={status} value={status}>{statusLabel(status, lang)}</option>)}</select><select value={props.intervalFilter} onChange={e => props.setIntervalFilter(e.target.value)}><option value="">{t.allIntervals}</option>{intervals.map(interval => <option key={interval} value={interval}>{intervalLabels[lang][interval as keyof typeof intervalLabels.ru]}</option>)}</select><select value={props.categoryFilter} onChange={e => props.setCategoryFilter(e.target.value)}><option value="">{t.allCategories}</option>{categories.map(category => <option key={category} value={category}>{category}</option>)}</select><select value={props.groupFilter} onChange={e => props.setGroupFilter(e.target.value)}><option value="">{t.allGroups}</option><option value="standalone">{t.standalone}</option>{groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}</select></div></div>
    <div className="panel flush"><table><thead><tr><th>{t.name}</th><th>{t.group}</th><th>{t.renewal}</th><th>{t.type}</th><th>{t.month}</th><th>{t.year}</th><th>{t.status}</th><th>{t.calendar}</th><th></th></tr></thead><tbody>{subs.map(s => <tr key={s.id}><td><b>{s.name}</b><small>{s.account_identifier_masked || s.service_url || s.category_key || '—'}</small></td><td>{s.group_id ? groupById.get(s.group_id)?.name || '—' : '—'}</td><td>{s.renewal_date || '—'}</td><td><Badge>{t[s.amount_model as keyof Labels] || s.amount_model}</Badge></td><td>{formatMoney(s.monthly_minor, s.is_estimated)}</td><td>{formatMoney(s.yearly_minor, s.is_estimated)}</td><td><Badge tone={badgeClass(s.status)}>{statusLabel(s.status, lang)}</Badge></td><td><Badge tone={badgeClass(s.calendar_sync_status)}>{statusLabel(s.calendar_sync_status, lang)}</Badge></td><td><div className="button-row"><button className="small" onClick={() => props.onPaid(s.id)}>{t.paid}</button><button className="small secondary" onClick={() => props.onEdit(s)}>{t.save}</button></div></td></tr>)}</tbody></table>{!subs.length && <Empty text={t.noData} />}</div>
  </section>;
}

function Groups({ groups, subs, t, lang, onEdit, onAddChild, onRemoveChild, onPaid }: { groups: Group[]; subs: Subscription[]; t: Labels; lang: Lang; onEdit: (item: Group) => void; onAddChild: (id: string) => void; onRemoveChild: (groupId: string, item: Subscription) => void; onPaid: (id: string) => void }) {
  const standalone = subs.filter(s => !s.group_id).length;
  return <div className="grid-list">{groups.map(g => <div className="panel" key={g.id}><div className="button-row" style={{ justifyContent: 'space-between' }}><h2>{g.name}</h2><Badge tone={badgeClass(g.calendar_sync_status)}>{statusLabel(g.calendar_sync_status, lang)}</Badge></div><div className="split"><Metric label={t.amount} value={formatMoney(g.amount_minor, g.is_estimated)} /><Metric label={t.renewal} value={g.renewal_date || '—'} /></div><h3>{t.composition}</h3>{g.subscriptions.length ? g.subscriptions.map(s => <Row key={s.id} title={s.name} meta={t.group_child} action={<button className="small secondary" onClick={() => onRemoveChild(g.id, s)}>{t.delete}</button>} />) : <p className="muted">{t.noData}</p>}<div className="button-row"><button className="small" onClick={() => onPaid(g.id)}>{t.paid}</button><button className="small secondary" onClick={() => onEdit(g)}>{t.save}</button><button className="small secondary" disabled={!standalone} onClick={() => onAddChild(g.id)}>{t.addSub}</button></div></div>)}{!groups.length && <Empty text={t.noData} />}</div>;
}

function ForecastView({ monthly, forecast, subs, groups, t }: { monthly: MonthlyPoint[]; forecast: ForecastSummary | null; subs: Subscription[]; groups: Group[]; t: Labels }) {
  const candidates = [...subs.filter(s => !s.group_id), ...groups];
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const saving = candidates.filter(item => selected.has(item.id)).reduce((sum, item) => sum + (item.yearly_minor || 0), 0);
  return <section className="stack"><div className="metric-grid"><Metric label={t.month} value={formatMoney(forecast?.monthly_total_minor)} /><Metric label={t.year} value={formatMoney(forecast?.yearly_total_minor)} /><Metric label={t.remaining} value={formatMoney(Math.max((forecast?.yearly_total_minor || 0) - saving, 0))} /><Metric label="Scenario saving" value={formatMoney(saving)} /></div><ForecastChart monthly={monthly} t={t} /><Panel title="Scenario">{candidates.map(item => <label className="row" key={item.id}><span><input type="checkbox" checked={selected.has(item.id)} onChange={(e) => { const next = new Set(selected); if (e.target.checked) next.add(item.id); else next.delete(item.id); setSelected(next); }} /> {item.name}</span><strong>{formatMoney(item.yearly_minor, item.is_estimated)}</strong></label>)}</Panel></section>;
}

function ForecastChart({ monthly, t, compact = false }: { monthly: MonthlyPoint[]; t: Labels; compact?: boolean }) { const max = Math.max(...monthly.map(m => m.amount_minor), 1); return <div className="panel"><h2>{t.forecast12}</h2><div className={compact ? 'chart compact' : 'chart'}>{monthly.map(m => <div className="bar-wrap" key={m.month}><div className="bar" style={{ height: `${Math.max(8, (m.amount_minor / max) * (compact ? 140 : 190))}px` }} /><span>{m.month.slice(5)}</span><small>{formatMoney(m.amount_minor)}{m.estimated_minor ? ` · ${formatMoney(m.estimated_minor, true)}` : ''}</small></div>)}</div>{!monthly.length && <Empty text={t.noData} />}</div>; }

function Recommendations({ items, t, onRun, onAction }: { items: Recommendation[]; t: Labels; onRun: () => void; onAction: (id: string, action: 'dismiss' | 'mark-checked') => void }) { return <div className="stack"><button className="primary fit" onClick={onRun}>{t.runAi}</button><div className="grid-list">{items.map(item => <div className="panel" key={item.id}><Badge tone={badgeClass(item.severity)}>{item.severity}</Badge><h2>{item.title}</h2><p>{item.explanation}</p><div className="button-row"><small className="muted">confidence {Math.round(Number(item.confidence) * 100)}%</small><button className="small secondary" onClick={() => onAction(item.id, 'mark-checked')}>checked</button><button className="small secondary" onClick={() => onAction(item.id, 'dismiss')}>hide</button></div></div>)}</div>{!items.length && <Empty text={t.noData} />}</div>; }
function Integrations({ status, t, onSync }: { status: IntegrationStatus | null; t: Labels; onSync: () => void }) { return <div className="panel"><div className="button-row" style={{ justifyContent: 'space-between' }}><h2>{t.planner}</h2><button className="primary" onClick={onSync}>{t.syncNow}</button></div><div className="metric-grid"><Metric label="Synced" value={String(status?.synced_count ?? 0)} /><Metric label="Pending" value={String(status?.pending_sync_count ?? 0)} /><Metric label="Failed" value={String(status?.failed_sync_count ?? 0)} /><Metric label="Calendar" value={status?.planner_calendar_title || 'Подписки'} /></div></div>; }
function History({ items, t }: { items: AuditItem[]; t: Labels }) { return <div className="panel"><h2>{t.history}</h2>{items.length ? items.map(item => <Row key={item.id} title={item.action} meta={`${item.target_type} · ${new Date(item.created_at).toLocaleString('ru-RU')}`} />) : <Empty text={t.noData} />}</div>; }
function Empty({ text }: { text: string }) { return <div className="empty">{text}</div>; }

function SubscriptionModal({ initial, groups, t, lang, onClose, onSaved }: { initial?: Subscription; groups: Group[]; t: Labels; lang: Lang; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState<SubForm>(() => makeSubForm(initial));
  const title = initial ? t.editSub : t.addSub;
  function patch(data: Partial<SubForm>) { setForm(prev => ({ ...prev, ...data })); }
  function updatePrice(kind: 'monthly' | 'yearly', value: string) { const minor = toMinor(value); if (kind === 'monthly') { patch({ monthly: value, yearly: fromMinor(minor * 12), amount_minor: amountFromMonthly(minor, form.billing_interval) }); } else { patch({ yearly: value, monthly: fromMinor(Math.round(minor / 12)), amount_minor: amountFromYearly(minor, form.billing_interval) }); } }
  async function submit() { const body = { name: form.name, service_url: form.service_url || null, account_identifier: form.account_identifier || null, category_key: form.category_key || null, status: form.status, billing_interval: form.billing_interval, amount_model: form.group_id ? 'group_child' : form.amount_model, amount_minor: form.amount_model === 'unknown' || form.group_id ? null : form.amount_minor, renewal_date: form.renewal_date || null, trial_end_date: form.trial_end_date || null, group_id: form.group_id || null, notes: form.notes || null }; await api(initial ? `/subscriptions/${initial.id}` : '/subscriptions', { method: initial ? 'PATCH' : 'POST', body: JSON.stringify(body) }); onSaved(); }
  async function remove() { if (!initial || !window.confirm(t.delete)) return; await api(`/subscriptions/${initial.id}`, { method: 'DELETE' }); onSaved(); }
  return <Modal title={title} onClose={onClose}><Field label={t.name}><input value={form.name} onChange={e => patch({ name: e.target.value })} /></Field><div className="form-grid"><Field label={t.url}><input value={form.service_url} onChange={e => patch({ service_url: e.target.value })} /></Field><Field label={t.account}><input value={form.account_identifier} placeholder={initial?.account_identifier_masked || ''} onChange={e => patch({ account_identifier: e.target.value })} /></Field></div><div className="form-grid"><Field label={t.category}><select value={form.category_key} onChange={e => patch({ category_key: e.target.value, amount_model: variableCategories.has(e.target.value) ? 'variable' : form.amount_model })}>{categories.map(c => <option value={c} key={c}>{c}</option>)}</select></Field><Field label={t.status}><select value={form.status} onChange={e => patch({ status: e.target.value })}>{statuses.map(status => <option value={status} key={status}>{statusLabel(status, lang)}</option>)}</select></Field></div><div className="form-grid"><Field label={t.interval}><select value={form.billing_interval} onChange={e => patch({ billing_interval: e.target.value })}>{intervals.map(i => <option value={i} key={i}>{intervalLabels[lang][i as keyof typeof intervalLabels.ru]}</option>)}</select></Field><Field label={t.group}><select value={form.group_id} onChange={e => patch({ group_id: e.target.value, amount_model: e.target.value ? 'group_child' : 'fixed' })}><option value="">—</option>{groups.map(g => <option value={g.id} key={g.id}>{g.name}</option>)}</select></Field></div><Field label={t.type}><select value={form.amount_model} disabled={!!form.group_id} onChange={e => patch({ amount_model: e.target.value })}>{amountModels.map(m => <option value={m} key={m}>{t[m as keyof Labels] || m}</option>)}</select></Field>{!form.group_id && form.amount_model !== 'free' && form.amount_model !== 'unknown' && <div className="form-grid"><Field label={t.month}><input value={form.monthly} onChange={e => updatePrice('monthly', e.target.value)} /></Field><Field label={t.year}><input value={form.yearly} onChange={e => updatePrice('yearly', e.target.value)} /></Field></div>}<div className="form-grid"><Field label={t.renewal}><input type="date" value={form.renewal_date} onChange={e => patch({ renewal_date: e.target.value })} /></Field><Field label={t.trialEnd}><input type="date" value={form.trial_end_date} onChange={e => patch({ trial_end_date: e.target.value })} /></Field></div><Field label={t.notes}><textarea value={form.notes} onChange={e => patch({ notes: e.target.value })} /></Field><div className="modal-actions"><div>{initial && <button className="danger" onClick={remove}>{t.delete}</button>}</div><div className="right"><button className="secondary" onClick={onClose}>{t.cancel}</button><button className="primary" onClick={submit}>{t.save}</button></div></div></Modal>;
}

function GroupModal({ initial, t, lang, onClose, onSaved }: { initial?: Group; t: Labels; lang: Lang; onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState<GroupForm>(() => makeGroupForm(initial));
  function patch(data: Partial<GroupForm>) { setForm(prev => ({ ...prev, ...data })); }
  function updatePrice(kind: 'monthly' | 'yearly', value: string) { const minor = toMinor(value); if (kind === 'monthly') patch({ monthly: value, yearly: fromMinor(minor * 12), amount_minor: amountFromMonthly(minor, form.billing_interval) }); else patch({ yearly: value, monthly: fromMinor(Math.round(minor / 12)), amount_minor: amountFromYearly(minor, form.billing_interval) }); }
  async function submit() { const body = { name: form.name, service_url: form.service_url || null, status: form.status, billing_interval: form.billing_interval, amount_model: form.amount_model, amount_minor: form.amount_model === 'unknown' ? null : form.amount_minor, renewal_date: form.renewal_date || null, notes: form.notes || null }; await api(initial ? `/groups/${initial.id}` : '/groups', { method: initial ? 'PATCH' : 'POST', body: JSON.stringify(body) }); onSaved(); }
  async function remove() { if (!initial || !window.confirm(t.delete)) return; await api(`/groups/${initial.id}?detach_children=true`, { method: 'DELETE' }); onSaved(); }
  return <Modal title={initial ? t.editGroup : t.addGroup} onClose={onClose}><Field label={t.name}><input value={form.name} onChange={e => patch({ name: e.target.value })} /></Field><Field label={t.url}><input value={form.service_url} onChange={e => patch({ service_url: e.target.value })} /></Field><div className="form-grid"><Field label={t.status}><select value={form.status} onChange={e => patch({ status: e.target.value })}>{statuses.map(status => <option value={status} key={status}>{statusLabel(status, lang)}</option>)}</select></Field><Field label={t.interval}><select value={form.billing_interval} onChange={e => patch({ billing_interval: e.target.value })}>{intervals.map(i => <option value={i} key={i}>{intervalLabels[lang][i as keyof typeof intervalLabels.ru]}</option>)}</select></Field></div><Field label={t.type}><select value={form.amount_model} onChange={e => patch({ amount_model: e.target.value })}>{amountModels.map(m => <option value={m} key={m}>{t[m as keyof Labels] || m}</option>)}</select></Field>{form.amount_model !== 'free' && form.amount_model !== 'unknown' && <div className="form-grid"><Field label={t.month}><input value={form.monthly} onChange={e => updatePrice('monthly', e.target.value)} /></Field><Field label={t.year}><input value={form.yearly} onChange={e => updatePrice('yearly', e.target.value)} /></Field></div>}<Field label={t.renewal}><input type="date" value={form.renewal_date} onChange={e => patch({ renewal_date: e.target.value })} /></Field><Field label={t.notes}><textarea value={form.notes} onChange={e => patch({ notes: e.target.value })} /></Field><div className="modal-actions"><div>{initial && <button className="danger" onClick={remove}>{t.delete}</button>}</div><div className="right"><button className="secondary" onClick={onClose}>{t.cancel}</button><button className="primary" onClick={submit}>{t.save}</button></div></div></Modal>;
}
function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) { return <div className="modal-backdrop"><div className="modal"><header><h2>{title}</h2><button className="secondary" onClick={onClose}>×</button></header>{children}</div></div>; }
function Field({ label, children }: { label: string; children: React.ReactNode }) { return <label className="field"><span>{label}</span>{children}</label>; }
