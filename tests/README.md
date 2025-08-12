# DJLibrary Testing Suite

This testing suite provides a way to test djtag operations without touching the filesystem, using the **pytest** framework.

## Overview

The testing suite consists of:

- **MockDJLibrary** (`mock_library.py`): A mock implementation of DJLibrary that can be serialized to/from YAML, used for testing
- **Unit Tests** (`test_library_operations.py`): Comprehensive tests for all library operations using pytest
- **Test Scenarios** (`test_scenarios.py`): Predefined scenarios that demonstrate different merge situations using pytest
- **Test Runner** (`run_pytest_tests.py`): A command-line tool to run all pytest tests
- **Documentation** (`README.md`): This documentation

## Key Features

### 1. **Simple Assertions**
Pytest uses simple, readable assertions:

```python
# Pytest assertions
assert actual == expected
assert item in container
assert value
assert isinstance(obj, type)
assert item not in container
```

### 2. **Fixtures**
Pytest uses fixtures for setup and teardown:

```python
import pytest

class TestMockLibrary:
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Set up test data using pytest fixtures."""
        # Initialize test data here
        pass
```

### 3. **Test Discovery**
Pytest has excellent test discovery:

```python
# Files starting with test_ or ending with _test.py
# Functions starting with test_
# Classes starting with Test
```

## Usage

### Running All Tests

```bash
python tests/run_pytest_tests.py --all
```

### Running Unit Tests Only

```bash
python tests/run_pytest_tests.py --unit
```

### Running Test Scenarios Only

```bash
python tests/run_pytest_tests.py --scenarios
```

### Running Individual Test Files

```bash
# Run unit tests directly
python -m pytest tests/test_library_operations.py -v

# Run scenarios directly
python -m pytest tests/test_scenarios.py -v -s
```

### Running Specific Tests

```bash
# Run a specific test function
python -m pytest tests/test_library_operations.py::TestMockLibrary::test_library_creation -v

# Run tests matching a pattern
python -m pytest tests/ -k "genre" -v
```

## MockDJLibrary Features

### Creating a Mock Library

```python
from tests.mock_library import MockDJLibrary
from track import Track

# Create a library
library = MockDJLibrary("ID3Library", "/music")

# Add tracks
track = Track("/music/song.mp3", {
    'title': ['Song Title'],
    'artist': ['Artist Name'],
    'genre': ['Rock', 'Alternative']
})
library.add_track("/music/song.mp3", track)
```

### YAML Serialization

```python
# Convert to YAML
yaml_str = library.to_yaml()
print(yaml_str)

# Create from YAML
restored_library = MockDJLibrary.from_yaml(yaml_str)

# Save to file
library.save_yaml("library.yaml")

# Load from file
loaded_library = MockDJLibrary.load_yaml("library.yaml")
```

### Merges

```python
# Create two libraries
library1 = MockDJLibrary("ID3Library", "/music")
library2 = MockDJLibrary("SwinsianLibrary", "/music")

# Add different tracks to each
# ... add tracks ...

# Merge library2 into library1
merged_library = library1.merge(library2)

# The merged library contains all tracks from both libraries
# Original libraries remain unchanged
```

### Diff Operations

```python
# Create diff between libraries
from library_diff import DJLibraryDiff
diff = DJLibraryDiff(library1, library2)

# Get diff as string
diff_str = str(diff)
print(diff_str)

# Check if there are differences
if diff:
    print("Libraries have differences")
```

## Test Scenarios

The pytest scenarios demonstrate common use cases:

### Scenario 1: Genre Conflicts
- Shows how genres are handled when they differ between libraries
- Demonstrates adding and changing genres

### Scenario 2: Track Additions/Removals
- Shows how new tracks are added and existing tracks are modified
- Demonstrates the merge behavior with track changes

### Scenario 3: Complex Tag Changes
- Shows complex scenarios with multiple tag types
- Demonstrates year changes, BPM additions, and album removals

## Example Output

When running scenarios, you'll see output like:

```
=== Test Scenario 1: Genre Conflicts ===
ID3 Library:
library_type: ID3Library
music_folder: /music
tracks:
  /music/song1.mp3:
    path: /music/song1.mp3
    tags:
      title: [Song 1]
      artist: [Artist 1]
      genre: [Rock]

Diff (ID3 vs Swinsian):
Library changes (2)
  ♫ Artist 1 - Song 1 // +Alternative
  ♫ Artist 2 - Song 2 // -Pop +Jazz

Merge (ID3 + Swinsian changes):
library_type: ID3Library
music_folder: /music
tracks:
  /music/song1.mp3:
    path: /music/song1.mp3
    tags:
      title: [Song 1]
      artist: [Artist 1]
      genre: [Rock, Alternative]

test_scenario_1_genre_conflicts PASSED
```

## Benefits of Pytest

1. **Simple Syntax**: Clean, readable assertion syntax
2. **Powerful Fixtures**: Flexible setup and teardown mechanisms
3. **Excellent Discovery**: Automatic test discovery and organization
4. **Rich Ecosystem**: Extensive plugin ecosystem
5. **Great Reporting**: Detailed test reports and failure information
6. **Parameterization**: Easy test parameterization
7. **Markers**: Flexible test categorization and filtering

## Integration with Main Code

The pytest testing suite uses the same core classes (`Track`, `DJLibraryDiff`) as the main application, ensuring that tests accurately reflect real behavior. The `MockDJLibrary` provides the same interface as real libraries but operates entirely in memory.

## Installation

To use the testing suite, install pytest:

```bash
pip install pytest
```

## Advanced Pytest Features

### Fixtures with Parameters

```python
@pytest.fixture(params=['ID3Library', 'SwinsianLibrary'])
def library_type(request):
    return request.param

def test_library_creation(library_type):
    library = MockDJLibrary(library_type, "/music")
    assert library.library_type == library_type
```

### Test Markers

```python
@pytest.mark.slow
def test_large_library_merge():
    # This test is marked as slow
    pass

# Run only slow tests
python -m pytest -m slow
```

### Test Parameterization

```python
@pytest.mark.parametrize("genre1,genre2,expected", [
    (['Rock'], ['Rock', 'Alternative'], ['Rock', 'Alternative']),
    (['Pop'], ['Jazz'], ['Jazz']),
])
def test_genre_merge(genre1, genre2, expected):
    # Test different genre merge scenarios
    pass
```

## File Structure

```
tests/
├── README.md                    # This documentation
├── mock_library.py             # Mock implementation of DJLibrary
├── test_library_operations.py  # Unit tests for library operations
├── test_scenarios.py           # Test scenarios demonstrating merge situations
└── run_pytest_tests.py         # Test runner for pytest
```

The testing suite provides comprehensive coverage of all library operations with a clean, modern pytest implementation. 