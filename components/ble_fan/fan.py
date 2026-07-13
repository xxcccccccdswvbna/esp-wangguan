import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import fan
from esphome.const import CONF_ID, CONF_NAME, CONF_RESTORE_MODE

DEPENDENCIES = ["ble_gateway"]

ble_fan_ns = cg.esphome_ns.namespace("ble_fan")
ble_gateway_ns = cg.esphome_ns.namespace("ble_gateway")
fan_ns = cg.esphome_ns.namespace("fan")

BLEFan = ble_fan_ns.class_("BLEFan", cg.Component, fan.Fan)
BLEGateway = ble_gateway_ns.class_("BLEGateway", cg.Component)

CONF_BLE_DEVICE_ID = "ble_device_id"
CONF_GATEWAY = "gateway"

# 【终极修正】将 FanRestoreMode 声明为 namespace (命名空间)
# 这样代码生成器在访问其内部的枚举值时，会强制使用 C++ 的 :: 作用域解析符
# 从而完美生成 fan::FanRestoreMode::RESTORE_DEFAULT_OFF
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
    
    await cg.register_component(var, config)
    await fan.register_fan(var, config)

    gateway_var = await cg.get_variable(config[CONF_GATEWAY])
    cg.add(var.set_gateway(gateway_var))
    cg.add(var.set_device_id(config[CONF_BLE_DEVICE_ID]))
