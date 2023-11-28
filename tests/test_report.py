import random
from datetime import datetime
from unittest.mock import patch
from unittest import mock

import pandas as pd
import pyarrow
import pyarrow as pa
import pytest
from pandas.errors import MergeError

from choc_an_simulator.report import _generate_data_dict, generate_member_report
from choc_an_simulator.schemas import SERVICE_LOG_INFO, TableInfo

"""
Create test data for the generate_member_report function.
"""
test_user_info = pd.DataFrame(
    {
        "id": [940672921, 265608022, 637066975, 483185890, 385685178, 807527890],
        # "type": random.sample(0, 1), 6),
        "name": ["Case Hall", "Regina George", "Ray Donald", "Karla Tanners", "Zelda Hammersmith", "Linda Smith"],
        "address": ["123 Main St", "456 Elm St", "789 Oak St", "1011 Pine St", "1213 Maple St", "1415 Cedar St"],
        "city": ["Chicago", "New York", "Los Angeles", "Portland", "Sandy", "Muscle Shoals"],
        "state": ["IL", "NY", "CA", "OR", "OR", "AL"],
        "zipcode": [15603, 38322, 84524, 64198, 34268, 73952],
        "password_hash": pa.array(["password1", "password2", "password3", "password4", "password5", "password6"],
                                  type=pa.binary()),
    }
)

test_member_info = pd.DataFrame(
    {
        "member_id": [137002632, 989635272, 752880910, 367868907, 344690896, 406072422],
        "name": ["John Doe", "Jane Doe", "Alex Smith", "Bob Henderson", "Rebecca Miller", "Leah Jones"],
        "address": ["123 Main St", "456 Elm St", "789 Oak St", "1011 Pine St", "1213 Maple St", "1415 Cedar St"],
        "city": ["Chicago", "New York", "Los Angeles", "Portland", "Sandy", "Muscle Shoals"],
        "state": ["IL", "NY", "CA", "OR", "OR", "AL"],
        "zipcode": [15603, 38322, 84524, 64198, 34268, 73952],
        "suspended": [False, False, False, False, True, False],
        # adding weights to decrease likelihood of suspended members
    }
)

test_service_log_info = pd.DataFrame(
    {
        "entry_datetime_utc": [datetime(2023, 11, 21), datetime(2023, 11, 24), datetime(2023, 11, 26),
                               datetime(2023, 11, 21), datetime(2023, 11, 21), datetime(2023, 11, 24)],
        "service_date_utc": [datetime(2023, 11, 21), datetime(2023, 11, 24), datetime(2023, 11, 26),
                             datetime(2023, 11, 21), datetime(2023, 11, 21), datetime(2023, 11, 24)],
        "member_id": [367868907, 752880910, 367868907, 989635272, 752880910, 137002632],
        "provider_id": [483185890, 483185890, 940672921, 385685178, 385685178, 637066975],
        "service_id": [889804, 951175, 495644, 805554, 427757, 708195],
        "comments": ["", "Test comment", "Test comment 2", "Test comment 3", "Test comment 4", "Test comment 5"],
    }
)

test_provider_directory_info = pd.DataFrame(
    {
        "service_id": [889804, 951175, 495644, 805554, 427757, 708195],
        "service_name": ["Service 1", "Service 2", "Service 3", "Service 4", "Service 5", "Service 6"],
        "price_cents": random.sample(range(0, 99), 6),
        "price_dollars": random.sample(range(1, 999), 6),
    }
)


def load_records_from_file_side_effect(*args, **kwargs):
    """
    Side effect for the load_records_from_file function.

    Returns-
        test_user_info: If the table_info argument is "providers"
        test_member_info: If the table_info argument is "members"
        test_service_log_info: If the table_info argument is "service_log"
        test_provider_directory_info: If the table_info argument is "provider_directory"
    """
    # Get the table_info argument
    table_info: TableInfo = args[0]

    if table_info.name == "service_log":
        return test_service_log_info
    elif table_info.name == "members":
        return test_member_info
    elif table_info.name == "providers":
        return test_user_info
    elif table_info.name == "provider_directory":
        return test_provider_directory_info


def save_report_side_effect(*args, **kwargs):
    """
    Side effect for the save_report function.

    Returns-
        Returns a mocked file path using the save_report file_name argument.
        "/path/to/report/{report_file_path}.csv"

    """
    # Get the report argument
    report_file_path: str = args[1]
    return f"/path/to/report/{report_file_path}.csv"


