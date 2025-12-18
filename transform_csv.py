"""
This script transforms user_sample.csv according to the requirements:
1. Convert UUIDs to sequential integers (maintaining uniqueness)
2. Redact sensitive data (names and emails)
3. Convert timestamps to YYYY-MM-DD format
"""

import csv
import random
import string
import argparse
import os
from datetime import datetime


# Pool of names and domains for generating redactions for the dataset
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
    "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Christopher",
    "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret",
    "Mark", "Sandra", "Donald", "Ashley", "Steven", "Kimberly", "Paul",
    "Emily", "Andrew", "Donna", "Joshua", "Michelle", "Kenneth", "Dorothy",
    "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa", "Timothy",
    "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts"
]

EMAIL_DOMAINS = [
    "test.com", "example.com", "demo.net", "sample.org", "redacted.io"
]


class CSVTransformer:
    """
    CSV Transformer class that handles all transformation operations.

    Maintains state for UUID mappings to ensure consistency across transformations.
    """

    def __init__(self):
        """Initialize the transformer with empty UUID mapping."""
        self.uuid_to_int_map = {}
        self.next_id = 1

    def uuid_to_sequential_int(self, uuid_string):
        """
        Convert a UUID to a sequential integer.

        Args:
            uuid_string: The UUID to convert

        Returns:
            int: Sequential integer ID
        """
        if uuid_string in self.uuid_to_int_map:
            return self.uuid_to_int_map[uuid_string]

        self.uuid_to_int_map[uuid_string] = self.next_id
        self.next_id += 1
        return self.uuid_to_int_map[uuid_string]

    def redact_name(self, name):
        """
        Redact a person's name by generating a random fake name.

        Args:
            name: The original name

        Returns:
            str: Random fake name (First Last format)
        """
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        return f"{first_name} {last_name}"

    def redact_email(self, email):
        """
        Redact an email address by generating a random fake email.

        Args:
            email: The original email

        Returns:
            str: Random fake email address
        """
        local_length = random.randint(5, 10)
        local_part = ''.join(random.choices(string.ascii_lowercase, k=local_length))
        domain = random.choice(EMAIL_DOMAINS)
        return f"{local_part}@{domain}"

    def timestamp_to_date(self, timestamp_string):
        """
        Convert timestamp to YYYY-MM-DD format.

        Args:
            timestamp_string: The timestamp to convert (e.g., "2025-Mar-01" or "2025-03-23 16:54:43 CET")

        Returns:
            str: Date in YYYY-MM-DD format
        """
        timestamp_string = timestamp_string.replace(" CET", "").strip()

        formats = [
            "%Y-%b-%d",           # 2025-Mar-01
            "%Y-%m-%d %H:%M:%S",  # 2025-03-23 16:54:43
            "%Y-%m-%d",           # 2025-03-23
        ]

        for fmt in formats:
            try:
                date_obj = datetime.strptime(timestamp_string, fmt)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return timestamp_string

    def redact(self, value):
        """
        Redact sensitive data - auto-detects if it's a name or email.

        Args:
            value: The value to redact

        Returns:
            str: Redacted value
        """
        if '@' in str(value):
            return self.redact_email(value)
        else:
            return self.redact_name(value)

    def get_transformations(self):
        """
        Get the transformation registry mapping names to methods.

        Returns:
            dict: Mapping of transformation names to their methods
        """
        return {
            'uuid_to_int': self.uuid_to_sequential_int,
            'redact': self.redact,
            'timestamp_to_date': self.timestamp_to_date,
        }

    def apply_transformation(self, value, transformation_type):
        """
        Apply a transformation to a value based on the transformation type.

        Args:
            value: The value to transform
            transformation_type: Type of transformation (key from transformations dict)

        Returns:
            Transformed value, or original value if no transformation specified
        """
        if transformation_type is None:
            return value

        transformations = self.get_transformations()

        if transformation_type not in transformations:
            raise ValueError(f"Unknown transformation type: '{transformation_type}'. "
                            f"Available: {list(transformations.keys())}")

        transformer_func = transformations[transformation_type]
        return transformer_func(value)

    def transform_csv(self, input_file, output_file, transformations=None, column_order=None):
        """
        Main function to transform the CSV file.

        Args:
            input_file: Path to input CSV
            output_file: Path to output CSV
            transformations: Dictionary mapping column names to transformation types.
                            Format: {'column_name': 'transformation_type'}
                            Supported transformation types:
                              - 'uuid_to_int': Convert UUID to sequential integer
                              - 'redact': Redact sensitive data (auto-detects names vs emails)
                              - 'timestamp_to_date': Convert timestamp to YYYY-MM-DD
                            Columns not in this dict will be kept as-is.
                            If None, no transformations are applied (pass-through mode).
            column_order: List of column names in desired output order.
                         If None, uses the order from input CSV
        """
        if transformations is None:
            transformations = {}

        transformed_rows = []

        with open(input_file, 'r') as infile:
            reader = csv.DictReader(infile)
            input_columns = reader.fieldnames

            for row in reader:
                transformed_row = {}
                for column in input_columns:
                    transformation_type = transformations.get(column)
                    transformed_row[column] = self.apply_transformation(row[column], transformation_type)
                transformed_rows.append(transformed_row)

        output_columns = column_order if column_order else input_columns

        with open(output_file, 'w', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_columns)
            writer.writeheader()
            writer.writerows(transformed_rows)


def interactive_mode(input_file, transformer):
    """
    Interactive mode to configure transformations for each column.

    Args:
        input_file: Path to input CSV
        transformer: CSVTransformer instance to get available transformations from

    Returns:
        Tuple of (transformations dict, column_order list)
    """
    os.system('clear' if os.name == 'posix' else 'cls')
    print("CSV Transformer\n")

    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames)

    print(f"Detected columns: {', '.join(columns)}")

    transformations_list = list(transformer.get_transformations().keys())
    print("\nAvailable transformations:")
    for i, trans in enumerate(transformations_list, 1):
        print(f"  [{i}] {trans}")
    print("  [0] No transformation")

    transformation_config = {}

    for column in columns:
        while True:
            choice = input(f"Transform '{column}' with (0-{len(transformations_list)}): ").strip()

            if not choice.isdigit():
                print("  Please enter a number")
                continue

            choice_num = int(choice)

            if choice_num == 0:
                break
            elif 1 <= choice_num <= len(transformations_list):
                transformation_config[column] = transformations_list[choice_num - 1]
                break
            else:
                print(f"  Please enter a number between 0 and {len(transformations_list)}")

    reorder = input("\nReorder columns? (y/n): ").strip().lower()

    if reorder == 'y':
        print(f"Current order: {', '.join(columns)}")
        order_input = input("Enter desired order (comma-separated): ").strip()
        column_order = [col.strip() for col in order_input.split(',')]
    else:
        column_order = None

    return transformation_config, column_order


def main():
    """
    Main CLI entry point.
    """
    parser = argparse.ArgumentParser(
        description='Transform CSV files with configurable column transformations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python transform_csv.py --input user_sample.csv --output output.csv
        """
    )

    parser.add_argument('-i', '--input', required=True, help='Input CSV file path')
    parser.add_argument('-o', '--output', required=True, help='Output CSV file path')

    args = parser.parse_args()

    transformer = CSVTransformer()
    transformations, column_order = interactive_mode(args.input, transformer)

    transformer.transform_csv(args.input, args.output, transformations=transformations, column_order=column_order)

    print(f"\nOutput saved to: {args.output}")


if __name__ == "__main__":
    main()
