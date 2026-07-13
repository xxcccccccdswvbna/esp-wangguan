import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import fan
from esphome.const import CONF_OUTPUT_ID, CONF_NAME, CONF_ID

DEPENDENCIES = ["ble_gateway"]

ble_fan_ns = cg.esphome_ns.namespace("ble_fan")
ble_gateway_ns = cg.esphome_ns.namespace("ble_gateway")

# 声明 C++ 类
BLEFan = ble_fan_ns.class_("BLEFan", cg.Component, fan.Fan)
BLEGateway = ble_gateway_ns.class_("BLEGateway", cg.Component)

CONF_BLE_DEVICE_ID = "ble_device_id"
CONF_GATEWAY = "gateway"

# 【修正】不再使用 fan.FAN_SCHEMA，直接使用 cv.Schema 并包含 fan 必须的字段
CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(CONF_OUTPUT_ID): cv.declare_id(BLEFan),
    cv.Required(CONF_NAME): cv.string,
    cv.Required(CONF_BLE_DEVICE_ID): cv.string,
    cv.Required(CONF_GATEWAY): cv.use_id(BLEGateway),
}).extend(cv.COMPONENT_SCHEMA)

async def to_code(config):
    # 实例化 BLEFan 对象
    var = cg.new_Pvariable(config[CONF_OUTPUT_ID])
    
    # 注册为 Component
    await cg.register_component(var, config)
    
    # 注册为 Fan 实体 (这会自动处理 HA 的实体注册)
    await fan.register_fan(var, config)

    # 注入依赖
    gateway_var = await cg.get_variable(config[CONF_GATEWAY])
    cg.add(var.set_gateway(gateway_var))
    cg.add(var.set_device_id(config[CONF_BLE_DEVICE_ID]))
