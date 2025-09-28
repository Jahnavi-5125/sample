// frontend/components/PreferencePanel.jsx
import { useState, useEffect } from "react";

export default function PreferencePanel({ onChange }) {
  const [prefs, setPrefs] = useState({
    tone: "formal",
    detail: "summary",
    charts: true,
    news: false
  });

  // persist to localStorage so prefs stay across refresh
  useEffect(() => {
    const saved = localStorage.getItem("user_prefs");
    if (saved) setPrefs(JSON.parse(saved));
  }, []);

  useEffect(() => {
    localStorage.setItem("user_prefs", JSON.stringify(prefs));
    onChange && onChange(prefs);
  }, [prefs]);

  const handleChange = (key, value) => {
    setPrefs(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div style={{ padding: 12, border: "1px solid #ddd", borderRadius: 8, marginBottom: 12 }}>
      <h4>User Preferences</h4>
      <div style={{ marginBottom: 8 }}>
        <label>Tone: </label>
        <select value={prefs.tone} onChange={e => handleChange("tone", e.target.value)}>
          <option value="formal">Formal</option>
          <option value="casual">Casual</option>
          <option value="friendly">Friendly</option>
        </select>
      </div>

      <div style={{ marginBottom: 8 }}>
        <label>Detail: </label>
        <select value={prefs.detail} onChange={e => handleChange("detail", e.target.value)}>
          <option value="summary">Summary</option>
          <option value="detailed">Detailed</option>
        </select>
      </div>

      <div>
        <label>
          <input type="checkbox" checked={prefs.charts} onChange={e => handleChange("charts", e.target.checked)} />
          {" "}Show charts
        </label>
      </div>
      <div>
        <label>
          <input type="checkbox" checked={prefs.news} onChange={e => handleChange("news", e.target.checked)} />
          {" "}Show related news
        </label>
      </div>
    </div>
  );
}

