"""Tests of the database_managemenr module"""
from datetime import datetime, date, timezone
import pandas as pd
import pyarrow as pa
import os
import pytest
from choc_an_simulator.schemas import TableInfo
from choc_an_simulator.database_management import (
    add_records_to_file,
    load_records_from_file,
    update_record,
    remove_record,
    save_report,
    _load_all_records_from_file_,
    _overwrite_records_to_file_,
    _PARQUET_DIR_,
    _convert_parquet_name_to_path_,
)

TEST_NAME = "test"
TEST_RECORDS = pd.DataFrame({"ID": [1, 2], "value": [1.1, 2.2]})
MISMATCHED_TEST_RECORDS = pd.DataFrame({"mismatched": [1, 2], "records": [1.1, 2.2]})
TEST_TABLE_INFO = TableInfo(
    name="test",
    schema=pa.schema([("ID", pa.int64()), ("value", pa.float64())]),
    numeric_limits={"value": range(0, 3)},
)
MISMATCHED_TEST_TABLE_INFO = TableInfo(
    name="test",
    schema=pa.schema([("mismatched", pa.int64()), ("records", pa.float64())]),
)


@pytest.fixture()
def test_file():
    """Fixture to setup and teardown an test file"""
    _overwrite_records_to_file_(TEST_RECORDS, TEST_TABLE_INFO)
    yield TEST_NAME
    test_path = os.path.join(_PARQUET_DIR_, f"{TEST_NAME}.pkt")
    if os.path.exists(test_path):
        os.remove(test_path)


@pytest.fixture()
def corrupted_test_file():
    """Fixture to setup and teardown an test file"""
    test_name = f"{TEST_NAME}"
    test_path = os.path.join(_PARQUET_DIR_, f"{test_name}.pkt")
    _overwrite_records_to_file_(TEST_RECORDS, TEST_TABLE_INFO)
    with open(test_path, "w") as f:
        f.write("some extra garbage")
    yield test_name
    if os.path.exists(test_path):
        os.remove(test_path)


class TestAddRecordsToFile:
    """Tests for the add_records_to_file function."""

    new_records = pd.DataFrame({"ID": [3, 4], "value": [1.1, 2.2]})
    mismatched_records = pd.DataFrame({"mismatched": [3, 4], "test": [1.1, 2.2]})
    mismatched_records_correct_index = pd.DataFrame({"ID": [3, 4], "test": [1.1, 2.2]})
    wrong_type_records = pd.DataFrame({"ID": [3, 4], "value": ["1.1", "2.2"]})
    out_of_range_records = pd.DataFrame({"ID": [3, 4], "value": [5.0, -1.0]})

    def test_add_records_to_file_normal_conditions(self, test_file):
        """Test normal add to file."""
        add_records_to_file(self.new_records, TEST_TABLE_INFO)
        updated_records = load_records_from_file(TEST_TABLE_INFO)
        expected_records = pd.concat([TEST_RECORDS, self.new_records]).reset_index(
            drop=True
        )
        assert updated_records.equals(
            expected_records
        ), f"\n{expected_records}\n{updated_records}"

    @pytest.mark.parametrize(
        "records,info,error_type",
        [
            # Duplicate Entries.
            (TEST_RECORDS, TEST_TABLE_INFO, ValueError),
            # Records with mismatched columns, but correct index.
            (mismatched_records_correct_index, TEST_TABLE_INFO, KeyError),
            # Records with all mismatched columns.
            (mismatched_records, TEST_TABLE_INFO, KeyError),
            # Records with incorrect type defined by schema in TableInfo
            (wrong_type_records, TEST_TABLE_INFO, TypeError),
            # Records with values out of range defined by TableInfo
            (out_of_range_records, TEST_TABLE_INFO, ArithmeticError),
        ],
    )
    def test_add_invalid_records_to_file(self, records, info, error_type, test_file):
        """Test add duplicate entries."""
        with pytest.raises(error_type):
            add_records_to_file(records, info)

    def test_add_records_to_corrupted_file(self, corrupted_test_file):
        """Test adding records to an un-openable parquet file"""
        with pytest.raises(pa.ArrowInvalid):
            add_records_to_file(self.new_records, TEST_TABLE_INFO)

    def test_add_records_to_file_read_error(self, test_file, mocker):
        """Test adding records to an unreadable file."""
        mocker.patch("pyarrow.parquet.read_table", side_effect=pa.ArrowIOError)
        with pytest.raises(pa.ArrowIOError):
            add_records_to_file(self.new_records, TEST_TABLE_INFO)

    def test_add_records_to_file_write_error(self, test_file, mocker):
        """Test adding records to an unwriteable file."""
        mocker.patch("pyarrow.parquet.write_table", side_effect=pa.ArrowIOError)
        with pytest.raises(pa.ArrowIOError):
            add_records_to_file(self.new_records, TEST_TABLE_INFO)


