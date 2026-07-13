#include "device_table.h"


namespace esphome {
namespace ble_gateway {


static BLEAction make_action(
    const char *name,
    const char *p1,
    const char *p2
)
{
    BLEAction action;

    action.name = name;

    action.packets.push_back(p1);
    action.packets.push_back(p2);

    return action;
}



void DeviceTable::load(
    std::vector<BLEDevice> &devices
)
{

    BLEDevice light;


    light.id =
        "light.room1";


    light.type =
        "light";


    light.name =
        "卧室灯";



    /*
     * 开
     */
    light.actions["on"] =
        make_action(
            "on",
            "0201021BFF114D1914F0CF2D70000001F1FC39CFCF9D2D2D7070005CBF1D68",
            "0201021BFF114D1911F0CF2D700000011C60F0F0FC3FCFCF9D2D2D7070005E"
        );



    /*
     * 关
     */
    light.actions["off"] =
        make_action(
            "off",
            "0201021BFF114D191AF0CF2D700000012C2D7670005CBF1D60F0F0FC3FCFC7",
            "0201021BFF114D1912F0CF2D7000000161F0F0FC3FCFCF9D2D2D7070005CBD"
        );



    /*
     * 色温
     */
    light.actions["color_2700"] =
        make_action(
            "color_2700",
            "0201021BFF114D1914F0CF2D70000001F1FD6ACFCF9D2D2D7070005CBF1D38",
            "0201021BFF114D1911F0CF2D700000011C60F0F0FC3FCFCF9D2D2D7070005E"
        );



    light.actions["color_3500"] =
        make_action(
            "color_3500",
            "0201021BFF114D1910F0CF2D70000001BE1C358DF0FC3FCFCF9D2D2D7070D5",
            "0201021BFF114D191BF0CF2D700000012C7070005CBF1D60F0F0FC3FCFCF9F"
        );



    light.actions["color_6500"] =
        make_action(
            "color_6500",
            "0201021BFF114D1917F0CF2D70000001CECEC8D22D7070005CBF1D60F0F0AB",
            "0201021BFF114D191EF0CF2D70000001015CBF1D60F0F0FC3FCFCF9D2D2D72"
        );



    /*
     * 亮度
     */
    light.actions["brightness_1"] =
        make_action(
            "brightness_1",
            "0201021BFF114D1912F0CF2D7000000161F1A1FE3FCFCF9D2D2D7070005CE9",
            "0201021BFF114D191BF0CF2D700000012C7070005CBF1D60F0F0FC3FCFCF9F"
        );


    light.actions["brightness_20"] =
        make_action(
            "brightness_20",
            "0201021BFF114D191CF0CF2D700000017171516FBF1D60F0F0FC3FCFCF9DAA",
            "0201021BFF114D1914F0CF2D70000001F1FC3FCFCF9D2D2D7070005CBF1D62"
        );



    light.actions["brightness_40"] =
        make_action(
            "brightness_40",
            "0201021BFF114D1915F0CF2D70000001FD3FCFCF9D2D2D7070005CBF1D60F2",
            "0201021BFF114D1911F0CF2D700000011C60F0F0FC3FCFCF9D2D2D7070005E"
        );



    light.actions["brightness_50"] =
        make_action(
            "brightness_50",
            "0201021BFF114D191BF0CF2D700000012C7070005CBF1D60F0F0FC3FCFCF9F",
            "0201021BFF114D191FF0CF2D700000015DBE4CF9F0F0FC3FCFCF9D2D2D709D"
        );



    light.actions["brightness_60"] =
        make_action(
            "brightness_60",
            "0201021BFF114D191FF0CF2D700000015DBE4CF9F0F0FC3FCFCF9D2D2D709D",
            "0201021BFF114D1913F0CF2D70000001F1F0FC3FCFCF9D2D2D7070005CBF1F"
        );



    light.actions["brightness_80"] =
        make_action(
            "brightness_80",
            "0201021BFF114D191EF0CF2D70000001015DEED160F0F0FC3FCFCF9D2D2D50",
            "0201021BFF114D1918F0CF2D70000001CE9D2D2D7070005CBF1D60F0F0FC3D"
        );



    light.actions["brightness_100"] =
        make_action(
            "brightness_100",
            "0201021BFF114D191AF0CF2D700000012C2C218F005CBF1D60F0F0FC3FCF9C",
            "0201021BFF114D1912F0CF2D7000000161F0F0FC3FCFCF9D2D2D7070005CBD"
        );



    devices.push_back(
        light
    );

}



}
}
