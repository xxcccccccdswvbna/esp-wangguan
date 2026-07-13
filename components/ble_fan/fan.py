import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import fan
# 【修正】在这里加上 CONF_NAME 的导入
from esphome.const import CONF_ID, CONF_NAME

DEPENDENCIES = ["ble_gateway"]

ble_fan_ns = cg.esphome_ns.namespace("ble_fan")
ble_gateway_ns = cg.esphome_ns.namespace("ble_gateway")

# BLEFan 继承自 fan::Fan (即 FanState)
BLEFan = ble_fan_ns.class_("BLEFan", cg.Component, fan.Fan)
BLEGateway = ble_gateway_ns.class_("BLEGateway", cg.Component)

CONF_BLE_DEVICE_ID = "ble_device_id"
CONF_GATEWAY = "gateway"

CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(BLEFan),
    cv.Required(CONF_NAME): cv.string,
    cv.Required(CONF_BLE_DEVICE_ID): cv.string,
    cv.Required(CONF_GATEWAY): cv.use_id(BLEGateway),
}).extend(cv.COMPONENT_SCHEMA)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    
    await cg.register_component(var, config)
    await fan.register_fan(var, config)

    gateway_var = await cg.get_variable(config[CONF_GATEWAY])
    cg.add(var.set_gateway(gateway_var))
    cg.add(var.set_device_id(config[CONF_BLE_DEVICE_ID]))
