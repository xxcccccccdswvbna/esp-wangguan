import esphome.codegen as cg
import esphome.config_validation as cv

from esphome.components import light

from esphome.const import (
    CONF_ID,
    CONF_NAME,
)

from . import ble_gateway_ns


BLELight = ble_gateway_ns.class_(
    "BLELight",
    cg.Component,
    light.LightOutput
)


CONF_DEVICE_ID = "device_id"


CONFIG_SCHEMA = light.LIGHT_SCHEMA.extend(
    {
        cv.Required(CONF_DEVICE_ID): cv.string,
    }
)


async def to_code(config):

    var = cg.new_Pvariable(
        config[CONF_ID],
        BLELight
    )


    await cg.register_component(
        var,
        config
    )


    await light.register_light(
        var,
        config
    )


    cg.add(
        var.set_device(
            config[CONF_DEVICE_ID]
        )
    )
