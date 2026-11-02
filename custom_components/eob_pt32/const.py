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

# Bajty položky stavu (0x0002), ověřeno proti aplikaci a displeji.
ST_ACTUAL = 0  # skutečná teplota, celé °C
ST_AUTO = 4  # 1 = auto (program), 0 = ruční
ST_DESIRED = 5  # nastavená teplota × 2
ST_RELAY = 6  # bit 0x40 = topí
ST_FLAGS = 7  # 0x20 = čas z NTP, 0x40 = zamčená klávesnice

MODE_AUTO = 0x01
MODE_KEEP_MASK = 0x60  # NTP a zámek klávesnice se při zápisu zachovají
RELAY_HEATING = 0x40

TEMP_MIN = 3.0
TEMP_MAX = 39.0
POLL_SECONDS = 60
