"""
Manager Sub-System.

The manager sub-system allows managers to manage member, provider, and provider directory records.
"""
import pandas as pd
from pyarrow import ArrowIOError
from pandas.api.types import is_numeric_dtype
from .database_management import (
    load_records_from_file,
    add_records_to_file,
    update_record,
    remove_record,
    update_record,
)
from .schemas import USER_INFO, MEMBER_INFO, PROVIDER_DIRECTORY_INFO, TableInfo
from .user_io import prompt_str, prompt_int, PColor, prompt_menu_options
from .report import (
    generate_member_report,
    generate_summary_report,
    generate_provider_report,
)


def manager_menu() -> None:
    """
    The Manager menu provides access to the following key functionalities.

    Add Member
    Update Member
    Remove Member
    Add Provider
    Update Provider
    Remove Provider
    Add Provider Directory
    Update Provider Directory
    Remove Provider Directory
    Generate Member Report
    Generate Provider Report
    Generate Summary Report
    """
    user_exit = False
    message = "Manger Terminal"
    choices = ["Member", "Provider", "Provider Directory", "Reports"]

    while user_exit is False:
        match prompt_menu_options(message, choices):
            case (_, "Member"):
                _prompt_member_options()
            case (_, "Provider"):
                _prompt_provider_options()
            case (_, "Provider Directory"):
                _prompt_provider_directory_options()
            case (_, "Reports"):
                _prompt_report_options()
            case None:
                user_exit = True


def _prompt_member_options() -> None:
    """
    Display member options menu to the manager.

    The member options menu provides access to the following key functionalities.
    Add Member
    Update Member
    Remove Member
    """
    user_exit = False
    message = "Member Options"
    choices = ["Add", "Update", "Remove"]

    while user_exit is False:
        match prompt_menu_options(message, choices):
            case (_, "Add"):
                add_member_record()
            case (_, "Update"):
                update_member_record()
            case (_, "Remove"):
                remove_member_record()
            case None:
                user_exit = True


def _prompt_provider_options() -> None:
    """
    Display provider options menu to the manager.

    The provider options menu provides access to the following key functionalities.
    Add Provider
    Update Provider
    Remove Provider
    """
    user_exit = False
    message = "Provider Options"
    choices = ["Add", "Update", "Remove"]

    while user_exit is False:
        match prompt_menu_options(message, choices):
            case (_, "Add"):
                add_provider_record()
            case (_, "Update"):
                update_provider_record()
            case (_, "Remove"):
                remove_provider_record()
            case None:
                user_exit = True


def _prompt_provider_directory_options() -> None:
    """
    Display provider directory options menu to the manager.

    The provider directory options menu provides access to the following key functionalities.
    Add Provider Directory
    Update Provider Directory
    Remove Provider Directory
    """
    user_exit = False
    message = "Provider Directory Options"
    choices = ["Add", "Update", "Remove"]

    while user_exit is False:
        match prompt_menu_options(message, choices):
            case (_, "Add"):
                add_provider_directory_record()
            case (_, "Update"):
                update_provider_directory_record()
            case (_, "Remove"):
                remove_provider_directory_record()
            case None:
                user_exit = True


def _prompt_report_options() -> None:
    """
    Display report options menu to the manager.

    The report options menu provides access to the following key functionalities.
    Generate Member Report
    Generate Provider Report
    Generate Summary Report
    """
    user_exit = False
    message = "Reports Options"
    choices = ["Member", "Provider", "Summary"]

    while user_exit is False:
        match prompt_menu_options(message, choices):
            case (_, "Member"):
                generate_member_report()
            case (_, "Provider"):
                generate_provider_report()
            case (_, "Summary"):
                generate_summary_report()
            case None:
                user_exit = True


def add_member_record() -> None:
    """
    Manager is prompted to enter member information.

    Member information: member id, name, street address, city, state, zip code, and suspended.
    The member number will be generated from generate_unique_id().
    """
    try:
        member_id = generate_unique_id(MEMBER_INFO)
    except IndexError:
        PColor.pfail(
            "The maximum number of members has been reached. No new member added."
        )
        return

    member_df = pd.DataFrame(
        {
            "member_id": member_id,
            "name": prompt_str("Name", MEMBER_INFO.character_limits["name"]),
            "address": prompt_str("Address", MEMBER_INFO.character_limits["address"]),
            "city": prompt_str("City", MEMBER_INFO.character_limits["city"]),
            "state": prompt_str("State", MEMBER_INFO.character_limits["state"]),
            "zipcode": prompt_int("Zipcode", MEMBER_INFO.character_limits["zipcode"]),
            "suspended": False,
        },
        index=[0],
    )
    if member_df.isna().values.any():
        return
    try:
        add_records_to_file(member_df, MEMBER_INFO)
    except ArrowIOError:
        PColor.pwarn("There was an issue accessing the database. Member was not added.")
        return
    PColor.pok(f"Member #{member_id} Added.")


