import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from life_board import Board


@dataclass
class LifeState:
    board: Board
    width: int
    height: int
    generation: int


def _default_board(width: int, height: int) -> Board:
    # Simple deterministic seed: a small glider near the top-left if it fits.
    board: Board = [[False for _ in range(height)] for _ in range(width)]
    if width >= 3 and height >= 3:
        # Coordinates are (x, y) with x = column, y = row.
        board[1][0] = True
        board[2][1] = True
        board[0][2] = True
        board[1][2] = True
        board[2][2] = True
    return board


def load_state(
    path: str, default_width: int, default_height: int
) -> LifeState:
    """
    Load the canonical Game of Life state from a JSON file.

    If the file does not exist or is invalid, initialize a new universe with
    the given default dimensions and a deterministic seed pattern.
    """
    p = Path(path)
    if not p.exists():
        board = _default_board(default_width, default_height)
        return LifeState(board=board, width=default_width, height=default_height, generation=0)

    try:
        data = json.loads(p.read_text())
    except Exception:
        board = _default_board(default_width, default_height)
        return LifeState(board=board, width=default_width, height=default_height, generation=0)

    try:
        width = int(data["width"])
        height = int(data["height"])
        generation = int(data.get("generation", 0))
        raw_board = data["board"]
    except (KeyError, TypeError, ValueError):
        board = _default_board(default_width, default_height)
        return LifeState(board=board, width=default_width, height=default_height, generation=0)

    if not isinstance(raw_board, list) or len(raw_board) != width:
        board = _default_board(default_width, default_height)
        return LifeState(board=board, width=default_width, height=default_height, generation=0)

    board: Board = []
    for col in raw_board:
        if not isinstance(col, list) or len(col) != height:
            board = _default_board(default_width, default_height)
            return LifeState(board=board, width=default_width, height=default_height, generation=0)
        board.append([bool(cell) for cell in col])

    return LifeState(board=board, width=width, height=height, generation=generation)


def save_state(path: str, state: LifeState) -> None:
    """
    Persist the canonical Game of Life state to a JSON file.
    """
    p = Path(path)
    payload = {
        "width": state.width,
        "height": state.height,
        "generation": state.generation,
        # Store as width-major: list of columns, each a list of rows.
        "board": [[1 if cell else 0 for cell in col] for col in state.board],
    }
    p.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True))


__all__ = ["LifeState", "load_state", "save_state"]

