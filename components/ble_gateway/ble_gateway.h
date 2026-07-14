#pragma once

#include "esphome/core/component.h"
#include "config_manager.h"
#include "command_router.h"

#include <deque>
#include <string>
#include <vector>

namespace esphome {
namespace ble_gateway {

class BLEGateway : public Component {
public:
    void setup() override;
    void loop() override;

    // MQTT 或 API 入口: 支持单包 HEX、多包 HEX (用 '|' 分隔) 或 device.action 形式
    void send_hex(const std::string &hex);

    // 兼容旧版命令入口
    void handle_command(const std::string &cmd);

    // 供 CommandRouter 调用的发送接口
    bool send_command(const std::string &device, const std::string &action);

    // 状态解析接口 (保留原有签名)
    bool parse_status(const std::string &hex);

    // 统一的入队 API，供内部和外部调用
    void enqueue_packets(const std::vector<std::string> &packets);

protected:
    // 工具方法
    static std::vector<uint8_t> hex_to_bytes(const std::string &hex);
    static std::vector<std::string> split_by(const std::string &s, char delim);

private:
    // 【优化】使用 constexpr 替代魔法数字，提升可读性和编译期优化
    static constexpr uint32_t ADV_DURATION_MS  = 100;
    static constexpr uint32_t ADV_COOLDOWN_MS  = 800;
    static constexpr uint32_t PACKET_GAP_MS    = 1000;
    static constexpr size_t   MIN_PACKET_BYTES = 5;

    static constexpr uint16_t ADV_INT_MIN = 0x40;
    static constexpr uint16_t ADV_INT_MAX = 0x80;

    // 依赖组件
    ConfigManager config_manager_;
    CommandRouter command_router_;

    // 广播状态机变量
    bool     adv_running_{false};
    uint32_t adv_start_time_{0};
    uint32_t adv_stop_time_{0};
    bool     cooldown_{false};

    // 【优化】使用 std::deque 管理发送队列，支持高效的头部弹出和尾部插入
    bool     waiting_next_packet_{false};
    uint32_t next_packet_time_{0};
    std::deque<std::string> packet_queue_;

    // 内部动作
    void send_raw_packet(const std::string &packet);
    void send_next_packet();
    bool dispatch_action_(const std::string &hex);
};

}  // namespace ble_gateway
}  // namespace esphome
