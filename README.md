<p align="center">
  <img src="https://brands.home-assistant.io/_/govee/logo.png" alt="Govee Logo" width="150"/>
</p>

<h1 align="center">Govee Integration for Home Assistant</h1>

<p align="center">
  <em>Your Govee lights + Home Assistant = RGB bliss with real-time control</em>
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge" alt="HACS Custom"></a>
  <a href="https://github.com/lasswellt/govee-homeassistant/releases"><img src="https://img.shields.io/github/v/release/lasswellt/govee-homeassistant?style=for-the-badge" alt="GitHub Release"></a>
  <a href="https://github.com/lasswellt/govee-homeassistant/blob/master/LICENSE.txt"><img src="https://img.shields.io/github/license/lasswellt/govee-homeassistant?style=for-the-badge" alt="License"></a>
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=lasswellt&repository=govee-homeassistant&category=integration">
    <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open in HACS">
  </a>
</p>

---

## What's This?

Ever wanted your Govee lights to actually *talk* to Home Assistant? This integration gives you:

- **Full light control** — brightness, RGB colors, color temp, the works
- **Scene magic** — your Govee scenes become HA scenes
- **RGBIC segment control** — paint each segment a different color
- **Real-time sync** — optional MQTT for instant updates (bye-bye polling lag)

---

## Get Started

### 1. Grab Your API Key

In the **Govee Home** app: **Profile** → **Settings** → **About Us** → **Apply for API Key**

Check your email in ~5 minutes.

### 2. Install via HACS

Click the button above, search "Govee", hit **Download**, restart Home Assistant.

### 3. Add the Integration

**Settings** → **Devices & Services** → **Add Integration** → **Govee**

Enter your API key. Want instant updates? Add your Govee email/password for MQTT.

---

## What Works

| Device | Features |
|--------|----------|
| **LED Lights & Strips** | On/off, brightness, RGB, color temp |
| **RGBIC Strips** | All the above + per-segment colors |

> **Note:** Cloud-enabled devices only. Bluetooth-only devices need a different integration.

---

## Real-time Updates

Polling is *so* 2020. Add your Govee account credentials during setup for instant state sync via AWS IoT MQTT.

No credentials? Polling works fine (every 60 seconds by default).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Devices not showing | Make sure they're WiFi devices, not Bluetooth-only |
| Slow updates | Enable MQTT or reduce poll interval in options |
| Rate limit errors | Increase poll interval (Govee allows 100 req/min) |

Need debug logs? Add `custom_components.govee: debug` to your logger config.

---

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE.txt](LICENSE.txt)
