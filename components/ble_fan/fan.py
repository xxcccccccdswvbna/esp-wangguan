import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import fan
from esphome.const import CONF_ID

DEPENDENCIES = ["ble_gateway"]

ns = cg.esphome_ns.namespace("ble_fan")
gw_ns = cg.esphome_ns.namespace("ble_gateway")

BLEFan = ns.class_("BLEFan", cg.Component, fan.Fan)
BLEGateway = gw_ns.class_("BLEGateway", cg.Component)

CONF_BLE_DEVICE_ID = "ble_device_id"
CONF_GATEWAY = "gateway"

CONFIG_SCHEMA = fan.fan_schema(BLEFan).extend({
    cv.Required(CONF_BLE_DEVICE_ID): cv.string,
    cv.Required(CONF_GATEWAY): cv.use_id(BLEGateway),
}).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    var = await fan.new_fan(config)
    await cg.register_component(var, config)
    gw = await cg.get_variable(config[CONF_GATEWAY])
    cg.add(var.set_gateway(gw))
    cg.add(var.set_device_id(config[CONF_BLE_DEVICE_ID]))
