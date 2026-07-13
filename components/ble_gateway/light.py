import esphome.codegen as cg
import esphome.config_validation as cv

from esphome.components import light

from . import ble_gateway_ns


BLELight = ble_gateway_ns.class_(
    "BLELight",
    light.LightOutput
)


CONF_DEVICE = "device"


CONFIG_SCHEMA = light.light_schema(
    BLELight
).extend(
    {
        cv.Required(CONF_DEVICE): cv.string,
    }
)


async def to_code(config):

    var = cg.new_Pvariable(
        config[cv.GenerateID()]
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