def update_member_record() -> None:
    """
    Prompt the user to update the member's information.

    Prompts the user for a member ID, then prompts for which field to change.
    This prompt repeats until the user chooses to exit.
    """
    try:
        member_id = prompt_int("Member ID")
        if member_id is None:
            return
        member_record = load_records_from_file(
            MEMBER_INFO, eq_cols={"member_id": member_id}
        )
    except ArrowIOError:
        PColor.pwarn("There was an error loading the member record.")
        return

    if member_record.empty:
        PColor.pwarn("Warning: No matching member.\n")
        return

    member_record = member_record.iloc[0]

    options = []
    for field in member_record.index.values[1:]:
        options.append(field)
    selection = prompt_menu_options("Choose field to change", options)
    if selection is None:
        return
    field_to_update = selection[1]
    if field_to_update == "zipcode":
        new_value = prompt_int(
            f"New value for {field_to_update}", MEMBER_INFO.character_limits["zipcode"]
        )
    else:
        new_value = prompt_str(
            f"New value for {field_to_update}", MEMBER_INFO.character_limits["address"]
        )

    if new_value is None:
        return

    try:
        update_record(member_id, MEMBER_INFO, **{field_to_update: new_value})
        PColor.pok("Member record updated.")
    except ArrowIOError:
        PColor.pfail("There was an error updating the member record.")
        return


def remove_member_record() -> None:
    """
    Prompt the user to remove the member's information.

    Prompts the user for a member ID, and then removes the record.
    """
    # try:
    #     member_id = prompt_int("Member ID")
    #     if member_id is not None:
    #         if remove_record(member_id, MEMBER_INFO):
    #             print(f"Member {member_id} Removed")
    #         else:
    #             print(f"Member {member_id} Not Found.")
    #     else:
    #         print("Member ID cannot be a NULL value!")
    # except ArrowIOError:
    #     PColor.pfail("Member was not removed!")
    #     return
    member_id = prompt_int("Member ID")
    if member_id is None:
        return
    try:
        result = remove_record(member_id, MEMBER_INFO)
    except ArrowIOError:
        PColor.pfail(f"There was an error and member {member_id} was not removed!")
        return

    if result is True:
        print(f"Member {member_id} Removed")
    else:
        print(f"Member {member_id} Not Found.")


def generate_unique_id(table_info: TableInfo) -> int:
    """
    Generate a unique 9 digit ID. ID's increment by 1.

    Returns-
        int: The generated ID.

    Raises-
        IndexError: ID limit exceeded.
    """
    df = None
    try:
        df = load_records_from_file(table_info)
    except ArrowIOError:
        PColor.pwarn(
            "There was an issue accessing the database."
        )
    if df.empty:
        return 1000000000

    id = df.iloc[:, 0]
    if not is_numeric_dtype(id):
        raise TypeError("Only integers are allowed.")

    max_id = id.max()
    if max_id >= 9999999999:
        raise IndexError("User Limit Exceeded.")
    return max_id + 1


def add_provider_record() -> None:
    """
    Manager is prompted to enter provider information.

    Provider information: name, street address, city, state, zip code, and email address.
    Provider number is generated from generate_unique_id().

    This prompt repeats until the user chooses to exit.

    Raises-
        IndexError: Maximum number of providers exceeded
    """
    try:
        provider_id = generate_unique_id(USER_INFO)
    except IndexError:
        PColor.pfail("The maximum number of users has been reached. No new user added.")
        return

    provider_df = pd.DataFrame(
        {
            "id": provider_id,
            "type": 1,
            "name": prompt_str("Name", USER_INFO.character_limits["name"]),
            "address": prompt_str("Address", USER_INFO.character_limits["address"]),
            "city": prompt_str("City", USER_INFO.character_limits["city"]),
            "state": prompt_str("State", USER_INFO.character_limits["state"]),
            "zipcode": prompt_int("Zipcode", USER_INFO.character_limits["zipcode"]),
            "password_hash": bytes(0),
        },
        index=[0],
    )
    if provider_df.isna().values.any():
        return
    try:
        add_records_to_file(provider_df, USER_INFO)
    except ArrowIOError:
        PColor.pwarn(
            "There was an issue accessing the database. Provider was not added."
        )
        return
    # value / type errors are impossible due to checks during prompting.
    PColor.pok(f"Provider #{provider_id} Added.")


