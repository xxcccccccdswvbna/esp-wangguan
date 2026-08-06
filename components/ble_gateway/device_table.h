#pragma once

#include "device_model.h"
#include <string>
#include <vector>

namespace esphome {
namespace ble_gateway {

class DeviceTable {
public:
    void load(std::vector<BLEDevice> &devices);

private:
    static void add_device(std::vector<BLEDevice> &devices,
                           const std::string &id,
                           const std::string &type,
                           const std::string &name,
                           const std::string &mac,
                           const std::string &protocol);

    static void add_action(std::vector<BLEDevice> &devices,
                           const std::string &device_id,
                           const std::string &action,
                           std::vector<std::string> packets);
};

}  // namespace ble_gateway
}  // namespace esphome
