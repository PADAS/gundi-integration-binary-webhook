import json
import datetime
import logging

import stamina
import httpx

from app.actions import action_handlers, AuthActionConfiguration, PullActionConfiguration, PushActionConfiguration
from app.settings.integration import INTEGRATION_TYPE_SLUG
from .core import ActionTypeEnum


logger = logging.getLogger(__name__)


async def register_integration_in_gundi(gundi_client, type_slug=None, service_url=None):
    # Prepare the integration name and value
    integration_type_slug = type_slug or INTEGRATION_TYPE_SLUG
    if not integration_type_slug:
        raise ValueError("Please define a slug id for this integration type, either passing it in the type_slug argument or setting it in the INTEGRATION_TYPE_SLUG setting.")
    integration_type_slug = integration_type_slug.strip().lower()
    integration_type_name = integration_type_slug.replace("_", " ").title()
    logger.info(f"Registering integration type '{integration_type_slug}'...")
    data = {
        "name": integration_type_name,
        "value": integration_type_slug,
        "description": f"Default type for integrations with {integration_type_name}",
    }
    if service_url:
        logger.info(f"Registering '{integration_type_slug}' with service_url: '{service_url}'")
        data["service_url"] = service_url
    # Prepare the actions and schemas
    actions = []
    for action_id, handler in action_handlers.items():
        _, config_model = handler
        action_name = action_id.replace("_", " ").title()
        action_schema = json.loads(config_model.schema_json())
        if issubclass(config_model, AuthActionConfiguration):
            action_type = ActionTypeEnum.AUTHENTICATION.value
        elif issubclass(config_model, PullActionConfiguration):
            action_type = ActionTypeEnum.PULL_DATA.value
        elif issubclass(config_model, PushActionConfiguration):
            action_type = ActionTypeEnum.PUSH_DATA.value
        else:
            action_type = ActionTypeEnum.GENERIC.value
        actions.append(
            {
                "type": action_type,
                "name": action_name,
                "value": action_id,
                "description": f"{integration_type_name} {action_name} action",
                "schema": action_schema,
                "is_periodic_action": True if issubclass(config_model, PullActionConfiguration) else False,
            }
        )
    data["actions"] = actions
    logger.info(f"Registering '{integration_type_slug}' with actions: '{actions}'")
    # Register the integration type and actions in Gundi
    async for attempt in stamina.retry_context(on=httpx.HTTPError, wait_initial=datetime.timedelta(seconds=1),attempts=3):
        with attempt:
            response = await gundi_client.register_integration_type(data)
    logger.info(f"Registering integration type '{integration_type_slug}'...DONE")
    return response
