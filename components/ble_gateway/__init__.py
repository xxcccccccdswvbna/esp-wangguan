import esphome.codegen as cg


ble_gateway_ns = cg.esphome_ns.namespace(
    "ble_gateway"
)


BLEGateway = ble_gateway_ns.class_(
    "BLEGateway",
    cg.Component
)
