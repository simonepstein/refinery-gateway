from typing import Any, List, Dict, Optional, Union
from controller.misc import config_service

from graphql_api.types import UserCountsWrapper
from submodules.model import enums
from submodules.model.business_objects import organization, general, user
from submodules.model.exceptions import EntityAlreadyExistsException
from submodules.model.models import User as User_model, Organization, User


def change_organization(org_id: str, changes: Dict[str, Any]) -> None:
    org = organization.get(org_id)
    if not org:
        raise ValueError(f"Organization with id {org_id} does not exist")

    for k in changes:
        if hasattr(org, k):
            setattr(org, k, changes[k])
        else:
            raise ValueError(f"Organization has no attribute {k}")
    general.commit()


def get_all_organizations() -> List[Organization]:
    return organization.get_all()


def get_organization_by_name(name: str) -> Organization:
    return organization.get_by_name(name)


def get_all_users(organization_id: str, user_role: Optional[str] = None) -> List[User]:
    parsed = None
    if user_role:
        try:
            parsed = enums.UserRoles[user_role.upper()]
        except KeyError:
            raise ValueError(f"Invalid UserRoles: {user_role}")
    return user.get_all(organization_id, parsed)


def get_all_users_with_record_count(
    organization_id: str, project_id: str
) -> List[UserCountsWrapper]:
    users = user.get_user_count(organization_id, project_id)
    return [
        UserCountsWrapper(user=User_model(id=row[0]), counts=row[1]) for row in users
    ]


def create_organization(name: str) -> Organization:
    if organization.get_by_name(name):
        raise EntityAlreadyExistsException(
            f"Organization with name {name} already exists"
        )
    organization_item = organization.create(name, with_commit=True)
    return organization_item


def delete_organization(name: str) -> None:
    org = organization.get_by_name(name)
    organization.delete(org.id, with_commit=True)


def get_overview_stats(org_id: str) -> List[Dict[str, Union[str, int]]]:
    return organization.get_organization_overview_stats(org_id)


def can_create_local(org: bool = True) -> bool:
    if config_service.get_config_value("is_managed"):
        return False
    existing_orgs = organization.get_all()
    checkvalue = 0 if org else 1
    if len(existing_orgs) != checkvalue:
        return False
    if user.get_count_assigned() != 0:
        return False
    return True
