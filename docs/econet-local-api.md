# ecoNET300 local HTTP API — ecoVENT recuperator

LAN `/econet/…` reference for this ecoVENT module. Includes only facts confirmed on this installation.

| | |
| --- | --- |
| Host | `http://<module-ip>` |
| Auth | HTTP Basic (`WWW-Authenticate: Basic realm="Password protected area"`) |
| Server | `lighttpd/1.4.35` |
| Controller / protocol | `ecoVENT` / `gm3_pomp` (`/econet/sysParams`) |
| Remote menu | `false` |
| `regRefresh` | `5` (seconds) |
| Firmware (A / panel / ecoNET) | `S003.80` / `S003.56_1.80` / `3.2.3881` |

Placeholders: `<module-ip>`, `<device-uid>`, `<redacted>`.

> **Security:** HTTP Basic over plain HTTP. Keep the module and Home Assistant on a trusted LAN or VPN. Do not expose the module to the Internet. Local credentials are not the econet24 account.

---

## 1. Calling convention

Every call is `GET` with Basic auth and a JSON body. Unauthenticated calls return **401**.

```bash
curl -sS -u 'USER' 'http://<module-ip>/econet/sysParams'
```

| Identifier | Source | Use |
| --- | --- | --- |
| **name** | `/econet/editParams` `data[*].name`, `/econet/regParams` `curr` keys | Read |
| **id** | `/econet/editParams` `data` keys, `/econet/regParams` `currNumbers` values | Write (`newParamName=<id>`) |

Writes use the numeric id. String names in `newParamName` are not established here. `data[<id>].edit === true` means the module marks the parameter writable; success is still defined by `/econet/newParam` returning `result: "OK"` (§2.4).

---

## 2. Endpoints

| Path | Role |
| --- | --- |
| `/econet/sysParams` | Identity, versions, poll hint |
| `/econet/regParams` | Live subset (`curr`) |
| `/econet/editParams` | Full registry + info slots |
| `/econet/newParam` | Write by numeric id |
| `/econet/rm*` | Unavailable (`remoteMenu=false`) |

### 2.1 `/econet/sysParams`

Module identity, versions, poll hint, and LAN/Wi‑Fi status. Identity values for this module are in the header table above.

| Field | Meaning |
| --- | --- |
| `uid` | Device UID |
| `controllerID` | Controller identity string |
| `protocolType` | Protocol type string |
| `remoteMenu` | When `false`, `/econet/rm*` endpoints are unavailable |
| `softVer` / `moduleASoftVer` / `modulePanelSoftVer` | Software version strings |
| `regRefresh` | Suggested `/econet/regParams` poll interval (seconds) |
| `settingsVer` | Settings generation |
| `wifi` | Wi‑Fi associated (`true` / `false`) |
| `wlan0` | Module IPv4 address on Wi‑Fi |
| `signal` | Wi‑Fi RSSI in dBm (string, e.g. `"-60"`) |
| `quality` | Wi‑Fi link quality `0`–`100` |
| `password` / `login` / `key` / `ssid` / `servicePassword` | Secrets — do not log |

`ssid` is the connected network name (secret — redact in logs/diagnostics). A related quality percentage also appears in `editParams.informationParams` slot `234` (unit index `2`); prefer `sysParams.signal` / `sysParams.quality` as the canonical Wi‑Fi strength source.

### 2.2 `/econet/regParams`

| Key | Role |
| --- | --- |
| `curr` | Live name→value (subset of the registry) |
| `currNumbers` | name→id |
| `currUnits` | name→unit index (subset of `curr`) |
| `settingsVer` / `editableParamsVer` | Version stamps |

Poll on `regRefresh` from `/econet/sysParams`. Re-fetch `/econet/editParams` when the version stamps change, or when a needed name is absent from `curr`.

### 2.3 `/econet/editParams`

| Key | Role |
| --- | --- |
| `data` | Full registry, keyed by stringified id |
| `choiceParams` | Discrete-option metadata for some ids |
| `informationParams` | Read-only display slots (see §3.3) |
| `editableParamsVer` | Version integer |

`data[<id>]` fields:

| Field | Meaning |
| --- | --- |
| `name` | Read key |
| `value` | Current value |
| `edit` | Writable per module metadata |
| `minv` / `maxv` | Inclusive limits when not both `0`; `0`/`0` = no range advertised |
| `mult` | Scale factor |
| `unit` | Unit index (integer). No local unit-name endpoint; `currUnits` matches where both exist |

