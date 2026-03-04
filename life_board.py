import datetime as _dt
from typing import List


Board = List[List[bool]]
DateGrid = List[List[_dt.date]]


def build_date_grid(
    today: _dt.date, *, width_weeks: int = 52, height_days: int = 7
) -> DateGrid:
    """
    Build a 7×52 date grid matching GitHub's contribution calendar layout,
    using only the current date and a fixed calendar model.

    Assumptions:
      - Weeks start on Sunday.
      - The rightmost column corresponds to the week containing `today`.
      - Columns proceed leftwards in whole-week steps.
    """
    # Python's weekday(): Monday=0 .. Sunday=6
    # We want the most recent Sunday <= today.
    delta = (today.weekday() + 1) % 7  # 0 if today is Sunday, 6 if Saturday
    sunday_this_week = today - _dt.timedelta(days=delta)

    grid: DateGrid = []

    for col in range(width_weeks):
        # Column index 0 is the oldest; 51 is the newest (containing today).
        weeks_from_oldest = width_weeks - 1 - col
        sunday = sunday_this_week - _dt.timedelta(weeks=weeks_from_oldest)
        column_dates: List[_dt.date] = []
        for row in range(height_days):
            column_dates.append(sunday + _dt.timedelta(days=row))
        grid.append(column_dates)

    return grid


def next_generation(board: Board) -> Board:
    """
    Compute the next Game of Life generation on a bounded 2D grid.

    The grid is treated as finite (no wrapping). Cells outside the grid are
    considered dead.
    """
    if not board:
        return []

    width = len(board)
    height = len(board[0])

    def neighbors_alive(x: int, y: int) -> int:
        count = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and board[nx][ny]:
                    count += 1
        return count

    new_board: Board = [[False] * height for _ in range(width)]
    for x in range(width):
        for y in range(height):
            alive = board[x][y]
            n = neighbors_alive(x, y)
            if alive and n in (2, 3):
                new_board[x][y] = True
            elif not alive and n == 3:
                new_board[x][y] = True
            else:
                new_board[x][y] = False

    return new_board


__all__ = ["Board", "DateGrid", "build_date_grid", "next_generation"]


