import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import fan
from esphome.const import CONF_ID, CONF_NAME, CONF_RESTORE_MODE

DEPENDENCIES = ["ble_gateway"]

ble_fan_ns = cg.esphome_ns.namespace("ble_fan")
ble_gateway_ns = cg.esphome_ns.namespace("ble_gateway")

BLEFan = ble_fan_ns.class_("BLEFan", cg.Component, fan.Fan)
BLEGateway = ble_gateway_ns.class_("BLEGateway", cg.Component)

CONF_BLE_DEVICE_ID = "ble_device_id"
CONF_GATEWAY = "gateway"

# 【终极修正】使用 global_ns 强制指定完整的 C++ 命名空间路径，杜绝任何 Python 变量名污染
# 这行代码明确告诉生成器：我要 C++ 里的 ::esphome::fan::FanRestoreMode 枚举
FanRestoreMode = cg.global_ns.namespace("esphome").namespace("fan").enum("FanRestoreMode")

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
    
    await cg.register_component(var, config)
    await fan.register_fan(var, config)

    gateway_var = await cg.get_variable(config[CONF_GATEWAY])
    cg.add(var.set_gateway(gateway_var))
    cg.add(var.set_device_id(config[CONF_BLE_DEVICE_ID]))
