"""Tests of functions in the manager module."""
import pytest
import pandas as pd
import pyarrow as pa
from choc_an_simulator.manager import (
    _generate_user_id,
    manager_menu,
    add_member_record,
    remove_member_record,
    add_provider_record,
    update_provider_record,
    remove_provider_record,
    add_provider_directory_record,
    update_provider_directory_record,
    remove_provider_directory_record,
    generate_member_report,
    generate_provider_report,
    generate_summary_report,
)
from choc_an_simulator.schemas import MEMBER_INFO, USER_INFO


class TestGenerateUserID:
    """Tests of the _generate_user_id function"""

    @pytest.mark.parametrize(
        "existing_ids,table_info",
        [
            # First valid ID
            ([1000000000], MEMBER_INFO),
            # Second to last valid ID
            ([9999999998], MEMBER_INFO),
            # Empty
            ([], MEMBER_INFO),
            # First valid ID
            ([1000000000], USER_INFO),
            # Second to last valid ID
            ([9999999998], USER_INFO),
            # Empty
            ([], USER_INFO),
        ],
    )
    def test_generate_user_id_valid(self, mocker, existing_ids, table_info):
        """Test generating a valid user ID"""
        mocker.patch(
            "choc_an_simulator.manager.load_records_from_file",
            return_value=pd.DataFrame({"id": existing_ids}),
        )
        # print(load_records_from_file(None))
        new_id = _generate_user_id(table_info)
        assert new_id == max(existing_ids, default=999999999) + 1

    @pytest.mark.parametrize(
        "table_info",
        [USER_INFO, MEMBER_INFO],
    )
    def test_generate_user_id_out_of_range(self, mocker, table_info):
        """Test generating a user ID that exceeds the max value"""
        mocker.patch(
            "choc_an_simulator.manager.load_records_from_file",
            return_value=pd.DataFrame({"id": [9999999999]}),
        )
        with pytest.raises(IndexError):
            _ = _generate_user_id(table_info)

    @pytest.mark.parametrize(
        "table_info",
        [USER_INFO, MEMBER_INFO],
    )
    def test_generate_user_id_nonnumeric_id(self, mocker, table_info):
        """Test generating a user ID that exceeds the max value"""
        mocker.patch(
            "choc_an_simulator.manager.load_records_from_file",
            return_value=pd.DataFrame({"id": ["hello"]}),
        )
        with pytest.raises(TypeError):
            _ = _generate_user_id(table_info)


def test_manager_menu():
    with pytest.raises(NotImplementedError):
        manager_menu()


class TestAddMemberRecord:
    """Tests of the add_provider_record function"""

    @pytest.mark.parametrize(
        "input_strs", [["Donald", "1234 NE Street st.", "Portland", "OR", "97212"]]
    )
    @pytest.mark.usefixtures("mock_input_series")
    def test_add_member_record_valid(self, mocker, mock_input_series):
        """Test of the add_member_record function with valid input"""
        mocker.patch("choc_an_simulator.manager.add_records_to_file", return_value=None)
        add_member_record()

    @pytest.mark.parametrize(
        "input_strs", [["Donald", "1234 NE Street st.", "Portland", "OR", "97212"]]
    )
    @pytest.mark.usefixtures("mock_input_series")
    def test_add_member_record_io_error(self, mocker, mock_input_series, capsys):
        """Test of the add_member_record function with an IO error"""
        mocker.patch(
            "choc_an_simulator.manager.add_records_to_file",
            side_effect=pa.ArrowIOError,
        )
        add_member_record()
        assert (
            "There was an issue accessing the database. Member was not added."
            in capsys.readouterr().out
        )

    @pytest.mark.usefixtures("mock_input_ctrl_c")
    def test_add_member_record_user_exit(self, mocker, mock_input_ctrl_c, capsys):
        """Test of the add_member_record function with user exit."""
        mock_add_records = mocker.patch("choc_an_simulator.manager.add_records_to_file")
        add_member_record()
        mock_add_records.assert_not_called()

    def test_add_member_record_bad_user_id(self, mocker, capsys):
        """
        Test of the add_member_record function when the system has reached the maximum
        number of members.
        """
        mocker.patch(
            "choc_an_simulator.manager._generate_user_id",
            side_effect=IndexError,
        )
        add_member_record()
        assert "No new member added." in capsys.readouterr().out


def test_remove_member_record():
    with pytest.raises(NotImplementedError):
        remove_member_record()


class TestAddProviderRecord:
    """Tests of the add_provider_record function"""

    @pytest.mark.parametrize(
        "input_strs", [["Donald", "1234 NE Street st.", "Portland", "OR", "97212"]]
    )
    @pytest.mark.usefixtures("mock_input_series")
    def test_add_provider_record_valid(self, mocker, mock_input_series):
        """Test of the add_provider_record function with valid input"""
        mocker.patch("choc_an_simulator.manager.add_records_to_file", return_value=None)
        add_provider_record()

    @pytest.mark.parametrize(
        "input_strs", [["Donald", "1234 NE Street st.", "Portland", "OR", "97212"]]
    )
    @pytest.mark.usefixtures("mock_input_series")
    def test_add_provider_record_io_error(self, mocker, mock_input_series, capsys):
        """Test of the add_provider_record function with an IO error"""
        mocker.patch(
            "choc_an_simulator.manager.add_records_to_file",
            side_effect=pa.ArrowIOError,
        )
        add_provider_record()
        assert (
            "There was an issue accessing the database. Provider was not added."
            in capsys.readouterr().out
        )

    @pytest.mark.usefixtures("mock_input_ctrl_c")
    def test_add_provider_record_user_exit(self, mocker, mock_input_ctrl_c, capsys):
        """Test of the add_provider_record function with user exit."""
        mock_add_records = mocker.patch("choc_an_simulator.manager.add_records_to_file")
        add_provider_record()
        mock_add_records.assert_not_called()

    def test_add_provider_record_bad_user_id(self, mocker, capsys):
        """
        Test of the add_provider_record function when the system has reached the maximum
        number of providers.
        """
        mocker.patch(
            "choc_an_simulator.manager._generate_user_id",
            side_effect=IndexError,
        )
        add_provider_record()
        assert "No new user added." in capsys.readouterr().out


def test_update_provider_record():
    with pytest.raises(NotImplementedError):
        update_provider_record()


def test_remove_provider_record():
    with pytest.raises(NotImplementedError):
        remove_provider_record()


def test_add_provider_directory_record():
    with pytest.raises(NotImplementedError):
        add_provider_directory_record()


def test_update_provider_directory_record():
    with pytest.raises(NotImplementedError):
        update_provider_directory_record()


def test_remove_provider_directory_record():
    with pytest.raises(NotImplementedError):
        remove_provider_directory_record()


def test_generate_member_report():
    with pytest.raises(NotImplementedError):
        generate_member_report()


def test_generate_provider_report():
    with pytest.raises(NotImplementedError):
        generate_provider_report()


def test_generate_summary_report():
    with pytest.raises(NotImplementedError):
        generate_summary_report()
