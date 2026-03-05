"""
Curses-based terminal ASCII renderer for A-Maze-ing.

Renders the maze using block characters. Each maze cell is drawn as a
3x3 block of characters in the terminal. Walls are drawn as solid blocks,
corridors as spaces.

Controls displayed in a menu below the maze:
  1 - Re-generate a new maze
  2 - Show/Hide shortest path
  3 - Rotate wall colour
  4 - Quit
"""

from __future__ import annotations

import curses
import sys
from typing import Callable

from mazegen_src.mazegen import MazeGenerator, NORTH, EAST, SOUTH, WEST

# Wall colour palette (curses colour pairs)
COLOUR_WALL = 1
COLOUR_PATH = 2
COLOUR_ENTRY = 3
COLOUR_EXIT = 4
COLOUR_42 = 5
COLOUR_MENU = 6

WALL_COLORS = [
    curses.COLOR_WHITE,
    curses.COLOR_YELLOW,
    curses.COLOR_GREEN,
    curses.COLOR_CYAN,
    curses.COLOR_MAGENTA,
    curses.COLOR_RED,
]

WALL_CHAR = '█'
OPEN_CHAR = ' '


def _init_colors() -> None:
    """Initialize curses colour pairs."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOUR_WALL, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOUR_PATH, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOUR_ENTRY, curses.COLOR_MAGENTA, -1)
    curses.init_pair(COLOUR_EXIT, curses.COLOR_RED, -1)
    curses.init_pair(COLOUR_42, curses.COLOR_WHITE, curses.COLOR_WHITE)
    curses.init_pair(COLOUR_MENU, curses.COLOR_YELLOW, -1)


def _set_wall_color(color_idx: int) -> None:
    """Change the wall colour to the given palette index."""
    curses.init_pair(COLOUR_WALL, WALL_COLORS[color_idx % len(WALL_COLORS)], -1)


def _draw_maze(
    stdscr: curses.window,
    gen: MazeGenerator,
    show_path: bool,
    wall_color_idx: int,
) -> None:
    """
    Draw the entire maze to the curses window.

    Each maze cell occupies a 3x3 block of terminal characters:
      - Top row:    NW-corner, N-wall, NE-corner
      - Middle row: W-wall,   cell,   E-wall
      - Bottom row: SW-corner, S-wall, SE-corner

    Args:
        stdscr: The curses window.
        gen: MazeGenerator instance with generated maze.
        show_path: Whether to overlay the solution path.
        wall_color_idx: Index into WALL_COLORS for wall colour.
    """
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()

    path_set = set(gen.solution) if show_path else set()
    forty_two_set = set(gen.forty_two_cells)

    # Cell size in terminal chars
    cell_w = 3
    cell_h = 2  # We use a 2-row approach: top wall + cell body

    wall_attr = curses.color_pair(COLOUR_WALL)
    path_attr = curses.color_pair(COLOUR_PATH)
    entry_attr = curses.color_pair(COLOUR_ENTRY)
    exit_attr = curses.color_pair(COLOUR_EXIT)
    ft_attr = curses.color_pair(COLOUR_42)

    W = gen.width
    H = gen.height

    # Each cell = 2 rows tall (top wall row + body row)
    # Plus one final bottom wall row
    # Each cell = 2 cols wide (left wall col + body col)
    # Plus one final right wall col

    def safe_addstr(y: int, x: int, s: str, attr: int = 0) -> None:
        """Add string safely, ignoring out-of-bounds errors."""
        try:
            if 0 <= y < max_y and 0 <= x < max_x:
                # Truncate if needed
                avail = max_x - x
                if avail > 0:
                    stdscr.addstr(y, x, s[:avail], attr)
        except curses.error:
            pass

    for cy in range(H):
        for cx in range(W):
            cell = gen.grid[cy][cx]
            # Terminal position of top-left corner of this cell block
            ty = cy * 2
            tx = cx * 2

            is_42 = (cx, cy) in forty_two_set
            is_entry = (cx, cy) == gen.entry
            is_exit = (cx, cy) == gen.exit_
            is_path = (cx, cy) in path_set

            # Determine cell body attribute
            if is_42:
                body_attr = ft_attr
                body_char = ' '
            elif is_entry:
                body_attr = entry_attr
                body_char = 'S'
            elif is_exit:
                body_attr = exit_attr
                body_char = 'E'
            elif is_path:
                body_attr = path_attr
                body_char = '·'
            else:
                body_attr = 0
                body_char = ' '

            # Top-left corner (always wall)
            safe_addstr(ty, tx, WALL_CHAR, wall_attr)

            # Top wall (N wall of cell)
            if cell & NORTH:
                safe_addstr(ty, tx + 1, WALL_CHAR, wall_attr)
            else:
                safe_addstr(ty, tx + 1, ' ', 0)

            # Body row
            # Left wall (W wall)
            if cell & WEST:
                safe_addstr(ty + 1, tx, WALL_CHAR, wall_attr)
            else:
                safe_addstr(ty + 1, tx, ' ', 0)

            # Cell interior
            safe_addstr(ty + 1, tx + 1, body_char, body_attr)

        # After all columns in this row, draw the right border
        cx = W - 1
        ty = cy * 2
        cell = gen.grid[cy][cx]
        # Top-right corner
        safe_addstr(ty, W * 2, WALL_CHAR, wall_attr)
        # Right wall body
        if cell & EAST:
            safe_addstr(ty + 1, W * 2, WALL_CHAR, wall_attr)
        else:
            safe_addstr(ty + 1, W * 2, ' ', 0)

    # Draw final bottom border row
    ty = H * 2
    for cx in range(W):
        cell = gen.grid[H - 1][cx]
        tx = cx * 2
        safe_addstr(ty, tx, WALL_CHAR, wall_attr)
        if cell & SOUTH:
            safe_addstr(ty, tx + 1, WALL_CHAR, wall_attr)
        else:
            safe_addstr(ty, tx + 1, ' ', 0)
    safe_addstr(ty, W * 2, WALL_CHAR, wall_attr)

    # Draw menu below maze
    menu_y = ty + 2
    menu_line = (
        "==== A-Maze-ing ===="
    )
    safe_addstr(menu_y, 0, menu_line, curses.color_pair(COLOUR_MENU))
    safe_addstr(menu_y + 1, 0, "1. Re-generate a new maze", 0)
    safe_addstr(menu_y + 2, 0, "2. Show/Hide path from entry to exit", 0)
    safe_addstr(menu_y + 3, 0, "3. Rotate maze colors", 0)
    safe_addstr(menu_y + 4, 0, "4. Quit", 0)
    safe_addstr(menu_y + 5, 0, "Choice (1-4): ", curses.color_pair(COLOUR_MENU))

    stdscr.refresh()


def run_visualizer(
    gen: MazeGenerator,
    regenerate_cb: Callable[[], MazeGenerator],
) -> None:
    """
    Launch the curses interactive visualizer.

    Args:
        gen: Initial MazeGenerator with generated maze.
        regenerate_cb: Callable that returns a new MazeGenerator
                       (regenerates maze with new random seed).
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