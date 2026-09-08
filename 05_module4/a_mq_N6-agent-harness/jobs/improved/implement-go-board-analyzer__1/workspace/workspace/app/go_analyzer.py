"""Go Board Analyzer - Efficient Go (Weiqi) board analysis engine."""


class GoBoardAnalyzer:
    """Class for analyzing Go board states, counting liberties, and detecting captures."""

    def __init__(self, size: int = 19):
        """Initialize the board analyzer with specified board size.

        Args:
            size: Board dimensions (rows, columns). Default is 19x19.
        """
        self.size = size
        # Track all stones on the board as {(row, col): {'live': bool, 'captured': Set[Tuple[int, int]]}}
        self.stones = {}  # Row, Col -> {Live: bool, Captured: Set of (r, c)}
        self.liberties = [[0] * size for _ in range(size)]  # Track liberty counts per position
        self.captured_stones = set()  # All stones that have been captured

    def load_state(self, config_file: str) -> None:
        """Load board state from a JSON configuration file.

        Args:
            config_file: Path to the JSON configuration file.
        """
        import json

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Validate and process board configuration
            if not isinstance(config, dict):
                raise ValueError("Invalid JSON: expected a dictionary")

            self.size = config.get('size', 19)
            rows, cols = self.size, self.size

            # Initialize board state
            for row in range(rows):
                for col in range(cols):
                    self.stones[(row, col)] = {
                        'live': True,
                        'captured': set()
                    }

        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"Failed to load JSON config from {config_file}: {e}")

    def count_liberties(self, row: int, col: int) -> int:
        """Count the number of liberties for a stone at given position.

        A liberty is any empty adjacent cell (up, down, left, right).
        Does not include itself or diagonals.

        Args:
            row: Row coordinate.
            col: Column coordinate.

        Returns:
            Number of liberties for the specified position.
        """
        if 0 <= row < self.size and 0 <= col < self.size:
            return self.liberty_count_stone(row, col)
        return 0

    def liberty_count_stone(self, row: int, col: int) -> int:
        """Count liberties for a single stone (without tracking captured stones).

        Args:
            row: Row coordinate.
            col: Column coordinate.

        Returns:
            Number of liberties for the specified position.
        """
        count = 0
        direction = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # 4 cardinal directions

        for dr, dc in direction:
            r, c = row + dr, col + dc
            if 0 <= r < self.size and 0 <= c < self.size:
                if (r, c) not in self.stones or not self.stones[(r, c)]['live']:
                    count += 1

        return count

    def find_captured_stones(self) -> Dict[str, List[Tuple[int, int]]]:
        """Find all captured stones on the board.

        Returns:
            Dictionary mapping coordinate tuples to lists of captured stone coordinates.
            Format: { "(r,c)": [(r2,c2), ...] }
        """
        result = {}
        for (r, c), info in self.stones.items():
            if not info['live'] and c > 0 and (r, c - 1) not in self.captured_stones:
                captured = sorted(
                    tuple(info['captured']) + ((r, c - 1),),
                    key=lambda x: x[0] * self.size + x[1]
                )
                result[f"({r},{c})"] = list(captured)

        return result

    def _get_live_stones(self) -> set:
        """Get coordinates of all live stones."""
        return {
            (r, c) for r in range(self.size) for c in range(self.size)
            if self.stones[(r, c)]['live'] and (r, c) not in self.captured_stones
        }


if __name__ == "__main__":
    # Basic testing
    import sys

    if len(sys.argv) > 1:
        analyzer = GoBoardAnalyzer()
        try:
            analyzer.load_state("test_board.json")
        except Exception as e:
            print(f"Test error: {e}")
    else:
        print("Usage: python go_analyzer.py <config_file>")
