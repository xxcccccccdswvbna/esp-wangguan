#include "device_table.h"

namespace esphome {
namespace ble_gateway {

void DeviceTable::load(std::vector<BLEDevice> &devices) {

    add_device(devices, "light.diningroom", "light", "Diningroom Light");
    add_action(devices, "light.diningroom", "on", {
        "0201021BFF114D191048802770000001C96FBE4848A7F08080972727707008",
        "0201021BFF114D191048802770000001C96FB84848A7F08080972727707002"
    });
    add_action(devices, "light.diningroom", "off", {
        "0201021BFF114D191A4880277000000126277670005FC86FB84848A7F08088",
        "0201021BFF114D1911488027700000016EB84848A7F080809727277070005D"
    });
    add_action(devices, "light.diningroom", "brightness_1", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "light.diningroom", "brightness_20", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "light.diningroom", "brightness_40", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "light.diningroom", "brightness_50", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "light.diningroom", "brightness_60", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "light.diningroom", "brightness_80", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "light.diningroom", "brightness_100", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "light.diningroom", "color_2700", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "light.diningroom", "color_3500", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "light.diningroom", "color_6500", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });

    add_device(devices, "fan.diningroom", "fan", "Diningroom Fan");
    add_action(devices, "fan.diningroom", "on", {
        "0201021BFF114D19194880277000000196272E7070005FC86FB84848A7F08B",
        "0201021BFF114D191E48802770000001015FC86FB84848A7F0808097272772"
    });
    add_action(devices, "fan.diningroom", "off", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "fan.diningroom", "speed_1", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "fan.diningroom", "speed_2", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "fan.diningroom", "speed_3", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "fan.diningroom", "speed_4", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "fan.diningroom", "speed_5", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "fan.diningroom", "speed_6", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "fan.diningroom", "forward", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });
    add_action(devices, "fan.diningroom", "reverse", {
        "替换为真实HEX_1",
        "替换为真实HEX_2"
    });

}
void DeviceTable::add_device(std::vector<BLEDevice> &devices, std::string id, std::string type, std::string name) {
    BLEDevice device; device.id = id; device.type = type; device.name = name; devices.push_back(device);
}
void DeviceTable::add_action(std::vector<BLEDevice> &devices, std::string device_id, std::string action, std::vector<std::string> packets) {
    for (auto &device : devices) {
        if (device.id == device_id) {
            BLEAction act; act.name = action; act.packets = packets; device.actions[action] = act; return;
        }
    }
}
} // namespace ble_gateway
} // namespace esphome
