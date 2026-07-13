import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import fan
# 【修正】使用 CONF_ID 而不是 CONF_OUTPUT_ID
from esphome.const import CONF_ID

DEPENDENCIES = ["ble_gateway"]

ble_fan_ns = cg.esphome_ns.namespace("ble_fan")
ble_gateway_ns = cg.esphome_ns.namespace("ble_gateway")

# BLEFan 继承自 fan::Fan (即 FanState)，所以直接绑定到 CONF_ID
BLEFan = ble_fan_ns.class_("BLEFan", cg.Component, fan.Fan)
BLEGateway = ble_gateway_ns.class_("BLEGateway", cg.Component)

CONF_BLE_DEVICE_ID = "ble_device_id"
CONF_GATEWAY = "gateway"

# 【修正】使用 cv.GenerateID() 生成 CONF_ID，满足 fan.register_fan 的要求
CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(BLEFan),
    cv.Required(CONF_NAME): cv.string,
    cv.Required(CONF_BLE_DEVICE_ID): cv.string,
    cv.Required(CONF_GATEWAY): cv.use_id(BLEGateway),
}).extend(cv.COMPONENT_SCHEMA)

async def to_code(config):
    # 【修正】使用 config[CONF_ID] 实例化 BLEFan
    var = cg.new_Pvariable(config[CONF_ID])
    
    # 注册为 Component
    await cg.register_component(var, config)
    
    # 注册为 Fan 实体 (此时 config 中已有 CONF_ID，不会报 KeyError)
    await fan.register_fan(var, config)

    # 注入依赖
    gateway_var = await cg.get_variable(config[CONF_GATEWAY])
    cg.add(var.set_gateway(gateway_var))
    cg.add(var.set_device_id(config[CONF_BLE_DEVICE_ID]))
