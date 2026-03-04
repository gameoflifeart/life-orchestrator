## Game of Life on GitHub Contributions

This repository contains a Python script and GitHub Actions workflow that
rewrite the history of a dedicated target repository so that the commit dates
encode one frame of Conway’s Game of Life on your GitHub contributions graph.

Each scheduled run:

- **Reads** your current public contribution grid via the GitHub GraphQL API.
- **Interprets** the last 52 weeks as a 7×52 Game of Life board.
- **Computes** the next generation of the board.
- **Regenerates** the history of a dedicated "art" repository so that its
  commits fall exactly on the dates of the alive cells.
- **Force-pushes** the new history, so when the contribution calendar refreshes
  it shows the next frame.

### Important warnings

- The target repository’s default branch is **force-pushed** on every run.
- Use a dedicated repository for this project; do **not** store real code or
  important history there.
- This project artificially shapes the contribution graph and should be treated
  as art/experimentation, not a measure of real activity.

### Configuration

The updater is driven entirely by environment variables:

- `ACCESS_TOKEN` – PAT with at least `repo` scope for the target repo and
  GraphQL access.
- `TARGET_USERNAME` – GitHub username whose contribution graph is used as the
  Game of Life board.
- `TARGET_REPO` – `owner/repo` slug of the dedicated art repository whose
  history will be rewritten.
- `DEFAULT_BRANCH` – Default branch name of the target repo (e.g. `main`).
- `AUTHOR_NAME` / `AUTHOR_EMAIL` – Name and email that should own the commits.
  These must match your GitHub identity for contributions to count.
- `CONFIRM_FORCE_PUSH` – Must be set to `1` to allow the script to rewrite
  history. This is a safety toggle.

### GitHub Actions setup

The included workflow `.github/workflows/life.yml` is intended to run in this
orchestrator repository.

1. Create a **personal access token** for your account with:
   - Access to the target repository (fine-grained or classic `repo` scope).
2. Add secrets and variables to this repository:
   - Secrets:
     - `LIFE_ACCESS_TOKEN` – the PAT created above.
     - `CONFIRM_FORCE_PUSH` – set to `1` once you are sure about the setup.
   - Repository variables:
     - `TARGET_USERNAME` – your GitHub username.
     - `TARGET_REPO` – `owner/repo` of the dedicated art repo.
     - `DEFAULT_BRANCH` – e.g. `main`.
     - `AUTHOR_NAME` – your display name.
     - `AUTHOR_EMAIL` – the email GitHub associates with your commits.
3. Ensure the target repo is created and empty (or disposable), with the
   configured default branch.
4. Enable GitHub Actions in this orchestrator repo.

By default the workflow runs daily at 02:00 UTC and can also be triggered
manually with the **Run workflow** button.

