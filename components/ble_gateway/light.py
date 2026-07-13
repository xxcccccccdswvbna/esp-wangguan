import esphome.codegen as cg
import esphome.config_validation as cv

from esphome.components import light


ble_gateway_ns = cg.esphome_ns.namespace(
    "ble_gateway"
)


BLELight = ble_gateway_ns.class_(
    "BLELight",
    light.LightOutput
)


CONF_DEVICE = "device"


CONFIG_SCHEMA = light.LIGHT_SCHEMA.extend(
    {
        cv.Required(CONF_DEVICE): cv.string,
    }
)


async def to_code(config):

    var = cg.new_Pvariable(
        config[cv.GenerateID()]
    )


    cg.add(
        var.set_device(
            config[CONF_DEVICE]
        )
    )
