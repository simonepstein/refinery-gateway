import logging

from api.project import ProjectDetails
from api.transfer import (
    DatabaseSessionHandler,
    FileExport,
    KnowledgeBaseExport,
    Notify,
    PrepareImport,
)

import graphene
from starlette.applications import Starlette
from starlette.graphql import GraphQLApp
from starlette.middleware import Middleware
from starlette.routing import Route

from graphql_api import schema
from submodules.model.models import Base, UploadTask
from submodules.model.session import engine

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


Base.metadata.create_all(bind=engine)
routes = [
    Route(
        "/graphql/",
        GraphQLApp(
            schema=graphene.Schema(query=schema.Query, mutation=schema.Mutation)
        ),
    ),
    Route("/notify/{path:path}", Notify),
    Route("/project/{project_id:str}", ProjectDetails),
    Route(
        "/project/{project_id:str}/knowledge_base/{knowledge_base_id:str}",
        KnowledgeBaseExport,
    ),
    Route("/project/{project_id:str}/export", FileExport),
    Route("/project/{project_id:str}/import", PrepareImport),
    Route("/project/{project_id:str}/import/task/{task_id:str}", UploadTask),
]

middleware = [Middleware(DatabaseSessionHandler)]

app = Starlette(routes=routes, middleware=middleware)
