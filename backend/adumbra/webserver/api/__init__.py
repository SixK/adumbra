from flask import Blueprint
from flask_restx import Api

from adumbra.config import CONFIG
from adumbra.webserver.api.admin import api as ns_admin
from adumbra.webserver.api.annotations import api as ns_annotations
from adumbra.webserver.api.annotator import api as ns_annotator
from adumbra.webserver.api.categories import api as ns_categories
from adumbra.webserver.api.datasets import api as ns_datasets
from adumbra.webserver.api.exports import api as ns_exports
from adumbra.webserver.api.images import api as ns_images
from adumbra.webserver.api.info import api as ns_info
from adumbra.webserver.api.tasks import api as ns_tasks
from adumbra.webserver.api.undo import api as ns_undo

# from adumbra.webserver.api.models import api as ns_models
from adumbra.webserver.api.users import api as ns_users

# Create /api/ space
blueprint = Blueprint("api", __name__, url_prefix="/api")

api = Api(
    blueprint,
    title=CONFIG.name,
    version=CONFIG.version,
)

# Remove default namespace
api.namespaces.pop(0)

# Setup API namespaces
api.add_namespace(ns_info)
api.add_namespace(ns_users)
api.add_namespace(ns_images)
api.add_namespace(ns_annotations)
api.add_namespace(ns_categories)
api.add_namespace(ns_datasets)
api.add_namespace(ns_exports)
api.add_namespace(ns_tasks)
api.add_namespace(ns_undo)
# api.add_namespace(ns_models)
api.add_namespace(ns_admin)
api.add_namespace(ns_annotator)
