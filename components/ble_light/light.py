import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import light
from esphome.const import CONF_ID, CONF_OUTPUT_ID

DEPENDENCIES = ["ble_gateway"]

ble_light_ns = cg.esphome_ns.namespace("ble_light")
ble_gateway_ns = cg.esphome_ns.namespace("ble_gateway")

BLELight = ble_light_ns.class_("BLELight", cg.Component, light.LightOutput)
BLEGateway = ble_gateway_ns.class_("BLEGateway", cg.Component)

CONF_BLE_DEVICE_ID = "ble_device_id"
CONF_GATEWAY = "gateway"
# 【新增】专门用于在 lambda 中引用 LightOutput 的 ID
CONF_BLE_OUTPUT_ID = "ble_output_id"

CONFIG_SCHEMA = light.LIGHT_SCHEMA.extend({
    cv.GenerateID(CONF_OUTPUT_ID): cv.declare_id(BLELight),
    cv.Optional(CONF_BLE_OUTPUT_ID): cv.declare_id(BLELight), # 允许用户显式命名 output
    cv.Required(CONF_BLE_DEVICE_ID): cv.string,
    cv.Required(CONF_GATEWAY): cv.use_id(BLEGateway),
})

async def to_code(config):
    # 优先使用用户指定的 ble_output_id，如果没有，则使用 ESPHome 自动生成的 CONF_OUTPUT_ID
    out_id = config.get(CONF_BLE_OUTPUT_ID, config[CONF_OUTPUT_ID])
    var = cg.new_Pvariable(out_id)
    
    await cg.register_component(var, config)
    await light.register_light(var, config)

    gateway_var = await cg.get_variable(config[CONF_GATEWAY])
    cg.add(var.set_gateway(gateway_var))
    cg.add(var.set_device_id(config[CONF_BLE_DEVICE_ID]))
    
    # 将 LightState 指针传给 LightOutput，用于从 BLE 广播更新状态
    state_var = await cg.get_variable(config[CONF_ID])
    cg.add(var.set_state_parent(state_var))
