# hello-ledger 📗

![tests](https://github.com/AI-Lab-for-Accountants/hello-ledger/actions/workflows/tests.yml/badge.svg)

A tiny general ledger you already understand — so you can learn **GitHub** on it.

Built for the [AI Lab for Accountants](https://ailabforaccountants.com). You know
debits and credits; this repo teaches forks, branches, commits, and pull requests
by letting you practice them on a working set of books.

## What this is

- A real, working double-entry general ledger: chart of accounts, journal
  entries, ledgers, and a trial balance. About 800 lines of readable Python.
- A **classroom**. It ships deliberately incomplete — the missing features
  (income statement, CSV export, date filters…) are the
  [open issues](../../issues), each one sized to be someone's first pull request.
- A place where AI is welcome. Point Claude (or any AI assistant) at this repo
  and it will read [`CLAUDE.md`](CLAUDE.md) and act as your **tutor** — it
  explains and guides, but you drive.

## What this is not

- Not bookkeeping software for real work, and not tax or accounting advice.
  It's a teaching prop — a friendly one, but a prop.
- **Never put client data in it.** Use the bundled fictional demo books. The
  data you enter stays in a local `hello_ledger.db` file on your machine (or in
  your Codespace) and is never committed to GitHub — but client work belongs in
  your real systems, not here.

## Quick start

**The easy way — GitHub Codespaces, nothing to install:**

1. Click **Fork** (top right) — this creates *your own copy* of the repo.
2. On **your fork**, click **Code → Codespaces → Create codespace on main**.
3. Wait a minute. The app opens on its own; if it doesn't, run
   `streamlit run app.py` in the terminal.

**On your own computer** (needs [Python](https://www.python.org/downloads/) 3.11+):

```bash
git clone https://github.com/YOUR-USERNAME/hello-ledger.git
cd hello-ledger
pip install -r requirements.txt
streamlit run app.py
```

## Meet the demo books

The **Get Started** page in the app walks you through onboarding a client, the
way it happens in real life, using the fictional **Sample Company LLC** (a small
consulting firm) from the [`demo_data/`](demo_data) folder:

1. **Chart of accounts** — `accounts.csv`
2. **Beginning balances** — the prior-year ending trial balance as of
   12/31/2025 (`trial_balance_2025-12-31.csv`). It has to balance; the app checks.
3. **Q1 2026 activity** — 47 transactions (`transactions_q1_2026.csv`): rent,
   payroll, retainers, a member draw… and one invoice still sitting in A/R.

Or click **⚡ Load all the demo data for me** and skip to exploring.

## Your first hour

1. **Make it yours** *(on your fork — nothing to submit)*: open
   [`branding.toml`](branding.toml) and put your firm's name on the app. Swap
   `primaryColor` in `.streamlit/config.toml` for your brand color. Commit the
   change and you've made your first commit. Show it off in the
   [show-and-tell issue](../../issues).
2. **Make it better** *(your first pull request)*: pick an issue labeled
   [`good first issue`](../../labels/good%20first%20issue), then follow
   [CONTRIBUTING.md](CONTRIBUTING.md) — it walks you through branch → change →
   commit → pull request in plain language.

When your pull request goes green ✅ (the tests pass) and a maintainer merges
it, your code is part of the repo everyone downloads. That's the whole loop —
and after you've done it once here, you've done it, period.

## Working with AI

Totally encouraged — most of us build with AI assistance. Open this folder with
Claude Code (or paste the repo link to your AI of choice) and ask it to *walk
you through* an issue. The [`CLAUDE.md`](CLAUDE.md) file asks the AI to explain
each step and let you do the work — if it just does everything for you, you've
learned nothing, and that defeats the point.

## License

[MIT](LICENSE) — copy it, fork it, teach with it.