def update_provider_record() -> None:
    """
    Prompt the user to update the provider's information.

    Prompts the user for a provider ID, then prompts for which field to change.
    """
    provider_id = prompt_int("Provider ID")
    if provider_id is None:
        return None
    try:
        provider_record = load_records_from_file(USER_INFO, eq_cols={"id": provider_id})
    except ArrowIOError:
        PColor.pwarn("There was an error loading the provider record.")
        return
    if provider_record.empty:
        PColor.pwarn("Provider ID not found.")
        return
    provider_record = provider_record.iloc[0]

    options = []
    for field in provider_record.index.values[1:]:
        options.append(field)
    selection = prompt_menu_options("Choose field to change", options)
    if selection is None:
        return
    field_to_update = selection[1]
    if field_to_update == "zipcode":
        new_value = prompt_int(
            f"New value for {field_to_update}", USER_INFO.character_limits["zipcode"]
        )
    else:
        new_value = prompt_str(
            f"New value for {field_to_update}", USER_INFO.character_limits["address"]
        )

    if new_value is None:
        return

    try:
        update_record(provider_id, USER_INFO, **{field_to_update: new_value})
    except ArrowIOError:
        PColor.pfail("There was an error updating the provider record.")
        return


def remove_provider_record() -> None:
    """
    Prompt the user to remove the provider's information.

    Prompts the user for a provider ID, then prompts for which field to remove.
    This prompt repeats until the user chooses to exit.
    """
    # try:
    #     provider_id = prompt_int("Provider ID")
    #     if provider_id is not None:
    #         if remove_record(provider_id, USER_INFO):
    #             print(f"Provider {provider_id} Removed")
    #         else:
    #             print(f"Provider {provider_id} Not Found.")
    #     else:
    #         print("Provider ID cannot be a NULL value!")
    # except ArrowIOError:
    #     PColor.pfail("Provider was not removed!")
    #     return
    provider_id = prompt_int("Provider ID")
    try:
        result = remove_record(provider_id, USER_INFO)
    except ArrowIOError:
        PColor.pfail(f"There was an error and provider {provider_id} was not removed!")
        return

    if result is True:
        print(f"Provider {provider_id} Removed")
    else:
        print(f"Provider {provider_id} Not Found.")


def add_provider_directory_record() -> None:
    """
    Manager is prompted to enter service information.

    This is the service information: service_id, service_name, price_dollars, and price_cents.
    """
    try:
        service_id = generate_unique_id(PROVIDER_DIRECTORY_INFO)
    except IndexError:
        PColor.pfail(
            "The maximum number of services has been reached. No new services added."
        )
        return

    service_df = pd.DataFrame(
        {
            "service_id": service_id,
            "service_name": prompt_str(
                "Service name", PROVIDER_DIRECTORY_INFO.character_limits["service_name"]
            ),
            "price_dollars": prompt_int("Price (dollars)"),
            "price_cents": prompt_int(
                "Price (cents)",
                numeric_limit=PROVIDER_DIRECTORY_INFO.numeric_limits["price_cents"],
            ),
        },
        index=[0],
    )
    if service_df.isna().values.any():
        return
    try:
        add_records_to_file(service_df, PROVIDER_DIRECTORY_INFO)
    except ArrowIOError:
        PColor.pwarn(
            "There was an issue accessing the database. Service was not added."
        )
        return
    # value / type errors are impossible due to checks during prompting.
    PColor.pok(f"Service #{service_id} Added.")


def update_provider_directory_record() -> None:
    """The manager is prompted for a service id and then the service is updated based on the id."""
    service_id = prompt_int("Service ID")
    if service_id is None:
        return None
    try:
        service_record = load_records_from_file(
            PROVIDER_DIRECTORY_INFO, eq_cols={"service_id": service_id}
        )
    except ArrowIOError:
        PColor.pfail("There was an error loading the service record.")
        return

    if service_record.empty:
        PColor.pfail("Error: No record loaded.")
        return

    service_record = service_record.iloc[0]

    options = []
    for field in service_record.index.values[1:]:
        options.append(field)
    selection = prompt_menu_options("Choose field to change", options)
    if selection is None:
        return
    field_to_update = selection[1]
    if field_to_update == "price_dollars" or field_to_update == "price_cents":
        new_value = prompt_int(
            f"New value for {field_to_update}",
            numeric_limit=PROVIDER_DIRECTORY_INFO.numeric_limits["price_cents"],
        )
    else:
        new_value = prompt_str(
            f"New value for {field_to_update}",
            PROVIDER_DIRECTORY_INFO.character_limits["service_name"],
        )

    try:
        update_record(
            service_id, PROVIDER_DIRECTORY_INFO, **{field_to_update: new_value}
        )
    except ArrowIOError:
        PColor.pfail("There was an error updating the service record.")
        return


def remove_provider_directory_record() -> None:
    """Manager is prompted for a service id, and a lookup is performed, and a service is removed."""
    service_id = prompt_int("Service ID")
    result = None
    try:
        result = remove_record(service_id, PROVIDER_DIRECTORY_INFO)
    except ArrowIOError:
        PColor.pfail(f"There as an error and service {service_id} was not removed!")
        return
    if result is True:
        print(f"Service {service_id} Removed")
    else:
        print(f"Service {service_id} was not found")
