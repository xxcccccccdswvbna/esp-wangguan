import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import light
# 【修正】导入 CONF_OUTPUT_ID
from esphome.const import CONF_OUTPUT_ID

DEPENDENCIES = ["ble_gateway"]

ble_light_ns = cg.esphome_ns.namespace("ble_light")
ble_gateway_ns = cg.esphome_ns.namespace("ble_gateway")

BLELight = ble_light_ns.class_("BLELight", light.LightOutput)
BLEGateway = ble_gateway_ns.class_("BLEGateway", cg.Component)

CONF_BLE_DEVICE_ID = "ble_device_id"
CONF_GATEWAY = "gateway"

CONFIG_SCHEMA = light.LIGHT_SCHEMA.extend({
    # 【关键修正】必须在这里显式声明 CONF_OUTPUT_ID，并绑定到 BLELight 类
    # 这样 ESPHome 就会自动为 LightOutput 生成一个不冲突的内部 ID (如 xxx_output)
    cv.GenerateID(CONF_OUTPUT_ID): cv.declare_id(BLELight),
    
    cv.Required(CONF_BLE_DEVICE_ID): cv.string,
    cv.Required(CONF_GATEWAY): cv.use_id(BLEGateway),
})

async def to_code(config):
    # 现在 config 里就有 CONF_OUTPUT_ID 了
    var = cg.new_Pvariable(config[CONF_OUTPUT_ID])
    
    # 注册为 Light 实体 (这会自动处理你在 YAML 里写的 id，分配给 LightState)
    await light.register_light(var, config)

    # 注入依赖
    gateway_var = await cg.get_variable(config[CONF_GATEWAY])
    cg.add(var.set_gateway(gateway_var))
    cg.add(var.set_device_id(config[CONF_BLE_DEVICE_ID]))
