*This project has been created as part of the 42 curriculum by mbenamar, schanqou.*

## Description
This project is a heavily engineered, Python-based graph theory application designed to procedurally generate and solve complex mazes. The system is built on strict Object-Oriented principles, decoupling the configuration parsing layer from the core algorithmic execution. It is capable of generating both "Perfect" (acyclic spanning trees with exactly one unique path between any two nodes) and "Imperfect" (cyclic braid mazes with multiple topological loops) matrices, subsequently calculating the absolute shortest mathematical path from an entry to an exit coordinate.

## Instructions
**Environment Setup:**
The project requires a modern Python Virtual Machine (Python 3.11 or higher is recommended) due to the heavy reliance on advanced type hinting and explicit exception chaining. It operates entirely within user space and requires no elevated system permissions. 

**Execution:**
You must instantiate a virtual environment to ensure process isolation, though the core algorithms rely strictly on the Python standard library. Execute the main entry point script directly through your terminal's Python binary, passing your configuration file as a positional argument. The system will validate the file, allocate the grid on the private heap, execute the graph traversal, and output the final structural matrix to the specified destination file.

## Resources
* **Documentation:** Python 3 standard library documentation, specifically regarding the `collections.deque` and `random` modules for memory-safe queue allocations and pseudo-random state generation.
* **Algorithmic Theory:** "Introduction to Algorithms" (CLRS) and "The Algorithm Design Manual" by Steven S. Skiena provided the foundational mathematics for unweighted shortest-path reconstruction.
* **AI Assistance:** AI tooling was strictly utilized as an architectural mentor to review memory management constraints, debug hash collision detection within the custom configuration parser, and validate the time/space complexities of the chosen graph traversal methodologies.

## Configuration File Architecture
The system accepts a strict `KEY=VALUE` text configuration file. The parser enforces strict fail-fast validation, explicitly rejecting duplicate keys or memory-unsafe dimensions.
* **WIDTH / HEIGHT:** Integers representing the total grid dimensions. Minimum of 3, maximum strictly bounded (e.g., 70x50) to prevent Out-Of-Memory (OOM) heap fragmentation during array allocation.
* **ENTRY / EXIT:** Coordinate tuples formatted as `x,y`. Must fall strictly within the mathematically defined boundaries of the grid and cannot overlap the exact same topological node.
* **PERFECT:** A boolean flag (`True`, `1`, `yes` vs `False`, `0`, `no`). Dictates whether the topological graph mutator should induce cycles (destroy additional walls) after the initial spanning tree is carved.
* **SEED:** An optional integer (or explicitly `None`). Locks the internal state of the Mersenne Twister pseudo-random number generator to guarantee deterministic, reproducible graph mutations.
* **OUTPUT_FILE:** A string representing the absolute or relative path where the final serialized matrix will be written.

## Chosen Maze Algorithm
**Generation:** Iterative Randomized Backtracking Depth-First Search (DFS).  
**Solving:** Breadth-First Search (BFS) with Topological Parent Mapping.

## Reason for Algorithm Selection
**DFS (Generation):** A recursive DFS would immediately shatter the PVM's maximum call stack limit (1000 frames) on large grids. By shifting the architecture to an iterative approach using a LIFO (Last-In-First-Out) list on the heap, the algorithm safely carves an acyclic spanning tree constrained only by available physical RAM. The randomized neighbor selection guarantees complex, unpredictable branching.

**BFS (Solving):** In an unweighted matrix where every edge transition costs exactly 1, BFS is mathematically guaranteed to find the absolute shortest path. By utilizing a FIFO (First-In-First-Out) double-ended queue (`deque`) paired with an $O(1)$ hash map to track visited parent nodes, the solver expands radially and reconstructs the optimal path via backward pointer traversal without falling into cyclic infinite loops.

## Maze Generator Reusable Module
The `MazeGenerator` class is engineered as a strict Builder pattern. The `__init__` method is strictly responsible for memory shape allocation (mapping coordinate and property boundaries), while the `.generate()` and `.solve()` methods handle heavy state mutation. This idempotent design guarantees that a single instantiated module can generate thousands of distinct mazes in a sequential loop without residual memory corruption or state aliasing across the 2D grid pointers.

## Team and Project Management

**Roles:**
* **mbenamar:** Technical writing, configuration I/O parsing, and visualization geometry. Responsible for strictly translating disk state into memory-safe Python objects and handling the architectural fail-fast guard clauses.
* **schanqou:** Core algorithmic architecture. Responsible for the iterative DFS generation engine, the BFS shortest-path solver, and the low-level bitwise operations used to track wall states in heap memory.

**Anticipated Planning vs. Evolution:**
The initial plan assumed a purely sequential workflow: build the parser completely, then build the generator, then build the solver. This quickly evolved into a parallel development model. Because the API boundaries between the parser's output dictionary and the generator's `__init__` method were strictly defined early on, both members could engineer their respective modules simultaneously without blocking each other.

**What Worked Well & What Could Be Improved:**
The strict separation of concerns—isolating I/O logic from mathematical graph theory—was highly successful and prevented monolithic "god functions." However, integration testing could be significantly improved. Discovering edge cases (such as the parser returning the string "None" instead of the `NoneType` singleton) occurred late in the pipeline. Implementing automated Abstract Syntax Tree static analysis or rigorous schema validation earlier would have accelerated the data handoff.

**Specific Tools Used:**
* **Python 3:** Core execution environment.
* **Git:** Version control and parallel branch integration.