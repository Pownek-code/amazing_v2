import random
from collections import deque
from typing import Optional


NORTH = 0x1
EAST = 0x2
SOUTH = 0x4
WEST = 0x8

ALL_WALLS = NORTH | EAST | SOUTH | WEST

DIRECTIONS = [
    ('N', 0, -1, NORTH, SOUTH),
    ('E', 1, 0, EAST, WEST),
    ('S', 0, 1, SOUTH, NORTH),
    ('W', -1, 0, WEST, EAST),
]

DIGIT_4 = [
    (0, 0), (0, 1), (0, 2),
    (1, 2),
    (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
]
DIGIT_2 = [
    (0, 0), (1, 0), (2, 0),
    (2, 1),
    (0, 2), (1, 2), (2, 2),
    (0, 3),
    (0, 4), (1, 4), (2, 4),
]


class MazeGenerator:
    # """
    # Generates mazes using a recursive backtracker (DFS) algorithm.

    # Attributes:
    #     width (int): Number of columns.
    #     height (int): Number of rows.
    #     seed (Optional[int]): Random seed for reproducibility.
    #     grid (list[list[int]]): 2D grid of wall bitmasks after generation.
    #     entry (tuple[int, int]): Entry cell (x, y).
    #     exit_ (tuple[int, int]): Exit cell (x, y).
    #     solution (list[tuple[int, int]]): Shortest path from entry to exit.
    #     solution_str (str): Path as direction string (N/E/S/W).
    #     forty_two_cells (list[tuple[int, int]]): Cells forming "42" pattern.
    #     forty_two_omitted (bool): True if "42" pattern could not be placed.
    # """
    def __init__(
        self,
        width: int,
        height: int,
        seed: Optional[int] = None
    ) -> None:
        # """
        # Initialize the MazeGenerator.

        # Args:
        #     width: Maze width in cells (must be >= 3).
        #     height: Maze height in cells (must be >= 3).
        #     seed: Optional random seed for reproducibility.
        # """
        self.width = width
        self.height = height
        self.seed = seed
        self.grid: list[list[int]] = []
        self.entry: tuple[int, int] = (0, 0)
        self.exit_: tuple[int, int] = (width - 1, height - 1)
        self.solution: list[tuple[int, int]] = []
        self.solution_str: str = ""
        self.forty_two_cells: list[tuple[int, int]] = []
        self.forty_two_omitted: bool = False
        self.rng = random.Random(seed)

    def generate(
        self,
        perfect: bool = True,
        entry: tuple[int, int] = (0, 0),
        exit: tuple[int, int] | None = None
    ) -> None:
        # """
        # Generate the maze.

        # Args:
        #     perfect: If True, generates a perfect maze (one unique path).
        #     entry: Entry cell coordinates (x, y).
        #     exit_: Exit cell coordinates (x, y). Defaults to bottom-right.
        # """
        if exit is None:
            exit = (self.width - 1, self.height - 1)

        self.entry = entry
        self.exit = exit
        self.rng = random.Random(self.seed)
        self.grid = [[ALL_WALLS] * self.width for _ in range(self.height)]
        self.place_42_pattern()
        self.dfs_generate(perfect)
        self.enforce_borders()
        self.solve()

    def place_42_pattern(self) -> None:
        """Place the '42' pattern as a reserved set of fully walled cells."""
        min_w = 10
        min_h = 7
        if self.width < min_w or self.height < min_h:
            self.forty_two_omitted = True
            self.forty_two_cells = []
            return
        self.forty_two_omitted = False
        pattern_w = 7
        pattern_h = 5
        start_col = (self.width - pattern_w) // 2
        start_row = (self.height - pattern_h) // 2
        cells: list[tuple[int, int]] = []
        for (dc, dr) in DIGIT_4:
            cells.append((start_col + dc, start_row + dr))
        for (dc, dr) in DIGIT_2:
            cells.append((start_col + 4 + dc, start_row + dr))
        self.forty_two_cells = cells

    def _is_42_cell(self, x: int, y: int) -> bool:
        """Check if a cell is part of the '42' pattern."""
        return (x, y) in self.forty_two_cells

    @staticmethod
    def compute_42_cells(width: int, height: int) -> list[tuple[int, int]]:
        # """
        # Compute which cells the '42' pattern occupies for a given maze size.

        # Returns an empty list if the maze is too small to fit the pattern.
        # Call this before generation to validate entry/exit positions.

        # Args:
        #     width: Maze width in cells.
        #     height: Maze height in cells.

        # Returns:
        #     List of (x, y) cell coordinates occupied by the '42' pattern.
        # """
        min_w, min_h = 10, 7
        if width < min_w or height < min_h:
            return []
        pattern_w = 7
        pattern_h = 5
        start_col = (width - pattern_w) // 2
        start_row = (height - pattern_h) // 2
        cells: list[tuple[int, int]] = []
        for (dc, dr) in DIGIT_4:
            cells.append((start_col + dc, start_row + dr))
        for (dc, dr) in DIGIT_2:
            cells.append((start_col + 4 + dc, start_row + dr))
        return cells

    def dfs_generate(self, perfect: bool) -> None:
        """Run DFS to carve passages through the maze."""
        visited = [[False] * self.width for _ in range(self.height)]
        for (cx, cy) in self.forty_two_cells:
            visited[cy][cx] = True
        ex, ey = self.entry
        stack = [(ex, ey)]
        visited[ey][ex] = True
        while stack:
            x, y = stack[-1]
            neighbors = []
            for (_, dx, dy, wall_here, wall_there) in DIRECTIONS:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height
                        and not visited[ny][nx]
                        and not self._is_42_cell(nx, ny)):
                    neighbors.append((nx, ny, wall_here, wall_there))
            if neighbors:
                nx, ny, wh, wt = self._rng.choice(neighbors)
                self.grid[y][x] &= ~wh
                self.grid[ny][nx] &= ~wt
                visited[ny][nx] = True
                stack.append((nx, ny))
            else:
                stack.pop()
        if not perfect:
            extra = (self.width * self.height) // 8
            for _ in range(extra):
                x = self._rng.randint(0, self.width - 2)
                y = self._rng.randint(0, self.height - 2)
                if not self._is_42_cell(x, y) and not self._is_42_cell(x + 1, y):
                    self.grid[y][x] &= ~EAST
                    self.grid[y][x + 1] &= ~WEST
        self._connect_isolated(visited)

    def _connect_isolated(
        self, visited: list[list[bool]]
    ) -> None:
        """Connect any unvisited (isolated) cells to the main maze."""
        for y in range(self.height):
            for x in range(self.width):
                if not visited[y][x] and not self._is_42_cell(x, y):
                    for (_, dx, dy, wh, wt) in DIRECTIONS:
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < self.width and 0 <= ny < self.height
                                and visited[ny][nx]
                                and not self._is_42_cell(nx, ny)):
                            self.grid[y][x] &= ~wh
                            self.grid[ny][nx] &= ~wt
                            visited[y][x] = True
                            break

    def enforce_borders(self) -> None:
        """Ensure all border cells have their outer walls closed."""
        for x in range(self.width):
            self.grid[0][x] |= NORTH
            self.grid[self.height - 1][x] |= SOUTH
        for y in range(self.height):
            self.grid[y][0] |= WEST
            self.grid[y][self.width - 1] |= EAST

    def solve(self) -> None:
        """Find the shortest path from entry to exit using BFS."""
        ex, ey = self.entry
        xx, xy = self.exit_
        from_cell: dict[tuple[int, int], tuple[int, int] | None] = {
            (ex, ey): None
        }
        queue: deque[tuple[int, int]] = deque([(ex, ey)])
        while queue:
            x, y = queue.popleft()
            if (x, y) == (xx, xy):
                break
            for (_, dx, dy, wall_here, _) in DIRECTIONS:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height
                        and (nx, ny) not in from_cell
                        and not (self.grid[y][x] & wall_here)):
                    from_cell[(nx, ny)] = (x, y)
                    queue.append((nx, ny))
        path: list[tuple[int, int]] = []
        cur: tuple[int, int] | None = (xx, xy)
        while cur is not None:
            path.append(cur)
            cur = from_cell.get(cur)
        path.reverse()
        self.solution = path
        dirs = []
        for i in range(len(path) - 1):
            cx, cy = path[i]
            nx2, ny2 = path[i + 1]
            dx = nx2 - cx
            dy = ny2 - cy
            if dy == -1:
                dirs.append('N')
            elif dx == 1:
                dirs.append('E')
            elif dy == 1:
                dirs.append('S')
            else:
                dirs.append('W')
        self.solution_str = ''.join(dirs)

    def to_hex_grid(self) -> list[str]:
        # """
        # Convert grid to list of hex strings (one per row).

        # Returns:
        #     List of strings, each containing WIDTH hex digits.
        # """
        rows = []
        for row in self.grid:
            rows.append(''.join(format(cell, 'X') for cell in row))
        return rows