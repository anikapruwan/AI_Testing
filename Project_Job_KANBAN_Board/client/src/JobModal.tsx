import { useState, useEffect, type FormEvent } from "react";
import { COLUMNS } from "./types";
import type { Job, HRContact, Interview } from "./types";

interface Props {
  job: Job | null;
  onSave: (data: Record<string, unknown>) => void;
  onClose: () => void;
}

interface ContactRow {
  name: string;
  email: string;
  phone: string;
}

export default function JobModal({ job, onSave, onClose }: Props) {
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [dateApplied, setDateApplied] = useState("");
  const [state, setState] = useState("wishlist");
  const [resumeVersion, setResumeVersion] = useState("");
  const [keyRequirements, setKeyRequirements] = useState("");
  const [contacts, setContacts] = useState<ContactRow[]>([]);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    if (job) {
      setCompany(job.company);
      setRole(job.role);
      setDateApplied(job.date_applied);
      setState(job.state);
      setResumeVersion(job.resume_version ?? "");
      setKeyRequirements((job.key_requirements ?? []).join(", "));
      setContacts((job.hr_contacts ?? []).map((c) => ({ ...c })));
      setInterviews((job.interviews ?? []).map((iv) => ({ ...iv })));
      setNotes(job.notes ?? "");
    } else {
      setCompany("");
      setRole("");
      setDateApplied(new Date().toISOString().slice(0, 10));
      setState("wishlist");
      setResumeVersion("");
      setKeyRequirements("");
      setContacts([]);
      setInterviews([]);
      setNotes("");
    }
  }, [job]);

  function addContact() {
    setContacts([...contacts, { name: "", email: "", phone: "" }]);
  }

  function updateContact(i: number, field: keyof ContactRow, val: string) {
    const next = [...contacts];
    next[i] = { ...next[i], [field]: val };
    setContacts(next);
  }

  function removeContact(i: number) {
    setContacts(contacts.filter((_, idx) => idx !== i));
  }

  function addInterview() {
    setInterviews([...interviews, { date: "", time: "", label: "" }]);
  }

  function updateInterview(i: number, field: keyof Interview, val: string) {
    const next = [...interviews];
    next[i] = { ...next[i], [field]: val };
    setInterviews(next);
  }

  function removeInterview(i: number) {
    setInterviews(interviews.filter((_, idx) => idx !== i));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSave({
      company,
      role,
      date_applied: dateApplied,
      state,
      resume_version: resumeVersion || null,
      key_requirements: keyRequirements
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      hr_contacts: contacts.filter((c) => c.name || c.email || c.phone),
      interviews: interviews.filter((iv) => iv.date),
      notes,
    });
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <h2>{job ? "Edit Job" : "Add Job"}</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>Company *</label>
              <input required value={company} onChange={(e) => setCompany(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Role *</label>
              <input required value={role} onChange={(e) => setRole(e.target.value)} />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Date Applied *</label>
              <input type="date" required value={dateApplied} onChange={(e) => setDateApplied(e.target.value)} />
            </div>
            <div className="form-group">
              <label>State</label>
              <select value={state} onChange={(e) => setState(e.target.value)}>
                {COLUMNS.map((c) => (
                  <option key={c.key} value={c.key}>{c.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label>Resume Version</label>
            <input value={resumeVersion} onChange={(e) => setResumeVersion(e.target.value)} placeholder="resume_v2_genai.pdf" />
          </div>
          <div className="form-group">
            <label>Key Requirements (comma-separated)</label>
            <input value={keyRequirements} onChange={(e) => setKeyRequirements(e.target.value)} placeholder="Python, React, AWS..." />
          </div>

          <div className="hr-section">
            <h4>📅 Interview Schedule</h4>
            {interviews.map((iv, i) => (
              <div key={i} className="hr-row">
                <input
                  type="date"
                  value={iv.date}
                  onChange={(e) => updateInterview(i, "date", e.target.value)}
                />
                <input
                  type="time"
                  value={iv.time}
                  onChange={(e) => updateInterview(i, "time", e.target.value)}
                />
                <input
                  placeholder="Label (e.g. Phone Screen)"
                  value={iv.label}
                  onChange={(e) => updateInterview(i, "label", e.target.value)}
                />
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => removeInterview(i)}>✕</button>
              </div>
            ))}
            <button type="button" className="btn btn-ghost btn-sm" onClick={addInterview}>+ Add Interview</button>
          </div>

          <div className="hr-section">
            <h4>HR / Recruiter Contacts</h4>
            {contacts.map((c, i) => (
              <div key={i} className="hr-row">
                <input
                  placeholder="Name"
                  value={c.name}
                  onChange={(e) => updateContact(i, "name", e.target.value)}
                />
                <input
                  placeholder="Email"
                  value={c.email}
                  onChange={(e) => updateContact(i, "email", e.target.value)}
                />
                <input
                  placeholder="Phone"
                  value={c.phone}
                  onChange={(e) => updateContact(i, "phone", e.target.value)}
                />
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => removeContact(i)}>✕</button>
              </div>
            ))}
            <button type="button" className="btn btn-ghost btn-sm" onClick={addContact}>+ Add Contact</button>
          </div>

          <div className="form-group">
            <label>Notes</label>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
}
