import random
import sys
from config_parser import ConfigError, parse_config
from mazegen_src.mazegen import MazeGenerator
from output_writer import write_output
from visualizer import run_visualizer


def build_generator(config: dict) -> MazeGenerator:  # type: ignore[type-arg]
    # """
    # Build and run a MazeGenerator from a config dict.

    # Args:
    #     config: Parsed configuration dictionary.

    # Returns:
    #     A fully generated MazeGenerator instance.
    # """
    gen = MazeGenerator(
        width=config['WIDTH'],
        height=config['HEIGHT'],
        seed=config['SEED'],
    )
    gen.generate(
        perfect=config['PERFECT'],
        entry=config['ENTRY'],
        exit_=config['EXIT'],
    )

    if gen.forty_two_omitted:
        print(
            "Warning: maze is too small to include the '42' pattern.",
            file=sys.stderr
        )

    return gen


def main() -> int:
    # """
    # Main entry point.

    # Returns:
    #     Exit code (0 = success, 1 = error).
    # """
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} config.txt", file=sys.stderr)
        return 1
    config_path = sys.argv[1]
    try:
        config = parse_config(config_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    try:
        gen = build_generator(config)
    except Exception as e:
        print(f"Maze generation error: {e}", file=sys.stderr)
        return 1

    try:
        write_output(gen, config['OUTPUT_FILE'])
        print(f"Maze written to {config['OUTPUT_FILE']}")
    except OSError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1
    fixed_seed: int | None = config['SEED']
    startup_seed: int = fixed_seed if fixed_seed is not None         else random.randint(0, 2**31)
    config['SEED'] = startup_seed

    def regenerate() -> MazeGenerator:
        # """Generate a new maze.

        # Fixed seed in config  -> always reproduces the exact same maze.
        # No seed in config     -> picks a new random seed each click.
        # """
        new_config = dict(config)
        if fixed_seed is None:
            new_config['SEED'] = random.randint(0, 2**31)
        new_gen = build_generator(new_config)
        try:
            write_output(new_gen, config['OUTPUT_FILE'])
        except OSError:
            pass
        return new_gen

    run_visualizer(gen, regenerate)
    return 0


if __name__ == '__main__':
    sys.exit(main())