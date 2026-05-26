import { Router, Request, Response } from "express";
import { STATES, TRANSITIONS, allowedNext } from "../stateMachine.js";
import {
  getAllJobs,
  getJob,
  createJob,
  saveJob,
  deleteJob,
} from "../store.js";
import type { JobCreate, JobUpdate } from "../types.js";

const router = Router();

router.get("/states", (_req: Request, res: Response) => {
  res.json({ states: STATES, transitions: TRANSITIONS });
});

router.get("/jobs", (_req: Request, res: Response) => {
  res.json(getAllJobs());
});

router.post("/jobs", (req: Request, res: Response) => {
  const data = req.body as JobCreate;
  if (!data.company?.trim()) {
    res.status(422).json({ detail: "company is required" });
    return;
  }
  if (!data.role?.trim()) {
    res.status(422).json({ detail: "role is required" });
    return;
  }
  if (!data.date_applied) {
    res.status(422).json({ detail: "date_applied is required" });
    return;
  }
  if (data.state && !STATES.includes(data.state)) {
    res.status(422).json({ detail: `Invalid state: ${data.state}` });
    return;
  }
  const job = createJob(data);
  res.status(201).json(job);
});

router.get("/jobs/:id", (req: Request, res: Response) => {
  const job = getJob(req.params.id);
  if (!job) {
    res.status(404).json({ detail: "Job not found" });
    return;
  }
  res.json(job);
});

router.put("/jobs/:id", (req: Request, res: Response) => {
  const job = getJob(req.params.id);
  if (!job) {
    res.status(404).json({ detail: "Job not found" });
    return;
  }
  const data = req.body as JobUpdate;
  const fields = [
    "company",
    "role",
    "date_applied",
    "state",
    "resume_version",
    "key_requirements",
    "hr_contacts",
    "interviews",
    "notes",
  ] as const;
  for (const key of fields) {
    if (data[key] !== undefined) {
      (job as Record<string, unknown>)[key] = data[key];
    }
  }
  if (data.state && !STATES.includes(data.state)) {
    res.status(400).json({ detail: `Invalid state: ${data.state}` });
    return;
  }
  job.updated_at = new Date().toISOString();
  saveJob(job);
  res.json(job);
});

router.delete("/jobs/:id", (req: Request, res: Response) => {
  if (!getJob(req.params.id)) {
    res.status(404).json({ detail: "Job not found" });
    return;
  }
  deleteJob(req.params.id);
  res.json({ deleted: true });
});

router.post("/jobs/:id/transition", (req: Request, res: Response) => {
  const job = getJob(req.params.id);
  if (!job) {
    res.status(404).json({ detail: "Job not found" });
    return;
  }
  const { to_state } = req.body;
  if (!to_state || !STATES.includes(to_state)) {
    res.status(400).json({ detail: `Invalid state: ${to_state}` });
    return;
  }
  if (to_state === job.state) {
    res.json(job);
    return;
  }
  const allowed = allowedNext(job.state);
  if (!allowed.includes(to_state)) {
    res.status(400).json({
      detail: `Cannot transition from '${job.state}' to '${to_state}'`,
      allowed,
    });
    return;
  }
  job.state = to_state;
  job.updated_at = new Date().toISOString();
  saveJob(job);
  res.json(job);
});

router.get("/jobs/:id/allowed-transitions", (req: Request, res: Response) => {
  const job = getJob(req.params.id);
  if (!job) {
    res.status(404).json({ detail: "Job not found" });
    return;
  }
  res.json({ from: job.state, allowed: allowedNext(job.state) });
});

export default router;
