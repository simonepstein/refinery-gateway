from typing import Any, Dict, List
from controller.misc import config_service
from controller.misc import black_white_demo
from graphql_api.types import ServiceVersionResult
from datetime import datetime
import os

from util import service_requests

BASE_URI_UPDATER = os.getenv("UPDATER")


def check_is_managed() -> bool:
    return config_service.get_config_value("is_managed")


def update_config(dict_str: str) -> None:
    return config_service.change_config(dict_str)


def refresh_config() -> None:
    config_service.refresh_config()


def get_black_white_demo() -> Dict[str, List[str]]:
    return black_white_demo.get_black_white_demo()


def get_version_overview() -> List[ServiceVersionResult]:
    updater_version_overview = __updater_version_overview()
    date_format = "%Y-%m-%dT%H:%M:%S.%f"  # 2022-09-06T12:10:39.167397
    version_overview = [
        ServiceVersionResult(
            service=service["name"],
            installed_version=service["installed_version"],
            remote_version=service["remote_version"],
            last_checked=datetime.strptime(service["last_checked"], date_format),
            remote_has_newer=service["remote_has_newer"],
            link=service["link"],
        )
        for service in updater_version_overview
    ]
    return version_overview


def has_updates() -> List[ServiceVersionResult]:
    has_updates = __updater_has_updates()
    return has_updates


def __updater_version_overview() -> List[Dict[str, Any]]:
    url = f"{BASE_URI_UPDATER}/version_overview"
    return service_requests.get_call_or_raise(url)


def __updater_has_updates() -> bool:
    url = f"{BASE_URI_UPDATER}/has_updates"
    return service_requests.get_call_or_raise(url)


def __updater_update_to_newest() -> None:
    raise ValueError("This endpoint should only be called from the update batch script")