### 2.4 `/econet/newParam`

```
GET /econet/newParam?newParamName=<id>&newParamValue=<wire>
```

Success body:

```json
{"paramName": "17", "paramValue": 3, "result": "OK"}
```

| Field | Meaning |
| --- | --- |
| `paramName` | Echo of `newParamName` |
| `paramValue` | Echo of accepted value |
| `result` | `"OK"` on success |

Any non-object response or `result` ≠ `"OK"` is failure. Confirm by re-reading `curr` when present, otherwise `data[<id>].value`. Parameters that appear only in `editParams.data` (absent from `regParams.curr`) can still be writable; verify with `newParam` and a follow-up `editParams` read.

---

## 3. Parameter catalog

Parameters used by the integration sensors/select, confirmed mode maps, and other writable parameters verified on this module (not necessarily exposed by the integration yet).

### 3.1 Fan speeds — `/econet/regParams` `curr`

`edit: false`. Unit index `6` (presented as `%`).

| name | id | Role |
| --- | --- | --- |
| `REKcurSupFanSpeed` | `30` | Supply fan speed |
| `REKcurExhFanSpeed` | `31` | Exhaust fan speed |

### 3.2 Air-path temperatures — `/econet/regParams` `curr`

`edit: false`. Unit index `1` (presented as °C).

| name | id | Role |
| --- | --- | --- |
| `REKcurSupTemp` | `34` | Supply air temperature |
| `REKcurIntTemp` | `40` | Intake air temperature |
| `REKcurExtTemp` | `36` | Extracted air temperature |
| `REKcuExhTemp` | `37` | Exhaust air temperature |

### 3.3 Filter status — `/econet/editParams` `informationParams` slots 61–64

Read-only slots (not `data` ids). Shape: `[visible, [[value, unitIndex, …]]]`.

| Slot | Role | `unitIndex` |
| --- | --- | --- |
| `61` | Supply filter depletion | `2` |
| `62` | Extract filter depletion | `2` |
| `63` | Supply filter operation days | `13` |
| `64` | Extract filter operation days | `13` |

Cross-check against named `FILTERtimeToAlarm` in `data` (id `574` here; `edit: true`, `minv`/`maxv` `1`/`1500`). Depletion ≈ `days / FILTERtimeToAlarm × 100`. The integration exposes diagnostic **days to alert** sensors as remaining days until that threshold (`FILTERtimeToAlarm − operation days`, floored at `0`); it does not expose the raw threshold as a writable setting.

### 3.4 `REKWS1` — operation mode (id 17)

Halt + Mode 1–4. `edit: true`, in `curr`. Write: `/econet/newParam?newParamName=17`.

| Wire | Option |
| --- | --- |
| `3` | Mode 1 |
| `4` | Mode 2 |
| `5` | Mode 3 |
| `6` | Halt |
| `7` | Mode 4 |
| other | Unknown |

#### Related User Mode parameters

`edit: true`, `mult` `1`. Write via `/econet/newParam?newParamName=<id>`. Confirm via `curr` when present, otherwise `data[<id>].value`. Modes 1–3 appear in `regParams.curr`; Mode 4 is `editParams.data` only on this module.

| name | id | Role | `minv` / `maxv` | `unit` | in `curr` |
| --- | --- | --- | --- | --- | --- |
| `REKUser1SupFanSpeed` | `273` | User Mode 1 supply fan velocity | `20` / `100` | `6` (%) | yes |
| `REKUser1ExhFanSpeed` | `276` | User Mode 1 exhaust fan velocity | `20` / `100` | `6` (%) | yes |
| `REKUser1SetPoint` | `286` | User Mode 1 preset temperature | `8` / `30` | `1` (°C) | yes |
| `REKUser2SupFanSpeed` | `274` | User Mode 2 supply fan velocity | `20` / `100` | `6` (%) | yes |
| `REKUser2ExhFanSpeed` | `277` | User Mode 2 exhaust fan velocity | `20` / `100` | `6` (%) | yes |
| `REKUser2SetPoint` | `287` | User Mode 2 preset temperature | `8` / `30` | `1` (°C) | yes |
| `REKUser3SupFanSpeed` | `275` | User Mode 3 supply fan velocity | `20` / `100` | `6` (%) | yes |
| `REKUser3ExhFanSpeed` | `278` | User Mode 3 exhaust fan velocity | `20` / `100` | `6` (%) | yes |
| `REKUser3SetPoint` | `288` | User Mode 3 preset temperature | `8` / `30` | `1` (°C) | yes |
| `REKUser4SupFanSpeed` | `469` | User Mode 4 supply fan velocity | `20` / `100` | `6` (%) | no |
| `REKUser4ExhFanSpeed` | `470` | User Mode 4 exhaust fan velocity | `20` / `100` | `6` (%) | no |
| `REKUser4SetPoint` | `468` | User Mode 4 preset temperature | `8` / `30` | `1` (°C) | no |