@patch("choc_an_simulator.report.save_report", side_effect=save_report_side_effect)
@patch("choc_an_simulator.report.load_records_from_file", side_effect=load_records_from_file_side_effect)
def test_generate_member_report(mock_load_records_from_file, mock_save_report, capfd):
    """
    Test the generate_member_report function.
    """
    current_date = datetime.now().strftime("%m-%d-%Y")
    expected_output = ''.join([
        f"Report saved to /path/to/report/John Doe_{current_date}.csv\n",
        f"Report saved to /path/to/report/Bob Henderson_{current_date}.csv\n",
        f"Report saved to /path/to/report/Alex Smith_{current_date}.csv\n",
        f"Report saved to /path/to/report/Jane Doe_{current_date}.csv\n",
    ])
    expected_keys = [
        "Member name",
        "Member number",
        "Member street address",
        "Member city",
        "Member state",
        "Member zip code",
        "Services",
    ]
    mock_df = mock.Mock()

    generate_member_report()
    captured = capfd.readouterr()

    assert (captured.out == expected_output)

    actual_df = mock_save_report.call_args_list[0][0][0]
    assert set(actual_df.columns) == set(expected_keys)


@patch("choc_an_simulator.report.load_records_from_file", side_effect=load_records_from_file_side_effect)
@patch("choc_an_simulator.report._load_all_records", return_value={'service_log': pd.DataFrame()})
def test_generate_member_report_no_members(mock_load_records_from_file, mock_load_all_records, capfd):
    """
    Test the generate_member_report function with no members.
    """
    expected_output = "No records found within the last 7 days.\n"

    generate_member_report()
    captured = capfd.readouterr()

    assert (captured.out == expected_output)


@patch("choc_an_simulator.report.load_records_from_file", side_effect=KeyError)
def test_generate_member_report_key_error(mock_load_records_from_file):
    """
    Test the generate_member_report function with a KeyError.
    """
    with pytest.raises(KeyError):
        generate_member_report()


@patch("choc_an_simulator.report.load_records_from_file", side_effect=pyarrow.ArrowTypeError)
def test_generate_member_report_arrow_type_error(mock_load_records_from_file):
    """
    Test the generate_member_report function with a ArrowTypeError.
    """
    with pytest.raises(pyarrow.ArrowTypeError):
        generate_member_report()


@patch("choc_an_simulator.report.load_records_from_file", side_effect=pyarrow.ArrowInvalid)
def test_generate_member_report_arrow_invalid(mock_load_records_from_file):
    """
    Test the generate_member_report function with a ArrowInvalid.
    """
    with pytest.raises(pyarrow.ArrowInvalid):
        generate_member_report()


@patch("choc_an_simulator.report.load_records_from_file", side_effect=pyarrow.ArrowIOError)
def test_generate_member_report_arrow_io_error(mock_load_records_from_file):
    """
    Test the generate_member_report function with a ArrowIOError.
    """
    with pytest.raises(pyarrow.ArrowIOError):
        generate_member_report()


@patch("choc_an_simulator.report.load_records_from_file", side_effect=TypeError)
def test_generate_member_report_type_error(mock_load_records_from_file):
    """
    Test the generate_member_report function with a TypeError.
    """
    with pytest.raises(TypeError):
        generate_member_report()


@patch("choc_an_simulator.report.pd.merge", side_effect=MergeError)
@patch("choc_an_simulator.report.load_records_from_file", side_effect=load_records_from_file_side_effect)
def test_generate_member_report_merge_error(mock_load_records_from_file, mock_merge):
    """
    Test the generate_member_report function with a MergeError.
    """
    with pytest.raises(MergeError):
        generate_member_report()


@patch("choc_an_simulator.report.load_records_from_file", side_effect=load_records_from_file_side_effect)
@patch("choc_an_simulator.report.pd.merge", side_effect=ValueError)
def test_generate_member_report_value_error(mock_load_records_from_file, mock_merge):
    """
    Test the generate_member_report function with a ValueError.
    """
    with pytest.raises(ValueError):
        generate_member_report()


kept_cols = ["member_id", "name", "address", "city", "state", "zipcode", "suspended"]
table_info = SERVICE_LOG_INFO

FILTERS = [
    ('eq_cols', {"member_id": 137002632}),
    ('lt_cols', {"member_id": 137002632}),
    ('gt_cols', {"member_id": 137002632}),
    (None, None)
]


@pytest.mark.parametrize('filter_type, filter_value', FILTERS)
def test_generate_data_dict(filter_type, filter_value):
    """
    Parameterized test for the _generate_data_dict function.
    """
    params = {'kept_cols': kept_cols}

    if filter_type:
        params[filter_type] = filter_value

    result = _generate_data_dict(table_info, **params)

    assert result['table'] == table_info
    assert result['kept_cols'] == kept_cols

    if filter_type:
        assert result['filter'][filter_type] == filter_value
