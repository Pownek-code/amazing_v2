import curses
from typing import Callable
from mazegen_src.mazegen import MazeGenerator, NORTH, EAST, SOUTH, WEST

PAIR_WALL = 1
PAIR_PATH = 2
PAIR_ENTRY = 3
PAIR_EXIT = 4
PAIR_42 = 5
PAIR_MENU = 6
PAIR_EMPTY = 7

WALL_COLORS = [
    curses.COLOR_WHITE,
    curses.COLOR_YELLOW,
    curses.COLOR_GREEN,
]

BLOCK = "█"


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(PAIR_EMPTY, curses.COLOR_BLACK, curses.COLOR_BLACK)
    curses.init_pair(PAIR_WALL, curses.COLOR_WHITE, curses.COLOR_WHITE)
    curses.init_pair(PAIR_PATH, curses.COLOR_CYAN, curses.COLOR_CYAN)
    curses.init_pair(PAIR_ENTRY, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
    curses.init_pair(PAIR_EXIT, curses.COLOR_RED, curses.COLOR_RED)
    curses.init_pair(PAIR_42, curses.COLOR_BLUE, curses.COLOR_BLUE)
    curses.init_pair(PAIR_MENU, curses.COLOR_YELLOW, -1)


def set_wall_color(index: int) -> None:
    new_color = WALL_COLORS[index % len(WALL_COLORS)]
    curses.init_pair(PAIR_WALL, new_color, new_color)


def write_char(win: curses.window,
               row: int, col: int, ch: str, attr: int = 0) -> None:
    max_row, max_col = win.getmaxyx()
    if 0 <= row < max_row and 0 <= col < max_col - 1:
        try:
            win.addstr(row, col, ch, attr)
        except curses.error:
            pass


def is_big_enough(win: curses.window, gen: MazeGenerator) -> bool:
    max_rows, max_cols = win.getmaxyx()
    needed_cols = 3 * gen.width + 1
    needed_rows = 2 * gen.height + 1 + 7

    if max_rows < needed_rows or max_cols < needed_cols:
        win.clear()
        write_char(win, 0, 0, "Terminal too small!",
                   curses.color_pair(PAIR_EXIT))
        write_char(win, 1, 0, f"Need: {needed_cols} cols x {needed_rows} rows")
        write_char(win, 2, 0, f"Got : {max_cols} cols x {max_rows} rows")
        write_char(
            win, 3, 0, "Please resize and try again.",
            curses.color_pair(PAIR_MENU)
        )
        win.refresh()
        return False
    return True


def draw_maze(win: curses.window, gen: MazeGenerator, show_path: bool) -> None:
    if not is_big_enough(win, gen):
        return

    path_cells = set(gen.solution) if show_path else set()
    cells_42 = set(gen.forty_two_cells)

    attr_wall = curses.color_pair(PAIR_WALL)
    attr_path = curses.color_pair(PAIR_PATH)
    attr_entry = curses.color_pair(PAIR_ENTRY)
    attr_exit = curses.color_pair(PAIR_EXIT)
    attr_42 = curses.color_pair(PAIR_42)
    attr_empty = curses.color_pair(PAIR_EMPTY)

    W = gen.width
    H = gen.height
    total_cols = 3 * W + 1
    total_rows = 2 * H + 1

    max_rows, max_cols = win.getmaxyx()
    for r in range(total_rows):
        try:
            win.addstr(r, 0, " " * (max_cols - 1))
        except curses.error:
            pass

    for row in range(total_rows):
        for col in range(total_cols):
            cx = col // 3
            cy = row // 2
            on_wall_row = row % 2 == 0
            on_wall_col = col % 3 == 0

            if on_wall_row and on_wall_col:
                write_char(win, row, col, BLOCK, attr_wall)

            elif on_wall_row and not on_wall_col:
                cell_above = cy - 1
                cell_below = cy
                is_border = row == 0 or row == 2 * H
                wall_closed = is_border

                if not is_border:
                    if (0 <= cell_above < H
                            and (gen.grid[cell_above][cx] & SOUTH)):
                        wall_closed = True
                    elif (0 <= cell_below < H
                            and (gen.grid[cell_below][cx] & NORTH)):
                        wall_closed = True

                if wall_closed:
                    write_char(win, row, col, BLOCK, attr_wall)
                elif (
                    show_path
                    and 0 <= cell_above < H
                    and (cx, cell_above) in path_cells
                    and 0 <= cell_below < H
                    and (cx, cell_below) in path_cells
                ):
                    write_char(win, row, col, BLOCK, attr_path)
                else:
                    write_char(win, row, col, " ", attr_empty)

            elif not on_wall_row and on_wall_col:
                cell_left = cx - 1
                cell_right = cx
                is_border = col == 0 or col == 3 * W
                wall_closed = is_border

                if not is_border:
                    if 0 <= cell_left < W and (gen.grid[cy][cell_left] & EAST):
                        wall_closed = True
                    elif (0 <= cell_right < W
                            and (gen.grid[cy][cell_right] & WEST)):
                        wall_closed = True

                if wall_closed:
                    write_char(win, row, col, BLOCK, attr_wall)
                elif (
                    show_path
                    and 0 <= cell_left < W
                    and (cell_left, cy) in path_cells
                    and 0 <= cell_right < W
                    and (cell_right, cy) in path_cells
                ):
                    write_char(win, row, col, BLOCK, attr_path)
                else:
                    write_char(win, row, col, " ", attr_empty)

            else:
                if cy >= H or cx >= W:
                    continue

                if (cx, cy) in cells_42:
                    write_char(win, row, col, BLOCK, attr_42)
                elif (cx, cy) == gen.entry:
                    write_char(win, row, col, BLOCK, attr_entry)
                elif (cx, cy) == gen.exit:
                    write_char(win, row, col, BLOCK, attr_exit)
                elif show_path and (cx, cy) in path_cells:
                    write_char(win, row, col, BLOCK, attr_path)
                else:
                    write_char(win, row, col, " ", attr_empty)

    menu_row = total_rows + 1
    write_char(win, menu_row, 0,
               "==== A-Maze-ing ====", curses.color_pair(PAIR_MENU))
    write_char(win, menu_row + 1, 0, "1. Generate new maze")
    write_char(win, menu_row + 2, 0, "2. Show / Hide solution path")
    write_char(win, menu_row + 3, 0, "3. Change wall color")
    write_char(win, menu_row + 4, 0, "4. Quit")
    write_char(win, menu_row + 5, 0,
               "Choice (1-4): ", curses.color_pair(PAIR_MENU))
    win.refresh()


def run_visualizer(
    gen: MazeGenerator, regenerate_cb: Callable[[], MazeGenerator]
) -> None:
    def main(win: curses.window) -> None:
        init_colors()
        curses.curs_set(0)
        win.keypad(True)

        current_gen = gen
        show_path = False
        color_index = 0

        draw_maze(win, current_gen, show_path)

        while True:
            try:
                key = win.getch()
            except curses.error:
                continue

            if key == curses.KEY_RESIZE:
                curses.update_lines_cols()
                win.clear()
                win.refresh()
                draw_maze(win, current_gen, show_path)

            elif key == ord("1"):
                max_r, max_c = win.getmaxyx()
                for r in range(2 * current_gen.height + 1):
                    try:
                        win.addstr(r, 0, " " * (max_c - 1))
                    except curses.error:
                        pass
                win.refresh()
                curses.napms(120)
                current_gen = regenerate_cb()
                show_path = False
                draw_maze(win, current_gen, show_path)

            elif key == ord("2"):
                show_path = not show_path
                draw_maze(win, current_gen, show_path)

            elif key == ord("3"):
                color_index = (color_index + 1) % len(WALL_COLORS)
                set_wall_color(color_index)
                draw_maze(win, current_gen, show_path)

            elif key in (ord("4"), ord("q"), ord("Q")):
                break

    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
