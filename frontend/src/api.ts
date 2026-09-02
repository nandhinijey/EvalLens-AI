export const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type ScoreColor = "green" | "yellow" | "red";

export interface DimensionAggregate {
  average: number;
  color: ScoreColor;
}

export interface RunAggregate {
  faithfulness: DimensionAggregate;
  format: DimensionAggregate;
  safety: DimensionAggregate;
}

export interface RunSummary {
  id: number;
  name: string;
  created_at: string;
  item_count: number;
  aggregate: RunAggregate;
}

export interface Item {
  id: number;
  prompt: string;
  context: string;
  response: string;
  faithfulness_score: number;
  faithfulness_rationale: string;
  faithfulness_confidence: "high" | "low";
  format_score: number;
  format_rationale: string;
  format_confidence: "high" | "low";
  safety_score: number;
  safety_rationale: string;
  safety_confidence: "high" | "low";
}

export interface RunDetail {
  id: number;
  name: string;
  created_at: string;
  aggregate: RunAggregate;
  items: Item[];
}

export interface CompareResult {
  run_a: RunSummary;
  run_b: RunSummary;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore — fall back to statusText
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export function listRuns(): Promise<RunSummary[]> {
  return request("/runs");
}

export function getRun(runId: number): Promise<RunDetail> {
  return request(`/runs/${runId}`);
}

export function deleteRun(runId: number): Promise<void> {
  return request(`/runs/${runId}`, { method: "DELETE" });
}

export function getFlaggedItems(
  runId: number,
  opts: { threshold?: number; sortBy?: string; order?: "asc" | "desc" } = {},
): Promise<Item[]> {
  const params = new URLSearchParams();
  if (opts.threshold !== undefined) params.set("threshold", String(opts.threshold));
  if (opts.sortBy) params.set("sort_by", opts.sortBy);
  if (opts.order) params.set("order", opts.order);
  const qs = params.toString();
  return request(`/runs/${runId}/flagged${qs ? `?${qs}` : ""}`);
}

export function compareRuns(runA: number, runB: number): Promise<CompareResult> {
  return request(`/compare?run_a=${runA}&run_b=${runB}`);
}

export async function evaluateCsv(file: File, name: string): Promise<RunDetail> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("name", name);
  return request("/evaluate", { method: "POST", body: formData });
}
