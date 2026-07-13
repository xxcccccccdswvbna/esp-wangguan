#include "device_table.h"

namespace esphome {
namespace ble_gateway {

void DeviceTable::load(std::vector<BLEDevice> &devices) {

    /*
     * 添加设备
     */
    add_device(
        devices,
        "light.room1",
        "light",
        "卧室灯"
    );

    /*
     * 灯 开
     */
    add_action(
        devices,
        "light.room1",
        "on",
        {
            "0201021BFF114D1914F0CF2D70000001F1FC39CFCF9D2D2D7070005CBF1D68",
            "0201021BFF114D1911F0CF2D700000011C60F0F0FC3FCFCF9D2D2D7070005E"
        }
    );

    /*
     * 灯 关
     */
    add_action(
        devices,
        "light.room1",
        "off",
        {
            "0201021BFF114D191AF0CF2D700000012C2D7670005CBF1D60F0F0FC3FCFC7",
            "0201021BFF114D1912F0CF2D7000000161F0F0FC3FCFCF9D2D2D7070005CBD"
        }
    );

    /*
     * 亮度 1%
     */
    add_action(
        devices,
        "light.room1",
        "brightness_1",
        {
            "0201021BFF114D1912F0CF2D7000000161F1A1FE3FCFCF9D2D2D7070005CE9",
            "0201021BFF114D191BF0CF2D700000012C7070005CBF1D60F0F0FC3FCFCF9F"
        }
    );

    /*
     * 亮度 20%
     */
    add_action(
        devices,
        "light.room1",
        "brightness_20",
        {
            "0201021BFF114D191CF0CF2D700000017171516FBF1D60F0F0FC3FCFCF9DAA",
            "0201021BFF114D1914F0CF2D70000001F1FC3FCFCF9D2D2D7070005CBF1D62"
        }
    );

    /*
     * 亮度 40%
     */
    add_action(
        devices,
        "light.room1",
        "brightness_40",
        {
            "0201021BFF114D1915F0CF2D70000001FD3FCFCF9D2D2D7070005CBF1D60F2",
            "0201021BFF114D1911F0CF2D700000011C60F0F0FC3FCFCF9D2D2D7070005E"
        }
    );

    /*
     * 亮度 50%
     */
    add_action(
        devices,
        "light.room1",
        "brightness_50",
        {
            "0201021BFF114D191BF0CF2D700000012C7070005CBF1D60F0F0FC3FCFCF9F",
            "0201021BFF114D191FF0CF2D700000015DBE4CF9F0F0FC3FCFCF9D2D2D709D"
        }
    );

    /*
     * 亮度 60%
     */
    add_action(
        devices,
        "light.room1",
        "brightness_60",
        {
            "0201021BFF114D191FF0CF2D700000015DBE4CF9F0F0FC3FCFCF9D2D2D709D",
            "0201021BFF114D1913F0CF2D70000001F1F0FC3FCFCF9D2D2D7070005CBF1F"
        }
    );

    /*
     * 亮度 80%
     */
    add_action(
        devices,
        "light.room1",
        "brightness_80",
        {
            "0201021BFF114D191EF0CF2D70000001015DEED160F0F0FC3FCFCF9D2D2D50",
            "0201021BFF114D1918F0CF2D70000001CE9D2D2D7070005CBF1D60F0F0FC3D"
        }
    );

    /*
     * 亮度 100%
     */
    add_action(
        devices,
        "light.room1",
        "brightness_100",
        {
            "0201021BFF114D191AF0CF2D700000012C2C218F005CBF1D60F0F0FC3FCF9C",
            "0201021BFF114D1912F0CF2D7000000161F0F0FC3FCFCF9D2D2D7070005CBD"
        }
    );

    /*
     * 色温 2700K
     */
    add_action(
        devices,
        "light.room1",
        "color_2700",
        {
            "0201021BFF114D1914F0CF2D70000001F1FD6ACFCF9D2D2D7070005CBF1D38",
            "0201021BFF114D1911F0CF2D700000011C60F0F0FC3FCFCF9D2D2D7070005E"
        }
    );

    /*
     * 色温 3500K
     */
    add_action(
        devices,
        "light.room1",
        "color_3500",
        {
            "0201021BFF114D1910F0CF2D70000001BE1C358DF0FC3FCFCF9D2D2D7070D5",
            "0201021BFF114D191BF0CF2D700000012C7070005CBF1D60F0F0FC3FCFCF9F"
        }
    );

    /*
     * 色温 6500K
     */
    add_action(
        devices,
        "light.room1",
        "color_6500",
        {
            "0201021BFF114D1917F0CF2D70000001CECEC8D22D7070005CBF1D60F0F0AB",
            "0201021BFF114D191EF0CF2D70000001015CBF1D60F0F0FC3FCFCF9D2D2D72"
        }
    );
       /*
     * ==========================================
     * 新增设备：卧室风扇
     * ==========================================
     */
    add_device(
        devices,
        "fan.room1",
        "fan",
        "卧室风扇"
    );

    /* 风扇 开 */
    add_action(devices, "fan.room1", "on", {
        "REPLACE_WITH_REAL_HEX_ON_1",
        "REPLACE_WITH_REAL_HEX_ON_2"
    });

    /* 风扇 关 */
    add_action(devices, "fan.room1", "off", {
        "REPLACE_WITH_REAL_HEX_OFF_1",
        "REPLACE_WITH_REAL_HEX_OFF_2"
    });

    /* 风扇 1档 */
    add_action(devices, "fan.room1", "speed_1", {
        "REPLACE_WITH_REAL_HEX_SPEED1_1",
        "REPLACE_WITH_REAL_HEX_SPEED1_2"
    });

    /* 风扇 2档 */
    add_action(devices, "fan.room1", "speed_2", {
        "REPLACE_WITH_REAL_HEX_SPEED2_1",
        "REPLACE_WITH_REAL_HEX_SPEED2_2"
    });

    /* 风扇 3档 */
    add_action(devices, "fan.room1", "speed_3", {
        "REPLACE_WITH_REAL_HEX_SPEED3_1",
        "REPLACE_WITH_REAL_HEX_SPEED3_2"
    });

    /* 风扇 4档 */
    add_action(devices, "fan.room1", "speed_4", {
        "REPLACE_WITH_REAL_HEX_SPEED4_1",
        "REPLACE_WITH_REAL_HEX_SPEED4_2"
    });

    /* 风扇 5档 */
    add_action(devices, "fan.room1", "speed_5", {
        "REPLACE_WITH_REAL_HEX_SPEED5_1",
        "REPLACE_WITH_REAL_HEX_SPEED5_2"
    });

    /* 风扇 6档 */
    add_action(devices, "fan.room1", "speed_6", {
        "REPLACE_WITH_REAL_HEX_SPEED6_1",
        "REPLACE_WITH_REAL_HEX_SPEED6_2"
    });

    /* 风扇 正转 */
    add_action(devices, "fan.room1", "forward", {
        "REPLACE_WITH_REAL_HEX_FWD_1",
        "REPLACE_WITH_REAL_HEX_FWD_2"
    });

    /* 风扇 反转 */
    add_action(devices, "fan.room1", "reverse", {
        "REPLACE_WITH_REAL_HEX_REV_1",
        "REPLACE_WITH_REAL_HEX_REV_2"
    }); 
}

void DeviceTable::add_device(
    std::vector<BLEDevice> &devices,
    std::string id,
    std::string type,
    std::string name
) {
    BLEDevice device;
    device.id = id;
    device.type = type;
    device.name = name;
    devices.push_back(device);
}

void DeviceTable::add_action(
    std::vector<BLEDevice> &devices,
    std::string device_id,
    std::string action,
    std::vector<std::string> packets
) {
    for (auto &device : devices) {
        if (device.id == device_id) {
            BLEAction act;
            act.name = action;
            act.packets = packets;
            device.actions[action] = act;
            return;
        }
    }
}

} // namespace ble_gateway
} // namespace esphome
