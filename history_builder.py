import os
import shutil
import subprocess
import tempfile
from datetime import date, datetime
from typing import List

from life_board import Board, DateGrid


class HistoryBuildError(Exception):
    pass


def _run_git(args: List[str], cwd: str) -> None:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HistoryBuildError(
            f"git {' '.join(args)} failed with code {result.returncode}:\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def _format_commit_date(d: date) -> str:
    # Use a stable midday UTC time so all commits on the same date are grouped
    # into a single calendar cell but remain deterministic.
    return datetime(d.year, d.month, d.day, 12, 0, 0).isoformat() + "Z"


def _collect_alive_cells(board: Board, dates: DateGrid) -> List[date]:
    """
    Return a sorted list of dates for which the Game of Life board has a live
    cell. The shape of `board` and `dates` must match.
    """
    if len(board) != len(dates):
        raise HistoryBuildError("Board and date grid width mismatch.")
    if board and len(board[0]) != len(dates[0]):
        raise HistoryBuildError("Board and date grid height mismatch.")

    alive_dates: List[date] = []
    for x, week in enumerate(board):
        for y, alive in enumerate(week):
            if alive:
                alive_dates.append(dates[x][y])

    # Sort chronologically and deduplicate (multiple alive cells on same date
    # are indistinguishable in the contribution calendar).
    unique_dates = sorted(set(alive_dates))
    return unique_dates


def generate_synthetic_history(
    token: str,
    repo_slug: str,
    default_branch: str,
    board: Board,
    dates: DateGrid,
    author_name: str,
    author_email: str,
) -> None:
    """
    Regenerate the target repository's history so that its commit author dates
    match the alive cells of the provided Game of Life board.

    The existing history on `default_branch` is replaced by force-pushing a new
    orphan branch whose commits are backdated using GIT_AUTHOR_DATE and
    GIT_COMMITTER_DATE. Each alive date will have at least one empty commit.
    """
    repo_url = f"https://x-access-token:{token}@github.com/{repo_slug}.git"
    tmpdir = tempfile.mkdtemp(prefix="life-history-")
    try:
        _run_git(["clone", "--no-tags", "--single-branch", repo_url, "."], cwd=tmpdir)

        # Create an orphan branch for the synthetic history.
        _run_git(["checkout", "--orphan", "temp-history"], cwd=tmpdir)

        # Remove all tracked files from index and working tree, but keep .git.
        # Ignore errors if there is nothing to remove.
        try:
            _run_git(["rm", "-rf", "."], cwd=tmpdir)
        except HistoryBuildError:
            # If the rm fails because there is nothing tracked yet, continue.
            pass

        # Clean untracked files but preserve the .git directory.
        for entry in os.listdir(tmpdir):
            if entry == ".git":
                continue
            path = os.path.join(tmpdir, entry)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

        alive_dates = _collect_alive_cells(board, dates)

        if not alive_dates:
            # Still need at least one commit so the branch exists; use an
            # ancient date well outside the visible contributions window.
            ancient = date(1970, 1, 1)
            env = os.environ.copy()
            iso = _format_commit_date(ancient)
            env["GIT_AUTHOR_DATE"] = iso
            env["GIT_COMMITTER_DATE"] = iso
            env["GIT_AUTHOR_NAME"] = author_name
            env["GIT_AUTHOR_EMAIL"] = author_email
            env["GIT_COMMITTER_NAME"] = author_name
            env["GIT_COMMITTER_EMAIL"] = author_email
            result = subprocess.run(
                ["git", "commit", "--allow-empty", "-m", "Initialize empty history"],
                cwd=tmpdir,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            if result.returncode != 0:
                raise HistoryBuildError(
                    f"Initial empty commit failed:\nSTDOUT:\n{result.stdout}\n"
                    f"STDERR:\n{result.stderr}"
                )
        else:
            for d in alive_dates:
                env = os.environ.copy()
                iso = _format_commit_date(d)
                env["GIT_AUTHOR_DATE"] = iso
                env["GIT_COMMITTER_DATE"] = iso
                env["GIT_AUTHOR_NAME"] = author_name
                env["GIT_AUTHOR_EMAIL"] = author_email
                env["GIT_COMMITTER_NAME"] = author_name
                env["GIT_COMMITTER_EMAIL"] = author_email
                result = subprocess.run(
                    [
                        "git",
                        "commit",
                        "--allow-empty",
                        "-m",
                        f"Life cell at {d.isoformat()}",
                    ],
                    cwd=tmpdir,
                    check=False,
                    capture_output=True,
                    text=True,
                    env=env,
                )
                if result.returncode != 0:
                    raise HistoryBuildError(
                        f"Commit for {d.isoformat()} failed:\nSTDOUT:\n"
                        f"{result.stdout}\nSTDERR:\n{result.stderr}"
                    )

        # Force-push the orphan branch to the default branch on origin.
        _run_git(["push", "origin", "+temp-history:" + default_branch], cwd=tmpdir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


__all__ = ["HistoryBuildError", "generate_synthetic_history"]

