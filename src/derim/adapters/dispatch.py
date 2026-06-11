"""
Control-command dispatch service.

Given a registered device and a command, this resolves the device's protocol
adapter, connects to the device, writes the command, and disconnects. The
real adapter result is returned. If the device has no usable adapter, the
command is **rejected** (not silently accepted); if the device cannot be
reached, an honest **error** response is returned with the underlying cause.
"""

from __future__ import annotations

from derim.adapters.registry import SUPPORTED_PROTOCOLS, get_adapter_class
from derim.models.common import CommandRequest, CommandResponse, DERDevice
from derim.utils.logger import get_logger

logger = get_logger(__name__)


async def dispatch_command(
    device: DERDevice, command: CommandRequest
) -> CommandResponse:
    """
    Dispatch ``command`` to ``device`` via its protocol adapter.

    Connection parameters are taken from ``device.metadata`` (e.g. ``host``,
    ``port``, ``unit_id`` for Modbus) and passed to the adapter constructor.
    """
    adapter_cls = get_adapter_class(device.protocol)
    if adapter_cls is None:
        logger.warning(
            "control_no_adapter",
            device_id=device.device_id,
            protocol=device.protocol,
        )
        return CommandResponse(
            device_id=device.device_id,
            command=command.command,
            status="rejected",
            message=(
                f"No protocol adapter configured for device "
                f"'{device.device_id}' (protocol: {device.protocol or 'none'}). "
                f"Supported protocols: {', '.join(SUPPORTED_PROTOCOLS)}."
            ),
        )

    config = dict(device.metadata or {})
    adapter = adapter_cls(device.device_id, config)

    try:
        await adapter.connect()
    except Exception as exc:
        logger.error(
            "control_connect_failed",
            device_id=device.device_id,
            protocol=device.protocol,
            error=str(exc),
        )
        return CommandResponse(
            device_id=device.device_id,
            command=command.command,
            status="error",
            message=(
                f"Could not reach device '{device.device_id}' via "
                f"{device.protocol}: {exc}"
            ),
        )

    try:
        response = await adapter.write_command(command)
        logger.info(
            "control_command_dispatched",
            device_id=device.device_id,
            command=command.command,
            value=command.value,
            protocol=device.protocol,
            status=response.status,
        )
        return response
    except Exception as exc:
        logger.error(
            "control_write_failed",
            device_id=device.device_id,
            protocol=device.protocol,
            error=str(exc),
        )
        return CommandResponse(
            device_id=device.device_id,
            command=command.command,
            status="error",
            message=f"Command write failed on device '{device.device_id}': {exc}",
        )
    finally:
        try:
            await adapter.disconnect()
        except Exception:
            logger.warning("control_disconnect_failed", device_id=device.device_id)