class TestLoadRecordsFromFile:
    """Tests of the load_records_from_file function."""

    def test_load_records_from_file_all_records(self, test_file):
        """Test loading with no filters"""
        all_records = load_records_from_file(TEST_TABLE_INFO)
        assert TEST_RECORDS.equals(all_records)

    def test_load_records_from_file_corrupted_file(self, corrupted_test_file):
        """Test loading a corrupted file"""
        with pytest.raises(pa.ArrowInvalid):
            load_records_from_file(TEST_TABLE_INFO)

    def test_load_records_from_file_io_error(self, test_file, mocker):
        """Test loading an inacessible file"""
        mocker.patch("pyarrow.parquet.read_table", side_effect=pa.ArrowIOError)
        with pytest.raises(pa.ArrowIOError):
            load_records_from_file(TEST_TABLE_INFO)

    def test_load_records_from_file_valid_filters(self, test_file):
        """Test loading with valid filters"""
        # Test 1: Equality filter
        eq_records = load_records_from_file(TEST_TABLE_INFO, eq_cols={"ID": 1})
        assert TEST_RECORDS[TEST_RECORDS["ID"] == 1].equals(eq_records)
        # Test 2: Less-than filter
        lt_records = load_records_from_file(TEST_TABLE_INFO, lt_cols={"value": 2.0})
        assert TEST_RECORDS[TEST_RECORDS["value"] < 2.0].equals(lt_records)
        # Test 3: Greater-than filter
        lt_records = load_records_from_file(TEST_TABLE_INFO, gt_cols={"value": 2.0})
        assert TEST_RECORDS[TEST_RECORDS["value"] > 2.0].equals(lt_records)

    def test_load_records_from_file_invalid_equality(self, test_file):
        """Test loading records with an unsupported equality filter"""

        class NoEq:
            """Example of a class that doesn't support equality"""

            def __eq__(self, other):
                raise TypeError(
                    "Equality between no_eq and {type(other)} not supported"
                )

        with pytest.raises(TypeError):
            load_records_from_file(TEST_TABLE_INFO, eq_cols={"ID": NoEq()})

    @pytest.mark.parametrize(
        "kwargs,error_type",
        [
            # Less-than filter with invalid type
            ({"lt_cols": {"value": "a"}}, TypeError),
            # Greater-than filter with invalid type
            ({"gt_cols": {"value": "a"}}, TypeError),
            # Equality filter with invalid column name
            ({"eq_cols": {"invalid": 1}}, KeyError),
            # Less-than filter with invalid column name
            ({"lt_cols": {"invalid": 1}}, KeyError),
            # Greater-than filter with invalid column name.
            ({"gt_cols": {"invalid": 1}}, KeyError),
        ],
    )
    def test_load_records_from_file_invalid_filters(
        self, kwargs, error_type, test_file
    ):
        """Test loading with invalid filters"""
        with pytest.raises(error_type):
            load_records_from_file(TEST_TABLE_INFO, **kwargs)

    def test_load_records_from_file_missing_file(self):
        """Test loading from a file that doesn't exist."""
        empty_records = load_records_from_file(TEST_TABLE_INFO)
        assert empty_records.empty

    def test_load_records_from_file_mismatched_schema(self, test_file):
        """Test loading from a file that was written with a different schema."""
        with pytest.raises(KeyError):
            load_records_from_file(MISMATCHED_TEST_TABLE_INFO)


