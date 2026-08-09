"""Constants for the Plum ecoVENT integration."""

DOMAIN = "plum_ecovent"
NAME = "Plum ecoVENT"
DEFAULT_MODEL = "ecoVENT"

# Explicit opt-in before using cleartext HTTP (including host-only inputs).
CONF_ALLOW_INSECURE_HTTP = "allow_insecure_http"

DEFAULT_REG_REFRESH = 5

# Optimistic overlay after a successful newParam write until regParams /
# editParams catch up (see docs/econet-local-api.md §2.4).
PENDING_WRITE_TIMEOUT = 30

API_PATH_SYS_PARAMS = "sysParams"
API_PATH_REG_PARAMS = "regParams"
API_PATH_EDIT_PARAMS = "editParams"
API_PATH_NEW_PARAM = "newParam"

MANUFACTURER = "Plum"

# Live fan speeds in regParams.curr (unit index 6 = %).
PARAM_SUPPLY_FAN_SPEED = "REKcurSupFanSpeed"
PARAM_EXHAUST_FAN_SPEED = "REKcurExhFanSpeed"

# Air-path temperatures in regParams.curr (unit index 1 = °C).
PARAM_SUPPLY_AIR_TEMP = "REKcurSupTemp"
PARAM_INTAKE_AIR_TEMP = "REKcurIntTemp"
PARAM_EXTRACTED_AIR_TEMP = "REKcurExtTemp"
PARAM_EXHAUST_AIR_TEMP = "REKcuExhTemp"

# Filter lifetime setpoint in editParams.data (by name, not numeric id).
PARAM_FILTER_TIME_TO_ALARM = "FILTERtimeToAlarm"

# Fixed informationParams slot ids for ecoVENT filter status.
INFO_SLOT_SUPPLY_FILTER_DEPLETION = "61"
INFO_SLOT_EXTRACT_FILTER_DEPLETION = "62"
INFO_SLOT_SUPPLY_FILTER_DAYS = "63"
INFO_SLOT_EXTRACT_FILTER_DAYS = "64"

# Presentation units inside editParams.informationParams (not data.unit).
INFO_UNIT_CELSIUS = 1
INFO_UNIT_PERCENT = 2
INFO_UNIT_DAYS = 13
INFO_UNIT_MODE = 0

# Fixed informationParams slot ids for Current work status (§3.8).
INFO_SLOT_CURRENT_COMFORT_TEMP = "101"
INFO_SLOT_CURRENT_LEADING_TEMP = "102"
INFO_SLOT_CONTROL_MODE = "103"
INFO_SLOT_EXTERNAL_TEMP = "104"
INFO_SLOT_SUMMER_WINTER_STATUS = "105"

# Operation mode in regParams.curr / editParams.data (write by numeric id).
# Writable wire values live in operation_mode.OperationMode.
PARAM_OPERATION_MODE = "REKWS1"
PARAM_OPERATION_MODE_ID = 17

# Additional / timed work mode in regParams.curr / editParams.data.
# Writable wire values live in additional_work_mode.AdditionalWorkMode.
PARAM_ADDITIONAL_WORK_MODE = "REKWS4"
PARAM_ADDITIONAL_WORK_MODE_ID = 20

# Summer / winter mode in editParams.data only (not in regParams.curr).
# Writable wire values live in summer_winter_mode.SummerWinterMode.
PARAM_SUMMER_WINTER_MODE = "REKWS2"
PARAM_SUMMER_WINTER_MODE_ID = 18

# Related summer / winter setpoints in editParams.data only.
PARAM_WINTER_ACTIVE_TEMP = "REKwinterActiveTemp"
PARAM_WINTER_ACTIVE_TEMP_ID = 137
PARAM_SUMMER_HYSTERESIS = "REKsummerHyst"
PARAM_SUMMER_HYSTERESIS_ID = 138

