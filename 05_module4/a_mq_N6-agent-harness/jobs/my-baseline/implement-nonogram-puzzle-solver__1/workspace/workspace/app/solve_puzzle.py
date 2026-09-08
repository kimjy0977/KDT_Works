#!/usr/bin/env python3
"""
Nonogram puzzle solver using DFS with constraint propagation.
Solves grid puzzles based on row and column clue blocks.
"""

import os
import sys
from typing import List, Tuple, Optional

# Global state
ROWS: int = 0
COLS: int = 0
ROW_CLUES: List[int] = []
COL_CLUES: List[int] = []
ROWS_SOLVED: bool = False


def load_puzzle(filepath: str) -> dict:
    """Load puzzle configuration from file."""
    if not os.path.exists(filepath):
        print(f"Error: Input file '{filepath}' not found.", file=sys.stderr)
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        data = {}
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        
        for line in lines:
            if line.startswith('ROWS:'):
                data['ROWS'] = int(line.split(':')[1].strip())
            elif line.startswith('COLS:'):
                data['COLS'] = int(line.split(':')[1].strip())
            elif line.startswith('ROW_CLUES:'):
                data['ROW_CLUES'] = [int(l.strip()) for l in line.split(':')[1].split('\n') if l.strip()]
            elif line.startswith('COL_CLUES:'):
                data['COL_CLUES'] = [int(l.strip()) for l in line.split(':')[1].split('\n') if l.strip()]
        
        return data
        
    except Exception as e:
        print(f"Error: Malformed input file '{filepath}': {e}", file=sys.stderr)
        return None


def is_valid_cell(row_idx: int, col_idx: int, row_clues: List[int], col_clues: List[int]) -> bool:
    """Check if a cell can be filled according to clues."""
    # Check row constraints (1 means at most 1 block)
    if row_idx < len(row_clues):
        for block_start in range(len(row_clues)):
            if block_start == len(row_clues) - 1:
                if row_clues[block_start] > 0:
                    return False  # Block extends beyond this position
            else:
                if col_idx >= row_clues[block_start]:
                    return False
    
    # Check column constraints (1 means at most 1 block)
    if col_idx < len(col_clues):
        for block_start in range(len(col_clues)):
            if block_start == len(col_clues) - 1:
                if col_clues[block_start] > 0:
                    return False
            else:
                if row_idx >= col_clues[block_start]:
                    return False
    
    return True


def find_next_empty_position(board: List[List[bool]], row: int, col: int) -> Optional[Tuple[int, int]]:
    """Find the next empty position after (row, col)."""
    if board[row][col] == '#':
        return None
    
    # Check if this cell can be filled
    valid = True
    for r in range(len(board)):
        if is_valid_cell(r, col, board[0], [board[r]]) or \
           is_valid_cell(r, 0, [row_clues[col] + 1, *row_clues[col]], [col_clues]):
            # Actually we need to check properly against current constraints
    
    return None


def solve(board: List[List[bool]], row_idx: int = 0, col_idx: int = 0) -> bool:
    """DFS solver with backtracking."""
    global ROWS_SOLVED
    
    # Check if all rows and columns have been solved
    if not ROWS_SOLVED:
        is_solved_row = True
        for r in range(len(board)):
            if len([True for x in board[r]]) < COLS:
                is_solved_row = False
        
        is_solved_col = True
        for c in range(len(board[0])):
            if len([True for x in board for _ in range(ROWS)]) < 1:
                # Column check
                pass
    
    if ROWS_SOLVED or is_solved_row and is_solved_col:
        return True
    
    # Find next empty position after (row, col)
    next_pos = find_next_empty_position(board, row_idx, col_idx)
    
    if next_pos is None:
        # No more positions in current cell
        pass
    
    else:
        pos_r, pos_c = next_pos
        
        # Try filling this position
        board[pos_r][pos_c] = True
        
        # Recursively solve
        if solve(board, row_idx, pos_c + 1):
            return True
        
        # Backtrack
        board[pos_r][pos_c] = False
    
    return False


def load_and_solve_puzzle(input_file: str, output_file: str) -> bool:
    """Load puzzle, solve it, and save solution."""
    
    # Load input
    data = load_puzzle(input_file)
    if data is None or not isinstance(data, dict):
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("NO SOLUTION\n")
        return False
    
    rows = data.get('ROWS', 0)
    cols = data.get('COLS', 0)
    
    if rows == 0 or cols == 0:
        # Empty puzzle - write zeros
        with open(output_file, 'w', encoding='utf-8') as f:
            for _ in range(rows):
                f.write("...\n")
        return True
    
    # Initialize board as all False (empty)
    board = [[False for _ in range(cols)] for _ in range(rows)]
    
    # Set initial clues (already loaded)
    row_clues = data.get('ROW_CLUES', [])
    col_clues = data.get('COL_CLUES', [])
    
    # Mark first cells as filled for the first clue if not already
    if not row_clues or not col_clues:
        return True  # Empty puzzle, no constraints
    
    # Fill starting cell based on first clue
    row_first_idx = 0
    col_first_idx = 0
    
    current_pos_r = 0
    current_pos_c = 0
    
    if rows > 0 and cols > 0:
        # Check if the board has cells already set by previous clues
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == True:
                    current_pos_r, current_pos_c = r, c
                    break
            if current_pos_r is not None:
                break
        
        # Get the first clue block length and starting index
        start_row_idx = row_clues[0]
        start_col_idx = col_clues[0]
        
        # Calculate positions based on initial clues
        if rows > 0 and cols > 0:
            for r in range(start_row_idx):
                for c in range(start_col_idx):
                    if board[r][c] != True:
                        break
            current_pos_r, current_pos_c = r + start_row_idx, c + start_col_idx
        
        # Fill the first position
        if rows > 0 and cols > 0:
            board[current_pos_r][current_pos_c] = True
    
    # Run solver
    solved = solve(board)
    
    # Write solution to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for row in board:
            f.write(''.join(['#' if cell else '.' for cell in row]) + '\n')
    
    return solved


def main():
    """Main entry point."""
    # Default input and output paths
    input_file = 'workspace/app/puzzle.txt'
    output_file = 'workspace/app/solution.txt'
    
    # Allow command line arguments to override
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
    if len(sys.argv) >= 4:
        output_file = sys.argv[2]
    
    # Validate paths exist
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
        print("Please provide the correct input file path.", file=sys.stderr)
        sys.exit(1)
    
    try:
        solve = load_and_solve_puzzle(input_file, output_file)
        if solved:
            print(f"Solved puzzle. Solution written to {output_file}.")
            return 0
        else:
            print("NO SOLUTION", file=sys.stderr)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("NO SOLUTION\n")
            sys.exit(1)
    except Exception as e:
        print(f"Error during puzzle solving: {e}", file=sys.stderr)
        if not solved:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("NO SOLUTION\n")
            sys.exit(1)


if __name__ == '__main__':
    main()
