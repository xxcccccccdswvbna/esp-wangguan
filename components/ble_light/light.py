import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import light
# 【修正】导入 CONF_OUTPUT_ID 而不是 CONF_ID
from esphome.const import CONF_OUTPUT_ID

DEPENDENCIES = ["ble_gateway"]

ble_light_ns = cg.esphome_ns.namespace("ble_light")
ble_gateway_ns = cg.esphome_ns.namespace("ble_gateway")

BLELight = ble_light_ns.class_("BLELight", light.LightOutput)
BLEGateway = ble_gateway_ns.class_("BLEGateway", cg.Component)

CONF_BLE_DEVICE_ID = "ble_device_id"
CONF_GATEWAY = "gateway"

# 【修正】移除手动 extend CONF_ID，light.LIGHT_SCHEMA 内部已经处理好了
CONFIG_SCHEMA = light.LIGHT_SCHEMA.extend({
    cv.Required(CONF_BLE_DEVICE_ID): cv.string,
    cv.Required(CONF_GATEWAY): cv.use_id(BLEGateway),
})

async def to_code(config):
    # 【关键修正】使用 CONF_OUTPUT_ID 来实例化 LightOutput，避免与 LightState 的 ID 冲突
    var = cg.new_Pvariable(config[CONF_OUTPUT_ID])
    
    # 注册为 Light 实体
    await light.register_light(var, config)

    # 注入依赖
    gateway_var = await cg.get_variable(config[CONF_GATEWAY])
    cg.add(var.set_gateway(gateway_var))
    cg.add(var.set_device_id(config[CONF_BLE_DEVICE_ID]))
