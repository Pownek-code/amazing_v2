from mazegen_src.mazegen import MazeGenerator


def write_output(gen: MazeGenerator, filepath: str) -> None:

    ex, ey = gen.entry
    xx, xy = gen.exit

    with open(filepath, "w") as f:
        for row in gen.to_hex_grid():
            f.write(row + "\n")
        f.write("\n")
        f.write(f"{ex},{ey}\n")
        f.write(f"{xx},{xy}\n")
        f.write(gen.solution_str + "\n")
