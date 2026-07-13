import esphome.codegen as cg
import esphome.config_validation as cv


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
        cv.GenerateID(): cv.declare_id(
            BLEGateway
        ),
    }
)