Modes 3–4 preset temperatures are °C in the UI; some `editParams` dumps advertise `unit` `0` for those two ids — treat as °C.

### 3.5 `REKWS4` — additional / timed work mode (id 20)

Off / Outside / Party / Airing. `edit: true`, in `curr`. Write: `/econet/newParam?newParamName=20`.

| Wire | Option |
| --- | --- |
| `0` | Off |
| `1` | Outside |
| `2` | Party |
| `4` | Airing |
| other | Unknown |

From Halt, Outside / Party / Airing leaves Halt and runs Mode 1 in one `REKWS4` write (no separate `REKWS1` write for that transition).

#### Related Airing parameters

Writable Airing presets are `edit: true`, in `regParams.curr`. Write via `/econet/newParam?newParamName=<id>`; confirm via `curr` or `data[<id>].value`. No separate Airing supply-fan velocity name is present in this module's registry (exhaust only).

| name | id | Role | `minv` / `maxv` | `unit` |
| --- | --- | --- | --- | --- |
| `REKAiringExhFanSpeed` | `75` | Airing mode exhaust fan velocity | `20` / `100` | `6` (%) |
| `REKAiringDur` | `143` | Airing mode duration | `0` / `20` | `3` (minutes) |

##### Airing remaining time — `REKtimeToEndAiring` (id 446)

Read-only countdown while Airing is active. `edit: false`. Present only in `editParams.data` (not in `regParams.curr`). `mult` `1`, `unit` `3` (minutes). `-1` when inactive; positive remaining minutes when Airing is running. The integration maps `-1` to `0`.

#### Related Party parameters

`edit: true`, `mult` `1`. Write via `/econet/newParam?newParamName=<id>`. Confirm via `curr` when present, otherwise `data[<id>].value`.

| name | id | Role | `minv` / `maxv` | `unit` | in `curr` |
| --- | --- | --- | --- | --- | --- |
| `REKPartySupFanSpeed` | `74` | Party mode supply fan velocity | `20` / `100` | `6` (%) | no |
| `REKPartyExhFanSpeed` | `260` | Party mode exhaust fan velocity | `20` / `100` | `6` (%) | yes |
| `REKPartyDur` | `141` | Party mode duration | `0` / `10` | `4` (hours) | yes |
| `REKPartySetPoint` | `261` | Party mode preset temperature | `8` / `30` | `1` (°C) | yes |

##### Party remaining time — `REKtimeToEndParty` (id 444)

Read-only countdown while Party is active. `edit: false`. Present only in `editParams.data` (not in `regParams.curr`). `mult` `1`, advertised `unit` `4` (hours). **Unit quirk:** the live countdown is in **minutes**, not hours (e.g. ~`180` after a `3` hour Party duration). `-1` when inactive; positive remaining minutes when Party is running. The integration presents this sensor in minutes and maps `-1` to `0`.

#### Related Outside parameters

`edit: true`, `mult` `1`. Present only in `editParams.data` (not in `regParams.curr`). Write via `/econet/newParam?newParamName=<id>`; confirm via `data[<id>].value`. No Outside fan-velocity names are present in this module's registry.

| name | id | Role | `minv` / `maxv` | `unit` |
| --- | --- | --- | --- | --- |
| `REKOutDur` | `142` | Outside mode duration | `0` / `10` | `4` (hours) |

##### Outside remaining time — `REKtimeToEndOut` (id 445)

Read-only countdown while Outside is active. `edit: false`. Present only in `editParams.data` (not in `regParams.curr`). `mult` `1`, advertised `unit` `4` (hours). **Unit quirk:** same as Party — countdown is in **minutes**, not hours. `-1` when inactive; positive remaining minutes when Outside is running. The integration presents this sensor in minutes and maps `-1` to `0`.

### 3.6 Summer / winter mode

#### `REKWS2` — mode switch (id 18)

Summer / winter mode select. `edit: true`. Present only in `editParams.data` (not in `regParams.curr` / `choiceParams`). No range advertised (`minv`/`maxv` `0`/`0`), `mult` `1`, `unit` `0`. Write: `/econet/newParam?newParamName=18`. Confirm via `data["18"].value`.

