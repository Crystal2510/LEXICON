const API = import.meta.env.VITE_API_URL || '/api';

export async function previewCSV(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API}/preview`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function enrichCSV(file: File, deepSourcing = false) {
  const form = new FormData();
  form.append('file', file);
  const params = deepSourcing ? '?deep_sourcing=true' : '';
  const res = await fetch(`${API}/enrich${params}`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function getStats() {
  const res = await fetch(`${API}/stats`);
  return res.json();
}

export async function getReviewQueue() {
  const res = await fetch(`${API}/review-queue`);
  return res.json();
}

export async function approveRow(rowIndex: number, edits: Record<string, string>) {
  const res = await fetch(`${API}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ row_index: rowIndex, edits }),
  });
  return res.json();
}

export async function downloadCSV(rows: any[]) {
  const res = await fetch(`${API}/download/csv`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.blob();
}

export async function downloadXLSX(rows: any[]) {
  const res = await fetch(`${API}/download/xlsx`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.blob();
}

export async function approveBatch(rowIndices: number[], edits?: Record<string, string>) {
  const res = await fetch(`${API}/approve-batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ row_indices: rowIndices, edits: edits || null }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function getReviewQueueGrouped() {
  const res = await fetch(`${API}/review-queue-grouped`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getClasspathSuggestions(q: string = '') {
  const res = await fetch(`${API}/classpath-suggestions?q=${encodeURIComponent(q)}`);
  return res.json();
}

export async function downloadReviewItems() {
  const res = await fetch(`${API}/download/review-items`, { method: 'POST' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.blob();
}

export async function getAllRows() {
  const res = await fetch(`${API}/all-rows`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function uploadReferenceFiles(files: File[]) {
  const form = new FormData();
  for (const f of files) {
    form.append('files', f);
  }
  const res = await fetch(`${API}/upload-reference`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function downloadUnilog() {
  const res = await fetch(`${API}/download/unilog`, { method: 'POST' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.blob();
}
