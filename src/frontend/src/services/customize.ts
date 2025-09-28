export type CustomizePayload = {
  prompt: string;
  tone: 'formal' | 'informal';
  include_charts: boolean;
  length: 'short' | 'long';
};

export type CustomizeResponse = {
  text: string;
  chart_data?: Array<{ label: string; value: number }> | null;
};

export async function postCustomize(payload: CustomizePayload) {
  const base = process.env.NEXT_PUBLIC_BASE_URL || '';
  const res = await fetch(`${base}/api/customize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Request failed');
  }
  return (await res.json()) as CustomizeResponse;
}
