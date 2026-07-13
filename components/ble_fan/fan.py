import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import fan
from esphome.const import CONF_ID, CONF_NAME, CONF_RESTORE_MODE

DEPENDENCIES = ["ble_gateway"]

ble_fan_ns = cg.esphome_ns.namespace("ble_fan")
ble_gateway_ns = cg.esphome_ns.namespace("ble_gateway")
fan_ns = cg.esphome_ns.namespace("fan")

# 【关键】声明继承 cg.Component 和 fan.Fan，与 C++ 端完全对齐
BLEFan = ble_fan_ns.class_("BLEFan", cg.Component, fan.Fan)
BLEGateway = ble_gateway_ns.class_("BLEGateway", cg.Component)

CONF_BLE_DEVICE_ID = "ble_device_id"
CONF_GATEWAY = "gateway"

FanRestoreMode = fan_ns.namespace("FanRestoreMode")

RESTORE_MODES = {
    "NO_RESTORE": FanRestoreMode.NO_RESTORE,
    "RESTORE_DEFAULT_OFF": FanRestoreMode.RESTORE_DEFAULT_OFF,
    "RESTORE_DEFAULT_ON": FanRestoreMode.RESTORE_DEFAULT_ON,
    "RESTORE_INVERTED_DEFAULT_OFF": FanRestoreMode.RESTORE_INVERTED_DEFAULT_OFF,
    "RESTORE_INVERTED_DEFAULT_ON": FanRestoreMode.RESTORE_INVERTED_DEFAULT_ON,
    "ALWAYS_OFF": FanRestoreMode.ALWAYS_OFF,
    "ALWAYS_ON": FanRestoreMode.ALWAYS_ON,
}

CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(BLEFan),
    cv.Required(CONF_NAME): cv.string,
    cv.Required(CONF_BLE_DEVICE_ID): cv.string,
    cv.Required(CONF_GATEWAY): cv.use_id(BLEGateway),
    cv.Optional(CONF_RESTORE_MODE, default="RESTORE_DEFAULT_OFF"): cv.enum(RESTORE_MODES, upper=True, space="UNDERSCORE"),
}).extend(cv.COMPONENT_SCHEMA).extend(cv.ENTITY_BASE_SCHEMA)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    
    # 【关键】注册为 Component，确保 ESPHome 能正确调用 setup/loop
    await cg.register_component(var, config)
    await fan.register_fan(var, config)

    gateway_var = await cg.get_variable(config[CONF_GATEWAY])
    cg.add(var.set_gateway(gateway_var))
    cg.add(var.set_device_id(config[CONF_BLE_DEVICE_ID]))
