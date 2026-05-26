import type { JobCreate, Job } from "./types";

const BASE = "/api";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? res.statusText);
  }
  return res.json();
}

export function fetchJobs(): Promise<Job[]> {
  return request<Job[]>("/jobs");
}

export function createJob(data: JobCreate): Promise<Job> {
  return request<Job>("/jobs", { method: "POST", body: JSON.stringify(data) });
}

export function updateJob(id: string, data: Partial<JobCreate>): Promise<Job> {
  return request<Job>(`/jobs/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteJob(id: string): Promise<void> {
  return request<void>(`/jobs/${id}`, { method: "DELETE" });
}

export function transitionJob(
  id: string,
  toState: string
): Promise<Job> {
  return request<Job>(`/jobs/${id}/transition`, {
    method: "POST",
    body: JSON.stringify({ to_state: toState }),
  });
}
