import { useState, useEffect, useCallback } from "react";
import { COLUMNS } from "./types";
import type { Job, JobCreate } from "./types";
import { fetchJobs, createJob, updateJob, deleteJob, transitionJob } from "./api";
import JobModal from "./JobModal";
import "./App.css";

export default function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [modalJob, setModalJob] = useState<Job | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [dragId, setDragId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ msg: string; err?: boolean } | null>(null);

  const load = useCallback(async () => {
    try {
      setJobs(await fetchJobs());
    } catch {
      showToast("Failed to load jobs", true);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function showToast(msg: string, err?: boolean) {
    setToast({ msg, err });
    setTimeout(() => setToast(null), 2500);
  }

  function openAdd() {
    setModalJob(null);
    setShowModal(true);
  }

  function openEdit(job: Job) {
    setModalJob(job);
    setShowModal(true);
  }

  async function handleSave(data: Record<string, unknown>) {
    try {
      if (modalJob) {
        await updateJob(modalJob.id, data as Partial<JobCreate>);
        showToast("Updated!");
      } else {
        await createJob(data as JobCreate);
        showToast("Added!");
      }
      setShowModal(false);
      await load();
    } catch {
      showToast("Error saving", true);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this job?")) return;
    try {
      await deleteJob(id);
      showToast("Deleted");
      await load();
    } catch {
      showToast("Error deleting", true);
    }
  }

  async function handleDrop(columnState: string) {
    if (!dragId) return;
    try {
      await transitionJob(dragId, columnState);
      showToast("Moved!");
      await load();
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Invalid move", true);
    }
    setDragId(null);
  }

  function handleDragStart(id: string) {
    setDragId(id);
  }

  const activeCount = jobs.filter((j) => j.state !== "done_archived").length;

  return (
    <div className="app">
      <header>
        <h1>⚡ Job Kanban</h1>
        <div className="header-actions">
          <div className="stats"><span>{activeCount}</span> active applications</div>
          <button className="btn btn-primary" onClick={openAdd}>+ Add Job</button>
        </div>
      </header>

      <div className="board">
        {COLUMNS.map((col) => {
          const items = jobs.filter((j) => j.state === col.key);
          return (
            <div
              key={col.key}
              className={`column col-${col.key}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => handleDrop(col.key)}
            >
              <div className="column-header">
                <span className="column-title">{col.label}</span>
                <span className="column-count">{items.length}</span>
              </div>
              <div className="card-list">
                {items.length === 0 && <div className="empty-state">Drop jobs here</div>}
                {items.map((job) => (
                  <div
                    key={job.id}
                    className="card"
                    draggable
                    onDragStart={() => handleDragStart(job.id)}
                    onDragEnd={() => setDragId(null)}
                  >
                    <div className="card-actions">
                      <button onClick={() => openEdit(job)}>✎</button>
                      <button onClick={() => handleDelete(job.id)}>✕</button>
                    </div>
                    <div className="card-company">{job.company}</div>
                    <div className="card-role">{job.role}</div>
                    <div className="card-meta">
                      <span>📅 {job.date_applied}</span>
                      {job.resume_version && <span>📄 {job.resume_version}</span>}
                    </div>
                    {job.interviews && job.interviews.length > 0 && (
                      <div className="card-interviews">
                        {job.interviews.map((iv, i) => (
                          <div key={i} className="interview-chip">
                            🗓 {iv.date}{iv.time ? ` ${iv.time}` : ""}{iv.label ? ` — ${iv.label}` : ""}
                          </div>
                        ))}
                      </div>
                    )}
                    {job.hr_contacts && job.hr_contacts.length > 0 && (
                      <div className="card-hr">
                        {job.hr_contacts.map((c, i) => (
                          <div key={i}>
                            <strong>{c.name}</strong>
                            {c.email ? ` · ${c.email}` : ""}
                            {c.phone ? ` · ${c.phone}` : ""}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {showModal && (
        <JobModal job={modalJob} onSave={handleSave} onClose={() => setShowModal(false)} />
      )}

      {toast && (
        <div className={`toast${toast.err ? " error" : ""} show`}>{toast.msg}</div>
      )}
    </div>
  );
}
