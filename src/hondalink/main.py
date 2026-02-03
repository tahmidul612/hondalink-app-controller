import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel

from .config import settings
from .controller import HondaLinkController, HondaLinkException
from .driver_impl import UiautomatorDriver
from .driver_mock import MockDriver
from .models import CommandType, VehicleStatus
from .security import (
    audit_logger,
    check_api_rate_limit,
    check_command_rate_limit,
    get_client_ip,
    verify_api_key,
    verify_ip_whitelist,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

controller: HondaLinkController | None = None
lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global controller
    if settings.use_mock_driver:
        logger.info("Using MOCK driver")
        driver = MockDriver()
        driver.connect()
        driver.register_element("text=Remote Commands")
        driver.register_element("text=Refresh")
        driver.register_element("text=Start")
        driver.register_element("text=Stop")
        driver.register_element("text=Lock")
        driver.register_element("text=Unlock")
        driver.register_element("text=Locked")
    else:
        logger.info("Using REAL driver")
        driver = UiautomatorDriver()

    controller = HondaLinkController(driver)
    try:
        controller.connect()
    except Exception as e:
        logger.error(f"Failed to connect on startup: {e}")

    yield

    if controller and not settings.use_mock_driver:
        try:
            logger.info("Shutting down: stopping HondaLink app")
            controller.driver.app_stop(settings.hondalink_package)
        except Exception as e:
            logger.error(f"Error stopping app on shutdown: {e}")


app = FastAPI(title="HondaLink Controller", lifespan=lifespan)


class ActionResponse(BaseModel):
    status: str
    message: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/debug/hierarchy", dependencies=[Depends(verify_ip_whitelist)])
async def get_hierarchy(
    request: Request,
    _api_key: Annotated[str, Depends(verify_api_key)],
):
    if not controller:
        raise HTTPException(status_code=500, detail="Controller not initialized")

    client_ip = get_client_ip(request)
    audit_logger.log_event(
        event_type="debug_hierarchy_access",
        client_ip=client_ip,
        details={"endpoint": "/debug/hierarchy"},
    )

    async with lock:
        xml = await asyncio.to_thread(controller.get_xml_hierarchy)
        return Response(content=xml, media_type="application/xml")


@app.get(
    "/status",
    response_model=VehicleStatus,
    dependencies=[
        Depends(verify_ip_whitelist),
        Depends(check_api_rate_limit),
    ],
)
async def get_status(
    request: Request,
    _api_key: Annotated[str, Depends(verify_api_key)],
):
    if not controller:
        raise HTTPException(status_code=500, detail="Controller not initialized")

    client_ip = get_client_ip(request)
    audit_logger.log_event(
        event_type="status_check",
        client_ip=client_ip,
        details={"endpoint": "/status"},
    )

    async with lock:
        try:
            return await asyncio.to_thread(controller.get_status)
        except HondaLinkException as e:
            logger.exception("Error getting status")
            audit_logger.log_event(
                event_type="status_check_failed",
                client_ip=client_ip,
                details={"error": str(e)},
            )
            raise HTTPException(status_code=500, detail=str(e)) from e


@app.post(
    "/action/{command}",
    response_model=ActionResponse,
    dependencies=[
        Depends(verify_ip_whitelist),
        Depends(check_command_rate_limit),
    ],
)
async def execute_command(
    command: CommandType,
    request: Request,
    _api_key: Annotated[str, Depends(verify_api_key)],
):
    if not controller:
        raise HTTPException(status_code=500, detail="Controller not initialized")

    client_ip = get_client_ip(request)
    audit_logger.log_event(
        event_type="vehicle_command",
        client_ip=client_ip,
        details={"command": command.value, "endpoint": f"/action/{command}"},
    )

    async with lock:
        try:
            await asyncio.to_thread(controller.execute_remote_command, command)
            audit_logger.log_event(
                event_type="vehicle_command_success",
                client_ip=client_ip,
                details={"command": command.value},
            )
            return ActionResponse(
                status="success", message=f"Command {command} executed successfully"
            )
        except HondaLinkException as e:
            logger.exception(f"Error executing command {command}")
            audit_logger.log_event(
                event_type="vehicle_command_failed",
                client_ip=client_ip,
                details={"command": command.value, "error": str(e)},
            )
            raise HTTPException(status_code=500, detail=str(e)) from e
