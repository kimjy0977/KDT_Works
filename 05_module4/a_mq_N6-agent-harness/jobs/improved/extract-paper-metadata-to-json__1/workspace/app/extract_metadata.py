import json


def read_paper(path):
    """Read a paper file and extract JSON content."""
    with open(path, 'r') as f:
        content = f.read()
    try:
        data = json.loads(content)
        return data.get('path'), data.get('content')
    except:
        return None, None


def validate_json_data(data):
    """Validate that the JSON data contains required fields."""
    required_fields = ['path', 'content']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field '{field}'")
    return True


if __name__ == '__main__':
    path, content = read_paper('protected/papers/paper1.txt')
    validate_json_data(path)
    print(f"Validated paper1.txt - Path: {path}, Content length: {len(content)}")
