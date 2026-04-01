import os
from typing import Any
from mazegen_src.mazegen import MazeGenerator

REQUIRED_KEYS = {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"}


class ConfigError(Exception):
    """Raises a configuration is invalid."""

    pass


def parse_config(filepath: str) -> dict[str, Any]:
    """
    This function takes a path to the config file as an argument.
    parses its elements into a Key Value and returns a dict.
    raises an error either in validation/parsing, or file not existing.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Config file not found: {filepath}")
    raw: dict[str, str] = {}
    try:
        with open(filepath, "r") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    raise ConfigError(
                        f"Line {lineno}: invalid format (expected KEY=VALUE): {line!r}"
                    )
                key, _, value = line.partition("=")
                parsed_key = key.strip().upper()
                if parsed_key in raw:
                    raise ConfigError(
                        f"Line {lineno}: Duplicate key detected for {parsed_key!r}. "
                        "Configuration files must not contain overlapping states."
                    )

                raw[parsed_key] = value.strip()
    except OSError as e:
        raise ConfigError(f"Cannot read config file: {e}") from e

    missing = REQUIRED_KEYS - raw.keys()
    if missing:
        raise ConfigError(
            f"Missing required keys: {', '.join(sorted(missing))}"
        )

    config: dict[str, Any] = {}
    # add a line for ommited 42
    # name file config a_maze_ing.py fix
    try:
        config["WIDTH"] = int(raw["WIDTH"])
        config["HEIGHT"] = int(raw["HEIGHT"])
    except ValueError as e:
        raise ConfigError(f"WIDTH and HEIGHT must be integers: {e}") from e

    if config["WIDTH"] < 3 or config["HEIGHT"] < 3:
        raise ConfigError("WIDTH and HEIGHT must be at least 3.")

    MAX_WIDTH: int = 77
    MAX_HEIGHT: int = 25
    if config["WIDTH"] > MAX_WIDTH or config["HEIGHT"] > MAX_HEIGHT:
        raise ConfigError(
            f"Grid dimensions ({config['WIDTH']}x{config['HEIGHT']}) exceed "
            f"the maximum safety limits of {MAX_WIDTH}x{MAX_HEIGHT}."
        )

    def parse_coord(val: str, key: str) -> tuple[int, int]:
        """
        this function parses an (x, y) coordinate string.
        """
        parts = val.split(",")
        if len(parts) != 2:
            raise ConfigError(f"{key} must be in format x,y (got {val!r})")
        try:
            return int(parts[0].strip()), int(parts[1].strip())
        except ValueError as exc:
            raise ConfigError(f"{key} coordinates must be integers") from exc

    config["ENTRY"] = parse_coord(raw["ENTRY"], "ENTRY")
    config["EXIT"] = parse_coord(raw["EXIT"], "EXIT")

    ex, ey = config["ENTRY"]
    xx, xy = config["EXIT"]

    if not (0 <= ex < config["WIDTH"] and 0 <= ey < config["HEIGHT"]):
        raise ConfigError(
            f"ENTRY {config['ENTRY']} is outside maze bounds "
            f"({config['WIDTH']}x{config['HEIGHT']})"
        )
    if not (0 <= xx < config["WIDTH"] and 0 <= xy < config["HEIGHT"]):
        raise ConfigError(
            f"EXIT {config['EXIT']} is outside maze bounds "
            f"({config['WIDTH']}x{config['HEIGHT']})"
        )
    if config["ENTRY"] == config["EXIT"]:
        raise ConfigError("ENTRY and EXIT must be different cells.")
    forty_two = MazeGenerator.compute_42_cells(
        config["WIDTH"], config["HEIGHT"]
    )
    if forty_two:
        forty_two_set = set(forty_two)
        if config["ENTRY"] in forty_two_set:
            raise ConfigError(
                f"ENTRY {config['ENTRY']} overlaps the '42' pattern. "
                f"Choose a different entry cell."
            )
        if config["EXIT"] in forty_two_set:
            raise ConfigError(
                f"EXIT {config['EXIT']} overlaps the '42' pattern. "
                f"Choose a different exit cell."
            )

    perfect_str = raw["PERFECT"].strip().lower()
    if perfect_str in ("true", "1", "yes"):
        config["PERFECT"] = True
    elif perfect_str in ("false", "0", "no"):
        config["PERFECT"] = False
    else:
        raise ConfigError(
            f"PERFECT must be True or False (got {raw['PERFECT']!r})"
        )

    config["OUTPUT_FILE"] = raw["OUTPUT_FILE"]
    config["SEED"] = None
    if "SEED" in raw:
        if raw["SEED"].strip().upper() == "NONE":
            pass
        else:
            try:
                config["SEED"] = int(raw["SEED"])
            except ValueError as e:
                raise ConfigError(f"SEED must be an integer or None: {e}") from e
    return config
