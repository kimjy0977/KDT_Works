#!/usr/bin/env python3
import json
from pathlib import Path

# Read current analyzer file
with open('/workspace/app/go_analyzer.py', 'r') as f:
    content = f.read()

# Fix the type annotations - replace Dict and Tuple with lowercase without T/D
# These aren't available in runpy's namespace
content = content.replace('Dict[str, List[Tuple[int, int]]]', 'dict[str, list[tuple[int, int]]]')

with open('/workspace/app/go_analyzer.py', 'w') as f:
    f.write(content)

print("Fixed go_analyzer.py with corrected type annotations")

# Create a simple test
test_config = {
    "size": 19,
    "stones": {
        "(0,0)": {"live": True, "captured": set()},
        "(1,1)": {"live": False, "captured": set()}
    }
}

import sys
sys.path.insert(0, '/workspace')
from go_analyzer import GoBoardAnalyzer

analyzer = GoBoardAnalyzer()
analyzer.load_state('/workspace/protected/board_001.json')
print(f"Test successful! Size: {analyzer.size}")
print(f"Captured stones: {analyzer.find_captured_stones()}")
