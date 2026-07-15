#include "ble_gateway.h"
#include "esphome/core/log.h"
#include "esp_gap_ble_api.h"
#include <cctype> // 用于 std::isxdigit

namespace esphome {
namespace ble_gateway {

static const char *TAG = "ble_gateway";

void BLEGateway::setup() {
    ESP_LOGI(TAG, "BLE Gateway setup started");
    config_manager_.load();

    command_router_.set_gateway(this);
    command_router_.set_config(&config_manager_);
    ESP_LOGI(TAG, "BLE Gateway ready");
}

void BLEGateway::loop() {
    const uint32_t now = millis();

    // 1. 处理冷却时间 (确保两个包之间有足够的间隔)
    if (cooldown_) {
        if (now - adv_stop_time_ < ADV_COOLDOWN_MS) return;
        cooldown_ = false;
        ESP_LOGI(TAG, "BLE GAP READY");
    }

    // 2. 处理广播超时 (每个包固定广播 100ms)
    if (adv_running_ && now - adv_start_time_ >= ADV_DURATION_MS) {
        esp_ble_gap_stop_advertising();
        adv_running_   = false;
        adv_stop_time_ = now;
        cooldown_      = true;
        ESP_LOGI(TAG, "BLE ADV STOP");

        // 如果队列里还有包，设定下一次发送的时间
        if (!packet_queue_.empty()) {
            next_packet_time_    = now + PACKET_GAP_MS;
            waiting_next_packet_ = true;
        }
    }

    // 3. 处理下一个数据包 (时间到了自动发送)
    if (waiting_next_packet_ && now >= next_packet_time_) {
        waiting_next_packet_ = false;
        ESP_LOGI(TAG, "SEND NEXT PACKET");
        send_next_packet();
    }
}

// ---------- 工具方法 ----------

std::vector<uint8_t> BLEGateway::hex_to_bytes(const std::string &hex) {
    std::vector<uint8_t> data;
    data.reserve(hex.size() / 2);

    char pair[3] = {0, 0, 0};
    int n = 0;
    for (char c : hex) {
        // 使用标准库函数判断十六进制字符，更安全、语义更清晰
        if (!std::isxdigit(static_cast<unsigned char>(c))) continue;
        pair[n++] = c;
        if (n == 2) {
            data.push_back(static_cast<uint8_t>(strtol(pair, nullptr, 16)));
            n = 0;
        }
    }
    return data;
}

std::vector<std::string> BLEGateway::split_by(const std::string &s, char delim) {
    std::vector<std::string> out;
    size_t start = 0;
    while (true) {
        size_t pos = s.find(delim, start);
        if (pos == std::string::npos) {
            out.push_back(s.substr(start));
            return out;
        }
        out.push_back(s.substr(start, pos - start));
        start = pos + 1;
    }
}

// ---------- 命令分发 ----------

bool BLEGateway::dispatch_action_(const std::string &hex) {
    size_t pos = hex.rfind('.');
    if (pos == std::string::npos) return false;

    std::string device_id   = hex.substr(0, pos);
    std::string action_name = hex.substr(pos + 1);

    const BLEAction *act = config_manager_.find_action(device_id, action_name);
    if (!act) return false;

    ESP_LOGI(TAG, "COMMAND FOUND: %s", hex.c_str());
    enqueue_packets(act->packets);
    return true;
}

void BLEGateway::send_hex(const std::string &hex) {
    ESP_LOGI(TAG, "BLE RX CMD: %s", hex.c_str());

    // 1) HA 动作命令: 无 "020102" 前缀且不含 '|'
    if (hex.rfind("020102", 0) != 0 && hex.find('|') == std::string::npos) {
        if (!dispatch_action_(hex)) {
            ESP_LOGW(TAG, "device command not found: %s", hex.c_str());
        }
        return;
    }

    // 2) 多包 HEX (用 '|' 分隔)
    if (hex.find('|') != std::string::npos) {
        enqueue_packets(split_by(hex, '|'));
        return;
    }

    // 3) 单包 HEX
    send_raw_packet(hex);
}

void BLEGateway::handle_command(const std::string &cmd) {
    auto p1 = cmd.find('.');
    if (p1 == std::string::npos) return;
    auto p2 = cmd.find('.', p1 + 1);
    if (p2 == std::string::npos) return;

    std::string device = cmd.substr(0, p2);
    std::string action = cmd.substr(p2 + 1);

    ESP_LOGI(TAG, "DEVICE: %s ACTION: %s", device.c_str(), action.c_str());
    send_command(device, action);
}

bool BLEGateway::send_command(const std::string &device, const std::string &action) {
    return command_router_.send_command(device, action);
}

// ---------- 发送队列管理 (核心修复区) ----------

void BLEGateway::enqueue_packets(const std::vector<std::string> &packets) {
    if (packets.empty()) return;
    
    // 【核心逻辑 1】使用 assign 替换队列。
    // 配合“单选指令”逻辑，这里放入的就是当前动作的完整包序列（1个、2个或3个）。
    // 如果此时有新的指令进来，它会直接接管队列（符合“开灯就是开灯，不追加”的要求）。
    packet_queue_.assign(packets.begin(), packets.end());
    
    // 【核心逻辑 2】状态机保护。
    // 只有在当前没有正在广播，也没有在等待发送下一个包时，才主动启动发送流程。
    // 如果已经在发送队列中（比如正在发双包的第 1 个包），loop() 会自动处理后续的包，
    // 此时绝不能在这里打断，必须等待当前 100ms 广播自然结束，否则会丢包或报错。
    if (!adv_running_ && !waiting_next_packet_) {
        send_next_packet();
    }
}

void BLEGateway::send_next_packet() {
    if (packet_queue_.empty()) return;
    
    // 取出队首的包并发送
    std::string packet = std::move(packet_queue_.front());
    packet_queue_.pop_front();
    send_raw_packet(packet);
}

void BLEGateway::send_raw_packet(const std::string &packet) {
    ESP_LOGI(TAG, "BLE TX RAW: %s", packet.c_str());

    auto data = hex_to_bytes(packet);
    if (data.size() < MIN_PACKET_BYTES) {
        ESP_LOGW(TAG, "packet too short");
        return;
    }

    esp_err_t err = esp_ble_gap_config_adv_data_raw(data.data(), data.size());
    ESP_LOGI(TAG, "RAW ADV len=%u err=%d", (unsigned) data.size(), err);

    esp_ble_adv_params_t params = {};
    params.adv_int_min = ADV_INT_MIN;
    params.adv_int_max = ADV_INT_MAX;
    params.adv_type    = ADV_TYPE_NONCONN_IND;
    params.channel_map = ADV_CHNL_ALL;

    esp_ble_gap_start_advertising(&params);
    adv_start_time_ = millis();
    adv_running_    = true;
    ESP_LOGI(TAG, "BLE ADV START");
}

bool BLEGateway::parse_status(const std::string &hex) {
    // 保留原有接口，具体解析逻辑在 ct1.yaml 的 lambda 中处理
    ESP_LOGV(TAG, "BLE RX: %s", hex.c_str());
    return true;
}

}  // namespace ble_gateway
}  // namespace esphome