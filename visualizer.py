"""
Curses-based terminal ASCII renderer for A-Maze-ing.

Terminal characters are roughly twice as tall as they are wide (~2:1 ratio),
so a naive 1×1 interior per cell makes vertical corridors look narrower than
horizontal ones.

Fix: use a non-square cell layout where each cell interior is 2 chars wide
and 1 char tall. The full character grid is then (3W+1) cols × (2H+1) rows:

  col bands:  [wall=1][interior=2][wall=1][interior=2]...  → 3W+1 total cols
  row bands:  [wall=1][interior=1][wall=1][interior=1]...  → 2H+1 total rows

Column index mapping:
  col % 3 == 0            → vertical wall column
  col % 3 == 1 or 2       → cell interior or h-wall fill

Cell (cx, cy) occupies:
  terminal cols  cx*3+1  and  cx*3+2   (2 chars wide)
  terminal row   cy*2+1               (1 char tall)

Controls:
  1 - Re-generate a new maze
  2 - Show/Hide shortest path
  3 - Rotate wall colour
  4 - Quit
"""

from __future__ import annotations

import curses
from typing import Callable

from mazegen_src.mazegen import MazeGenerator, NORTH, EAST, SOUTH, WEST

COLOUR_WALL = 1
COLOUR_PATH = 2
COLOUR_ENTRY = 3
COLOUR_EXIT = 4
COLOUR_42 = 5
COLOUR_MENU = 6
COLOUR_OPEN = 7

WALL_COLORS = [
    curses.COLOR_WHITE,
    curses.COLOR_YELLOW,
    curses.COLOR_GREEN,
    curses.COLOR_CYAN,
    curses.COLOR_MAGENTA,
    curses.COLOR_RED,
]

WALL_CHAR = '█'
PATH_CHAR = '█'


