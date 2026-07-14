#include "device_table.h"
#include <utility> // for std::move

namespace esphome {
namespace ble_gateway {

void DeviceTable::load(std::vector<BLEDevice> &devices) {
    // 👇 以下内容完全由 Python 脚本 (generate_device_table.py) 自动生成 👇
    add_device(devices, "light.diningroom", "light", "Diningroom Light");
    add_action(devices, "light.diningroom", "on", {
        "0201021BFF114D191048802770000001C96FBE4848A7F08080972727707008",
        "0201021BFF114D191048802770000001C96FB84848A7F08080972727707002"
    });
    add_action(devices, "light.diningroom", "off", {
        "0201021BFF114D191A4880277000000126277670005FC86FB84848A7F08088",
        "0201021BFF114D1911488027700000016EB84848A7F080809727277070005D"
    });
    // ... (此处省略其他 brightness/color 动作，由 Python 自动填充) ...

    add_device(devices, "fan.diningroom", "fan", "Diningroom Fan");
    add_action(devices, "fan.diningroom", "on", {
        "0201021BFF114D19194880277000000196272E7070005FC86FB84848A7F08B",
        "0201021BFF114D191E48802770000001015FC86FB84848A7F0808097272772"
    });
    // ... (此处省略其他 fan 动作，由 Python 自动填充) ...
    // 👆 以上内容完全由 Python 脚本自动生成 👆
}

void DeviceTable::add_device(std::vector<BLEDevice> &devices,
                             const std::string &id,
                             const std::string &type,
                             const std::string &name) {
    BLEDevice device;
    device.id = id;
    device.type = type;
    device.name = name;
    // 使用 std::move 避免对象拷贝
    devices.push_back(std::move(device));
}

void DeviceTable::add_action(std::vector<BLEDevice> &devices,
                             const std::string &device_id,
                             const std::string &action,
                             std::vector<std::string> packets) {
    for (auto &device : devices) {
        if (device.id == device_id) {
            BLEAction act;
            act.name = action;
            // 使用 std::move 高效转移 vector 的所有权，避免深拷贝
            act.packets = std::move(packets);
            device.actions.emplace(action, std::move(act));
            return;
        }
    }
}

}  // namespace ble_gateway
}  // namespace esphome
