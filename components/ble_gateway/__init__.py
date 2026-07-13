import esphome.codegen as cg
import esphome.config_validation as cv

from esphome.core import CORE
from esphome.const import CONF_ID

from esphome.components import esp32


DEPENDENCIES = [
    "esp32_ble_tracker"
]


ble_gateway_ns = cg.esphome_ns.namespace(
    "ble_gateway"
)


BLEGateway = ble_gateway_ns.class_(
    "BLEGateway",
    cg.Component
)


CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(BLEGateway),
    }
)
