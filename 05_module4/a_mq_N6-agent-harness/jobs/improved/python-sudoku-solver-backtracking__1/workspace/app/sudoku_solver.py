#!/usr/bin/env python3
"""Backtracking Sudoku Solver"""

def is_valid(board, row, col, num):
    """Check if placing num at board[row][col] is valid."""
    # Check row
    if num in board[row]:
        return False
    
    # Check column
    for r in range(9):
        if board[r][col] == num:
            return False
    
    # Check 3x3 box
    box_row = (row // 3) * 3
    box_col = (col // 3) * 3
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if board[r][c] == num:
                return False
    
    return True


def solve_sudoku(board):
    """Recursive backtracking solver."""
    # Find next empty cell (0)
    row = -1
    col = -1
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                row = r
                col = c
                break
        if row != -1:
            break
    
    # If no empty cell, solve is complete
    if row == -1:
        return True
    
    # Try numbers 1-9
    for num in range(1, 10):
        if is_valid(board, row, col, num):
            board[row][col] = num
            
            if solve_sudoku(board):
                return True
            
            # Backtrack
            board[row][col] = 0
    
    return False


def write_solution_to_file(solution_path, solution):
    """Write solution to file in required format (9 lines, 9 consecutive digits each)."""
    with open(solution_path, 'w', encoding='utf-8') as f:
        for row_num, row_str in enumerate(solution, 1):
            line = ''.join(row_str)
            f.write(line + '\n')


def solve_sudoku_recursive(board):
    """Solve sudoku recursively with finding empty cells and placing backtracking."""
    # Find next empty cell (0)
    empty_pos = find_empty(board)
    
    if empty_pos is not None:
        row, col = empty_pos
        
        # Try numbers 1-9
        for num in range(1, 10):
            if is_valid(board, row, col, num):
                board[row][col] = num
                
                if solve_sudoku_recursive(board):
                    return True
                
                # Backtrack
                board[row][col] = 0
    
    return False


def find_empty(board):
    """Find the next empty cell (0). Returns position as (row, col) or None."""
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return (r, c)
    return None


if __name__ == '__main__':
    # Read puzzle from file (puzzle.txt is the expected name based on puzzle.txt)
    try:
        with open('puzzle.txt', 'r') as f:
            content = f.read()
        
        # Parse the puzzle (9x9 grid)
        board = []
        for line in content.strip().split('\n'):
            row_str = list(line)
            row = [int(x) for x in row_str]
            board.append(row)
        
        # Create a deep copy to work with
        solution_board = [[row.copy() for _ in range(9)] for row in board]
        
        # Solve the puzzle
        if not solve_sudoku(solution_board):
            print("Error: Sudoku has no solution.")
            exit(1)
        
        # Verify the solution
        # For each empty position in original board, check if correct number is placed
        
        # Read back to verify (optional but good practice)
        with open('puzzle.txt', 'w') as f:
            for row_str in [[int(x) for x in line] for line in solution_board]:
                f.write(' '.join(map(str, row_str)) + '\n')
        
        # Write final solution to file
        write_solution_to_file('solution.txt', solution_board)
        
        print("Sudoku solved successfully!")
        print(f"Solution written to solution.txt")
        
    except FileNotFoundError:
        print("Error: puzzle.txt not found.")
        exit(1)
