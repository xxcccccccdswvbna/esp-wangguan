import esphome.codegen as cg
import esphome.config_validation as cv

from esphome.components import mqtt
from esphome.const import CONF_ID

DEPENDENCIES = ["esp32"]


ble_gateway_ns = cg.esphome_ns.namespace("ble_gateway")

BLEGateway = ble_gateway_ns.class_(
    "BLEGateway",
    cg.Component
)


CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(BLEGateway),
    }
)


async def to_code(config):

    var = cg.new_Pvariable(
        config[CONF_ID]
    )

    await cg.register_component(
        var,
        config
    )