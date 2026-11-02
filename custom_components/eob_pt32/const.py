"""Konstanty integrace Elektrobock PT32 WiFi."""

DOMAIN = "eob_pt32"

API_BASE = "https://data.elektrobock.cz"
API_LOGIN = "/api/Auth/login"
API_DEVICES = "/api/UsersDevices/withFcmData"

MQTT_HOST = "mqtt.elbock.cz"
MQTT_PORT = 8081
MQTT_WS_PATH = "/wss"
TOPIC_BASE = "PTWIFI"

DEVICE_TYPE_PT32_WIFI = 0

# Rámec: [hlavička 2 B][délka 2 B][položky]; položka: [typ 2 B][délka 2 B][data].
# Termostat přijímá jen hlavičku 0x7FFF (jako aplikace) a odpovídá s 0xFFFF.
FRAME_REQUEST = 0x7FFF
FRAME_RESPONSE = 0xFFFF
READ_FLAG = 0x8000
LEN_MASK = 0x3FFF

ITEM_STATUS = 0x0002
ITEM_CLOCK = 0x0007
ITEM_PROGRAM = 0x000D  # čtení s 1 B čísla programu → [číslo][rozvrh][název 16 B]
ITEM_BOILER_HOURS = 0x0022  # [hodiny 2 B][minuty 1 B]
PROGRAM_COUNT = 9
PROGRAM_NAME_LEN = 16

# Bajty položky stavu (0x0002), ověřeno proti aplikaci a displeji.
ST_ACTUAL = 0  # skutečná teplota, celé °C
ST_ACTUAL_TENTHS = 2  # desetiny skutečné teploty (20 + 6 → 20,6 °C, jako v aplikaci)
ST_PROGRAM = 3  # číslo aktivního programu (1 = Hlavni program)
ST_AUTO = 4  # 1 = auto (program), 0 = manual
ST_DESIRED = 5  # nastavená teplota × 2 (v off 0)
ST_STATE = 6  # 0x40 = kotel sepnutý, 0x04 = off
ST_FLAGS = 7  # 0x20 = čas z NTP, 0x40 = zamčená klávesnice

# Bajt režimu při zápisu položky 0x0002 (ověřeno z aplikace): auto 0x21, manual 0x20, off 0x24.
MODE_AUTO = 0x01
MODE_OFF = 0x04
MODE_KEEP_MASK = 0x60  # NTP a zámek klávesnice se při zápisu zachovají
STATE_HEATING = 0x40
STATE_OFF = 0x04

TEMP_MIN = 3.0
TEMP_MAX = 39.0
POLL_SECONDS = 60
BOILER_POLL_SECONDS = 300
SLOW_POLL_SECONDS = 3600  # názvy programů a název termostatu z účtu
