from typing import List, Any, Dict, Optional

import graphene

from graphene_sqlalchemy.fields import SQLAlchemyConnectionField

from graphql_api.types import Record, ExtendedSearch, TokenizedRecord
from submodules.model.business_objects import record
from controller.record import manager
from controller.auth import manager as auth
from controller.tokenization import manager as tokenization_manager


class RecordQuery(graphene.ObjectType):
    record_by_record_id = graphene.Field(
        Record,
        record_id=graphene.ID(required=True),
        project_id=graphene.ID(required=True),
    )

    all_records = SQLAlchemyConnectionField(
        Record, project_id=graphene.ID(required=True)
    )

    records_by_static_slice = graphene.Field(
        ExtendedSearch,
        project_id=graphene.ID(required=True),
        slice_id=graphene.ID(required=True),
        order_by=graphene.JSONString(),
        limit=graphene.Int(),
        offset=graphene.Int(),
    )

    search_records_extended = graphene.Field(
        ExtendedSearch,
        project_id=graphene.ID(required=True),
        filter_data=graphene.List(graphene.JSONString, required=True),
        limit=graphene.Int(),
        offset=graphene.Int(),
    )

    search_records_by_similarity = graphene.Field(
        ExtendedSearch,
        project_id=graphene.ID(required=True),
        embedding_id=graphene.ID(required=True),
        record_id=graphene.ID(required=True),
    )

    tokenize_record = graphene.Field(
        TokenizedRecord,
        # TODO check if project id should be added
        record_id=graphene.ID(required=True),
    )

    def resolve_all_records(self, info, project_id: str) -> List[Record]:
        auth.check_project_access(info, project_id)
        return manager.get_all_records(project_id)

    def resolve_record_by_record_id(
        self, info, project_id: str, record_id: str
    ) -> Record:
        auth.check_project_access(info, project_id)
        return manager.get_record(project_id, record_id)

    def resolve_records_by_static_slice(
        self,
        info,
        project_id: str,
        slice_id: str,
        order_by: Optional[Dict[str, str]] = None,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
    ) -> ExtendedSearch:
        auth.check_demo_access(info)
        auth.check_project_access(info, project_id)
        user_id = auth.get_user_by_info(info).id
        return manager.get_records_by_static_slice(
            user_id, project_id, slice_id, order_by, limit, offset
        )

    def resolve_search_records_extended(
        self,
        info,
        project_id: str,
        filter_data: List[Dict[str, Any]],
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
    ) -> ExtendedSearch:
        auth.check_demo_access(info)
        auth.check_project_access(info, project_id)
        user_id = auth.get_user_by_info(info).id
        return manager.get_records_by_extended_search(
            project_id, user_id, filter_data, limit, offset
        )

    def resolve_search_records_by_similarity(
        self, info, project_id: str, embedding_id: str, record_id: str
    ) -> ExtendedSearch:
        auth.check_demo_access(info)
        auth.check_project_access(info, project_id)
        user_id = auth.get_user_by_info(info).id
        return manager.get_records_by_similarity_search(
            project_id, user_id, embedding_id, record_id
        )

    def resolve_tokenize_record(self, info, record_id: str) -> TokenizedRecord:
        auth.check_demo_access(info)
        record_item = record.get_without_project_id(record_id)
        if not record_item:
            return None  # to prevent error calls in gql
        auth.check_project_access(info, record_item.project_id)
        return tokenization_manager.get_tokenized_record(
            record_item.project_id, record_id
        )
