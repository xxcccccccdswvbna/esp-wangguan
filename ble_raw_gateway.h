#pragma once

#include "esphome/core/component.h"

#include <vector>
#include <queue>
#include <string>

#include "esp_gap_ble_api.h"


namespace esphome {
namespace ble_gateway {


class BLEGateway : public Component {

 public:

  void setup() override;

  void loop() override;


  // MQTT 调用入口
  void send_hex(std::string hex);


  bool parse_status(std::string hex);



 protected:


  /*
   * HEX 转 BLE 数据
   */
  std::vector<uint8_t> hex_to_bytes(
      const std::string &hex
  );


  /*
   * 添加发送队列
   */
  void enqueue_packet(
      std::vector<uint8_t> packet
  );


  /*
   * 发送下一包
   */
  void send_next_packet();


  /*
   * 启动广播
   */
  void start_advertising();


  /*
   * 停止广播
   */
  void stop_advertising();



  /*
   * GAP事件
   */
  static void gap_callback(
      esp_gap_ble_cb_event_t event,
      esp_ble_gap_cb_param_t *param
  );


  /*
   * 当前实例
   * GAP回调用
   */
  static BLEGateway *instance_;



 private:


  /*
   * 发送队列
   */
  std::queue<
      std::vector<uint8_t>
  > tx_queue_;



  /*
   * 当前正在发送的数据
   */
  std::vector<uint8_t>
      current_packet_;



  /*
   * 当前广播参数
   */
  esp_ble_adv_params_t adv_params_{};



  /*
   * 状态
   */
  bool advertising_{false};


  bool busy_{false};


};



}
}
