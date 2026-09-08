def find_empty(board):
    """가장 작은 (row, col) 으로 빈 칸을 찾음"""
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                return (row, col)
    return None


def is_valid(board, row, col, num):
    """
    해당 위치를 num 로 채울 때 유효성 검사
    - 같은 행에 이미 존재하는 숫자와 중복인지 확인
    - 같은 열에 이미 존재하는 숫자와 중복인지 확인
    - 같은 3x3 공(宫中)에 이미 존재하는 숫자와 중복인지 확인
    """
    # 같은 행으로 채울 수 있는 경우 (0 이 아닌 숫자만 고려)
    if board[row][num] != 0:
        return False
    
    # 같은 열에 이미 존재하는 경우
    for col in range(9):
        if board[num][col] != 0 and num == board[row][col]:
            return False
    
    # 같은 3x3 공에서 이미 존재하는 경우
    start_row, start_col = row // 3, col // 3
    for r in range(start_row, start_row + 3):
        for c in range(start_col, start_col + 3):
            if board[r][c] != 0 and board[r][c] == num:
                return False
    
    return True


def solve_sudoku(board):
    """백트래킹 알고리즘으로 수단을 풀음. 유효성이 있는지 확인한다"""
    row, col = find_empty(board)
    
    # 빈 칸이 없으면 수단이 완성되었음을 의미
    if row is None:
        return True
    
    for num in range(1, 10):
        # 유효성을 검사하고 해당 숫자를 채움
        if is_valid(board, row, col, num):
            board[row][col] = num
            if solve_sudoku(board):
                return True
            # 백트래킹: 채운 상태가 되돌려 놓음
            board[row][col] = 0
    
    # 모든 숫자를 시도했을 때仍未 성공 (수단이 없음)
    return False


def write_solution_to_file(content, path):
    """주어진 콘텐츠를 파일로 쓰기"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == "__main__":
    import os
    
    # 입력 경로 설정 (상대경로를 사용)
    puzzle_path = "puzzle.txt"
    solution_path = "solution.txt"
    
    try:
        # 파일 읽기
        with open(puzzle_path, 'r', encoding='utf-8') as f:
            board = []
            for line in f:
                row = [int(x) for x in line.strip().split()]
                board.append(row)
        
        print("입력 수단을 확인:")
        print(board)
        
        # 초기화: 빈 상태로 재정의 (0 을 유지하고, 1-9 는 None 으로 처리)
        for row in range(9):
            new_board = [None] * 9
            for num in board[row]:
                if num != 0:
                    new_board[num] = True
            board[row] = new_board
        
        # 수단을 풀이
        solved = solve_sudoku(board)
        
        if not solved:
            print("오류: 이 수단은 해결할 수 없음")
            exit(1)
        
        print("수단 완성됨:")
        for row in board:
            print(row)
        
        # 결과 파일로 쓰기
        solution_content = []
        for num in board:
            if num is not None:
                solution_content.append(str(num))
            else:
                solution_content.append("")
        
        output = '\n'.join(solution_content) + '\n'
        write_solution_to_file(output, solution_path)
        print(f"\n결과를 solution.txt에 저장했습니다:")
        print(output)
        
    except FileNotFoundError as e:
        print(f"오류: 입력 파일 {puzzle_path}이 찾일 수 없음 - {e}")
    except Exception as e:
        print(f"오류: 실행 중 오류 발생 - {e}")
        raise