def _init_colors() -> None:
    """Initialize curses colour pairs."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOUR_OPEN, curses.COLOR_BLACK, curses.COLOR_BLACK)
    curses.init_pair(COLOUR_WALL, curses.COLOR_WHITE, curses.COLOR_WHITE)
    curses.init_pair(COLOUR_PATH, curses.COLOR_CYAN, curses.COLOR_CYAN)
    curses.init_pair(COLOUR_ENTRY, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
    curses.init_pair(COLOUR_EXIT, curses.COLOR_RED, curses.COLOR_RED)
    curses.init_pair(COLOUR_42, curses.COLOR_BLUE, curses.COLOR_BLUE)
    curses.init_pair(COLOUR_MENU, curses.COLOR_YELLOW, -1)


def _set_wall_color(color_idx: int) -> None:
    """Change the wall colour to the given palette index."""
    c = WALL_COLORS[color_idx % len(WALL_COLORS)]
    curses.init_pair(COLOUR_WALL, c, c)


def _draw_maze(
    stdscr: curses.window,
    gen: MazeGenerator,
    show_path: bool,
    wall_color_idx: int,
) -> None:
    """
    Draw the maze with aspect-ratio-corrected cell layout.

    Each maze cell interior is 2 terminal chars wide and 1 char tall,
    compensating for the ~2:1 terminal character aspect ratio so that
    horizontal and vertical corridors appear the same visual width.

    Grid structure (W cells wide, H cells tall):
      Total terminal cols: 3*W + 1
      Total terminal rows: 2*H + 1

    For a given terminal (row, col):
      row % 2 == 0             → horizontal wall/border row
      row % 2 == 1             → cell interior row
      col % 3 == 0             → vertical wall/border column
      col % 3 == 1 or 2        → cell interior or h-wall columns

    Cell (cx, cy) maps to:
      terminal row:  cy*2 + 1
      terminal cols: cx*3 + 1  and  cx*3 + 2

    Args:
        stdscr: The curses window.
        gen: Fully generated MazeGenerator instance.
        show_path: Whether to overlay the solution path.
        wall_color_idx: Current wall colour index (colour already applied).
    """
    max_y, max_x = stdscr.getmaxyx()
    # Clear only the maze area rows, not the menu below
    maze_rows = 2 * gen.height + 1
    blank_line = ' ' * (max_x - 1)
    for r in range(maze_rows):
        try:
            stdscr.addstr(r, 0, blank_line)
        except curses.error:
            pass

    path_set: set[tuple[int, int]] = set(gen.solution) if show_path else set()
    forty_two_set: set[tuple[int, int]] = set(gen.forty_two_cells)

    wall_attr = curses.color_pair(COLOUR_WALL)
    path_attr = curses.color_pair(COLOUR_PATH)
    entry_attr = curses.color_pair(COLOUR_ENTRY)
    exit_attr = curses.color_pair(COLOUR_EXIT)
    ft_attr = curses.color_pair(COLOUR_42)
    open_attr = curses.color_pair(COLOUR_OPEN)

    W = gen.width
    H = gen.height

    total_cols = 3 * W + 1
    total_rows = 2 * H + 1

    def safe_add(row: int, col: int, ch: str, attr: int = 0) -> None:
        """Write one character safely, ignoring out-of-bounds."""
        try:
            if 0 <= row < max_y and 0 <= col < max_x - 1:
                stdscr.addstr(row, col, ch, attr)
        except curses.error:
            pass

    def cell_of_col(col: int) -> int:
        """Return the maze cell x-index for a given terminal column."""
        return col // 3

    def is_vcol_border(col: int) -> bool:
        """True if this terminal column is a vertical wall column."""
        return col % 3 == 0

    def is_hrow_border(row: int) -> bool:
        """True if this terminal row is a horizontal wall row."""
        return row % 2 == 0

    for row in range(total_rows):
        for col in range(total_cols):
            cx = cell_of_col(col)
            cy = row // 2
            hborder = is_hrow_border(row)
            vborder = is_vcol_border(col)

            # ── Corner: vertical-wall col + horizontal-wall row ──────────
            if hborder and vborder:
                safe_add(row, col, WALL_CHAR, wall_attr)

            # ── Horizontal wall/gap: h-border row, interior col ──────────
            # Outer border rows are always solid wall (entry/exit open only
            # in the data, not visually — the box stays closed like the PDF).
            elif hborder and not vborder:
                above = cy - 1
                is_outer = (row == 0 or row == 2 * H)
                wall_closed = is_outer
                if not is_outer:
                    if 0 <= above < H and (gen.grid[above][cx] & SOUTH):
                        wall_closed = True
                    elif 0 <= cy < H and (gen.grid[cy][cx] & NORTH):
                        wall_closed = True

                if wall_closed:
                    safe_add(row, col, WALL_CHAR, wall_attr)
                elif (show_path
                        and 0 <= above < H and (cx, above) in path_set
                        and 0 <= cy < H and (cx, cy) in path_set):
                    safe_add(row, col, PATH_CHAR, path_attr)
                else:
                    safe_add(row, col, ' ', open_attr)

            # ── Vertical wall/gap: interior row, v-border col ────────────
            # Outer border cols are always solid wall for the same reason.
            elif not hborder and vborder:
                left = cx - 1
                is_outer = (col == 0 or col == 3 * W)
                wall_closed = is_outer
                if not is_outer:
                    if 0 <= left < W and (gen.grid[cy][left] & EAST):
                        wall_closed = True
                    elif 0 <= cx < W and (gen.grid[cy][cx] & WEST):
                        wall_closed = True

                if wall_closed:
                    safe_add(row, col, WALL_CHAR, wall_attr)
                elif (show_path
                        and 0 <= left < W and (left, cy) in path_set
                        and 0 <= cx < W and (cx, cy) in path_set):
                    safe_add(row, col, PATH_CHAR, path_attr)
                else:
                    safe_add(row, col, ' ', open_attr)

            # ── Cell interior: interior row, interior col ─────────────────
            else:
                if cy >= H or cx >= W:
                    continue

                is_42 = (cx, cy) in forty_two_set
                is_entry = (cx, cy) == gen.entry
                is_exit = (cx, cy) == gen.exit_
                is_path = (cx, cy) in path_set

                # First interior col of cell → may show label char
                col_in_cell = col % 3  # 1 or 2

                if is_42:
                    safe_add(row, col, WALL_CHAR, ft_attr)
                elif is_entry:
                    safe_add(row, col, WALL_CHAR, entry_attr)
                elif is_exit:
                    safe_add(row, col, WALL_CHAR, exit_attr)
                elif is_path:
                    safe_add(row, col, PATH_CHAR, path_attr)
                else:
                    safe_add(row, col, ' ', open_attr)

    # ── Menu ─────────────────────────────────────────────────────────────
    menu_y = total_rows + 1
    safe_add(menu_y,     0, "==== A-Maze-ing ====", curses.color_pair(COLOUR_MENU))
    safe_add(menu_y + 1, 0, "1. Re-generate a new maze")
    safe_add(menu_y + 2, 0, "2. Show/Hide path from entry to exit")
    safe_add(menu_y + 3, 0, "3. Rotate maze colors")
    safe_add(menu_y + 4, 0, "4. Quit")
    safe_add(menu_y + 5, 0, "Choice (1-4): ", curses.color_pair(COLOUR_MENU))

    stdscr.refresh()


def run_visualizer(
    gen: MazeGenerator,
    regenerate_cb: Callable[[], MazeGenerator],
) -> None:
    """
    Launch the curses interactive visualizer.

    Args:
        gen: Initial MazeGenerator with generated maze.
        regenerate_cb: Callable returning a freshly generated MazeGenerator.
    """
    def _main(stdscr: curses.window) -> None:
        _init_colors()
        curses.curs_set(0)
        stdscr.keypad(True)

        current_gen = gen
        show_path = False
        wall_color_idx = 0

        _draw_maze(stdscr, current_gen, show_path, wall_color_idx)

        while True:
            try:
                key = stdscr.getkey()
            except curses.error:
                continue

            if key == '1':
                # Wipe only the maze rows so the menu stays visible,
                # then redraw — user sees a clear wipe+redraw even with
                # a fixed seed producing the same maze.
                max_y2, max_x2 = stdscr.getmaxyx()
                blank = ' ' * (max_x2 - 1)
                maze_rows2 = 2 * current_gen.height + 1
                for r in range(maze_rows2):
                    try:
                        stdscr.addstr(r, 0, blank)
                    except curses.error:
                        pass
                stdscr.refresh()
                curses.napms(120)
                current_gen = regenerate_cb()
                show_path = False
                _draw_maze(stdscr, current_gen, show_path, wall_color_idx)
            elif key == '2':
                show_path = not show_path
                _draw_maze(stdscr, current_gen, show_path, wall_color_idx)
            elif key == '3':
                wall_color_idx = (wall_color_idx + 1) % len(WALL_COLORS)
                _set_wall_color(wall_color_idx)
                _draw_maze(stdscr, current_gen, show_path, wall_color_idx)
            elif key == '4' or key == 'q' or key == 'Q':
                break

    try:
        curses.wrapper(_main)
    except KeyboardInterrupt:
        pass