"use client";

import React, { useEffect, useState } from "react";

export type Preferences = {
  tone: "formal" | "informal";
  length: "short" | "long";
  include_charts: boolean;
};

export default function PreferencePanel({
  onChange,
  storageKey = "user_prefs",
  initial,
}: {
  onChange?: (prefs: Preferences) => void;
  storageKey?: string;
  initial?: Partial<Preferences>;
}) {
  const [prefs, setPrefs] = useState<Preferences>({
    tone: initial?.tone ?? "formal",
    length: initial?.length ?? "short",
    include_charts: initial?.include_charts ?? true,
  });

  // Load from localStorage on first mount
  useEffect(() => {
    try {
      const saved = typeof window !== "undefined" ? localStorage.getItem(storageKey) : null;
      if (saved) {
        const parsed = JSON.parse(saved);
        setPrefs((prev) => ({
          tone: parsed.tone ?? prev.tone,
          length: parsed.length ?? prev.length,
          include_charts: typeof parsed.include_charts === "boolean" ? parsed.include_charts : prev.include_charts,
        }));
      } else if (initial) {
        // ensure we notify parent of initial in case there is no saved value
        setPrefs((prev) => ({
          tone: initial.tone ?? prev.tone,
          length: initial.length ?? prev.length,
          include_charts: initial.include_charts ?? prev.include_charts,
        }));
      }
    } catch (e) {
      // ignore parse/storage errors
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Persist to localStorage and notify parent whenever prefs change
  useEffect(() => {
    try {
      if (typeof window !== "undefined") {
        localStorage.setItem(storageKey, JSON.stringify(prefs));
      }
    } catch (e) {
      // ignore storage write failures
    }
    onChange?.(prefs);
  }, [prefs, onChange, storageKey]);

  const handleChange = <K extends keyof Preferences>(key: K, value: Preferences[K]) => {
    setPrefs((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="p-3 border border-gray-200 rounded-md mb-4">
      <h4 className="text-sm font-semibold mb-3">User Preferences</h4>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-medium mb-1">Tone</label>
          <select
            value={prefs.tone}
            onChange={(e) => handleChange("tone", e.target.value as Preferences["tone"])}
            className="w-full border rounded p-2 text-sm"
          >
            <option value="formal">Formal</option>
            <option value="informal">Informal</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium mb-1">Length</label>
          <select
            value={prefs.length}
            onChange={(e) => handleChange("length", e.target.value as Preferences["length"])}
            className="w-full border rounded p-2 text-sm"
          >
            <option value="short">Short</option>
            <option value="long">Long</option>
          </select>
        </div>

        <div className="flex items-end">
          <label className="inline-flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={prefs.include_charts}
              onChange={(e) => handleChange("include_charts", e.target.checked)}
            />
            <span>Include chart</span>
          </label>
        </div>
      </div>
    </div>
  );
}
