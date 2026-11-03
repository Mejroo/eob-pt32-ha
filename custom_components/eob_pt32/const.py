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
ITEM_FIRMWARE = 0x0003  # [hlavní][vedlejší] verze, vypisuje se šestnáctkově (14 03 → 14.03)
ITEM_CLOCK = 0x0007
ITEM_PROGRAM = 0x000D  # čtení s 1 B čísla programu → [číslo][rozvrh][název 16 B]
ITEM_BOILER_HOURS = 0x0022  # [hodiny 2 B][minuty 1 B]
PROGRAM_COUNT = 9
PROGRAM_NAME_LEN = 16
PROGRAM_DAY_SLOTS = 6  # den = 6 párů [čas × 8 h][teplota × 2], Po–Ne
DAY_NAMES = ("Po", "Út", "St", "Čt", "Pá", "So", "Ne")

# Nastavení termostatu: položky s dvoupísmenným ASCII kódem (zápis 0x4B54 = "KT", čtení 0xCB54).
# Aplikace je čte všechny jedním rámcem (SETTINGS_READ); termostat zápis potvrdí stejnou hodnotou.
SET_OFFSET = 0x4B54  # KT korekce teploty: (hodnota − 100) / 10 °C, 0x57 = −1,3 (zápis ověřen)
SET_HYSTERESIS = 0x4853  # HS hystereze: hodnota / 10 °C (zápis ověřen)
SET_MIN_ON = 0x484D  # HM minimální doba zapnutí kotle v minutách (zápis ověřen)
SET_LOCK = 0x4C4B  # LK zámek klávesnice: "A" / "N" (zápis ověřen)
SET_TEMP_MIN = 0x4D49  # MI spodní mez nastavitelné teploty × 2 (jen čtení)
SET_TEMP_MAX = 0x4D58  # MX horní mez nastavitelné teploty × 2 (jen čtení)
SET_SERVICE_YEAR = 0x5252  # RR, RM, RD datum údržby kotle (měsíc od 0; jen čtení)
SET_SERVICE_MONTH = 0x524D
SET_SERVICE_DAY = 0x5244
# Kódy, které aplikace čte při otevření (význam ostatních zatím neznámý, ukládají se jen jako surová data).
SETTINGS_READ = (
    0x4853, 0x505A, 0x4C52, 0x4D58, 0x484D, 0x504D, 0x4D49, 0x5050, 0x5049, 0x4C45,
    0x5252, 0x524D, 0x5244, 0x544B, 0x4452, 0x4C4B, 0x4C53, 0x5554, 0x5443, 0x4B54, 0x4A41,
)
YES = 0x41  # "A"
NO = 0x4E  # "N"

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

TEMP_MIN = 3.0  # výchozí meze, než se načte rozsah z termostatu (MI, MX)
TEMP_MAX = 39.0
POLL_SECONDS = 60
BOILER_POLL_SECONDS = 300
SLOW_POLL_SECONDS = 3600  # programy, nastavení, hodiny a název termostatu z účtu
OFFLINE_SECONDS = 180  # bez odpovědi déle než 3 dotazy na stav = termostat nedostupný
WRITE_TIMEOUT = 4  # s na potvrzení zápisu
WRITE_ATTEMPTS = 3
