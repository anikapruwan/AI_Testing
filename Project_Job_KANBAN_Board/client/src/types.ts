export type State =
  | "wishlist"
  | "applied"
  | "interviewing"
  | "negotiating"
  | "offer_received"
  | "offer_not_received"
  | "done_archived";

export interface Interview {
  date: string;
  time: string;
  label: string;
}

export interface HRContact {
  name: string;
  email: string;
  phone: string;
}

export interface Job {
  id: string;
  company: string;
  role: string;
  date_applied: string;
  key_requirements: string[];
  resume_version: string | null;
  state: State;
  hr_contacts: HRContact[];
  interviews: Interview[];
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface JobCreate {
  company: string;
  role: string;
  date_applied: string;
  key_requirements?: string[];
  resume_version?: string | null;
  state?: State;
  hr_contacts?: HRContact[];
  interviews?: Interview[];
  notes?: string;
}

export const STATES: State[] = [
  "wishlist",
  "applied",
  "interviewing",
  "negotiating",
  "offer_received",
  "offer_not_received",
  "done_archived",
];

export const COLUMNS: { key: State; label: string }[] = [
  { key: "wishlist", label: "Wishlist" },
  { key: "applied", label: "Applied" },
  { key: "interviewing", label: "Interviewing" },
  { key: "negotiating", label: "Negotiating" },
  { key: "offer_received", label: "Offer Received" },
  { key: "offer_not_received", label: "Offer Not Received" },
  { key: "done_archived", label: "Done / Archived" },
];