# User Mode 1–4 fan velocities and preset temperatures (§3.4).
# Modes 1–3 appear in regParams.curr; Mode 4 is editParams.data only.
PARAM_USER_1_SUP_FAN_SPEED = "REKUser1SupFanSpeed"
PARAM_USER_1_SUP_FAN_SPEED_ID = 273
PARAM_USER_1_EXH_FAN_SPEED = "REKUser1ExhFanSpeed"
PARAM_USER_1_EXH_FAN_SPEED_ID = 276
PARAM_USER_1_SETPOINT = "REKUser1SetPoint"
PARAM_USER_1_SETPOINT_ID = 286

PARAM_USER_2_SUP_FAN_SPEED = "REKUser2SupFanSpeed"
PARAM_USER_2_SUP_FAN_SPEED_ID = 274
PARAM_USER_2_EXH_FAN_SPEED = "REKUser2ExhFanSpeed"
PARAM_USER_2_EXH_FAN_SPEED_ID = 277
PARAM_USER_2_SETPOINT = "REKUser2SetPoint"
PARAM_USER_2_SETPOINT_ID = 287

PARAM_USER_3_SUP_FAN_SPEED = "REKUser3SupFanSpeed"
PARAM_USER_3_SUP_FAN_SPEED_ID = 275
PARAM_USER_3_EXH_FAN_SPEED = "REKUser3ExhFanSpeed"
PARAM_USER_3_EXH_FAN_SPEED_ID = 278
PARAM_USER_3_SETPOINT = "REKUser3SetPoint"
PARAM_USER_3_SETPOINT_ID = 288

PARAM_USER_4_SUP_FAN_SPEED = "REKUser4SupFanSpeed"
PARAM_USER_4_SUP_FAN_SPEED_ID = 469
PARAM_USER_4_EXH_FAN_SPEED = "REKUser4ExhFanSpeed"
PARAM_USER_4_EXH_FAN_SPEED_ID = 470
PARAM_USER_4_SETPOINT = "REKUser4SetPoint"
PARAM_USER_4_SETPOINT_ID = 468

# Additional / timed work mode presets (§3.5 Related Party/Outside/Airing).
PARAM_PARTY_SUP_FAN_SPEED = "REKPartySupFanSpeed"
PARAM_PARTY_SUP_FAN_SPEED_ID = 74
PARAM_PARTY_EXH_FAN_SPEED = "REKPartyExhFanSpeed"
PARAM_PARTY_EXH_FAN_SPEED_ID = 260
PARAM_PARTY_DURATION = "REKPartyDur"
PARAM_PARTY_DURATION_ID = 141
PARAM_PARTY_SETPOINT = "REKPartySetPoint"
PARAM_PARTY_SETPOINT_ID = 261

PARAM_OUTSIDE_DURATION = "REKOutDur"
PARAM_OUTSIDE_DURATION_ID = 142

PARAM_AIRING_EXH_FAN_SPEED = "REKAiringExhFanSpeed"
PARAM_AIRING_EXH_FAN_SPEED_ID = 75
PARAM_AIRING_DURATION = "REKAiringDur"
PARAM_AIRING_DURATION_ID = 143

# Read-only remaining-time countdowns (editParams.data only; minutes).
PARAM_TIME_TO_END_PARTY = "REKtimeToEndParty"
PARAM_TIME_TO_END_PARTY_ID = 444
PARAM_TIME_TO_END_OUTSIDE = "REKtimeToEndOut"
PARAM_TIME_TO_END_OUTSIDE_ID = 445
PARAM_TIME_TO_END_AIRING = "REKtimeToEndAiring"
PARAM_TIME_TO_END_AIRING_ID = 446

# Bypass mode in editParams.data only (write by numeric id).
# Writable wire values live in bypass_mode.BypassMode.
PARAM_BYPASS_MODE = "BYPmodSett"
PARAM_BYPASS_MODE_ID = 342

# Live bypass companion readouts in regParams.curr (not user writes).
PARAM_BYPASS_MOTOR_STATE = "BYPmodState"
PARAM_BYPASS_OPEN_LEVEL = "BYPcurControl"
