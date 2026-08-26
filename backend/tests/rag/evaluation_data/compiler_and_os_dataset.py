"""
Comprehensive Evaluation Dataset for Member 2 RAG Engine Production Testing.
Contains realistic academic text spanning Compiler Construction and Operating Systems.
"""

COMPILER_TEXTBOOK = """
CHAPTER 1: INTRODUCTION TO COMPILERS
A compiler is a language translator that converts high-level source code into low-level target machine code.
The primary phases of a compiler include Lexical Analysis, Syntax Analysis, Semantic Analysis, Intermediate Code Generation, Code Optimization, and Code Generation.

CHAPTER 2: LEXICAL ANALYSIS
Lexical analysis, also known as scanning, converts a stream of source characters into a stream of meaningful tokens.
Tokens represent keywords, identifiers, operators, and literals using regular expressions and finite automata (DFA/NFA).

CHAPTER 3: SYNTAX ANALYSIS
Syntax analysis or parsing verifies that the token stream conforms to context-free grammar rules using pushdown automata.
Top-down parsers (LL) and bottom-up parsers (LR, LALR) generate an Abstract Syntax Tree (AST).

CHAPTER 4: SEMANTIC ANALYSIS
Semantic analysis checks type consistency, variable scope declarations, function signatures, and symbol table bindings.
Type checking ensures that operators match compatible data types (e.g., preventing string to integer addition without conversion).

CHAPTER 5: CODE OPTIMIZATION
Code optimization transforms intermediate code into more efficient execution form to minimize CPU cycles and memory bandwidth.
Common optimizations include dead code elimination, loop unrolling, constant folding, and common subexpression elimination.

CHAPTER 6: CODE GENERATION
Code generation maps intermediate representations onto physical target machine instructions and register allocations.
Instruction selection chooses efficient machine opcodes while register allocation manages hardware registers using graph coloring.
"""

OPERATING_SYSTEMS_TEXTBOOK = """
CHAPTER 1: OPERATING SYSTEM STRUCTURES
An operating system acts as an intermediary between user applications and system hardware resources.
Key system services include process management, memory management, file system storage, I/O device management, and security enforcement.

CHAPTER 2: PROCESS MANAGEMENT AND CPU SCHEDULING
A process is a program in execution containing program counter, stack, data, and heap segments.
CPU scheduling algorithms include First-Come First-Served (FCFS), Shortest Job First (SJF), Priority Scheduling, and Round-Robin (RR).

CHAPTER 3: PROCESS SYNCHRONIZATION AND DEADLOCKS
Process synchronization prevents race conditions using semaphores, mutex locks, and monitors.
Deadlock occurs when processes are blocked waiting for held resources. The Coffman conditions for deadlock are mutual exclusion, hold and wait, no preemption, and circular wait.

CHAPTER 4: MEMORY MANAGEMENT AND VIRTUAL MEMORY
Virtual memory separates logical memory from physical RAM using paging and segmentation.
Page replacement algorithms include Least Recently Used (LRU), First-In First-Out (FIFO), and Optimal (OPT).
"""
