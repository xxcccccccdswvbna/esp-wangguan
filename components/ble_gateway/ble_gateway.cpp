#include "ble_gateway.h"

#include "esphome/core/log.h"

#include "esp_gap_ble_api.h"


namespace esphome {
namespace ble_gateway {


static const char *TAG = "ble_gateway";



void BLEGateway::setup()
{

    ESP_LOGI(
        TAG,
        "BLE Gateway ready"
    );


    config_manager_.load();

}






void BLEGateway::loop()
{


    /*
     * BLE GAP 冷却等待
     */
    if(cooldown_)
    {

        if(
            millis() - adv_stop_time_ < 800
        )
        {
            return;
        }


        cooldown_ = false;


        ESP_LOGI(
            TAG,
            "BLE GAP READY"
        );

    }




    /*
     * 广播停止
     */
    if(
        adv_running_ &&
        millis() - adv_start_time_ >= 100
    )
    {

        esp_ble_gap_stop_advertising();


        adv_running_ = false;


        adv_stop_time_ =
            millis();


        cooldown_ = true;



        ESP_LOGI(
            TAG,
            "BLE ADV STOP"
        );



        if(
            !packet_queue_.empty()
        )
        {

            next_packet_time_ =
                millis() + 1000;


            waiting_next_packet_ = true;

        }

    }





    /*
     * 下一包
     */
    if(
        waiting_next_packet_ &&
        millis() >= next_packet_time_
    )
    {

        waiting_next_packet_ = false;


        ESP_LOGI(
            TAG,
            "SEND NEXT PACKET"
        );


        send_next_packet();

    }


}








std::vector<uint8_t>
BLEGateway::hex_to_bytes(
    const std::string &hex
)

{

    std::vector<uint8_t> data;


    std::string clean;



    for(
        char c : hex
    )
    {

        if(
            (c >= '0' && c <= '9') ||
            (c >= 'A' && c <= 'F') ||
            (c >= 'a' && c <= 'f')
        )
        {

            clean += c;

        }

    }




    for(
        size_t i = 0;
        i + 1 < clean.length();
        i += 2
    )
    {

        uint8_t value =
            strtol(
                clean.substr(i,2)
                .c_str(),
                nullptr,
                16
            );


        data.push_back(value);

    }



    return data;

}






void BLEGateway::send_hex(
    std::string hex
)

{

    ESP_LOGI(
        TAG,
        "BLE RX CMD:%s",
        hex.c_str()
    );



    /*
     * 查询设备配置
     *
     * 例如:
     *
     * light.room1
     *
     */
BLEAction action;


if(
    hex.find("|") == std::string::npos &&
    hex.find("020102") != 0 &&
    config_manager_.get_action(
        hex,
        action
    )
)
{

    ESP_LOGI(
        TAG,
        "COMMAND FOUND:%s",
        hex.c_str()
    );


    std::string packets;



    for(
        size_t i = 0;
        i < action.packets.size();
        i++
    )
    {

        if(i > 0)
            packets += "|";


        packets +=
            action.packets[i];

    }



    send_hex(
        packets
    );


    return;

}
    {


        ESP_LOGI(
            TAG,
            "COMMAND FOUND:%s",
            hex.c_str()
        );



        std::string packets;



        /*
         * 临时默认动作 on
         *
         * 后续扩展 action
         */
        auto action =
            device.actions["on"];




        for(
            size_t i = 0;
            i < action.packets.size();
            i++
        )
        {

            if(i > 0)
            {
                packets += "|";
            }


            packets +=
                action.packets[i];

        }



        send_hex(
            packets
        );


        return;

    }
    /*
     * 多包发送
     *
     * HEX|HEX
     */
    if(
        hex.find("|") != std::string::npos
    )
    {


        packet_queue_.clear();



        size_t start = 0;



        while(true)
        {

            size_t pos =
                hex.find(
                    "|",
                    start
                );



            if(
                pos == std::string::npos
            )
            {

                packet_queue_.push_back(
                    hex.substr(start)
                );


                break;

            }




            packet_queue_.push_back(
                hex.substr(
                    start,
                    pos - start
                )
            );



            start =
                pos + 1;


        }




        /*
         * 发送第一包
         */
        send_next_packet();



        return;

    }






    /*
     * 单HEX包
     */
    send_raw_packet(
        hex
    );


}








void BLEGateway::send_next_packet()
{


    if(
        packet_queue_.empty()
    )
    {

        return;

    }




    std::string packet =
        packet_queue_.front();



    packet_queue_.erase(
        packet_queue_.begin()
    );



    send_raw_packet(
        packet
    );


}









void BLEGateway::send_raw_packet(
    std::string packet
)

{

    ESP_LOGI(
        TAG,
        "BLE TX RAW:%s",
        packet.c_str()
    );



    auto data =
        hex_to_bytes(
            packet
        );



    if(
        data.size() < 5
    )
    {

        ESP_LOGW(
            TAG,
            "packet too short"
        );


        return;

    }





    esp_err_t err =
        esp_ble_gap_config_adv_data_raw(
            data.data(),
            data.size()
        );



    ESP_LOGI(
        TAG,
        "RAW ADV len=%d err=%d",
        data.size(),
        err
    );






    esp_ble_adv_params_t params = {};



    /*
     * 广播间隔
     */
    params.adv_int_min =
        0x40;


    params.adv_int_max =
        0x80;



    /*
     * 非连接广播
     */
    params.adv_type =
        ADV_TYPE_NONCONN_IND;



    params.channel_map =
        ADV_CHNL_ALL;



    esp_ble_gap_start_advertising(
        &params
    );



    adv_start_time_ =
        millis();



    adv_running_ =
        true;



    ESP_LOGI(
        TAG,
        "BLE ADV START"
    );


}









bool BLEGateway::parse_status(
    std::string hex
)

{

    ESP_LOGI(
        TAG,
        "BLE RX:%s",
        hex.c_str()
    );


    return true;

}





}
}