class TestUpdateRecord:
    """Tests of the update_record function."""

    def test_update_record_normal_update(self, test_file):
        """Test normal record update."""
        updated_record = update_record(2, TEST_TABLE_INFO, value=2.3)
        loaded_record = load_records_from_file(TEST_TABLE_INFO, eq_cols={"ID": 2}).iloc[
            0
        ]
        assert (updated_record == loaded_record).all()

    @pytest.mark.parametrize(
        "index,kwargs,error_type",
        [
            # No keyword arguments
            (2, {}, AssertionError),
            # Invalid index
            (3, {"value": 3.3}, IndexError),
            # Invalid column name
            (2, {"bad_column_name": "hello"}, KeyError),
            # Invalid type
            (2, {"value": "hello"}, TypeError),
            # Out of range
            (2, {"value": 5.0}, ArithmeticError),
        ],
    )
    def test_update_record_invalid(self, index, kwargs, error_type, test_file):
        """Perform parametrized tests of various invalid keyword arguments"""
        with pytest.raises(error_type):
            update_record(index, TEST_TABLE_INFO, **kwargs)

    def test_update_record_mismatched_schema(self, test_file):
        """Test updating with mismatched file / schema"""
        with pytest.raises(KeyError):
            update_record(2, MISMATCHED_TEST_TABLE_INFO, value=2.2)

    def test_update_record_corrupted_file(self, corrupted_test_file):
        """Test add record with mismatched file / schema"""
        with pytest.raises(pa.ArrowInvalid):
            update_record(2, TEST_TABLE_INFO, value=2.2)

    def test_update_record_read_error(self, test_file, mocker):
        """Test updating an unreadable file"""
        mocker.patch("pyarrow.parquet.read_table", side_effect=pa.ArrowIOError)
        with pytest.raises(pa.ArrowIOError):
            update_record(2, TEST_TABLE_INFO, value=2.2)

    def test_update_record_write_error(self, test_file, mocker):
        """Test updating an unwriteable file"""
        mocker.patch("pyarrow.parquet.write_table", side_effect=pa.ArrowIOError)
        with pytest.raises(pa.ArrowIOError):
            update_record(2, TEST_TABLE_INFO, value=2.2)


class TestRemoveRecord:
    """Tests of the remove_record function"""

    def test_remove_record_normal_removal(self, test_file):
        """Test normal removal"""
        records_before = load_records_from_file(TEST_TABLE_INFO)
        assert 1 in records_before["ID"]
        removed = remove_record(1, TEST_TABLE_INFO)
        assert removed
        records_after = load_records_from_file(TEST_TABLE_INFO)
        assert len(records_after) == len(records_before) - 1
        assert 1 not in records_after["ID"]

    def test_remove_record_missing_index(self, test_file):
        """Test removal at a non-existant index"""
        records_before = load_records_from_file(TEST_TABLE_INFO)
        removed = remove_record(3, TEST_TABLE_INFO)
        records_after = load_records_from_file(TEST_TABLE_INFO)
        assert removed is False
        assert records_before.equals(records_after)

    def test_remove_record_corrupted_file(self, corrupted_test_file):
        """Test removing from a corrupted file"""
        with pytest.raises(pa.ArrowInvalid):
            remove_record(2, TEST_TABLE_INFO)

    def test_remove_record_read_error(self, test_file, mocker):
        """Test removing from an unreadable file"""
        mocker.patch("pyarrow.parquet.read_table", side_effect=pa.ArrowIOError)
        with pytest.raises(pa.ArrowIOError):
            remove_record(2, TEST_TABLE_INFO)

    def test_remove_record_write_error(self, test_file, mocker):
        """Test removing from an unwriteable file"""
        mocker.patch("pyarrow.parquet.write_table", side_effect=pa.ArrowIOError)
        with pytest.raises(pa.ArrowIOError):
            remove_record(1, TEST_TABLE_INFO)

    def test_remove_record_mismatched_schema(self, test_file):
        """Test removing from a file with a mismatched schema"""
        with pytest.raises(KeyError):
            remove_record(1, MISMATCHED_TEST_TABLE_INFO)


