"use client";

import React, { useEffect, useState } from "react";
import { generateInsights, GenerateOut, getNews, NewsItem } from "@/services/prefs";
import UserSelector from "@/components/UserSelector";
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

const COLORS_LIGHT = ["#6366f1", "#22c55e", "#eab308", "#f97316", "#ef4444", "#06b6d4"];
const COLORS_DARK = ["#a5b4fc", "#86efac", "#fde68a", "#fdba74", "#fca5a5", "#67e8f9"];

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
  // Generate synthetic data length based on time range and granularity
  // This is demo data; in real app, fetch from backend/data API.
  const base = metric === "revenue" ? 100 : metric === "expenses" ? 70 : 10;
  const ranges: Record<string, number> = { "1M": 4, "3M": 12, "6M": 24, "1Y": 48, "5Y": 60 };
  const points = ranges[timeRange] || 12;
  const stepLabel = (idx: number) => `${idx + 1}`;
  const data = Array.from({ length: points }, (_, i) => ({ label: stepLabel(i), value: base + Math.round(Math.sin(i / 3) * 10) + (i % 5) }));

  // Optionally coarsen by granularity: daily ~ dense, weekly ~ medium, monthly ~ sparse
  if (granularity === "weekly") {
    return data.filter((_, i) => i % 2 === 0);
  }
  if (granularity === "monthly") {
    return data.filter((_, i) => i % 4 === 0);
  }
  return data; // daily
}

export default function DashboardPage() {
  const [userId, setUserId] = useState<string>("default_user");
  const [data, setData] = useState<GenerateOut | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [news, setNews] = useState<NewsItem[] | null>(null);
  const [newsError, setNewsError] = useState<string | null>(null);

  const fetchData = async (uid?: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await generateInsights(uid || userId);
      setData(res);
    } catch (e: any) {
      setError(e?.message || "Failed to load insights");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData("default_user");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const prefs = data?.preferences;
  const chartType = prefs?.chart_type || "bar";
  const metric = prefs?.finance_metric || "revenue";
  const timeRange = prefs?.time_range || "3M";
  const granularity = prefs?.granularity || "monthly";
  const theme = prefs?.theme || "light";
  const showNews = !!prefs?.show_news;
  const curr = prefs?.currency || "USD";
  const sym = currencySymbol(curr);
  const chartData = sampleData(metric, timeRange, granularity);
  const colors = theme === "dark" ? COLORS_DARK : COLORS_LIGHT;
  const cardClass = theme === "dark" ? "bg-gray-900 text-gray-100 border-gray-800" : "bg-white text-gray-900 border";

  // Fetch news when preferences indicate show_news
  useEffect(() => {
    const loadNews = async () => {
      if (!data || !showNews) {
        setNews(null);
        return;
      }
      try {
        setNewsError(null);
        const res = await getNews(userId);
        setNews(res.news || []);
      } catch (e: any) {
        setNewsError(e?.message || "Failed to fetch news");
        setNews(null);
      }
    };
    loadNews();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.preferences?.show_news, userId]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-indigo-800">Dashboard</h1>

      <div className={`${cardClass} rounded-lg p-5 shadow-sm`}>
        <div className="flex flex-col sm:flex-row items-start sm:items-end gap-3">
          <div className="flex-1">
            <UserSelector value={userId} onChange={setUserId} label="User ID" placeholder="default_user" />
          </div>
          <button
            onClick={() => fetchData(userId)}
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded disabled:opacity-50"
            aria-busy={loading}
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 border border-red-300 bg-red-50 text-red-700 rounded">{error}</div>
      )}

      <div className={`${cardClass} rounded-lg p-5 shadow-sm`}>
        <h2 className="text-lg font-semibold mb-3">{metric.toUpperCase()} — {chartType.toUpperCase()} Chart ({timeRange}, {granularity})</h2>
        <div style={{ width: "100%", height: 320 }}>
          <ResponsiveContainer>
            {chartType === "line" ? (
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis tickFormatter={(v) => `${sym}${v}`} />
                <Tooltip formatter={(v) => `${sym}${v}`} />
                <Line type="monotone" dataKey="value" stroke={colors[0]} strokeWidth={2} />
              </LineChart>
            ) : chartType === "pie" ? (
              <PieChart>
                <Tooltip formatter={(v) => `${sym}${v}`} />
                <Pie data={chartData} dataKey="value" nameKey="label" outerRadius={120} label>
                  {chartData.map((_, idx) => (
                    <Cell key={`cell-${idx}`} fill={colors[idx % colors.length]} />
                  ))}
                </Pie>
              </PieChart>
            ) : (
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis tickFormatter={(v) => `${sym}${v}`} />
                <Tooltip formatter={(v) => `${sym}${v}`} />
                <Bar dataKey="value" fill={colors[0]} />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${cardClass} rounded-lg p-5 shadow-sm`}>
        <h2 className="text-lg font-semibold mb-3">AI Insight</h2>
        {data ? (
          <div className="prose whitespace-pre-wrap">{data.response}</div>
        ) : (
          <div className="text-gray-500 text-sm">No insight yet.</div>
        )}
        {data?.cached && (
          <div className="mt-2 text-xs text-gray-500">(served from cache)</div>
        )}
      </div>

      {showNews && (
        <div className={`${cardClass} rounded-lg p-5 shadow-sm`}>
          <h2 className="text-lg font-semibold mb-3">Related News</h2>
          {newsError && (
            <div className="p-2 border border-red-300 bg-red-50 text-red-700 rounded text-sm">{newsError}</div>
          )}
          {!news && !newsError && (
            <div className="text-sm text-gray-500">Loading news…</div>
          )}
          {news && news.length > 0 ? (
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
          ) : news && news.length === 0 ? (
            <div className="text-sm text-gray-500">No news found.</div>
          ) : null}
        </div>
      )}
    </div>
  );
}
