"""
Tests for transform_csv.py

This test suite validates all core functionality of the CSV transformation tool:
- UUID to sequential integer conversion (with uniqueness preservation)
- Data redaction (names and emails with random fake data)
- Timestamp normalization to YYYY-MM-DD format
- Column reordering
- Full CSV transformation

Requirements:
- pytest

Run with:
    pytest test_transform_csv.py -v

Run with coverage:
    pytest test_transform_csv.py --cov=transform_csv --cov-report=html

Test Structure:
- TestUUIDTransformation: Tests for UUID → integer conversion
- TestRedactionTransformations: Tests for PII redaction (names/emails)
- TestTimestampTransformation: Tests for timestamp → date conversion
- TestApplyTransformation: Tests for the transformation dispatcher
- TestTransformCSVIntegration: End-to-end integration tests
"""

import pytest
import csv
import os
import tempfile
from transform_csv import CSVTransformer


class TestUUIDTransformation:
    """
    Test UUID to sequential integer transformation.

    These tests verify that UUIDs are correctly converted to sequential integers
    while maintaining uniqueness - a requirement for the CSV transformer to replace
    UUID values with simpler integer IDs.

    Key requirements tested:
    - UUIDs are assigned sequential integers starting from 1
    - The same UUID always maps to the same integer (consistency)
    - Different UUIDs get different integers (uniqueness)
    """

    def test_uuid_to_sequential_int_basic(self):
        """
        Test basic UUID to integer conversion.

        Verifies that the first UUID gets ID 1, second gets ID 2, etc.
        This is the fundamental behavior needed for the transformation.
        """
        # Create a fresh transformer instance for clean test environment
        transformer = CSVTransformer()

        uuid1 = "EFEABEA5-981B-4E45-8F13-425C456BF7F6"
        uuid2 = "CDD3AA5D-F8BF-40BB-B220-36147E1B75F7"

        result1 = transformer.uuid_to_sequential_int(uuid1)
        result2 = transformer.uuid_to_sequential_int(uuid2)

        assert result1 == 1, "First UUID should map to 1"
        assert result2 == 2, "Second UUID should map to 2"

    def test_uuid_to_sequential_int_maintains_uniqueness(self):
        """
        Test that same UUID always gets same integer.

        Critical for data integrity: if a UUID appears multiple times in the CSV
        (e.g., as both user_id and manager_id), it must always map to the same
        integer to preserve relationships.
        """
        transformer = CSVTransformer()

        uuid1 = "EFEABEA5-981B-4E45-8F13-425C456BF7F6"

        # Call multiple times with same UUID
        result1 = transformer.uuid_to_sequential_int(uuid1)
        result2 = transformer.uuid_to_sequential_int(uuid1)
        result3 = transformer.uuid_to_sequential_int(uuid1)

        assert result1 == result2 == result3, "Same UUID must always return same integer"

    def test_uuid_to_sequential_int_different_uuids(self):
        """
        Test multiple different UUIDs get different integers.

        Ensures uniqueness: different UUIDs must not collide and must receive
        distinct integer values.
        """
        transformer = CSVTransformer()

        uuids = [
            "EFEABEA5-981B-4E45-8F13-425C456BF7F6",
            "CDD3AA5D-F8BF-40BB-B220-36147E1B75F7",
            "2AB96C22-181C-42DC-8B11-3EDAA281D4F8",
        ]

        results = [transformer.uuid_to_sequential_int(uuid) for uuid in uuids]

        assert results == [1, 2, 3], "UUIDs should get sequential integers"
        assert len(set(results)) == 3, "All integers must be unique"


class TestRedactionTransformations:
    """Test redaction transformations."""

    def test_redact_name_returns_string(self):
        """Test that name redaction returns a string."""
        transformer = CSVTransformer()
        result = transformer.redact_name("John Doe")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_redact_name_different_outputs(self):
        """Test that redaction produces varied output (random)."""
        transformer = CSVTransformer()
        results = [transformer.redact_name("John Doe") for _ in range(10)]
        # Should have at least some variation (not all identical)
        assert len(set(results)) > 1

    def test_redact_email_returns_email_format(self):
        """Test that email redaction returns email format."""
        transformer = CSVTransformer()
        result = transformer.redact_email("test@example.com")
        assert '@' in result
        assert '.' in result.split('@')[1]

    def test_redact_email_different_outputs(self):
        """Test that email redaction produces varied output."""
        transformer = CSVTransformer()
        results = [transformer.redact_email("test@example.com") for _ in range(10)]
        # Should have some variation
        assert len(set(results)) > 1

    def test_redact_auto_detects_email(self):
        """Test that generic redact function detects emails."""
        transformer = CSVTransformer()
        result = transformer.redact("test@example.com")
        assert '@' in result

    def test_redact_auto_detects_name(self):
        """Test that generic redact function detects names."""
        transformer = CSVTransformer()
        result = transformer.redact("John Doe")
        assert isinstance(result, str)
        assert '@' not in result # It's a name, not email