| Wire | Option |
| --- | --- |
| `1` | Summer |
| `2` | Winter |
| `5` | Auto |
| `8` | Ventilation |
| other | Unknown |

#### Related setpoints

Both are `edit: true` and present only in `editParams.data`. `mult` `1`, `unit` `0`. Write via `/econet/newParam?newParamName=<id>`; confirm via `data[<id>].value`.

| name | id | Role | `minv` / `maxv` |
| --- | --- | --- | --- |
| `REKwinterActiveTemp` | `137` | Winter mode turn-on temperature | `-20` / `20` |
| `REKsummerHyst` | `138` | Summer mode turn-on threshold (ecoNET name: hysteresis; treated as absolute °C like winter) | `0` / `20` |

Resolved / displayed Summer–Winter status (including Auto — Summer / Winter) is **not** this setting alone — see §3.8 slot `105`.

### 3.7 Bypass

#### `BYPmodSett` — mode / position (id 342)

Bypass position / mode. `edit: true`. Present only in `editParams.data` (not in `regParams.curr` / `choiceParams`). No range advertised (`minv`/`maxv` `0`/`0`), `mult` `1`, `unit` `0`. Write: `/econet/newParam?newParamName=342`. Confirm via `data["342"].value`.

Values are large integers (packed bitfield: base `257` OR mode flag — Close `+8`, Open `+16`, Auto `+32`).

| Wire | Option |
| --- | --- |
| `289` | Auto |
| `273` | Open |
| `265` | Close |
| other | Unknown |

#### `BYPmodState` — Bypass / Rotor motor state (id 235)

Bypass / Rotor motor state. Live state (not a user setting) despite `edit: true` in metadata. In `regParams.curr`. No range advertised (`minv`/`maxv` `0`/`0`), `mult` `1`, `unit` `0`.

| Wire | Option |
| --- | --- |
| `0` | Off |
| `1` | On |
| other | Unknown |

#### `BYPcurControl` — bypass open level (id 343)

Live bypass open level in percent. In `regParams.curr`. `edit: true` in metadata (live control readout). No range advertised (`minv`/`maxv` `0`/`0`), `mult` `1`, `unit` `6` (%). `0.0` when closed/idle; `100.0` when `BYPmodSett` is Open; intermediate values while opening.

### 3.8 Current work status — `informationParams` slots `101`–`105`

econet24 **Current work status** panel (separate from the Summer / winter mode settings in §3.6). Rows below follow UI order. All are `informationParams` slots (not `regParams.curr`). Temperature slots use unit index `1` (°C); mode slots use `[true, [["<wire>", 0, 1]]]`.

| Slot | UI row | Shape / unit | Notes |
| --- | --- | --- | --- |
| `101` | Current comfort temperature | °C (`unit` `1`) | Matches live `REKcurSetPoint` / active mode preset |
| `102` | Current leading temperature | °C (`unit` `1`) | Leading control temperature |
| `103` | Control mode | wire `0`/`1` | Heating / Cooling (see below) |
| `104` | External temperature | °C (`unit` `1`) | Matches `REKcurIntTemp` (intake); not `REKcurExtTemp` (extracted) |
| `105` | Summer / Winter | wire enum | Setting + resolved Auto season (see below) |

#### Control mode — slot `103`

| Wire | Meaning |
| --- | --- |
| `0` | Heating |
| `1` | Cooling |
| other | Unknown |

Heating when comfort setpoint is above leading temperature; Cooling when below. Slot `131` matched `103` in every dump; treat `103` as canonical.

#### Summer / Winter — slot `105`

Status row for season / ventilation. This is **not** the writable `REKWS2` setting (§3.6) and **not** slot `91` (bypass activity).

| Wire | Meaning | Notes |
| --- | --- | --- |
| `0` | Summer | With `REKWS2=1` |
| `1` | Winter | With `REKWS2=2` |
| `2` | Auto — Summer | With `REKWS2=5` while status showed Summer |
| `3` | Auto — Winter | **Assumption** (symmetric to `2`; not yet observed) |
| `4` | Ventilation | With `REKWS2=8` |
| other | Unknown | |

When `REKWS2` is Auto (`5`), slot `105` is the resolved season (`2` / assumed `3`). Forced Summer / Winter / Ventilation map to `0` / `1` / `4`. Slot `91` tracks bypass only (`"0"` when `BYPmodState` On, `"1"` when Off).
