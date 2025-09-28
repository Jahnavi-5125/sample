export type PrefsPayload = {
  user_id?: string;
  chart_type: 'bar' | 'line' | 'pie';
  finance_metric: 'revenue' | 'expenses' | 'growth';
  time_range?: '1M' | '3M' | '6M' | '1Y' | '5Y';
  currency?: 'USD' | 'EUR' | 'GBP' | 'INR';
  granularity?: 'daily' | 'weekly' | 'monthly';
  theme?: 'light' | 'dark';
  show_news?: boolean;
};

export type CustomizeConfirm = {
  status: string;
  user_id: string;
  saved: Record<string, any>;
};

export type GenerateOut = {
  user_id: string;
  preferences: {
    user_id: string;
    chart_type: 'bar' | 'line' | 'pie';
    finance_metric: 'revenue' | 'expenses' | 'growth';
    updated_at?: string;
    created_at?: string;
    time_range?: '1M' | '3M' | '6M' | '1Y' | '5Y';
    currency?: 'USD' | 'EUR' | 'GBP' | 'INR';
    granularity?: 'daily' | 'weekly' | 'monthly';
    theme?: 'light' | 'dark';
    show_news?: boolean;
  };
  response: string;
  cached: boolean;
};

export async function savePreferences(payload: PrefsPayload) {
  const base = process.env.NEXT_PUBLIC_BASE_URL || '';
  const res = await fetch(`${base}/api/customize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Failed to save preferences');
  }
  return (await res.json()) as CustomizeConfirm;
}

export async function generateInsights(user_id?: string) {
  const base = process.env.NEXT_PUBLIC_BASE_URL || '';
  const url = new URL(`${base}/api/generate`);
  if (user_id) url.searchParams.set('user_id', user_id);
  const res = await fetch(url.toString(), { method: 'POST' });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Failed to generate insights');
  }
  return (await res.json()) as GenerateOut;
}

export async function getPreferences(user_id?: string) {
  const base = process.env.NEXT_PUBLIC_BASE_URL || '';
  const url = new URL(`${base}/api/preferences`);
  if (user_id) url.searchParams.set('user_id', user_id);
  const res = await fetch(url.toString());
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Failed to fetch preferences');
  }
  return (await res.json()) as { user_id: string; preferences: PrefsPayload & { created_at?: string; updated_at?: string } };
}

export type NewsItem = { title?: string; url?: string; score?: number; snippet?: string; source?: string };
export async function getNews(user_id?: string, q?: string, max_results = 5) {
  const base = process.env.NEXT_PUBLIC_BASE_URL || '';
  const url = new URL(`${base}/api/news`);
  if (user_id) url.searchParams.set('user_id', user_id);
  if (q) url.searchParams.set('q', q);
  if (max_results) url.searchParams.set('max_results', String(max_results));
  const res = await fetch(url.toString());
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Failed to fetch news');
  }
  return (await res.json()) as { user_id: string; query: string; news: NewsItem[] };
}
