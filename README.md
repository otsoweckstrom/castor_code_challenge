# CSV Transformer

**Author:** Otso Weckstrom
**Date:** December 2025

A command-line tool for transforming CSV files with configurable column transformations.

## Requirements

- Python 3.7+
- pytest (for running tests)

## Installation

No installation required. The tool uses only Python standard library for core functionality.

## Usage

Run the tool with input and output file paths:

```bash
python3 transform_csv.py --input user_sample.csv --output my_output.csv
```

The tool will prompt you to configure transformations for each column.

### Interactive Prompts

1. Shows detected columns from input CSV
2. Lists available transformations:
   - `[1] uuid_to_int` - Convert UUIDs to sequential integers
   - `[2] redact` - Replace sensitive data with random fake data
   - `[3] timestamp_to_date` - Convert timestamps to YYYY-MM-DD format
   - `[0]` No transformation (keep as-is)
3. Asks which transformation to apply to each column
4. Optionally reorder output columns

### Example Session

```
=== Transformation Configuration ===

Detected columns: user_id, manager_id, name, email_address, start_date, last_login

Available transformations:
  [1] uuid_to_int
  [2] redact
  [3] timestamp_to_date
  [0] No transformation (keep as-is)

Transform 'user_id' with (0-3): 1
Transform 'manager_id' with (0-3): 1
Transform 'name' with (0-3): 2
Transform 'email_address' with (0-3): 2
Transform 'start_date' with (0-3): 3
Transform 'last_login' with (0-3): 3

Reorder columns? (y/n): n

=== Starting Transformation ===
Transformations: {'user_id': 'uuid_to_int', 'manager_id': 'uuid_to_int', 'name': 'redact', 'email_address': 'redact', 'start_date': 'timestamp_to_date', 'last_login': 'timestamp_to_date'}

Transformation complete! Output saved to: my_output.csv
```

## Transformations

### UUID to Integer (`uuid_to_int`)
Converts UUID strings to sequential integers starting from 1. Maintains uniqueness - the same UUID always maps to the same integer.

**Example:**
```
EFEABEA5-981B-4E45-8F13-425C456BF7F6 → 1
CDD3AA5D-F8BF-40BB-B220-36147E1B75F7 → 2
EFEABEA5-981B-4E45-8F13-425C456BF7F6 → 1 (same UUID, same integer)
```

### Redaction (`redact`)
Replaces sensitive data with random fake data. Auto-detects whether the value is a name or email.

**Names:** Generates random first and last name combinations from predefined pools.
```
John Doe → Patricia Smith
Jane Smith → Michael Rodriguez
```

**Emails:** Generates random lowercase letter strings with random domains.
```
user@example.com → xhjtklm@test.com
admin@company.com → pqwertyx@sample.org
```

### Timestamp to Date (`timestamp_to_date`)
Converts various timestamp formats to YYYY-MM-DD. Handles abbreviated months and timezone information.

**Supported formats:**
- `2025-Mar-01` → `2025-03-01`
- `2025-03-23 16:54:43 CET` → `2025-03-23`
- `2025-03-23` → `2025-03-23` (already formatted)

## Testing

To run tests:
```bash
pip install pytest
```

Run the tests:

```bash
pytest test_transform_csv.py -v
```

The tests includes:
- 3 tests for UUID transformation (uniqueness, consistency)
- 6 tests for redaction (names, emails, auto-detection)
- 4 tests for timestamp transformation (various formats)
- 5 tests for transformation dispatcher
- 3 integration tests (full pipeline, column reordering)

Total: 21 tests

## Architecture

### CSVTransformer Class

The tool uses a class-based architecture with the `CSVTransformer` class that includes all the transformation logic and state:

**Core Methods:**
- `uuid_to_sequential_int(uuid_string)` - UUID to integer mapper
- `redact(value)` - Auto-detecting redaction wrapper
- `redact_name(name)` - Name redaction
- `redact_email(email)` - Email redaction
- `timestamp_to_date(timestamp_string)` - Timestamp parser
- `apply_transformation(value, transformation_type)` - Transformation dispatcher
- `transform_csv(input_file, output_file, transformations, column_order)` - Main transformation pipeline
- `get_transformations()` - Returns available transformations registry

### Design Pattern

The tool uses a registry pattern for transformations. The `get_transformations()` method returns a dictionary mapping transformation names to their methods, making it easy to add new transformation types.

Each `CSVTransformer` instance maintains its own UUID mapping state (`self.uuid_to_int_map`) to ensure consistency within a single transformation while allowing multiple independent transformations to run without interference.

## Scalability

### Current Implementation

The current implementation loads the entire CSV into memory before writing output. This works up to a point but has limitations for larger files.

### Scaling to 1,000,000+ Rows

**1. Streaming Processing**

Replace the current approach with row by row processing:
- Read one row, transform it, write it immediately
- Keeps memory usage constant regardless of file size
- Required change: Modify `transform_csv()` to use streaming `csv.reader/writer` instead of loading all rows into a list

**2. Parallel Processing**

For very large files, split into chunks and process in parallel:
- Divide file into 100K row chunks
- Process each chunk in a separate process using `multiprocessing.Pool`
- Merge results in order
- UUID mapping state needs coordination across processes I would approach this by pre-mapping the UUID's and then dividing them to the parallel processes.

**3. Memory-Mapped Files**

For files that don't fit in RAM:
- Use `mmap` module for input file access
- Let OS handle paging
- Particularly useful if scanning file multiple times

**4. Optimized Data Structures**

Current UUID dictionary is fine for thousands of unique UUIDs, but for millions:
- A persistent key-value store would make sense for the UUID mappings, storing them in SQLite for example
- Allows mappings to survive process restarts and stay out of RAM

**5. Progress Tracking**

For long-running jobs on large files:
- Add progress output every N rows
- Save intermediate state to allow resuming after interruption
- Example: Save UUID mapping and row offset every 10K rows


## File Structure

```
castor-code-challenge-otso-weckstrom/
├── Python Technical Test Brief.pdf    # Original requirements
├── user_sample.csv                     # Input data (100 rows)
├── README.md                           # This file
├── transform_csv.py                    # Main implementation (363 lines)
├── test_transform_csv.py               # Tests (21 tests, all passing)
├── my_output.csv                       # Example output (100 transformed rows)
└── requirements.txt                    # Test dependencies (pytest)
```

## Output Example

Input (user_sample.csv):
```csv
user_id,manager_id,name,email_address,start_date,last_login
EFEABEA5-981B-4E45-8F13-425C456BF7F6,CDD3AA5D-F8BF-40BB-B220-36147E1B75F7,Ashley Hernandez,ashley.hernandez@live.com,2025-Mar-01,2025-03-23 16:54:43 CET
```

Output (my_output.csv):
```csv
user_id,manager_id,name,email_address,start_date,last_login
1,2,Patricia Smith,xhjtklm@test.com,2025-03-01,2025-03-23
```
