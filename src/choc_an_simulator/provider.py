"""
Provider Sub-System.

This module facilitates interactions between healthcare providers and the ChocAn Data Center.
It encompasses functions for displaying menus, prompting for member IDs, recording service
billing entries, and managing provider directories. These functions collectively support
billing, service verification, and data retrieval processes in the ChocAn system.
"""


def show_provider_menu() -> None:
    """
    Display the provider menu to the user.

    Present the provider with a range of menu options, allowing access to various functionalities
    of the Provider Component, like requesting the provider directory or recording service entries.
    """
    # https://en.wikipedia.org/wiki/ANSI_escape_code
    # 1 means bold, 32 means green, 31 means red
    provider_terminal = "\033[1mProvider Terminal\033[m"
    request_provider_directory = "\033[1;32mRequest Provider Directory\033[m"
    record_service_entry = "\033[1;32mRecord Service Entry\033[m"
    exit = "\033[1;31mExit\033[m"

    print(f"\n{provider_terminal}\n")
    print(
        f"Press 1 to {request_provider_directory}  |  "
        f"2 to {record_service_entry}  |  "
        f"3 to {exit}\n\n"
    )


def prompt_member_id() -> int:
    """
    Prompt for a valid member ID from keycard reader or terminal.

    Initiates a prompt for the user to enter a member ID, which can be entered through a
    keycard reader or manually via the terminal. The function returns the entered member ID,
    which is used in subsequent operations like service billing or member status checks.

    Returns-
        int: The entered member ID.
    """
    raise NotImplementedError("prompt_member_id")


def display_member_information(member_id: int) -> None:
    """
    Fetch and display information about a member from the member database.

    The displayed data includes the member's name, ID, and status, aiding providers in
    verifying member eligibility and record accuracy.

    Args-
        member_id (int): ID of the member whose information is to be displayed.
    """
    raise NotImplementedError("display_member_information")


def record_service_billing_entry(member_id: int) -> None:
    """
    Record a billing entry for a service provided to a member.

    In this function, the provider enters details of the service rendered. It involves
    validating the member's status, collecting service details, and saving the information
    in the service logs.

    Args-
        member_id (int): The member ID for whom the service billing entry is being recorded.
    """
    raise NotImplementedError("records_service_billing_entry")


def request_provider_directory() -> None:
    """Save the provider directory to a CSV file, and display the path it was saved to."""
    raise NotImplementedError("request_provider_directory")
