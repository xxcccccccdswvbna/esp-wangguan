#include "ble_gateway.h"

#include "esphome/core/log.h"

#include "esp_gap_ble_api.h"
#include "esp_bt.h"


namespace esphome {
namespace ble_gateway {


static const char *TAG = "ble_gateway";


BLEGateway *BLEGateway::instance_ = nullptr;



void BLEGateway::setup()
{

    ESP_LOGI(
        TAG,
        "BLE Gateway V2 start"
    );


    instance_ = this;


    esp_ble_gap_register_callback(
        BLEGateway::gap_callback
    );


    adv_params_.adv_int_min = 0x20;

    adv_params_.adv_int_max = 0x40;

    adv_params_.adv_type =
        ADV_TYPE_NONCONN_IND;

    adv_params_.own_addr_type =
        BLE_ADDR_TYPE_PUBLIC;

    adv_params_.channel_map =
        ADV_CHNL_ALL;

    adv_params_.adv_filter_policy =
        ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY;

}



void BLEGateway::loop()
{

}



/*
 * HEX 转 BYTE
 */
std::vector<uint8_t>
BLEGateway::hex_to_bytes(
    const std::string &hex
)

{

    std::vector<uint8_t> data;


    std::string clean = hex;


    // 去掉0x

    if(
        clean.rfind("0x",0)==0 ||
        clean.rfind("0X",0)==0
    )
    {
        clean =
            clean.substr(2);
    }



    for(
        size_t i=0;
        i+1<clean.length();
        i+=2
    )
    {

        uint8_t b =
            strtol(
                clean.substr(i,2)
                .c_str(),
                nullptr,
                16
            );


        data.push_back(b);

    }


    return data;

}



/*
 * MQTT入口
 */
void BLEGateway::send_hex(
    std::string hex
)

{

    ESP_LOGI(
        TAG,
        "BLE RX CMD:%s",
        hex.c_str()
    );


    auto packet =
        hex_to_bytes(hex);



    if(packet.empty())
    {

        ESP_LOGW(
            TAG,
            "empty packet"
        );

        return;

    }



    enqueue_packet(packet);


}



/*
 * 放入队列
 */
void BLEGateway::enqueue_packet(
    std::vector<uint8_t> packet
)

{

    tx_queue_.push(
        packet
    );


    if(!busy_)
    {
        send_next_packet();
    }

}



/*
 * 发送下一包
 */
void BLEGateway::send_next_packet()

{

    if(tx_queue_.empty())
    {

        busy_=false;

        return;

    }



    busy_=true;


    current_packet_ =
        tx_queue_.front();


    tx_queue_.pop();



    ESP_LOGI(
        TAG,
        "RAW ADV SEND len=%d",
        current_packet_.size()
    );



    esp_err_t err =
        esp_ble_gap_config_adv_data_raw(
            current_packet_.data(),
            current_packet_.size()
        );


    ESP_LOGI(
        TAG,
        "config raw result=%d",
        err
    );

}




/*
 * 开始广播
 */
void BLEGateway::start_advertising()

{

    if(advertising_)
        return;



    advertising_=true;


    esp_ble_gap_start_advertising(
        &adv_params_
    );


}



/*
 * 停止广播
 */
void BLEGateway::stop_advertising()

{

    if(!advertising_)
        return;



    ESP_LOGI(
        TAG,
        "STOP ADV"
    );



    esp_ble_gap_stop_advertising();


    advertising_=false;



    send_next_packet();

}





/*
 * GAP 回调
 */
void BLEGateway::gap_callback(
    esp_gap_ble_cb_event_t event,
    esp_ble_gap_cb_param_t *param
)

{

    if(instance_==nullptr)
        return;



    switch(event)
    {


        /*
         * RAW数据配置完成
         */
        case ESP_GAP_BLE_ADV_DATA_RAW_SET_COMPLETE_EVT:
        {


            ESP_LOGI(
                TAG,
                "RAW DATA READY"
            );


            instance_->start_advertising();


            break;

        }



        /*
         * 广播启动完成
         */
        case ESP_GAP_BLE_ADV_START_COMPLETE_EVT:
        {


            ESP_LOGI(
                TAG,
                "ADV START"
            );



            /*
             * 广播50ms
             */

            instance_->set_timeout(
                "ble_stop",
                50,
                []()
                {

                    if(instance_)
                    {

                        instance_->stop_advertising();

                    }

                }
            );


            break;

        }



        case ESP_GAP_BLE_ADV_STOP_COMPLETE_EVT:
        {


            ESP_LOGI(
                TAG,
                "ADV STOP COMPLETE"
            );


            break;

        }



        default:
            break;

    }

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
