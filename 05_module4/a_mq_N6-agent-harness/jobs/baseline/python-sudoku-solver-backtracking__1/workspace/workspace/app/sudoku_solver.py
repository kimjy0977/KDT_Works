def is_valid(board, row, col, num):
    """检查在 board[row][col] 位置放置数字 num 是否有效"""
    # 检查行
    if num in board[row]:
        return False
    # 检查列
    for r in range(9):
        if board[r][col] == num:
            return False
    # 检查 3x3 宫格
    start_row = (row // 3) * 3
    start_col = (col // 3) * 3
    for r in range(start_row, start_row + 3):
        for c in range(start_col, start_col + 3):
            if board[r][c] == num:
                return False
    return True


def find_empty(board):
    """查找下一个空白位置（按照行优先顺序）"""
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                return (row, col)
    return None


def solve_sudoku(board):
    """使用递归回溯算法求解数独，返回 True/False"""
    empty_pos = find_empty(board)
    
    if empty_pos is None:
        return True  # 成功找到所有数字
    
    row, col = empty_pos
    
    for num in range(1, 10):
        if is_valid(board, row, col, num):
            board[row][col] = num
            
            if solve_sudoku(board):
                return True
            
            board[row][col] = 0  # 回溯
            
    return False


def main():
    # 读取 puzzle.txt
    with open('app/puzzle.txt', 'r') as f:
        lines = f.readlines()
    
    # 转置为二维列表（按照行优先顺序）
    board = [list(line.strip()) for line in lines]
    
    # 初始化并求解数独
    if solve_sudoku(board):
        # 写入 solution.txt
        with open('app/solution.txt', 'w') as f:
            for row in board:
                f.write(''.join(str(x) for x in row) + '\n')
    else:
        print("No solution found")
        exit(1)


if __name__ == '__main__':
    main()
