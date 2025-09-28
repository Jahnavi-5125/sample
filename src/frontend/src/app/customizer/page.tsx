"use client";

import React, { useEffect, useState } from "react";
import { postCustomize, CustomizePayload, CustomizeResponse } from "@/services/customize";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import PreferencePanel from "@/components/PreferencePanel";
import Link from "next/link";
import { getPreferences, PrefsPayload } from "@/services/prefs";

export default function CustomizerPage() {
  const [form, setForm] = useState<CustomizePayload>({
    prompt: "Explain the latest trends in AI for finance.",
    tone: "formal",
    include_charts: true,
    length: "short",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CustomizeResponse | null>(null);
  const [backendPrefs, setBackendPrefs] = useState<PrefsPayload | null>(null);
  const [prefsError, setPrefsError] = useState<string | null>(null);

  const onChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as any;
    if (type === "checkbox") {
      setForm((prev) => ({ ...prev, [name]: (e.target as HTMLInputElement).checked }));
    } else {
      setForm((prev) => ({ ...prev, [name]: value }));
    }
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await postCustomize(form);
      setResult(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const load = async () => {
      try {
        setPrefsError(null);
        const res = await getPreferences("default_user");
        setBackendPrefs(res.preferences as PrefsPayload);
      } catch (e: any) {
        setPrefsError(e?.message || "Could not load preferences");
      }
    };
    load();
  }, []);

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-semibold">UI Customizer (OpenAI)</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Prompt</label>
              <textarea
                name="prompt"
                value={form.prompt}
                onChange={onChange}
                rows={5}
                className="w-full border rounded p-3"
                placeholder="Enter your question or topic"
                required
              />
            </div>

            <PreferencePanel
              initial={{ tone: form.tone, length: form.length, include_charts: form.include_charts }}
              onChange={(prefs) => setForm((prev) => ({ ...prev, ...prefs }))}
            />

            <button
              type="submit"
              className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
              disabled={loading}
            >
              {loading ? "Generating..." : "Generate"}
            </button>
          </form>
        </div>

        <aside className="space-y-3">
          <div className="bg-white border rounded-lg p-4 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-semibold">Saved Preferences</h2>
              <Link href="/preferences" className="text-xs text-indigo-600 hover:underline">Edit</Link>
            </div>
            {prefsError && (
              <div className="text-xs text-red-600">{prefsError}</div>
            )}
            {backendPrefs ? (
              <ul className="text-sm space-y-1">
                <li><span className="text-gray-500">Chart:</span> {backendPrefs.chart_type}</li>
                <li><span className="text-gray-500">Metric:</span> {backendPrefs.finance_metric}</li>
                <li><span className="text-gray-500">Range:</span> {backendPrefs.time_range}</li>
                <li><span className="text-gray-500">Granularity:</span> {backendPrefs.granularity}</li>
                <li><span className="text-gray-500">Currency:</span> {backendPrefs.currency}</li>
                <li><span className="text-gray-500">Theme:</span> {backendPrefs.theme}</li>
                <li><span className="text-gray-500">News:</span> {backendPrefs.show_news ? "On" : "Off"}</li>
              </ul>
            ) : (
              <div className="text-xs text-gray-500">Loading preferences…</div>
            )}
            <div className="mt-3 flex gap-2">
              <Link href="/dashboard" className="text-xs text-gray-700 border rounded px-2 py-1 hover:bg-gray-50">Open Dashboard</Link>
              <Link href="/preferences" className="text-xs text-gray-700 border rounded px-2 py-1 hover:bg-gray-50">Edit Preferences</Link>
            </div>
          </div>
        </aside>
      </div>

      {error && (
        <div className="p-3 border border-red-300 bg-red-50 text-red-700 rounded">{error}</div>
      )}

      {result && (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-2">Response</h2>
            <div className="prose whitespace-pre-wrap border rounded p-4">
              {result.text}
            </div>
          </div>

          {result.chart_data && result.chart_data.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold mb-2">Chart</h2>
              <div style={{ width: "100%", height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={result.chart_data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="label" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#2563eb" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
