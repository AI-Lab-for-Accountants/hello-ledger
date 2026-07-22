# Contributing to hello-ledger

This guide assumes you've never sent a pull request before. That's the point.
Words in **bold** are the GitHub vocabulary worth keeping.

## The big picture

You never change this repo directly. You change **your copy** (your *fork*),
and then *ask* this repo to pull your change in — a **pull request** ("PR").
A maintainer reviews it, the automated tests check it, and if all's well it's
**merged**. That's how strangers safely build software together, and it's
exactly what we practice here.

## Step by step

### 0. Fork (once)

Click **Fork** at the top of the repo page. GitHub creates
`github.com/YOUR-USERNAME/hello-ledger` — yours to experiment on. You can't
break the original from your fork, so relax.

### 1. Open your fork

Easiest: **Code → Codespaces → Create codespace** *on your fork* — a ready
workspace in your browser. (Or clone it locally per the README.)

### 2. Pick an issue

Browse the [issues](../../issues) labeled **good first issue**. Each says which
file(s) to touch and what "done" looks like. Comment "I'll take this one!" so
two people don't duplicate work.

> **No terminal required.** Every step below is a button in your codespace or
> on github.com. If you *like* the terminal, the equivalent command is shown
> in a "prefer the terminal?" note — same result either way.

### 3. Make a branch

A **branch** is a parallel copy of the code inside your fork where your change
lives until it's ready — a working-paper copy of the file.

In your codespace, click the branch name in the **bottom-left corner** of the
window (it says `main`), choose **＋ Create new branch…**, and name it after
the work, e.g. `add-income-statement`.

> *Prefer the terminal?* `git switch -c add-income-statement`

### 4. Make the change

Edit the files. The app is already running in its preview tab (it started when
your codespace opened) — after you save a file, click **Rerun** in the app, or
choose **Always rerun** once and forget about it. To run the tests, click the
**Testing** icon in the left sidebar (the beaker 🧪) and press the play
button — all green means the books still tie out.

> *Prefer the terminal?* `streamlit run app.py` and `pytest`

Working with an AI assistant? Great — have it *explain* its suggestions until
you could make the change yourself. You're the reviewer of your own work; that
instinct is the whole profession, and it applies to code too.

### 5. Commit

A **commit** is a saved snapshot with a note about what changed and why —
a posted entry with a memo.

Click the **Source Control** icon in the left sidebar (the little branch
diagram — it grows a blue badge counting your changed files). Type your memo
in the message box — *"Add an income statement page"* — and press
**✓ Commit**. If it asks whether to stage all changes, say **Yes**.

> *Prefer the terminal?* `git add -A` then
> `git commit -m "Add an income statement page"`

### 6. Push and open the pull request

**Push** means sending your branch up to your fork on GitHub. After you
commit, that same blue button becomes **Publish Branch** (or **Sync
Changes**) — click it. Done: your branch is on GitHub.

> *Prefer the terminal?* `git push -u origin add-income-statement`

Now GitHub will show a **"Compare & pull request"** button on your fork — click it,
check that the target is `AI-Lab-for-Accountants/hello-ledger` `main`, write a
sentence or two about what you did, and submit.

### 7. Watch the checks, then the review

Within a minute you'll see the automated **checks** run on your PR — the same
`pytest` suite you ran, executed by GitHub Actions. Green check ✅ means the
books still balance. A maintainer will review, maybe ask a question or request
a tweak (that's normal, not a rejection — push another commit to the same
branch and the PR updates itself), and then **merge**. 🎉

## House rules

- **One issue, one branch, one PR.** Small and focused gets merged fast.
- **Tests must pass.** If you add a feature worth keeping, a small test is
  even better.
- **Don't refactor the world.** Leave code you didn't need to touch alone.
- **The branding exercise stays on your fork** — don't PR your firm's name
  onto everyone's app. 🙂 Post a screenshot in the show-and-tell issue instead.
- **No real client data, ever** — in code, in CSVs, in screenshots, anywhere.
- Be kind in comments and reviews. Everyone here is learning in public, which
  takes guts.

## Stuck?

Comment on your issue or bring it to the AI Lab call. Being stuck in a fork,
on a branch, is a completely safe place to be — nothing you do there can hurt
anything.
