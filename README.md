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
   - `[0]` No transformation
3. Asks which transformation to apply to each column
4. Optionally reorder output columns

### Example Session

```
CSV Transformer

Detected columns: user_id, manager_id, name, email_address, start_date, last_login

Available transformations:
  [1] uuid_to_int
  [2] redact
  [3] timestamp_to_date
  [0] No transformation

Transform 'user_id' with (0-3): 1
Transform 'manager_id' with (0-3): 1
Transform 'name' with (0-3): 2
Transform 'email_address' with (0-3): 2
Transform 'start_date' with (0-3): 3
Transform 'last_login' with (0-3): 3

Reorder columns? (y/n): n

Output saved to: my_output.csv
```

## Transformations

### UUID to Integer (`uuid_to_int`)
Converts UUID strings to sequential integers starting from 1. Maintains uniqueness - the same UUID always maps to the same integer.

**Example:**
```
EFEABEA5-981B-4E45-8F13-425C456BF7F6 → 1
CDD3AA5D-F8BF-40BB-B220-36147E1B75F7 → 2
EFEABEA5-981B-4E45-8F13-425C456BF7F6 → 1 /same UUID, same integer
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
Currently only works for CET time, future development would be to add other timezones as well.

**Supported formats:**
- `2025-Mar-01` → `2025-03-01`
- `2025-03-23 16:54:43 CET` → `2025-03-23`
- `2025-03-23` → `2025-03-23`

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
- 3 tests for UUID transformation 
- 6 tests for redaction 
- 4 tests for timestamp transformation 
- 5 tests for transformation dispatcher
- 3 integration tests 

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

The current implementation loads the entire CSV into memory before writing output. This works fine for the 100-row sample file, but runs out of RAM for files with 1,000,000+ rows.

### Scaling Approaches

**Streaming (Simple Fix)**

Process rows one at a time instead of loading everything into memory:
- Read row, transform it, write it immediately
- Memory usage stays constant regardless of file size
- Change needed: Instead of building a list of all transformed rows, write each row as we process it

**Parallel Processing**

If we need to process very large files faster, we can split the work across multiple processes:
- Pre-map all UUIDs first by scanning the file once
- Divide file into chunks
- Process chunks in parallel
- Each process gets the pre-mapped UUID dictionary so the same UUID always gets the same integer across all chunks
- Merge results back together in order

The UUID pre-mapping is critical without it, different chunks would assign different integers to the same UUID.


## File Structure

```
castor-code-challenge-otso-weckstrom/
├── Python Technical Test Brief.pdf    # Original requirements
├── user_sample.csv                     # Input data 
├── README.md                           # This file
├── transform_csv.py                    # Main implementation 
├── test_transform_csv.py               # Tests 
├── my_output.csv                       # Example output 
└── requirements.txt                    # Test dependencies 
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
