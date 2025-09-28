"use client";

import React, { useEffect, useState } from "react";
import { savePreferences, PrefsPayload, getPreferences } from "@/services/prefs";
import { toast } from "sonner";
import UserSelector from "@/components/UserSelector";

const chartOptions = [
  { value: "bar", label: "Bar" },
  { value: "line", label: "Line" },
  { value: "pie", label: "Pie" },
] as const;

const metricOptions = [
  { value: "revenue", label: "Revenue" },
  { value: "expenses", label: "Expenses" },
  { value: "growth", label: "Growth" },
] as const;

const timeOptions = [
  { value: "1M", label: "1M" },
  { value: "3M", label: "3M" },
  { value: "6M", label: "6M" },
  { value: "1Y", label: "1Y" },
  { value: "5Y", label: "5Y" },
];

const currencyOptions = [
  { value: "USD", label: "USD" },
  { value: "EUR", label: "EUR" },
  { value: "GBP", label: "GBP" },
  { value: "INR", label: "INR" },
];

const granularityOptions = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

export default function PreferencesPage() {
  const [form, setForm] = useState<PrefsPayload>({
    user_id: "default_user",
    chart_type: "bar",
    finance_metric: "revenue",
    time_range: "3M",
    currency: "USD",
    granularity: "monthly",
    theme: "light",
    show_news: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onChange = (
    e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>
  ) => {
    const target = e.target as HTMLInputElement | HTMLSelectElement;
    const { name } = target;
    const value = target instanceof HTMLInputElement && target.type === 'checkbox' ? (target as HTMLInputElement).checked : target.value;
    setForm((prev) => ({ ...prev, [name]: value as any }));
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await savePreferences(form);
      toast.success("Preferences saved successfully");
    } catch (err: any) {
      setError(err?.message || "Failed to save preferences");
      toast.error(err?.message || "Failed to save preferences");
    } finally {
      setLoading(false);
    }
  };

  const onLoad = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getPreferences(form.user_id || "default_user");
      const prefs = res.preferences || {} as any;
      setForm((prev) => ({ ...prev, ...prefs }));
      toast.success("Loaded saved preferences");
    } catch (err: any) {
      setError(err?.message || "Failed to load preferences");
      toast.error(err?.message || "Failed to load preferences");
    } finally {
      setLoading(false);
    }
  };

  // Auto-load on mount for convenience
  useEffect(() => {
    onLoad().catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold text-indigo-800">Preferences</h1>

      <form
        onSubmit={onSubmit}
        className="bg-white border rounded-lg p-5 shadow-sm space-y-4"
      >
        <div>
          <UserSelector
            value={form.user_id || "default_user"}
            onChange={(v) => setForm((prev) => ({ ...prev, user_id: v }))}
            label="User ID"
            placeholder="default_user"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Chart Type</label>
          <select
            name="chart_type"
            value={form.chart_type}
            onChange={onChange}
            className="w-full border rounded p-2"
          >
            {chartOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Finance Metric</label>
          <select
            name="finance_metric"
            value={form.finance_metric}
            onChange={onChange}
            className="w-full border rounded p-2"
          >
            {metricOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Time Range</label>
            <select name="time_range" value={form.time_range} onChange={onChange} className="w-full border rounded p-2">
              {timeOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Currency</label>
            <select name="currency" value={form.currency} onChange={onChange} className="w-full border rounded p-2">
              {currencyOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Granularity</label>
            <select name="granularity" value={form.granularity} onChange={onChange} className="w-full border rounded p-2">
              {granularityOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <label className="inline-flex items-center gap-2">
            <input type="checkbox" name="show_news" checked={!!form.show_news} onChange={onChange} />
            <span>Show related news</span>
          </label>

          <label className="inline-flex items-center gap-2">
            <input type="checkbox" name="theme" checked={form.theme === 'dark'} onChange={(e) => setForm(prev => ({ ...prev, theme: e.target.checked ? 'dark' : 'light' }))} />
            <span>Dark theme</span>
          </label>
        </div>

        {error && (
          <div className="p-2 text-sm border border-red-300 bg-red-50 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded disabled:opacity-50"
          >
            {loading ? "Saving..." : "Save Preferences"}
          </button>
          <button
            type="button"
            onClick={onLoad}
            disabled={loading}
            className="bg-gray-100 hover:bg-gray-200 text-gray-900 px-4 py-2 rounded border disabled:opacity-50"
          >
            {loading ? "Loading..." : "Load my preferences"}
          </button>
        </div>
      </form>
    </div>
  );
}
