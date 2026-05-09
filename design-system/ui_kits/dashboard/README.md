# Dashboard UI kit — Lena's morning briefing

The web dashboard. Editorial calm, not alert console. Lena should be able to spend twelve minutes here with her morning coffee.

## Files

- `index.html` — Briefing screen with samtal list + stat panel + click-thru detail sheet
- `SideNav.jsx` — left rail with Lucide-style line icons (rendered inline so we don't fight a CDN)
- `BriefingHeader.jsx` — editorial greeting + signal subhead
- `StatPanel.jsx` — 4-up tabular stats
- `CallList.jsx` — overnight calls, status pills, click to open detail
- `CallDetail.jsx` — slide-in sheet: summary + extracted fields + transcript

## What's interactive

Click any row in "I natt" — a detail sheet slides in from the right with the AI's summary, extracted fields, and full transcript. Press × or click the scrim to close.

## What's not built (deliberately)

The brief never specified an analytics view, billing screen, settings, or inbox-style triage. We chose not to invent them. When the codebase ships, replace what's here with the real screens — but the components in this kit (SideNav, status pills, call list row, detail sheet) should slot in directly.