class TestOverwriteRecordsToFile:
    """Tests of the _overwrite_records_to_file_ function"""

    new_records = pd.DataFrame({"ID": [3, 4], "value": [2.0, 1.0]})

    def test_overwrite_records_to_file_normal_overwrite(self, test_file):
        """Tests of the overwrite_records_to_file_ function"""
        _overwrite_records_to_file_(self.new_records, TEST_TABLE_INFO)
        updated_records = _load_all_records_from_file_(TEST_TABLE_INFO)
        assert updated_records.equals(self.new_records), (
            "\n" + str(self.new_records) + "\n" + str(updated_records)
        )

    def test_overwrite_records_to_file_mismatched_schema(self, test_file):
        """Test overwrite record with a mismatched schema"""
        mismatched_records = pd.DataFrame({"mismatched": [3, 4], "test": [1.1, 2.2]})

        with pytest.raises(KeyError):
            _overwrite_records_to_file_(mismatched_records, TEST_TABLE_INFO)

    def test_overwrite_records_to_file_out_of_range(self, test_file):
        """Test overwrite records with out-of-range values"""
        out_of_range_records = pd.DataFrame({"ID": [3, 4], "value": [-1, 4.0]})
        with pytest.raises(ArithmeticError):
            _overwrite_records_to_file_(out_of_range_records, TEST_TABLE_INFO)

    def test_overwrite_records_to_file_wrong_type(self, test_file):
        """Test overwrite records with out-of-range values"""
        wrong_type_records = pd.DataFrame({"ID": [3, 4], "value": ["1.1", "2.2"]})
        with pytest.raises(TypeError):
            _overwrite_records_to_file_(wrong_type_records, TEST_TABLE_INFO)

    def test_overwrite_records_to_file_io_error(self, test_file, mocker):
        """Test overwrite records with an I/O error"""
        mocker.patch("pyarrow.parquet.write_table", side_effect=pa.ArrowIOError)
        with pytest.raises(pa.ArrowIOError):
            _overwrite_records_to_file_(self.new_records, TEST_TABLE_INFO)


class TestSaveReport:
    """Tests of the save_report function"""

    # Local timezone calculated using a different method than save_report
    local_timezone = datetime.now().astimezone().tzinfo

    report_input: pd.DataFrame = pd.DataFrame(
        {
            "ID": [1, 2],
            "date": [date(2021, 1, 1), date(2022, 1, 1)],
            "dttm": [
                datetime(2021, 1, 1, tzinfo=timezone.utc),
                datetime(2022, 1, 1, tzinfo=timezone.utc),
            ],
            "bool": [True, False],
            "nullable": [1, None],
        }
    )
    expected_output: pd.DataFrame = pd.DataFrame(
        {
            "ID": [1, 2],
            "date": ["01-01-2021", "01-01-2022"],
            "dttm": [
                datetime(2021, 1, 1, tzinfo=timezone.utc)
                .astimezone(local_timezone)
                .strftime("%m-%d-%Y %H:%M"),
                datetime(2022, 1, 1, tzinfo=timezone.utc)
                .astimezone(local_timezone)
                .strftime("%m-%d-%Y %H:%M"),
            ],
            "bool": [True, False],
            "nullable": [1, None],
        }
    )

    def test_save_report_normal_save(self):
        """Test saving a report under normal conditions"""

        path = save_report(self.report_input, "test")
        reloaded_from_file = pd.read_csv(path)
        assert reloaded_from_file.equals(self.expected_output), (
            "\nMismatch with expected file: "
            + f"\nExpected: {self.expected_output}"
            + f"\nReturned: {reloaded_from_file}"
        )
        os.remove(path)

    def test_save_report_bad_path(self):
        """Test saving a report to a non-existent location"""
        with pytest.raises(IOError):
            save_report(self.report_input, "directory/test")


def test_convert_name_to_path():
    """Test of the _convert_name_to_path_ function"""
    assert _convert_parquet_name_to_path_("name") == os.path.join(
        _PARQUET_DIR_, "name.pkt"
    )
