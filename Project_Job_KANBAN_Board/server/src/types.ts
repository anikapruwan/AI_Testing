export type State =
  | "wishlist"
  | "applied"
  | "interviewing"
  | "negotiating"
  | "offer_received"
  | "offer_not_received"
  | "done_archived";

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
  notes?: string;
}

export interface JobUpdate {
  company?: string;
  role?: string;
  date_applied?: string;
  key_requirements?: string[];
  resume_version?: string | null;
  state?: State;
  hr_contacts?: HRContact[];
  interviews?: Interview[];
  notes?: string;
}
