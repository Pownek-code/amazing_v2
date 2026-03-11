from mazegen_src.mazegen import MazeGenerator

def write_output(gen: MazeGenerator, filepath: str) -> None:
    # """
    # Write the maze to a file in the required hex format.

    # Format:
    #     - One hex digit per cell, one row per line.
    #     - Empty line.
    #     - Entry coordinates: x,y
    #     - Exit coordinates: x,y
    #     - Shortest path as direction string (N/E/S/W)

    # Args:
    #     gen: A MazeGenerator instance after generate() has been called.
    #     filepath: Output file path.

    # Raises:
    #     OSError: If the file cannot be written.
    # """
    ex, ey = gen.entry
    xx, xy = gen.exit_

    with open(filepath, 'w') as f:
        for row in gen.to_hex_grid():
            f.write(row + '\n')
        f.write('\n')
        f.write(f"{ex},{ey}\n")
        f.write(f"{xx},{xy}\n")
        f.write(gen.solution_str + '\n')