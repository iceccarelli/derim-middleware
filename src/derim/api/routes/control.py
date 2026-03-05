"""
Device control API routes.

Endpoints
---------
- ``POST /control/{device_id}`` - Send a control command to a DER device.

Control commands are dispatched to the appropriate protocol adapter
based on the device's registered protocol.  If no adapter is available,
the command is acknowledged but logged as undeliverable.
"""

from fastapi import APIRouter, Depends, HTTPException

from derim.api.dependencies import get_storage
from derim.models.common import CommandRequest, CommandResponse
from derim.storage.base import StorageBackend
from derim.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/control/{device_id}",
    response_model=CommandResponse,
    summary="Send a control command to a DER device",
    description=(
        "Dispatch a control command (e.g. setpoint, on/off, charge, "
        "discharge) to the specified device.  The middleware routes the "
        "command to the appropriate protocol adapter.\n\n"
        "**Supported commands** (device-dependent):\n"
        "- ``setpoint`` - Set active power output (kW).\n"
        "- ``on`` / ``off`` - Enable or disable the device.\n"
        "- ``charge`` / ``discharge`` - Battery charge/discharge mode.\n"
        "- ``start`` / ``stop`` - Start or stop an EV charging session.\n\n"
        "The ``value`` field carries a numeric parameter when applicable "
        "(e.g. power setpoint in kW).  Additional parameters can be "
        "passed in the ``parameters`` dictionary."
    ),
)
async def send_command(
    device_id: str,
    command: CommandRequest,
    storage: StorageBackend = Depends(get_storage),
) -> CommandResponse:
    """
    Process and dispatch a control command.

    In a production deployment, this handler would look up the device's
    registered protocol adapter and call ``adapter.write_command()``.
    For the current release, the command is validated, logged, and
    acknowledged.  Adapter routing will be added in a future version.
    """
    # Verify that the device exists.
    device = await storage.get_device(device_id)
    if device is None:
        raise HTTPException(
            status_code=404,
            detail=f"Device '{device_id}' not found. Register it first.",
        )

    # Validate command type.
    valid_commands = {
        "setpoint",
        "on",
        "off",
        "charge",
        "discharge",
        "start",
        "stop",
    }
    if command.command not in valid_commands:
        logger.warning(
            "api_unknown_command",
            device_id=device_id,
            command=command.command,
        )
        return CommandResponse(
            device_id=device_id,
            command=command.command,
            status="rejected",
            message=(
                f"Unknown command '{command.command}'. "
                f"Valid commands: {', '.join(sorted(valid_commands))}"
            ),
        )

    # TODO: Route to the actual protocol adapter based on device.protocol.
    # For now, we acknowledge the command and log it.
    logger.info(
        "api_command_dispatched",
        device_id=device_id,
        command=command.command,
        value=command.value,
        protocol=device.protocol,
    )

    return CommandResponse(
        device_id=device_id,
        command=command.command,
        status="accepted",
        message=(
            f"Command '{command.command}' accepted for device "
            f"'{device_id}' (protocol: {device.protocol or 'N/A'}). "
            "Adapter dispatch pending."
        ),
    )
