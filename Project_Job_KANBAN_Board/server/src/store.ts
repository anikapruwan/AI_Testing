import fs from "node:fs";
import path from "node:path";
import { v4 as uuid } from "uuid";
import type { Job, JobCreate, State } from "./types.js";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_FILE = path.join(__dirname, "..", "..", ".tmp", "jobs.json");

function load(): Job[] {
  const dir = path.dirname(DATA_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  if (!fs.existsSync(DATA_FILE)) return [];
  return JSON.parse(fs.readFileSync(DATA_FILE, "utf-8"));
}

function save(jobs: Job[]): void {
  const dir = path.dirname(DATA_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(DATA_FILE, JSON.stringify(jobs, null, 2));
}

export function getAllJobs(): Job[] {
  return load();
}

export function getJob(id: string): Job | undefined {
  return load().find((j) => j.id === id);
}

export function createJob(data: JobCreate): Job {
  const jobs = load();
  const now = new Date().toISOString();
  const job: Job = {
    id: uuid(),
    company: data.company,
    role: data.role,
    date_applied: data.date_applied,
    key_requirements: data.key_requirements ?? [],
    resume_version: data.resume_version ?? null,
    state: (data.state as State) ?? "wishlist",
    hr_contacts: data.hr_contacts ?? [],
    interviews: data.interviews ?? [],
    notes: data.notes ?? "",
    created_at: now,
    updated_at: now,
  };
  jobs.push(job);
  save(jobs);
  return job;
}

export function saveJob(updated: Job): void {
  const jobs = load();
  const idx = jobs.findIndex((j) => j.id === updated.id);
  if (idx >= 0) {
    jobs[idx] = updated;
  } else {
    jobs.push(updated);
  }
  save(jobs);
}

export function deleteJob(id: string): void {
  const jobs = load().filter((j) => j.id !== id);
  save(jobs);
}
