"use client";

import React from "react";

type Props = {
  value: string;
  onChange: (v: string) => void;
  label?: string;
  placeholder?: string;
  options?: string[]; // optional predefined users
  disabled?: boolean;
};

export default function UserSelector({ value, onChange, label = "User ID", placeholder = "default_user", options = ["default_user"], disabled }: Props) {
  return (
    <div>
      {label && <label className="block text-sm font-medium mb-1">{label}</label>}
      {options && options.length > 0 ? (
        <div className="flex gap-2">
          <select
            className="w-full border rounded p-2"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
          >
            {options.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </select>
          <input
            className="w-full border rounded p-2"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            disabled={disabled}
          />
        </div>
      ) : (
        <input
          className="w-full border rounded p-2"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
        />
      )}
    </div>
  );
}