class TestTimestampTransformation:
    """Test timestamp to date transformation."""

    def test_timestamp_to_date_with_month_abbrev(self):
        """Test timestamp conversion with abbreviated month."""
        transformer = CSVTransformer()
        result = transformer.timestamp_to_date("2025-Mar-01")
        assert result == "2025-03-01"

    def test_timestamp_to_date_with_full_timestamp(self):
        """Test timestamp conversion with full timestamp."""
        transformer = CSVTransformer()
        result = transformer.timestamp_to_date("2025-03-23 16:54:43 CET")
        assert result == "2025-03-23"

    def test_timestamp_to_date_already_formatted(self):
        """Test timestamp that's already in correct format."""
        transformer = CSVTransformer()
        result = transformer.timestamp_to_date("2025-03-23")
        assert result == "2025-03-23"

    def test_timestamp_to_date_different_dates(self):
        """Test various date formats."""
        transformer = CSVTransformer()
        test_cases = [
            ("2021-Feb-17", "2021-02-17"),
            ("2020-Jun-19", "2020-06-19"),
            ("2024-Dec-31", "2024-12-31"),
            ("2025-01-15 10:30:00 CET", "2025-01-15"),
        ]

        for input_date, expected in test_cases:
            assert transformer.timestamp_to_date(input_date) == expected


class TestApplyTransformation:
    """Test the apply_transformation dispatcher function."""

    def test_apply_transformation_uuid_to_int(self):
        """Test applying uuid_to_int transformation."""
        transformer = CSVTransformer()
        result = transformer.apply_transformation("EFEABEA5-981B-4E45-8F13-425C456BF7F6", "uuid_to_int")
        assert result == 1

    def test_apply_transformation_redact(self):
        """Test applying redact transformation."""
        transformer = CSVTransformer()
        result = transformer.apply_transformation("John Doe", "redact")
        assert isinstance(result, str)

    def test_apply_transformation_timestamp_to_date(self):
        """Test applying timestamp_to_date transformation."""
        transformer = CSVTransformer()
        result = transformer.apply_transformation("2025-Mar-01", "timestamp_to_date")
        assert result == "2025-03-01"

    def test_apply_transformation_none(self):
        """Test that None transformation returns original value."""
        transformer = CSVTransformer()
        original = "some value"
        result = transformer.apply_transformation(original, None)
        assert result == original

    def test_apply_transformation_unknown_raises_error(self):
        """Test that unknown transformation type raises error."""
        transformer = CSVTransformer()
        with pytest.raises(ValueError, match="Unknown transformation type"):
            transformer.apply_transformation("value", "unknown_transform")


class TestTransformCSVIntegration:
    """Integration tests for the full transform_csv function."""

    def create_test_csv(self, filename, data):
        """Helper to create a test CSV file."""
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    def test_transform_csv_basic(self):
        """Test basic CSV transformation."""
        transformer = CSVTransformer()

        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            input_file = f.name
            writer = csv.DictWriter(f, fieldnames=['id', 'name', 'date'])
            writer.writeheader()
            writer.writerows([
                {'id': 'UUID-123', 'name': 'John Doe', 'date': '2025-Mar-01'},
                {'id': 'UUID-456', 'name': 'Jane Smith', 'date': '2024-Dec-31'},
            ])

        # Create temporary output file
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv').name

        try:
            # Apply transformations
            transformations = {
                'id': 'uuid_to_int',
                'name': 'redact',
                'date': 'timestamp_to_date'
            }

            transformer.transform_csv(input_file, output_file, transformations=transformations)

            # Read and verify output
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert rows[0]['id'] == '1'
            assert rows[1]['id'] == '2'
            assert rows[0]['date'] == '2025-03-01'
            assert rows[1]['date'] == '2024-12-31'

        finally:
            # Cleanup
            os.unlink(input_file)
            os.unlink(output_file)

    def test_transform_csv_no_transformations(self):
        """Test CSV processing with no transformations."""
        transformer = CSVTransformer()

        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            input_file = f.name
            writer = csv.DictWriter(f, fieldnames=['col1', 'col2'])
            writer.writeheader()
            writer.writerows([
                {'col1': 'value1', 'col2': 'value2'},
            ])

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv').name

        try:
            # No transformations
            transformer.transform_csv(input_file, output_file, transformations={})

            # Read and verify output is unchanged
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert rows[0]['col1'] == 'value1'
            assert rows[0]['col2'] == 'value2'

        finally:
            os.unlink(input_file)
            os.unlink(output_file)

    def test_transform_csv_column_reordering(self):
        """Test CSV column reordering."""
        transformer = CSVTransformer()

        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            input_file = f.name
            writer = csv.DictWriter(f, fieldnames=['col1', 'col2', 'col3'])
            writer.writeheader()
            writer.writerows([
                {'col1': 'a', 'col2': 'b', 'col3': 'c'},
            ])

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv').name

        try:
            # Reorder columns
            column_order = ['col3', 'col1', 'col2']
            transformer.transform_csv(input_file, output_file, transformations={}, column_order=column_order)

            # Read and verify column order
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                assert reader.fieldnames == column_order

        finally:
            os.unlink(input_file)
            os.unlink(output_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
