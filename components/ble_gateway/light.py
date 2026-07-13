import esphome.codegen as cg
import esphome.config_validation as cv

from esphome.components import light
from esphome.const import CONF_ID

from . import ble_gateway_ns, BLEGateway


BLELight = ble_gateway_ns.class_(
    "BLELight",
    light.LightOutput
)


CONF_DEVICE = "device"
CONF_GATEWAY_ID = "gateway_id"


CONFIG_SCHEMA = light.LIGHT_SCHEMA.extend(
    {
        cv.GenerateID(): cv.declare_id(BLELight),

        cv.Required(CONF_DEVICE): cv.string,

        cv.Required(CONF_GATEWAY_ID): cv.use_id(
            BLEGateway
        ),
    }
)


async def to_code(config):

    var = cg.new_Pvariable(
        config[CONF_ID]
    )


    await light.register_light(
        var,
        config
    )


    cg.add(
        var.set_device(
            config[CONF_DEVICE]
        )
    )


    gateway = await cg.get_variable(
        config[CONF_GATEWAY_ID]
    )


    cg.add(
        var.set_gateway(
            gateway
        )
    )
