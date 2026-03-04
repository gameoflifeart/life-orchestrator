import os
import sys
from datetime import date

from history_builder import HistoryBuildError, generate_synthetic_history
from life_board import Board, DateGrid, build_date_grid, next_generation
from state_store import LifeState, load_state, save_state


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def main() -> None:
    github_token = _require_env("GITHUB_TOKEN")
    repo_slug = _require_env("TARGET_REPO")
    default_branch = os.getenv("DEFAULT_BRANCH", "main")

    author_name = _require_env("AUTHOR_NAME")
    author_email = _require_env("AUTHOR_EMAIL")

    state_width = _get_int_env("STATE_WIDTH", 64)
    state_height = _get_int_env("STATE_HEIGHT", 64)
    viewport_x = _get_int_env("VIEWPORT_X", 0)
    viewport_y = _get_int_env("VIEWPORT_Y", 0)

    state: LifeState = load_state("state.json", state_width, state_height)

    if not state.board:
        print("State board is empty; nothing to evolve.", file=sys.stderr)
        sys.exit(1)

    next_board: Board = next_generation(state.board)
    state.board = next_board
    state.generation += 1

    save_state("state.json", state)

    today = date.today()
    dates_grid: DateGrid = build_date_grid(today, width_weeks=52, height_days=7)

    weeks = len(dates_grid)
    days = len(dates_grid[0]) if weeks > 0 else 0

    visible_board: Board = [[False for _ in range(days)] for _ in range(weeks)]

    for col in range(weeks):
        for row in range(days):
            x = viewport_x + col
            y = viewport_y + row
            if 0 <= x < state.width and 0 <= y < state.height:
                visible_board[col][row] = state.board[x][y]

    try:
        generate_synthetic_history(
            token=github_token,
            repo_slug=repo_slug,
            default_branch=default_branch,
            board=visible_board,
            dates=dates_grid,
            author_name=author_name,
            author_email=author_email,
        )
    except HistoryBuildError as exc:
        print(f"Failed to generate synthetic history: {exc}", file=sys.stderr)
        sys.exit(1)

    print(
        "Successfully updated history for "
        f"{repo_slug} on branch {default_branch} "
        f"at generation {state.generation}."
    )


if __name__ == "__main__":
    main()

