# Govee Protocol Reference

A comprehensive technical reference for Govee device communication protocols, compiled from official documentation, PCAP analysis of the Android app, and community reverse engineering efforts.

**Last Updated:** January 2026
**PCAP Source:** `logs/PCAPdroid_09_Jan_19_27_26.pcap` (Android app capture)

---

## Table of Contents

1. [Protocol Overview](#1-protocol-overview)
2. [Official Platform API v2.0](#2-official-platform-api-v20)
3. [Curl Testing Reference](#3-curl-testing-reference)
4. [AWS IoT MQTT (Undocumented)](#4-aws-iot-mqtt-undocumented)
5. [Undocumented Internal API](#5-undocumented-internal-api-app2goveecom)
6. [LAN API (UDP)](#6-lan-api-udp)
7. [BLE Protocol](#7-ble-protocol)
8. [State Management](#8-state-management)
9. [Device Capabilities](#9-device-capabilities)
10. [Scene & DIY Modes](#10-scene--diy-modes)
11. [PCAP Analysis Details](#11-pcap-analysis-details)
12. [References](#12-references)

---

## 1. Protocol Overview

Govee devices support multiple communication protocols, each with distinct characteristics:

| Protocol | Latency | Auth Method | Use Case | Rate Limits |
|----------|---------|-------------|----------|-------------|
| **Platform API v2** | 2-4s | API Key | Device control, state query | 10K/day |
| **AWS IoT MQTT** | ~50ms | Certificates | Real-time state push | None known |
| **Official MQTT** | ~100ms | API Key | Event notifications | None known |
| **LAN UDP** | <10ms | None | Local control | None |
| **BLE** | <50ms | Pairing | Direct control | None |

### Communication Flow (from PCAP)

```
┌─────────────────┐     HTTPS/443     ┌──────────────────┐
│   Govee App     │◄─────────────────►│  app2.govee.com  │
│   (Android)     │                    │  (Auth + API)    │
└────────┬────────┘                    └──────────────────┘
         │
         │  MQTT/8883 (TLS + Mutual Auth)
         ▼
┌─────────────────────────────────────────────────────────┐
│         AWS IoT Core (us-east-1)                        │
│   aqm3wd1qlc3dy-ats.iot.us-east-1.amazonaws.com        │
│                                                         │
│   Topic: GA/{account-uuid}                              │
│   - Device state push notifications                     │
│   - Bidirectional command/response                      │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐     UDP 4001-4003  ┌──────────────────┐
│   Home Network  │◄─────────────────►│  Govee Devices   │
│                 │     (LAN API)      │                  │
└─────────────────┘                    └──────────────────┘
```

---

## 2. Official Platform API v2.0

### 2.1 Base Configuration

| Parameter | Value |
|-----------|-------|
| **Base URL** | `https://openapi.api.govee.com/router/api/v1` |
| **Auth Header** | `Govee-API-Key: {your-api-key}` |
| **Content-Type** | `application/json` |

### 2.2 Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/user/devices` | GET | List all devices |
| `/device/state` | POST | Query device state |
| `/device/control` | POST | Send control command |
| `/device/scenes` | POST | Get dynamic scenes |
| `/device/diy-scenes` | POST | Get DIY scenes |

### 2.3 Request Format

All POST requests use this structure:

```json
{
  "requestId": "550e8400-e29b-41d4-a716-446655440000",
  "payload": {
    "sku": "H618E",
    "device": "8C:2E:9C:04:A0:03:82:D1",
    "capability": {
      "type": "devices.capabilities.TYPE",
      "instance": "INSTANCE_NAME",
      "value": "VALUE"
    }
  }
}
```

### 2.4 Response Format

```json
{
  "requestId": "550e8400-e29b-41d4-a716-446655440000",
  "code": 200,
  "msg": "success",
  "payload": {
    "sku": "H618E",
    "device": "8C:2E:9C:04:A0:03:82:D1",
    "capabilities": [
      {
        "type": "devices.capabilities.on_off",
        "instance": "powerSwitch",
        "state": { "value": 1 }
      },
      {
        "type": "devices.capabilities.range",
        "instance": "brightness",
        "state": { "value": 75 }
      },
      {
        "type": "devices.capabilities.color_setting",
        "instance": "colorRgb",
        "state": { "value": 16711680 }
      }
    ]
  }
}
```

### 2.5 Rate Limiting

**Limits:**
- 10,000 requests per day per account
- Per-minute limits (undocumented, ~10/min per device)

**Response Headers:**
```
API-RateLimit-Remaining: 95      # Per-minute remaining
API-RateLimit-Reset: 1704812400  # Per-minute reset timestamp
X-RateLimit-Remaining: 9500      # Per-day remaining
X-RateLimit-Reset: 1704844800    # Per-day reset timestamp
```

### 2.6 Control Examples

**Power On/Off:**
```json
{
  "type": "devices.capabilities.on_off",
  "instance": "powerSwitch",
  "value": 1
}
```

**Brightness (0-100):**
```json
{
  "type": "devices.capabilities.range",
  "instance": "brightness",
  "value": 75
}
```

**RGB Color (packed integer):**
```json
{
  "type": "devices.capabilities.color_setting",
  "instance": "colorRgb",
  "value": 16711680
}
```
*Note: RGB packed as `(R << 16) + (G << 8) + B`. 16711680 = RGB(255, 0, 0)*

**Color Temperature (Kelvin):**
```json
{
  "type": "devices.capabilities.color_setting",
  "instance": "colorTemperatureK",
  "value": 4500
}
```

**Segment Color (RGBIC devices):**
```json
{
  "type": "devices.capabilities.segment_color_setting",
  "instance": "segmentedColorRgb",
  "value": {
    "segment": [0, 1, 2, 3],
    "rgb": 255
  }
}
```

**Scene Activation:**
```json
{
  "type": "devices.capabilities.dynamic_scene",
  "instance": "lightScene",
  "value": {
    "id": 3853,
    "paramId": 4280
  }
}
```

### 2.7 Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Missing/invalid parameters |
| 401 | Authentication failure |
| 404 | Device/instance not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

## 3. Curl Testing Reference

Validated API testing with real device responses (H601F floor lamps with 7 segments).

### 3.1 Environment Setup

```bash
# Store your API key
export GOVEE_API_KEY="your-api-key-here"

# Base URL
export GOVEE_API="https://openapi.api.govee.com/router/api/v1"
```

### 3.2 List Devices

```bash
curl -s -X GET "$GOVEE_API/user/devices" \
  -H "Govee-API-Key: $GOVEE_API_KEY" \
  -H "Content-Type: application/json" | jq .
```

**Real Response (H601F - 7-segment floor lamp):**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "sku": "H601F",
      "device": "03:9C:DC:06:75:4B:10:7C",
      "deviceName": "Master F Left",
      "type": "devices.types.light",
      "capabilities": [
        {
          "type": "devices.capabilities.on_off",
          "instance": "powerSwitch",
          "parameters": {
            "dataType": "ENUM",
            "options": [
              {"name": "on", "value": 1},
              {"name": "off", "value": 0}
            ]
          }
        },
        {
          "type": "devices.capabilities.range",
          "instance": "brightness",
          "parameters": {
            "unit": "unit.percent",
            "dataType": "INTEGER",
            "range": {"min": 1, "max": 100, "precision": 1}
          }
        },
        {
          "type": "devices.capabilities.color_setting",
          "instance": "colorRgb",
          "parameters": {
            "dataType": "INTEGER",
            "range": {"min": 0, "max": 16777215, "precision": 1}
          }
        },
        {
          "type": "devices.capabilities.color_setting",
          "instance": "colorTemperatureK",
          "parameters": {
            "dataType": "INTEGER",
            "range": {"min": 2700, "max": 6500, "precision": 1}
          }
        },
        {
          "type": "devices.capabilities.segment_color_setting",
          "instance": "segmentedColorRgb",
          "parameters": {
            "dataType": "STRUCT",
            "fields": [
              {
                "fieldName": "segment",
                "size": {"min": 1, "max": 7},
                "dataType": "Array",
                "elementRange": {"min": 0, "max": 6},
                "elementType": "INTEGER",
                "required": true
              },
              {
                "fieldName": "rgb",
                "dataType": "INTEGER",
                "range": {"min": 0, "max": 16777215, "precision": 1},
                "required": true
              }
            ]
          }
        },
        {
          "type": "devices.capabilities.dynamic_scene",
          "instance": "lightScene",
          "parameters": {"dataType": "ENUM", "options": []}
        },
        {
          "type": "devices.capabilities.dynamic_scene",
          "instance": "diyScene",
          "parameters": {"dataType": "ENUM", "options": []}
        },
        {
          "type": "devices.capabilities.dynamic_scene",
          "instance": "snapshot",
          "parameters": {"dataType": "ENUM", "options": []}
        }
      ]
    }
  ]
}
```

### 3.3 Get Device State

```bash
curl -s -X POST "$GOVEE_API/device/state" \
  -H "Govee-API-Key: $GOVEE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "requestId": "state-001",
    "payload": {
      "sku": "H601F",
      "device": "03:9C:DC:06:75:4B:10:7C"
    }
  }' | jq .
```

**Real Response:**
```json
{
  "requestId": "state-001",
  "msg": "success",
  "code": 200,
  "payload": {
    "sku": "H601F",
    "device": "03:9C:DC:06:75:4B:10:7C",
    "capabilities": [
      {
        "type": "devices.capabilities.online",
        "instance": "online",
        "state": {"value": true}
      },
      {
        "type": "devices.capabilities.on_off",
        "instance": "powerSwitch",
        "state": {"value": 0}
      },
      {
        "type": "devices.capabilities.range",
        "instance": "brightness",
        "state": {"value": 20}
      },
      {
        "type": "devices.capabilities.color_setting",
        "instance": "colorRgb",
        "state": {"value": 0}
      },
      {
        "type": "devices.capabilities.color_setting",
        "instance": "colorTemperatureK",
        "state": {"value": 0}
      },
      {
        "type": "devices.capabilities.segment_color_setting",
        "instance": "segmentedColorRgb",
        "state": {"value": ""}
      },
      {
        "type": "devices.capabilities.dynamic_scene",
        "instance": "lightScene",
        "state": {"value": ""}
      }
    ]
  }
}
```

**Note:** Segment colors and active scenes return empty strings - this is a known API limitation.

### 3.4 Control Commands

**Power On:**
```bash
curl -s -X POST "$GOVEE_API/device/control" \
  -H "Govee-API-Key: $GOVEE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "requestId": "power-on-001",
    "payload": {
      "sku": "H601F",
      "device": "03:9C:DC:06:75:4B:10:7C",
      "capability": {
        "type": "devices.capabilities.on_off",
        "instance": "powerSwitch",
        "value": 1
      }
    }
  }' | jq .
```

**Response:**
```json
{
  "requestId": "power-on-001",
  "msg": "success",
  "code": 200,
  "capability": {
    "type": "devices.capabilities.on_off",
    "instance": "powerSwitch",
    "state": {"status": "success"},
    "value": 1
  }
}
```

**Set Brightness (50%):**
```bash
curl -s -X POST "$GOVEE_API/device/control" \
  -H "Govee-API-Key: $GOVEE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "requestId": "brightness-001",
    "payload": {
      "sku": "H601F",
      "device": "03:9C:DC:06:75:4B:10:7C",
      "capability": {
        "type": "devices.capabilities.range",
        "instance": "brightness",
        "value": 50
      }
    }
  }' | jq .
```

**Set RGB Color (Red = 16711680):**
```bash
curl -s -X POST "$GOVEE_API/device/control" \
  -H "Govee-API-Key: $GOVEE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "requestId": "color-001",
    "payload": {
      "sku": "H601F",
      "device": "03:9C:DC:06:75:4B:10:7C",
      "capability": {
        "type": "devices.capabilities.color_setting",
        "instance": "colorRgb",
        "value": 16711680
      }
    }
  }' | jq .
```

**Set Segment Colors (segments 0-2 = blue):**
```bash
curl -s -X POST "$GOVEE_API/device/control" \
  -H "Govee-API-Key: $GOVEE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "requestId": "segment-001",
    "payload": {
      "sku": "H601F",
      "device": "03:9C:DC:06:75:4B:10:7C",
      "capability": {
        "type": "devices.capabilities.segment_color_setting",
        "instance": "segmentedColorRgb",
        "value": {
          "segment": [0, 1, 2],
          "rgb": 255
        }
      }
    }
  }' | jq .
```

**Response:**
```json
{
  "requestId": "segment-001",
  "msg": "success",
  "code": 200,
  "capability": {
    "type": "devices.capabilities.segment_color_setting",
    "instance": "segmentedColorRgb",
    "state": {"status": "success"},
    "value": {"segment": [0, 1, 2], "rgb": 255}
  }
}
```

### 3.5 Get Dynamic Scenes

```bash
curl -s -X POST "$GOVEE_API/device/scenes" \
  -H "Govee-API-Key: $GOVEE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "requestId": "scenes-001",
    "payload": {
      "sku": "H601F",
      "device": "03:9C:DC:06:75:4B:10:7C"
    }
  }' | jq .
```

**Real Response (82 scenes for H601F):**
```json
{
  "requestId": "scenes-001",
  "msg": "success",
  "code": 200,
  "payload": {
    "sku": "H601F",
    "device": "03:9C:DC:06:75:4B:10:7C",
    "capabilities": [
      {
        "type": "devices.capabilities.dynamic_scene",
        "instance": "lightScene",
        "parameters": {
          "dataType": "ENUM",
          "options": [
            {"name": "Rainbow", "value": {"id": 17936, "paramId": 28098}},
            {"name": "Aurora", "value": {"id": 17937, "paramId": 28099}},
            {"name": "Glacier", "value": {"id": 17938, "paramId": 28100}},
            {"name": "Wave", "value": {"id": 17939, "paramId": 28101}},
            {"name": "Deep sea", "value": {"id": 17940, "paramId": 28102}},
            {"name": "Cherry blossoms", "value": {"id": 17941, "paramId": 28103}},
            {"name": "Firefly", "value": {"id": 17942, "paramId": 28104}},
            {"name": "Christmas", "value": {"id": 17961, "paramId": 28123}},
            {"name": "Halloween", "value": {"id": 17958, "paramId": 28120}},
            {"name": "Sunrise", "value": {"id": 17771, "paramId": 27933}},
            {"name": "Sunset", "value": {"id": 17772, "paramId": 27934}},
            {"name": "Sleep", "value": {"id": 17983, "paramId": 28145}},
            {"name": "Reading", "value": {"id": 17776, "paramId": 27938}},
            {"name": "Romantic", "value": {"id": 17998, "paramId": 28160}}
          ]
        }
      }
    ]
  }
}
```
*Note: Response truncated - actual response contains 82 scenes including nature, holidays, moods, activities, and space themes.*

### 3.6 Activate a Scene

```bash
curl -s -X POST "$GOVEE_API/device/control" \
  -H "Govee-API-Key: $GOVEE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "requestId": "scene-activate-001",
    "payload": {
      "sku": "H601F",
      "device": "03:9C:DC:06:75:4B:10:7C",
      "capability": {
        "type": "devices.capabilities.dynamic_scene",
        "instance": "lightScene",
        "value": {"id": 17937, "paramId": 28099}
      }
    }
  }' | jq .
```

### 3.7 Get DIY Scenes

```bash
curl -s -X POST "$GOVEE_API/device/diy-scenes" \
  -H "Govee-API-Key: $GOVEE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "requestId": "diy-scenes-001",
    "payload": {
      "sku": "H601F",
      "device": "03:9C:DC:06:75:4B:10:7C"
    }
  }' | jq .
```

**Real Response:**
```json
{
  "requestId": "diy-scenes-001",
  "msg": "success",
  "code": 200,
  "payload": {
    "sku": "H601F",
    "device": "03:9C:DC:06:75:4B:10:7C",
    "capabilities": [
      {
        "type": "devices.capabilities.dynamic_scene",
        "instance": "diyScene",
        "parameters": {
          "dataType": "ENUM",
          "options": [
            {"name": "tj diy", "value": 21104832}
          ]
        }
      }
    ]
  }
}
```

### 3.8 RGB Color Values Reference

| Color | RGB | Packed Integer |
|-------|-----|----------------|
| Red | (255, 0, 0) | 16711680 |
| Green | (0, 255, 0) | 65280 |
| Blue | (0, 0, 255) | 255 |
| White | (255, 255, 255) | 16777215 |
| Yellow | (255, 255, 0) | 16776960 |
| Cyan | (0, 255, 255) | 65535 |
| Magenta | (255, 0, 255) | 16711935 |
| Orange | (255, 165, 0) | 16753920 |
| Purple | (128, 0, 128) | 8388736 |
| Pink | (255, 192, 203) | 16761035 |

**Python conversion:**
```python
def rgb_to_int(r, g, b):
    return (r << 16) + (g << 8) + b

def int_to_rgb(color_int):
    r = (color_int >> 16) & 0xFF
    g = (color_int >> 8) & 0xFF
    b = color_int & 0xFF
    return (r, g, b)
```

### 3.9 Device Type Notes

**H601F (Floor Lamp):**
- 7 addressable segments (0-6)
- Color temp range: 2700K - 6500K
- Brightness: 1-100%
- 82 dynamic scenes available
- Supports DIY scenes and snapshots

**SameModeGroup:**
- Virtual device for group control
- Only supports powerSwitch capability
- Cannot query state (no response)

---

## 4. AWS IoT MQTT (Undocumented)

This protocol provides real-time device state updates and is used by the Govee mobile app for instant synchronization.

### 3.1 Connection Details

| Parameter | Value |
|-----------|-------|
| **Endpoint** | `aqm3wd1qlc3dy-ats.iot.us-east-1.amazonaws.com` |
| **Port** | 8883 (MQTT over TLS) |
| **Authentication** | Mutual TLS with client certificates |
| **Keepalive** | 120 seconds |

*Endpoint confirmed via PCAP analysis: IP 54.147.158.57*

### 3.2 Authentication Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  1. Login to app2.govee.com                                       │
│     POST /account/rest/account/v1/login                          │
│     Body: { email, password, client }                            │
│     Returns: { token, accountId, topic }                         │
├──────────────────────────────────────────────────────────────────┤
│  2. Get IoT Credentials                                          │
│     GET /app/v1/account/iot/key                                  │
│     Header: Authorization: Bearer {token}                        │
│     Returns: { endpoint, p12, p12_pass } or PEM format           │
├──────────────────────────────────────────────────────────────────┤
│  3. Extract Certificates                                         │
│     Parse P12/PFX container (base64 decoded)                     │
│     Extract: client_cert.pem, client_key.pem                     │
│     Use Amazon Root CA 1 for server verification                 │
├──────────────────────────────────────────────────────────────────┤
│  4. Connect to AWS IoT                                           │
│     Client ID: AP/{accountId}/{uuid}                             │
│     Subscribe: GA/{account-topic-from-login}                     │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 Client ID Format

```
AP/{accountId}/{clientId}
```
- `accountId`: Numeric account ID from login response (as string)
- `clientId`: 32-character UUID (generated client-side)

### 3.4 Message Formats

**Incoming State Update:**
```json
{
  "device": "8C:2E:9C:04:A0:03:82:D1",
  "sku": "H6072",
  "state": {
    "onOff": 1,
    "brightness": 50,
    "color": {
      "r": 255,
      "g": 0,
      "b": 0
    },
    "colorTemInKelvin": 0
  }
}
```

**State Request (Outbound):**
```json
{
  "msg": {
    "cmd": "status",
    "cmdVersion": 2,
    "transaction": "v_1704812400000",
    "type": 0
  }
}
```

**Power Control (Outbound):**
```json
{
  "msg": {
    "cmd": "turn",
    "data": { "val": 1 },
    "cmdVersion": 0,
    "transaction": "v_1704812400000",
    "type": 1
  }
}
```

**Brightness Control (Outbound):**
```json
{
  "msg": {
    "cmd": "brightness",
    "data": { "val": 75 },
    "cmdVersion": 0,
    "transaction": "v_1704812400000",
    "type": 1
  }
}
```

**Color Control (Outbound):**
```json
{
  "msg": {
    "cmd": "colorwc",
    "data": {
      "color": { "r": 255, "g": 0, "b": 128 },
      "colorTemInKelvin": 0
    },
    "cmdVersion": 0,
    "transaction": "v_1704812400000",
    "type": 1
  }
}
```

**BLE Passthrough (ptReal):**
```json
{
  "msg": {
    "cmd": "ptReal",
    "data": {
      "command": ["MwUEzycAAAAAAAAAAAAAAAAAANo="]
    },
    "cmdVersion": 0,
    "transaction": "v_1704812400000",
    "type": 1
  }
}
```

### 3.5 PCAP Traffic Analysis

From the captured PCAP file:

| Metric | Value |
|--------|-------|
| Session Duration | 296.2 seconds |
| Total Packets | 253 |
| Data Transferred | 64,307 bytes |
| Outbound Messages | 61 |
| Inbound Messages | 78 |
| Typical Request Size | ~205 bytes |
| Typical Response Size | 700-2000 bytes |

**Timing Pattern:**
- Initial TLS handshake: ~5 seconds
- State request/response: <1 second round-trip
- Idle keepalive: No activity for up to 54 seconds observed

---

## 5. Undocumented Internal API (app2.govee.com)

Used by the Govee mobile app for extended functionality not available in the public API.

### 4.1 Base Configuration

| Parameter | Value |
|-----------|-------|
| **Base URL** | `https://app2.govee.com` |
| **User-Agent** | `GoveeHome/5.6.01 (com.ihoment.GoVeeSensor; build:2; iOS 16.5.0) Alamofire/5.6.4` |

### 4.2 Authentication

**Login Request:**
```http
POST /account/rest/account/v1/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "client": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Login Response:**
```json
{
  "status": 200,
  "message": "Login successful",
  "client": {
    "A": "encrypted_value",
    "B": "encrypted_value",
    "accountId": 12345678,
    "client": "550e8400-e29b-41d4-a716-446655440000",
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "tokenExpireCycle": 604800,
    "topic": "GA/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

**Authenticated Request Headers:**
```http
Authorization: Bearer {token}
appVersion: 5.6.01
clientId: {uuid}
clientType: 1
iotVersion: 0
timestamp: 1704812400000
```

### 4.3 Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/account/rest/account/v1/login` | POST | User login |
| `/account/rest/v1/first/refresh-tokens` | POST | Refresh auth tokens |
| `/app/v1/account/iot/key` | GET | Get AWS IoT credentials |
| `/device/rest/devices/v1/list` | POST | List devices with full details |
| `/device/rest/devices/v1/control` | POST | Control devices |
| `/appsku/v1/light-effect-libraries` | GET | Get scene catalog |
| `/appsku/v2/devices/scenes/attributes` | GET | Get scene attributes |
| `/appsku/v1/diys/groups-diys` | GET | Get DIY scenes |
| `/bff-app/v1/exec-plat/home` | GET | Get One-Click/Tap-to-Run |

### 4.4 Scene Library Request

```http
GET /appsku/v1/light-effect-libraries?sku=H6072
AppVersion: 5.6.01
```

**Response:**
```json
{
  "data": {
    "categories": [
      {
        "categoryId": 1,
        "categoryName": "Dynamic",
        "scenes": [
          {
            "sceneId": 130,
            "sceneName": "Forest",
            "sceneCode": 10191,
            "sceneType": 1,
            "lightEffects": [
              {
                "scenceParamId": 123,
                "scenceParam": "base64-encoded-animation-data"
              }
            ]
          }
        ]
      },
      {
        "categoryId": 2,
        "categoryName": "Cozy",
        "scenes": [...]
      }
    ]
  }
}
```

### 4.5 Rate Limits

- Login: 30 attempts per 24 hours
- API calls: Undocumented, but appears generous

---

## 6. LAN API (UDP)

Local network control without cloud dependency. Must be enabled in Govee app device settings.

### 5.1 Network Configuration

| Parameter | Value |
|-----------|-------|
| **Multicast Address** | `239.255.255.250` |
| **Discovery Port** | 4001 (device listens) |
| **Response Port** | 4002 (client listens) |
| **Command Port** | 4003 (device listens) |
| **Protocol** | UDP |

### 5.2 Device Discovery

**Scan Request (to 239.255.255.250:4001):**
```json
{
  "msg": {
    "cmd": "scan",
    "data": {
      "account_topic": "reserve"
    }
  }
}
```

**Scan Response (from device to client:4002):**
```json
{
  "msg": {
    "cmd": "scan",
    "data": {
      "ip": "192.168.1.23",
      "device": "1F:80:C5:32:32:36:72:4E",
      "sku": "H618E",
      "bleVersionHard": "3.01.01",
      "bleVersionSoft": "1.03.01",
      "wifiVersionHard": "1.00.10",
      "wifiVersionSoft": "1.02.03"
    }
  }
}
```

### 5.3 Control Commands (to device-ip:4003)

**Power Control:**
```json
{"msg": {"cmd": "turn", "data": {"value": 1}}}
```

**Brightness:**
```json
{"msg": {"cmd": "brightness", "data": {"value": 75}}}
```

**Color/Temperature:**
```json
{
  "msg": {
    "cmd": "colorwc",
    "data": {
      "color": {"r": 255, "g": 0, "b": 128},
      "colorTemInKelvin": 0
    }
  }
}
```

**Status Query:**
```json
{"msg": {"cmd": "devStatus", "data": {}}}
```

**Status Response:**
```json
{
  "msg": {
    "cmd": "devStatus",
    "data": {
      "onOff": 1,
      "brightness": 100,
      "color": {"r": 255, "g": 0, "b": 0},
      "colorTemInKelvin": 0
    }
  }
}
```

### 5.4 BLE Passthrough (ptReal)

Send BLE commands through WiFi for devices supporting it:

```json
{
  "msg": {
    "cmd": "ptReal",
    "data": {
      "command": ["MwUEzycAAAAAAAAAAAAAAAAAANo="]
    }
  }
}
```

### 5.5 Supported Devices

Devices with confirmed LAN API support:
- H619Z, H6072, H619C, H7060, H619B
- H6066, H619D, H619E, H61A1, H61A3
- H61A2, H618A, H619A, H61A0, H6110
- H6117, H6159, H6163, H6141, H6052
- H6144, H615A, H6056, H6143, H6076
- H6062, H6061, and more

### 5.6 Python Implementation

```python
import socket
import json

MULTICAST_GROUP = '239.255.255.250'
DISCOVERY_PORT = 4001
COMMAND_PORT = 4003

def discover_devices(timeout=5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(timeout)

    # Bind to response port
    sock.bind(('', 4002))

    message = json.dumps({
        "msg": {"cmd": "scan", "data": {"account_topic": "reserve"}}
    }).encode()

    sock.sendto(message, (MULTICAST_GROUP, DISCOVERY_PORT))

    devices = []
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            devices.append(json.loads(data.decode()))
        except socket.timeout:
            break

    sock.close()
    return devices

def send_command(device_ip, cmd, data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = json.dumps({"msg": {"cmd": cmd, "data": data}}).encode()
    sock.sendto(message, (device_ip, COMMAND_PORT))
    sock.close()

# Example usage
devices = discover_devices()
for d in devices:
    ip = d['msg']['data']['ip']
    send_command(ip, "turn", {"value": 1})  # Turn on
    send_command(ip, "brightness", {"value": 50})  # 50% brightness
```

---

## 7. BLE Protocol

Direct Bluetooth Low Energy control for devices without WiFi or for local-only operation.

### 6.1 Service Configuration

| Parameter | Value |
|-----------|-------|
| **Service UUID** | `00010203-0405-0607-0809-0a0b0c0d1910` |
| **Write Characteristic** | `00010203-0405-0607-0809-0a0b0c0d2b11` |
| **Read Characteristic** | `00010203-0405-0607-0809-0a0b0c0d2b10` |

### 6.2 Packet Structure

All commands are **20 bytes** with XOR checksum:

```
┌──────────┬─────────┬──────────┬──────────────────┬──────────┐
│ ID (1B)  │ Cmd(1B) │ Mode(1B) │ Data (16B)       │ XOR (1B) │
└──────────┴─────────┴──────────┴──────────────────┴──────────┘
```

### 6.3 Identifier Bytes

| Byte | Purpose |
|------|---------|
| `0x33` | Standard command |
| `0xAA` | Keep-alive signal |
| `0xA1` | DIY mode data |
| `0xA3` | Multi-packet data |

### 6.4 Command Types

| Command | Byte | Description |
|---------|------|-------------|
| Power | `0x01` | On/Off control |
| Brightness | `0x04` | Brightness level |
| Color/Mode | `0x05` | Color and mode operations |
| Segment | `0x0B` | Segment control |
| Gradient | `0x14` | Gradient toggle |

### 6.5 Checksum Calculation

```python
def calculate_checksum(data: list[int]) -> int:
    """XOR all bytes together"""
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum & 0xFF

def build_packet(data: list[int]) -> bytes:
    """Build 20-byte packet with checksum"""
    packet = list(data)
    while len(packet) < 19:
        packet.append(0x00)
    packet.append(calculate_checksum(packet))
    return bytes(packet)
```

### 6.6 Command Examples

**Power On:**
```
33 01 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 33
```

**Power Off:**
```
33 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 32
```

**Brightness (50% = 0x80):**
```
33 04 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 B7
```

**RGB Color (Manual Mode):**
```
33 05 02 [R] [G] [B] 00 00 00 00 00 00 00 00 00 00 00 00 00 [XOR]
```

**Enable Gradient:**
```
33 14 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 26
```

### 6.7 Color Mode Bytes (after 0x05)

| Byte | Mode |
|------|------|
| `0x02` | Manual RGB |
| `0x01` | Music mode |
| `0x04` | Scene mode |
| `0x05` | Preset scenes |
| `0x0A` | DIY mode |
| `0x0B` | Segment color |

### 6.8 Scene Activation

```
33 05 04 [SceneCode_Low] [SceneCode_High] 00...00 [XOR]
```

Scene codes from the scene library API are split little-endian:
- Scene code 10191 = 0x27CF
- Packet: `33 05 04 CF 27 00...00 [XOR]`

### 6.9 Keep-Alive

Send every 2 seconds to maintain connection:
```
AA 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 AB
```

### 6.10 Python Implementation

```python
import asyncio
from bleak import BleakClient

WRITE_UUID = "00010203-0405-0607-0809-0a0b0c0d2b11"

def build_packet(data: list[int]) -> bytes:
    packet = list(data)
    while len(packet) < 19:
        packet.append(0x00)
    checksum = 0
    for b in packet:
        checksum ^= b
    packet.append(checksum)
    return bytes(packet)

async def control_light(address: str):
    async with BleakClient(address) as client:
        # Power on
        await client.write_gatt_char(
            WRITE_UUID,
            build_packet([0x33, 0x01, 0x01])
        )

        # Set brightness to 50%
        await client.write_gatt_char(
            WRITE_UUID,
            build_packet([0x33, 0x04, 0x80])
        )

        # Set color to red
        await client.write_gatt_char(
            WRITE_UUID,
            build_packet([0x33, 0x05, 0x02, 0xFF, 0x00, 0x00])
        )

asyncio.run(control_light("AA:BB:CC:DD:EE:FF"))
```

---

## 8. State Management

### 7.1 State Sources

| Source | Update Method | Latency | Completeness |
|--------|--------------|---------|--------------|
| API Polling | HTTP GET | 2-4s | Full state |
| AWS IoT MQTT | Push | ~50ms | Full state |
| Official MQTT | Push | ~100ms | Events only |
| LAN Status | UDP request | <10ms | Basic state |
| Optimistic | Assumed | 0ms | Command only |

### 7.2 State Fields

```typescript
interface DeviceState {
  // Core state
  onOff: 0 | 1;
  brightness: number;  // 0-100

  // Color state (mutually exclusive with colorTemp)
  color?: {
    r: number;  // 0-255
    g: number;  // 0-255
    b: number;  // 0-255
  };

  // Color temperature (mutually exclusive with color)
  colorTemInKelvin?: number;  // 2000-9000

  // Mode state
  mode?: string;
  scene?: {
    id: number;
    name: string;
  };

  // Segment state (RGBIC devices)
  segments?: Array<{
    index: number;
    color: { r: number; g: number; b: number };
    brightness: number;
  }>;
}
```

### 7.3 Optimistic Updates

After sending a command, update local state immediately:

```python
class StateManager:
    def __init__(self):
        self.confirmed_state = {}
        self.pending_state = {}

    async def send_command(self, device_id, command):
        # Apply optimistic update
        self.pending_state[device_id] = {
            **self.confirmed_state.get(device_id, {}),
            **command
        }

        # Send command
        await api.control_device(device_id, command)

        # Wait for confirmation via MQTT or poll
        # On confirmation, merge to confirmed_state
```

### 7.4 Conflict Resolution

When optimistic state conflicts with confirmed state:

1. **Timestamp-based**: Prefer most recent update
2. **Source priority**: MQTT > API Poll > Optimistic
3. **Attribute-specific**: Only update changed attributes

### 7.5 Known Limitations

These states are NOT returned by the API:
- Active music mode settings
- Night light mode status
- Gradient mode toggle
- Individual segment colors (RGBIC)
- Active scene name/ID

---

## 9. Device Capabilities

### 8.1 Capability Types

| Type | Description |
|------|-------------|
| `devices.capabilities.on_off` | Power control |
| `devices.capabilities.toggle` | Feature toggles |
| `devices.capabilities.range` | Ranged values (brightness) |
| `devices.capabilities.color_setting` | Color/temp control |
| `devices.capabilities.segment_color_setting` | RGBIC segment control |
| `devices.capabilities.dynamic_scene` | Scene selection |
| `devices.capabilities.diy_color_setting` | DIY scenes |
| `devices.capabilities.music_setting` | Music mode |
| `devices.capabilities.work_mode` | Appliance modes |
| `devices.capabilities.online` | Online status |
| `devices.capabilities.event` | Real-time events |

### 8.2 Instance Names

| Capability | Instances |
|------------|-----------|
| on_off | `powerSwitch` |
| toggle | `gradientToggle`, `nightlightToggle`, `oscillationToggle`, `warmMistToggle` |
| range | `brightness`, `humidity`, `volume` |
| color_setting | `colorRgb`, `colorTemperatureK` |
| segment_color_setting | `segmentedColorRgb`, `segmentedBrightness` |
| dynamic_scene | `lightScene`, `diyScene`, `snapshot` |
| music_setting | `musicMode` |

### 8.3 Device Type Detection

```python
def detect_capabilities(device_response):
    capabilities = device_response.get("capabilities", [])

    features = {
        "power": False,
        "brightness": False,
        "color": False,
        "color_temp": False,
        "segments": False,
        "scenes": False,
        "music": False,
    }

    for cap in capabilities:
        cap_type = cap.get("type", "")
        instance = cap.get("instance", "")

        if "on_off" in cap_type:
            features["power"] = True
        elif "range" in cap_type and instance == "brightness":
            features["brightness"] = True
        elif "color_setting" in cap_type:
            if instance == "colorRgb":
                features["color"] = True
            elif instance == "colorTemperatureK":
                features["color_temp"] = True
        elif "segment_color" in cap_type:
            features["segments"] = True
        elif "dynamic_scene" in cap_type:
            features["scenes"] = True
        elif "music_setting" in cap_type:
            features["music"] = True

    return features
```

### 8.4 Device Types

| Type | Examples |
|------|----------|
| `devices.types.light` | LED strips, bulbs, bars |
| `devices.types.socket` | Smart plugs |
| `devices.types.air_purifier` | Air purifiers |
| `devices.types.humidifier` | Humidifiers |
| `devices.types.heater` | Space heaters |
| `devices.types.thermometer` | Temp/humidity sensors |
| `devices.types.sensor` | Motion, presence sensors |

---

## 10. Scene & DIY Modes

### 9.1 Scene Types

| Type | Source | Description |
|------|--------|-------------|
| **Dynamic Scenes** | Official API | Pre-built animations |
| **DIY Scenes** | Official API | User-created via app |
| **Light Effect Library** | app2 API | Full scene catalog |

### 9.2 Fetching Scenes (Official API)

```http
POST /router/api/v1/device/scenes

{
  "requestId": "uuid",
  "payload": {
    "sku": "H618E",
    "device": "8C:2E:9C:04:A0:03:82:D1"
  }
}
```

### 9.3 Fetching Full Scene Catalog (Undocumented)

```http
GET https://app2.govee.com/appsku/v1/light-effect-libraries?sku=H6072
```

Response includes:
- Category organization
- Scene codes for BLE activation
- Animation parameters

### 9.4 Activating Scenes

**Via API:**
```json
{
  "type": "devices.capabilities.dynamic_scene",
  "instance": "lightScene",
  "value": {"id": 3853, "paramId": 4280}
}
```

**Via BLE:**
```
33 05 04 [code_low] [code_high] 00...00 [XOR]
```

### 9.5 DIY Mode Creation

DIY modes use multi-packet BLE sequences:

1. **Start packet:** `A1 02 00 [count] ...`
2. **Color data:** `A1 02 [num] [style] [mode] [speed] ...`
3. **End packet:** `A1 02 FF ...`
4. **Activate:** `33 05 0A ...`

DIY Styles:
- `0x00` = Fade
- `0x01` = Jumping
- `0x02` = Flicker
- `0x03` = Marquee
- `0x04` = Music reactive

---

## 11. PCAP Analysis Details

### 10.1 Capture Information

| Field | Value |
|-------|-------|
| **File** | `PCAPdroid_09_Jan_19_27_26.pcap` |
| **Size** | 7,091,980 bytes (6.8 MB) |
| **Packets** | 3,281 total |
| **Duration** | ~5 minutes |
| **Source** | PCAPdroid (Android) |

### 10.2 Traffic Breakdown

| Protocol | Packets | Bytes | Purpose |
|----------|---------|-------|---------|
| HTTPS (443) | 2,976 | ~5.8 MB | App API, CDN |
| MQTT (8883) | 285 | ~64 KB | AWS IoT |
| DNS (53) | 20 | ~2 KB | Name resolution |

### 10.3 Server IPs Observed

| IP | Service |
|----|---------|
| 54.90.251.176 | app2.govee.com |
| 54.147.158.57 | AWS IoT MQTT |
| 99.84.237.* | CloudFront CDN |
| 3.161.193.69 | Unknown (AWS) |
| 74.125.136.95 | Google (analytics) |

### 10.4 TLS SNI Hostnames

- `aqm3wd1qlc3dy-ats.iot.us-east-1.amazonaws.com`
- `app2.govee.com`
- `app-h5-manifest.govee.com`
- `govee.com`
- Various Amazon Trust CRL/OCSP endpoints

### 10.5 Connection Patterns

**MQTT Session:**
- Connection established at t=0
- TLS handshake: ~200ms
- State requests every 3-10 seconds during activity
- Keepalive maintains connection during idle
- Total session: 296 seconds

**API Patterns:**
- Burst of requests during app activity
- Scene/asset downloads from CDN
- Token refresh observed

---

## 12. References

### Official Documentation
- [Govee Developer Platform](https://developer.govee.com/)
- [API Reference PDF v2.0](https://govee-public.s3.amazonaws.com/developer-docs/GoveeDeveloperAPIReference.pdf)
- [LAN API Guide](https://app-h5.govee.com/user-manual/wlan-guide)

### Community Projects
- [wez/govee2mqtt](https://github.com/wez/govee2mqtt) - Rust, AWS IoT + LAN
- [homebridge-govee](https://github.com/bwp91/homebridge-govee) - Homebridge plugin
- [egold555/Govee-Reverse-Engineering](https://github.com/egold555/Govee-Reverse-Engineering) - BLE docs
- [BeauJBurroughs/Govee-H6127-Reverse-Engineering](https://github.com/BeauJBurroughs/Govee-H6127-Reverse-Engineering)

### Reverse Engineering
- [coding.kiwi - Reverse Engineering Govee](https://blog.coding.kiwi/reverse-engineering-govee-smart-lights/)
- [XDA - Govee Reverse Engineering](https://www.xda-developers.com/reverse-engineered-govee-smart-lights-smart-home/)
- [LAN API Gist](https://gist.github.com/mtwilliams5/08ae4782063b57a9b430069044f443f6)

### Home Assistant Community
- [Govee Integration Thread](https://community.home-assistant.io/t/govee-integration/228516)
- [Govee LAN API Announcement](https://community.home-assistant.io/t/govee-news-theres-a-local-api/460757)

---

*This document is based on analysis of the Govee Android app via PCAP capture and community reverse engineering efforts. The undocumented APIs may change without notice.*
