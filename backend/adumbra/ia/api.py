import logging
import shutil
import typing as t
import zipfile
from pathlib import Path

from fastapi import APIRouter, FastAPI, Form, HTTPException, Query
from mongoengine import QuerySet
from pydantic import BaseModel

from adumbra.database import connect_mongo
from adumbra.database.assistant import AssistantDBModel
from adumbra.ia.util import ModelDepends
from adumbra.ia.util.segmentation import config_adapter, run_segmentation
from adumbra.types.assistants import SAM2Config, SegmentationResult, ZIMConfig

# Replace these imports with your actual implementations
from adumbra.types.requests import (
    CreateAssistantRequest,
    GetAssistantsRequest,
    GetAssistantsResponse,
    PaginationParams,
    SAM2SegmentationRequest,
    ZimSegmentationRequest,
)
from adumbra.util.api_bridge import Pagination, queryset_to_json

Model_T = t.TypeVar("Model_T", bound=BaseModel)
AsForm = t.Annotated[Model_T, Form(media_type="multipart/form-data")]
QueryDepends = t.Annotated[Model_T, ModelDepends(Query)]

logger = logging.getLogger(__name__)
connect_mongo("ia")
AssistantDBModel.ensure_defaults_available()

# Initialize FastAPI application
app = FastAPI(
    title="Model API",
    description="API for model-related operations",
    version="1.0.0",
    swagger_ui_parameters={"defaultModelRendering": "model"},
)
router = APIRouter(tags=["assistants"])


@router.get("/", response_model=GetAssistantsResponse)
async def get_assistants(
    page_params: QueryDepends[PaginationParams],
    request: QueryDepends[GetAssistantsRequest],
) -> GetAssistantsResponse:
    """
    Get all models that match the given criteria.
    """
    kwargs = {}
    if request.assistant_name:
        kwargs["name"] = request.assistant_name
    if request.assistant_type:
        kwargs["assistant_type"] = request.assistant_type

    matches = t.cast(QuerySet, AssistantDBModel.objects(**kwargs))
    if page_params.page_size is not None:
        pagination = Pagination.from_count_and_page(
            matches.count(), page_params.page_size, page_params.page
        )
        matches = pagination.slice_objects(matches)
    assistants = queryset_to_json(matches)
    return GetAssistantsResponse(
        assistants=assistants, page=page_params.page, pagination=pagination.to_dict()
    )


@router.post("/")
async def create_assistant(request: AsForm[CreateAssistantRequest]):
    """
    Create a new model with the given parameters.
    """
    save_path = Path("/models") / request.assistant_type / request.assistant_name
    save_path.mkdir(parents=True, exist_ok=True)
    if isinstance(request.assets, list):
        files = request.assets
    else:
        files = [request.assets]

    new_config = request.config_parameters or {}
    file_as_param = request.config_parameters is None

    for file in files:
        assert file.filename is not None
        destination = save_path / file.filename
        if destination.suffix == ".zip":
            destination = destination.with_suffix("")
            destination.mkdir(exist_ok=True)
            with zipfile.ZipFile(file.file, "r") as zip_ref:
                zip_ref.extractall(destination)
        else:
            with open(destination, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        if file_as_param:
            new_config[destination.stem] = destination.as_posix()

    # Ensure parameters are recognized. This should fail with an informative error
    # message if the parameters are invalid.
    config_adapter.validate_python(
        {**new_config, "assistant_type": request.assistant_type}
    )
    new_model = AssistantDBModel(
        name=request.assistant_name,
        assistant_type=request.assistant_type,
        parameters=new_config,
    )
    new_model.save()

    return {"message": "Model created successfully"}


@router.delete("/{assistant_id}")
async def delete_assistant(assistant_id: str):
    """
    Delete a model with the given name and type.
    """
    assistant = AssistantDBModel.objects(id=assistant_id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Model not found")
    # Clean up assets
    save_path = Path("/models") / assistant.assistant_type / assistant.name
    shutil.rmtree(save_path, ignore_errors=True)
    assistant.delete()
    return {"message": "Model deleted successfully"}


@router.get("/dummies")
async def get_dummy_assistants():
    """
    Get all dummy models.
    """
    return [
        {
            "name": "dummy1",
            "assistant_type": "sam2",
            "parameters": {"ckpt_path": "dummy1.ckpt"},
        },
        {
            "name": "dummy2",
            "assistant_type": "zim",
            "parameters": {"checkpoint": "dummy2"},
        },
    ]


@router.post("/zim")
async def zim_segmentation(
    request: AsForm[ZimSegmentationRequest],
) -> SegmentationResult:
    """
    Perform segmentation with a ZIM model.
    """
    if request.assistant_name == "zim":
        # Use default config
        config = ZIMConfig()
    else:
        matching_config = AssistantDBModel.objects(
            name=request.assistant_name, assistant_type="zim"
        ).first()
        config = ZIMConfig(**matching_config.parameters)
    return run_segmentation(
        config,
        request.image.file,
        foreground_xy=request.foreground_xy,
        **request.parameters.model_dump(),
    )


@router.post("/sam2")
async def sam2_segmentation(
    request: AsForm[SAM2SegmentationRequest],
) -> SegmentationResult:
    """
    Perform segmentation with a SAM2 model.
    """
    if request.assistant_name == "sam2":
        # Use default config
        config = SAM2Config()
    else:
        matching_config = AssistantDBModel.objects(
            name=request.assistant_name, assistant_type="sam2"
        ).first()
        config = SAM2Config(**matching_config.parameters)
    return run_segmentation(
        config,
        request.image.file,
        foreground_xy=request.foreground_xy,
        **request.parameters.model_dump(),
    )


# Include the router in the FastAPI app
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=6001)
