import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import light
from esphome.const import CONF_ID

# 声明依赖 ble_gateway 组件
DEPENDENCIES = ["ble_gateway"]

# 获取命名空间
ble_light_ns = cg.esphome_ns.namespace("ble_light")
ble_gateway_ns = cg.esphome_ns.namespace("ble_gateway")

# 声明 C++ 类
BLELight = ble_light_ns.class_("BLELight", cg.Component, light.LightOutput)
BLEGateway = ble_gateway_ns.class_("BLEGateway", cg.Component)

# 【修改】使用自定义名称避免与 ESPHome 内部保留字冲突
CONF_BLE_DEVICE_ID = "ble_device_id"
CONF_GATEWAY = "gateway"

# 【修改】优化 Schema 定义，确保 ID 类型正确推断
CONFIG_SCHEMA = light.LIGHT_SCHEMA.extend({
    cv.GenerateID(): cv.declare_id(BLELight),
    cv.Required(CONF_BLE_DEVICE_ID): cv.string,
    cv.Required(CONF_GATEWAY): cv.use_id(BLEGateway),
}).extend(cv.COMPONENT_SCHEMA)

# 代码生成逻辑
async def to_code(config):
    # 实例化 BLELight 对象
    var = cg.new_Pvariable(config[CONF_ID])
    
    # 注册为 ESPHome 组件和 Light 实体
    await cg.register_component(var, config)
    await light.register_light(var, config)

    # 注入 gateway 指针
    gateway_var = await cg.get_variable(config[CONF_GATEWAY])
    cg.add(var.set_gateway(gateway_var))

    # 注入 ble_device_id 字符串
    cg.add(var.set_device_id(config[CONF_BLE_DEVICE_ID]))
