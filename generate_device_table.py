import json
import os
import glob

def clean_hex(hex_str):
    return str(hex_str).strip().replace(" ", "").replace("0x", "").replace("0X", "").upper()

def get_english_name(dev_id):
    return dev_id.split('.')[-1].replace('_', ' ').title()

def generate_all(config_dir, base_dir):
    print(f"Scanning: {config_dir}")
    json_files = sorted(glob.glob(os.path.join(config_dir, "*.json")))
    if not json_files:
        print("No .json files found!")
        return

    devices = []
    used_ids = set()
    for jf in json_files:
        try:
            with open(jf, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'id' in data:
                    if data['id'] in used_ids:
                        print(f"ERROR: Duplicate ID '{data['id']}' in {os.path.basename(jf)}")
                        return
                    used_ids.add(data['id'])
                    if 'protocol' not in data:
                        data['protocol'] = '8153'
                    devices.append(data)
                    print(f"  OK: {data['id']} (protocol: {data['protocol']})")
        except json.JSONDecodeError as e:
            print(f"  ERROR in {os.path.basename(jf)}: {e}")
            return

    # ========== 1. C++ device_table.cpp ==========
    cpp = '#include "device_table.h"\n\nnamespace esphome {\nnamespace ble_gateway {\n\nvoid DeviceTable::load(std::vector<BLEDevice> &devices) {\n'
    for dev in devices:
        n = get_english_name(dev['id'])
        for t in ['light', 'fan']:
            if t in dev:
                tid = dev[t]['id']
                cpp += f'\n    add_device(devices, "{tid}", "{t}", "{n} {t.title()}");\n'
                for act, pkts in dev[t].get('actions', {}).items():
                    pc = [clean_hex(p) for p in pkts if str(p).strip()]
                    if pc:
                        ps = ",\n        ".join([f'"{p}"' for p in pc])
                        cpp += f'    add_action(devices, "{tid}", "{act}", {{\n        {ps}\n    }});\n'
    cpp += '\n}\nvoid DeviceTable::add_device(std::vector<BLEDevice> &d, std::string id, std::string type, std::string name) { BLEDevice device; device.id=id; device.type=type; device.name=name; d.push_back(device); }\n'
    cpp += 'void DeviceTable::add_action(std::vector<BLEDevice> &d, std::string did, std::string action, std::vector<std::string> packets) { for(auto &device:d){if(device.id==did){BLEAction act;act.name=action;act.packets=packets;device.actions[action]=act;return;}} }\n'
    cpp += '} // namespace ble_gateway\n} // namespace esphome\n'
    with open(os.path.join(base_dir, "components", "ble_gateway", "device_table.cpp"), 'w') as f:
        f.write(cpp)

    # ========== 2. 按协议分组设备 ==========
    dev_8153 = [d for d in devices if d['protocol'] == '8153']
    dev_134d = [d for d in devices if d['protocol'] == '134D']

    # ========== 3. 生成实体列表 ==========
    bs, ss, ts, btns, ly, fy = [], [], [], [], [], []
    ss.append('  - platform: uptime\n    name: "Gateway Uptime"\n  - platform: internal_temperature\n    name: "ESP32 Chip Temperature"\n    unit_of_measurement: "°C"\n    accuracy_decimals: 1\n  - platform: wifi_signal\n    name: "WiFi Signal dBm"\n    id: wifi_signal_db\n    update_interval: 60s\n  - platform: copy\n    source_id: wifi_signal_db\n    name: "WiFi Signal Percent"\n    filters:\n      - lambda: return min(max(2*(x+100.0),0.0),100.0);\n    unit_of_measurement: "%"\n    icon: mdi:wifi-strength-4')
    ts.append('  - platform: wifi_info\n    ip_address:\n      name: "ESP IP Address"\n    ssid:\n      name: "ESP Connected SSID"\n    bssid:\n      name: "ESP Connected BSSID"')
    btns.append('  - platform: restart\n    name: "Restart Gateway"\n    icon: mdi:restart')

    for dev in devices:
        sid = dev['id'].replace('.','_')
        n = get_english_name(dev['id'])
        if 'mac' in dev and dev['mac']:
            bs.append(f'  - platform: template\n    id: {sid}_led_state\n    name: "{n} LED"\n    device_class: light')
            bs.append(f'  - platform: template\n    id: {sid}_fan_state\n    name: "{n} Fan State"\n    device_class: running')
            ss.append(f'  - platform: template\n    id: {sid}_brightness\n    name: "{n} Brightness"\n    unit_of_measurement: "%"\n    accuracy_decimals: 0')
            ss.append(f'  - platform: template\n    id: {sid}_color_temp\n    name: "{n} Color Temp"\n    unit_of_measurement: "K"\n    accuracy_decimals: 0')
            ss.append(f'  - platform: template\n    id: {sid}_fan_speed\n    name: "{n} Fan Speed"\n    accuracy_decimals: 0')
            ss.append(f'  - platform: template\n    id: {sid}_timer\n    name: "{n} Timer"\n    unit_of_measurement: "min"\n    accuracy_decimals: 0')
            ts.append(f'  - platform: template\n    id: {sid}_fan_direction\n    name: "{n} Fan Direction"')
        if 'light' in dev:
            ly.append(f'  - platform: ble_light\n    id: {sid}_light_ctrl\n    name: "{n} Light"\n    ble_device_id: "{dev["light"]["id"]}"\n    gateway: ct1_ble')
        if 'fan' in dev:
            fy.append(f'  - platform: ble_fan\n    id: {sid}_fan_ctrl\n    name: "{n} Fan"\n    ble_device_id: "{dev["fan"]["id"]}"\n    gateway: ct1_ble')

    # ========== 4. 生成 Tracker (多协议解析) ==========
    tracker = """esp32_ble_tracker:
  scan_parameters:
    interval: 320ms
    window: 30ms
    active: false
  on_ble_advertise:
    - then:
        - lambda: |-
            auto datas = x.get_manufacturer_datas();
            for (auto &data : datas) {
                auto &raw = data.data;
                if (raw.size() < 20) continue;
"""
    # --- 8153 协议解析块 ---
    if dev_8153:
        tracker += """
                // === Protocol 8153 ===
                if (raw[0] == 0x81 && raw[1] == 0x53) {
                    std::string he = "";
                    for (uint8_t b : raw) { char buf[3]; sprintf(buf, "%02x", b); he += buf; }
                    if (he.length() < 40) continue;
                    std::string mac_raw = he.substr(6, 12);
                    std::string mac = "";
                    for (int i = 10; i >= 0; i -= 2) { mac += mac_raw.substr(i, 2); if (i > 0) mac += ":"; }
                    int mode = strtol(he.substr(22, 2).c_str(), nullptr, 16);
                    bool led_on = (mode & 0x01) != 0;
                    bool fan_on = !(mode == 0x10 || mode == 0x11);
                    bool fan_reverse = (mode & 0x20) != 0;
                    float brightness_pct = (strtol(he.substr(28, 2).c_str(), nullptr, 16) / 255.0f) * 100.0f;
                    float color_pct = strtol(he.substr(30, 2).c_str(), nullptr, 16) / 255.0f;
                    float color_kelvin = 2700.0f + (6500.0f - 2700.0f) * color_pct;
                    int timer_min = strtol(he.substr(32, 4).c_str(), nullptr, 16);
                    int fan_speed = fan_on ? (strtol(he.substr(36, 2).c_str(), nullptr, 16) + 1) : 0;
                    std::string fan_dir_str = fan_on ? (fan_reverse ? "Reverse" : "Forward") : "Off";
"""
        for dev in dev_8153:
            sid = dev['id'].replace('.','_')
            mac = dev['mac'].lower()
            tracker += f"""
                    if (mac == "{mac}") {{
                        id({sid}_led_state).publish_state(led_on);
                        id({sid}_brightness).publish_state(brightness_pct);
                        id({sid}_color_temp).publish_state(color_kelvin);
                        id({sid}_fan_state).publish_state(fan_on);
                        id({sid}_fan_speed).publish_state(fan_speed);
                        id({sid}_fan_direction).publish_state(fan_dir_str);
                        id({sid}_timer).publish_state(timer_min);
                    }}
"""
        tracker += "                    break;\n                }\n"

    # --- 134D 协议解析块 (已应用破解的规则) ---
    if dev_134d:
        tracker += """
                // === Protocol 134D ===
                if (raw[0] == 0x21) {
                    char mac_buf[18];
                    sprintf(mac_buf, "%02x:%02x:%02x:%02x:%02x:%02x", raw[7], raw[6], raw[5], raw[4], raw[3], raw[2]);
                    std::string mac(mac_buf);
                    
                    bool power_on = (raw[9] == 0x01);
                    uint16_t brt_raw = (raw[14] << 8) | raw[15];
                    int brt_pct = (brt_raw == 0xFFFF) ? 100 : (int)(brt_raw / 655.35);
                    
                    uint8_t state_byte = raw[18];
                    bool fan_running = (state_byte == 0x13 || state_byte == 0x03);
                    uint8_t fan_gear = raw[19];
                    int fan_speed = fan_running ? (fan_gear + 1) : 0;
                    std::string fan_dir_str = fan_running ? "Forward" : "Off";
"""
        for dev in dev_134d:
            sid = dev['id'].replace('.','_')
            mac = dev['mac'].lower()
            tracker += f"""
                    if (mac == "{mac}") {{
                        id({sid}_led_state).publish_state(power_on);
                        id({sid}_brightness).publish_state(brt_pct);
                        id({sid}_fan_state).publish_state(fan_running);
                        id({sid}_fan_speed).publish_state(fan_speed);
                        id({sid}_fan_direction).publish_state(fan_dir_str);
                        id({sid}_color_temp).publish_state(0);
                        id({sid}_timer).publish_state(0);
                    }}
"""
        tracker += "                    break;\n                }\n"

    tracker += "            }\n"

    # ========== 5. 写入 YAML ==========
    base = """esphome:
  name: {name}
  friendly_name: {fn}
esp32:
  board: esp32dev
  flash_size: 4MB
  framework:
    type: esp-idf
    sdkconfig_options:
      CONFIG_FREERTOS_UNICORE: y
      CONFIG_BT_ENABLED: y
      CONFIG_BT_BLE_ENABLED: y
logger:
  baud_rate: 0
wifi:
  ssid: "CC"
  password: "chen1122"
  fast_connect: true
  power_save_mode: none
  ap:
    ssid: "CT1 Fallback"
    password: "12345678"
captive_portal:
web_server:
api:
  reboot_timeout: 0s
ota:
  - platform: esphome
external_components:
  - source:
      type: local
      path: components
ble_gateway:
  id: ct1_ble
"""
    def write(fn, hdr, extra=""):
        c = hdr
        if bs: c += "binary_sensor:\n" + "\n".join(bs) + "\n\n"
        if ss: c += "sensor:\n" + "\n".join(ss) + "\n\n"
        if ts: c += "text_sensor:\n" + "\n".join(ts) + "\n\n"
        if btns: c += "button:\n" + "\n".join(btns) + "\n\n"
        if ly: c += "light:\n" + "\n".join(ly) + "\n\n"
        if fy: c += "fan:\n" + "\n".join(fy) + "\n\n"
        c += extra + "\n" + tracker
        with open(os.path.join(base_dir, fn), 'w') as f: f.write(c)

    write("ct1.yaml", base.format(name="ct1", fn="CT1 Lite"))
    write("ct2.yaml", base.format(name="ct2", fn="CT2 Full") + "\nmqtt:\n  broker: \"192.168.6.88\"\n  discovery: true\n  on_message:\n    - topic: \"ct2/ble/send\"\n      then:\n        - lambda: |-\n            id(ct1_ble).send_hex(x);\nbluetooth_proxy:\n  active: false\n")
    write("ct3.yaml", base.format(name="ct3", fn="CT3 Custom"))

    # CT4 Pro (省略部分重复代码，保持与之前一致，此处用简写表示)
    ct4b = base.format(name="ct4", fn="CT4 Pro")
    # ... (CT4 的按键、LED 等配置与之前完全相同，此处为节省篇幅省略，请直接使用上一版的 CT4 生成逻辑，只需确保 tracker 部分被正确追加即可) ...
    # 注意：在实际替换时，请保留上一版脚本中 CT4 的完整生成代码，只需将最后的 `c4 += tracker` 确保使用的是上面新生成的 `tracker` 变量。
    
    # 为了完整性，这里直接输出 CT4
    ct4_full = """esphome:
  name: ct4
  friendly_name: CT4 Pro
  on_boot:
    priority: 600.0
    then:
      - light.turn_on: blue_led
      - light.turn_on: white_led
esp32:
  board: esp32dev
  flash_size: 4MB
  framework:
    type: esp-idf
    sdkconfig_options:
      CONFIG_FREERTOS_UNICORE: y
      CONFIG_BT_ENABLED: y
      CONFIG_BT_BLE_ENABLED: y
logger:
  baud_rate: 0
wifi:
  ssid: "CC"
  password: "chen1122"
  fast_connect: true
  power_save_mode: none
  ap:
    ssid: "CT1 Fallback"
    password: "12345678"
captive_portal:
web_server:
api:
  reboot_timeout: 0s
  on_client_connected:
    - script.stop: offline_flash
    - light.turn_off: white_led
    - light.turn_off: blue_led
  on_client_disconnected:
    - script.execute: offline_flash
ota:
  - platform: esphome
esp32_ble:
  io_capability: none
  enable_on_boot: true
bluetooth_proxy:
  active: true
  cache_services: true
globals:
  - id: do_factory_reset
    type: bool
    restore_value: no
    initial_value: 'false'
  - id: safe_mode_tap_count
    type: int
    restore_value: no
    initial_value: '0'
script:
  - id: offline_flash
    mode: restart
    then:
      - while:
          condition: { lambda: 'return true;' }
          then: [light.toggle: white_led, delay: 500ms]
output:
  - platform: gpio
    id: blue_led_out
    pin: { number: GPIO27, inverted: true }
  - platform: gpio
    id: white_led_out
    pin: { number: GPIO26, inverted: true }
external_components:
  - source:
      type: local
      path: components
ble_gateway:
  id: ct1_ble
"""
    c4 = ct4_full
    all_bs = "\n".join(bs) if bs else ""
    keys4 = """
  - platform: gpio
    id: key1
    name: KEY1
    pin: { number: GPIO34, inverted: true }
    filters: [delayed_on: 20ms, delayed_off: 20ms]
    on_multi_click:
      - timing: [ON for at least 8s]
        then:
          - if: { condition: { binary_sensor.is_on: key4 }, then: [delay: 500ms, if: { condition: { binary_sensor.is_on: key4 }, then: [lambda: 'id(do_factory_reset)=true;', repeat: { count: 5, then: [light.toggle: white_led, delay: 100ms] }, lambda: 'App.reboot();'] }]}
      - timing: [ON for at least 1.5s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key1", mode: "long" } }]
      - timing: [ON for at most 0.5s, OFF for at most 0.3s, ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key1", mode: "double" } }]
      - timing: [ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key1", mode: "single" } }]
  - platform: gpio
    id: key2
    name: KEY2
    pin: { number: GPIO35, inverted: true }
    filters: [delayed_on: 20ms, delayed_off: 20ms]
    on_multi_click:
      - timing: [ON for at least 1.5s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key2", mode: "long" } }]
      - timing: [ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key2", mode: "single" } }]
  - platform: gpio
    id: key3
    name: KEY3
    pin: { number: GPIO32, inverted: true }
    filters: [delayed_on: 20ms, delayed_off: 20ms]
    on_multi_click:
      - timing: [ON for at least 1.5s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key3", mode: "long" } }]
      - timing: [ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key3", mode: "single" } }]
  - platform: gpio
    id: key4
    name: KEY4
    pin: { number: GPIO33, inverted: true }
    filters: [delayed_on: 20ms, delayed_off: 20ms]
    on_multi_click:
      - timing: [ON for at least 1.5s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key4", mode: "long" } }]
      - timing: [ON for at most 0.5s, OFF for at least 0.3s]
        then: [light.turn_on: blue_led, delay: 200ms, light.turn_off: blue_led, homeassistant.event: { event: esphome.gateway_key, data: { key: "key4", mode: "single" } }]
"""
    if bs: c4 += "binary_sensor:\n" + all_bs + keys4 + "\n\n"
    else: c4 += "binary_sensor:\n" + keys4 + "\n\n"
    if ss: c4 += "sensor:\n" + "\n".join(ss) + "\n\n"
    if ts: c4 += "text_sensor:\n" + "\n".join(ts) + "\n\n"
    if btns: c4 += "button:\n" + "\n".join(btns) + "\n\n"
    
    led4 = ['  - platform: binary\n    name: Blue LED\n    id: blue_led\n    output: blue_led_out\n    restore_mode: RESTORE_DEFAULT_OFF', '  - platform: binary\n    name: White LED\n    id: white_led\n    output: white_led_out\n    restore_mode: RESTORE_DEFAULT_OFF']
    all_ly = "\n".join(led4 + ly) if (led4 or ly) else ""
    if all_ly: c4 += "light:\n" + all_ly + "\n\n"
    if fy: c4 += "fan:\n" + "\n".join(fy) + "\n\n"
    c4 += tracker
    with open(os.path.join(base_dir, "ct4.yaml"), 'w') as f: f.write(c4)

    print("All files generated successfully.")

if __name__ == "__main__":
    bd = os.path.dirname(os.path.abspath(__file__))
    cd = os.path.join(bd, "devices_config")
    if not os.path.exists(cd):
        print(f"Error: {cd} not found.")
        exit(1)
    generate_all(cd, bd)
