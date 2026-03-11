PYTHON = python3
MAIN   = a_maze_ing.py
CONFIG = config.txt

.PHONY: install run debug lint lint-strict clean

install:
	$(PYTHON) -m pip install flake8 mypy --break-system-packages
	$(PYTHON) -m pip install mazegen-1.0.0-py3-none-any.whl --break-system-packages

run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores \
	       --ignore-missing-imports --disallow-untyped-defs \
	       --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true