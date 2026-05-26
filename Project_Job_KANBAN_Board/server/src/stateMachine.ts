import type { State } from "./types.js";

export const STATES: State[] = [
  "wishlist",
  "applied",
  "interviewing",
  "negotiating",
  "offer_received",
  "offer_not_received",
  "done_archived",
];

export const TRANSITIONS: Record<State, State[]> = {
  wishlist: ["applied"],
  applied: ["interviewing"],
  interviewing: ["negotiating"],
  negotiating: ["offer_received", "offer_not_received"],
  offer_received: ["done_archived"],
  offer_not_received: ["done_archived"],
  done_archived: [],
};

export function allowedNext(state: State): State[] {
  const base = [...(TRANSITIONS[state] ?? [])];
  if (state !== "done_archived" && !base.includes("done_archived")) {
    base.push("done_archived");
  }
  return base;
}
