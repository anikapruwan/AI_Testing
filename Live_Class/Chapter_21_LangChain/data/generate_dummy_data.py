"""Generate dummy knowledge data for the VWO bug-triage RAG.

Run:  python data/generate_dummy_data.py

Produces (deterministic — safe to re-run):
  data/test_cases.csv          100 test cases (id, area, title, steps, expected,
                               severity, priority, team, tags)
  data/bug_reports/BUG-0xx.md  10 past-triaged bug reports (the triage "precedent"
                               knowledge: component -> team / severity / priority)
Drop any *.pdf into data/ as well; the ingester picks those up too.
"""
import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent
BUGS = DATA / "bug_reports"
BUGS.mkdir(parents=True, exist_ok=True)

# area -> (owning team, default severity, default priority, component)
AREAS = [
    ("Campaign Editor",     "Frontend Team",     "High",     "P1", "Editor"),
    ("A/B Test Engine",     "Backend Team",      "Critical", "P0", "Experimentation"),
    ("Reports & Analytics", "Data Team",         "High",     "P1", "Reporting"),
    ("Audience Targeting",  "Backend Team",      "High",     "P1", "Targeting"),
    ("SmartCode Snippet",   "Platform Team",     "Critical", "P0", "SmartCode"),
    ("Integrations",        "Integrations Team", "Medium",   "P2", "Integrations"),
    ("Account & Billing",   "Billing Team",      "High",     "P1", "Billing"),
    ("Heatmaps",            "Frontend Team",     "Medium",   "P2", "Heatmaps"),
    ("Surveys",             "Frontend Team",     "Low",      "P3", "Surveys"),
    ("Feature Rollout",     "Backend Team",      "High",     "P1", "FeatureFlags"),
]

# per-area action templates -> 10 each = 100 test cases
ACTIONS = [
    ("create a new {a} entry",              "{a} entry is created and saved"),
    ("edit an existing {a} item",           "changes persist after reload"),
    ("delete a {a} item",                   "item removed and audit-logged"),
    ("load {a} with 10k records",           "page renders under 3s, no timeout"),
    ("apply filters in {a}",                "only matching rows are shown"),
    ("export {a} data to CSV",              "CSV downloads with correct columns"),
    ("access {a} with read-only role",      "write actions are disabled"),
    ("open {a} on mobile viewport",         "layout is responsive, no overflow"),
    ("trigger {a} with invalid input",      "validation error shown, no 500"),
    ("concurrent edit of {a} by 2 users",   "last-write wins, no data loss"),
]


def gen_test_cases():
    rows = []
    n = 1
    for area, team, sev, prio, comp in AREAS:
        for act, exp in ACTIONS:
            rows.append({
                "id": f"TC-{n:03d}",
                "area": area,
                "component": comp,
                "title": f"Verify user can {act.format(a=area.lower())}",
                "steps": f"1. Log in to VWO. 2. Go to {area}. "
                         f"3. {act.format(a=area).capitalize()}. 4. Submit.",
                "expected": exp.format(a=area),
                "severity": sev,
                "priority": prio,
                "team": team,
                "tags": f"{comp.lower()},regression,vwo",
            })
            n += 1
    out = DATA / "test_cases.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} test cases -> {out}")


# 10 past-triaged bugs — the precedent the triager should lean on
BUG_REPORTS = [
    ("Forgot-password reset email never sent", "SmartCode", "Critical", "P0", "Platform Team",
     "SES sender domain un-verified after cert rotation; all transactional mail bounced.",
     "Re-verified DKIM, added synthetic monitor on the reset flow."),
    ("A/B test variation not splitting traffic 50/50", "Experimentation", "Critical", "P0", "Backend Team",
     "Bucketing hash seeded with campaign-id only; new campaigns collided.",
     "Seed now includes visitor-id; backfilled allocation."),
    ("Conversion report shows 0 conversions for live campaign", "Reporting", "High", "P1", "Data Team",
     "Goal event pipeline dropped events when payload >32KB.",
     "Raised Kafka max.message.bytes, added DLQ alert."),
    ("Editor crashes when adding 3rd widget", "Editor", "High", "P1", "Frontend Team",
     "Unbounded recursion in nested-widget render; stack overflow.",
     "Memoized render tree, capped nesting depth at 8."),
    ("Targeting rule 'country = IN' matches all visitors", "Targeting", "High", "P1", "Backend Team",
     "GeoIP lookup defaulted to match-all on cache miss.",
     "Cache-miss now fails closed (no match) + async refill."),
    ("Salesforce integration sync stuck in 'pending'", "Integrations", "Medium", "P2", "Integrations Team",
     "OAuth refresh token expired; worker retried forever without alert.",
     "Token auto-refresh + dead-letter after 5 retries."),
    ("Invoice overcharged annual plan by 2x", "Billing", "Critical", "P0", "Billing Team",
     "Proration ran twice on plan upgrade due to duplicate webhook.",
     "Idempotency key on webhook handler; refunds issued."),
    ("Heatmap not recording clicks on SPA route change", "Heatmaps", "Medium", "P2", "Frontend Team",
     "Recorder bound to initial DOM only; missed client-side nav.",
     "Re-attach listeners on history.pushState."),
    ("Survey popup blocks page on slow network", "Surveys", "Low", "P3", "Frontend Team",
     "Modal rendered before async config loaded, no timeout.",
     "Lazy-render after config or 2s timeout, whichever first."),
    ("Feature flag rollout 100% but 30% users see old UI", "FeatureFlags", "High", "P1", "Backend Team",
     "Edge CDN cached flag eval for 1h; stale after rollout.",
     "Flag responses now no-store; SSE invalidation added."),
]


def gen_bug_reports():
    for i, (summary, comp, sev, prio, team, cause, fix) in enumerate(BUG_REPORTS, 1):
        md = (
            f"# BUG-{i:03d}: {summary}\n\n"
            f"- **Component:** {comp}\n"
            f"- **Severity:** {sev}\n"
            f"- **Priority:** {prio}\n"
            f"- **Owning team:** {team}\n\n"
            f"## Root cause\n{cause}\n\n"
            f"## Resolution\n{fix}\n"
        )
        (BUGS / f"BUG-{i:03d}.md").write_text(md)
    print(f"wrote {len(BUG_REPORTS)} bug reports -> {BUGS}")


if __name__ == "__main__":
    gen_test_cases()
    gen_bug_reports()
