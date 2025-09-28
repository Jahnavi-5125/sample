"use client";

import React, { useEffect, useMemo, useState } from "react";
import UserSelector from "@/components/UserSelector";
import { savePreferences, getPreferences, PrefsPayload, generateInsights, getNews, NewsItem } from "@/services/prefs";
import { toast } from "sonner";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const timeOptions = ["1M", "3M", "6M", "1Y", "5Y"] as const;
const currencyOptions = ["USD", "EUR", "GBP", "INR"] as const;
const granularityOptions = ["daily", "weekly", "monthly"] as const;
const chartOptions = ["bar", "line", "pie"] as const;
const metricOptions = ["revenue", "expenses", "growth"] as const;

function currencySymbol(curr?: string) {
  switch (curr) {
    case "EUR":
      return "€";
    case "GBP":
      return "£";
    case "INR":
      return "₹";
    default:
      return "$"; // USD
  }
}

function sampleData(metric: string, timeRange: string, granularity: string) {
  const base = metric === "revenue" ? 100 : metric === "expenses" ? 70 : 10;
  const ranges: Record<string, number> = { "1M": 4, "3M": 12, "6M": 24, "1Y": 48, "5Y": 60 };
  const points = ranges[timeRange] || 12;
  const stepLabel = (idx: number) => `${idx + 1}`;
  const data = Array.from({ length: points }, (_, i) => ({ label: stepLabel(i), value: base + Math.round(Math.sin(i / 3) * 10) + (i % 5) }));
  if (granularity === "weekly") return data.filter((_, i) => i % 2 === 0);
  if (granularity === "monthly") return data.filter((_, i) => i % 4 === 0);
  return data;
}

