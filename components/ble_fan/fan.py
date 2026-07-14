import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import fan
from esphome.const import CONF_ID, CONF_RESTORE_MODE

DEPENDENCIES = ["ble_gateway"]

ble_fan_ns = cg.esphome_ns.namespace("ble_fan")
ble_gateway_ns = cg.esphome_ns.namespace("ble_gateway")
fan_ns = cg.esphome_ns.namespace("fan")

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

_DEFAULT_RESTORE = "RESTORE_DEFAULT_OFF"

CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(BLEFan),
    cv.Required(CONF_BLE_DEVICE_ID): cv.string,
    cv.Required(CONF_