export default function StudioPage() {
  const [userId, setUserId] = useState<string>("default_user");
  const [prefs, setPrefs] = useState<PrefsPayload>({ user_id: "default_user", chart_type: "bar", finance_metric: "revenue", time_range: "3M", currency: "USD", granularity: "monthly", theme: "light", show_news: false });
  const [saving, setSaving] = useState(false);
  const [genLoading, setGenLoading] = useState(false);
  const [newsLoading, setNewsLoading] = useState(false);
  const [insight, setInsight] = useState<string>("");
  const [cached, setCached] = useState<boolean>(false);
  const [news, setNews] = useState<NewsItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await getPreferences(userId);
        setPrefs({ ...(res.preferences as PrefsPayload) });
      } catch {
        // ignore
      }
    };
    load();
  }, [userId]);

  const onPrefChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const target = e.target as HTMLInputElement | HTMLSelectElement;
    const { name } = target;
    const value = target instanceof HTMLInputElement && target.type === "checkbox" ? target.checked : target.value;
    setPrefs((prev) => ({ ...prev, [name]: value as any }));
  };

  const save = async () => {
    setSaving(true);
    try {
      await savePreferences({ ...prefs, user_id: userId });
      toast.success("Preferences saved");
    } catch (e: any) {
      toast.error(e?.message || "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const refresh = async () => {
    setGenLoading(true);
    setError(null);
    try {
      const res = await generateInsights(userId);
      setCached(res.cached);
      setInsight(res.response);
    } catch (e: any) {
      setError(e?.message || "Failed to generate insights");
    } finally {
      setGenLoading(false);
    }
  };

  const loadNews = async () => {
    if (!prefs.show_news) {
      setNews(null);
      return;
    }
    setNewsLoading(true);
    try {
      const res = await getNews(userId);
      setNews(res.news || []);
    } catch (e: any) {
      setNews([]);
    } finally {
      setNewsLoading(false);
    }
  };

  useEffect(() => {
    loadNews();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefs.show_news, userId]);

  const sym = useMemo(() => currencySymbol(prefs.currency), [prefs.currency]);
  const data = useMemo(() => sampleData(prefs.finance_metric || "revenue", prefs.time_range || "3M", prefs.granularity || "monthly"), [prefs.finance_metric, prefs.time_range, prefs.granularity]);

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-semibold text-indigo-800">Studio: Preferences + Dashboard</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Preferences column */}
        <div className="bg-white border rounded-lg p-5 shadow-sm space-y-4">
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <UserSelector value={userId} onChange={setUserId} label="User ID" placeholder="default_user" />
            </div>
            <button onClick={save} disabled={saving} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded disabled:opacity-50" aria-busy={saving}>
              {saving ? "Saving..." : "Save"}
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Chart Type</label>
              <select name="chart_type" value={prefs.chart_type} onChange={onPrefChange} className="w-full border rounded p-2">
                {chartOptions.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Metric</label>
              <select name="finance_metric" value={prefs.finance_metric} onChange={onPrefChange} className="w-full border rounded p-2">
                {metricOptions.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Time Range</label>
              <select name="time_range" value={prefs.time_range} onChange={onPrefChange} className="w-full border rounded p-2">
                {timeOptions.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Currency</label>
              <select name="currency" value={prefs.currency} onChange={onPrefChange} className="w-full border rounded p-2">
                {currencyOptions.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Granularity</label>
              <select name="granularity" value={prefs.granularity} onChange={onPrefChange} className="w-full border rounded p-2">
                {granularityOptions.map((g) => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="show_news" name="show_news" checked={!!prefs.show_news} onChange={onPrefChange} />
              <label htmlFor="show_news" className="text-sm">Show related news</label>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="theme_dark" checked={prefs.theme === "dark"} onChange={(e) => setPrefs((p) => ({ ...p, theme: e.target.checked ? "dark" : "light" }))} />
              <label htmlFor="theme_dark" className="text-sm">Dark theme</label>
            </div>
          </div>
        </div>

        {/* Dashboard column */}
        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Dashboard</h2>
              <button onClick={refresh} disabled={genLoading} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded disabled:opacity-50" aria-busy={genLoading}>
                {genLoading ? "Loading..." : "Refresh"}
              </button>
            </div>
            {error && <div className="mt-3 p-2 text-sm border border-red-300 bg-red-50 text-red-700 rounded">{error}</div>}

            <div className="mt-4" style={{ width: "100%", height: 320 }}>
              <ResponsiveContainer>
                {prefs.chart_type === "line" ? (
                  <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="label" />
                    <YAxis tickFormatter={(v) => `${sym}${v}`} />
                    <Tooltip formatter={(v) => `${sym}${v}`} />
                    <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2} />
                  </LineChart>
                ) : prefs.chart_type === "pie" ? (
                  <PieChart>
                    <Tooltip formatter={(v) => `${sym}${v}`} />
                    <Pie data={data} dataKey="value" nameKey="label" outerRadius={120} label>
                      {data.map((_, idx) => (
                        <Cell key={`cell-${idx}`} fill={["#6366f1", "#22c55e", "#eab308", "#f97316", "#ef4444", "#06b6d4"][idx % 6]} />
                      ))}
                    </Pie>
                  </PieChart>
                ) : (
                  <BarChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="label" />
                    <YAxis tickFormatter={(v) => `${sym}${v}`} />
                    <Tooltip formatter={(v) => `${sym}${v}`} />
                    <Bar dataKey="value" fill="#6366f1" />
                  </BarChart>
                )}
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-5 shadow-sm">
            <h3 className="text-md font-semibold mb-2">AI Insight</h3>
            {genLoading && <div className="text-sm text-gray-500">Loading insight…</div>}
            {!genLoading && !insight && <div className="text-sm text-gray-500">No insight yet. Click Refresh.</div>}
            {!!insight && <div className="prose whitespace-pre-wrap">{insight}</div>}
            {cached && <div className="mt-2 text-xs text-gray-500">(served from cache)</div>}
          </div>

          {prefs.show_news && (
            <div className="bg-white border rounded-lg p-5 shadow-sm">
              <h3 className="text-md font-semibold mb-2">Related News</h3>
              {newsLoading && <div className="text-sm text-gray-500">Loading news…</div>}
              {!newsLoading && news && news.length > 0 ? (
                <ul className="space-y-3">
                  {news.map((n, idx) => (
                    <li key={idx} className="text-sm">
                      <a href={n.url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">
                        {n.title || n.url}
                      </a>
                      {n.snippet && <div className="text-gray-600 mt-1">{n.snippet}</div>}
                    </li>
                  ))}
                </ul>
              ) : !newsLoading ? (
                <div className="text-sm text-gray-500">No news found.</div>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
