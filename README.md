# System Dashboard

A **terminal-based system monitoring dashboard** built with Python and Textual.
It displays **CPU, RAM, GPU, Disk, Network, Battery, and Temperature stats** with **ASCII bars and sparkline graphs**.
Supports **server mode**, showing real-time network activity and ping logs.

---

## Features

* **CPU & RAM:** Percent usage with sparkline history.
* **GPU:** Utilization and memory usage (requires NVIDIA + `pynvml`).
* **Disk:** All mounted partitions with free space and usage bars.
* **Network:** Upload/download speed, sparkline graphs.
* **Battery:** Current battery percentage.
* **Temperatures:** Highlighted in red if critical.
* **Logging:** Logs all stats to CSV (`system_dashboard_log.csv`).
* **Server Mode:** Extra console panel at bottom showing ping and network logs.
* **Settings Button:** Toggle visibility of all panels.

---

## Installation

1. **Clone repository or copy files**:

```bash
git clone https://github.com/Hacknummberk/terminalbaseinfo.git
cd terminalbaseinfo
```

2. **Create Python virtual environment** (recommended):

```bash
python3 -m venv .venv      # if you need also need for debian or linux
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

3. **Install dependencies**:

```bash
pip install textual psutil pynvml
```

> `pynvml` is optional but required for NVIDIA GPU stats.

---

## Usage

Run the dashboard:

```bash
python main.py
```

### Server Mode

Enable **server mode** to monitor network traffic and ping:

```bash
python main.py server
```

* Displays **ping to 8.8.8.8** in a bottom console panel.
* Continuously logs **upload/download speed**.

---

## Controls

* **Settings Button:** Toggle visibility of all panels.
* **Keyboard:** Use `Ctrl+C` to exit the app.

---

## Logging

All stats are logged to CSV: `system_dashboard_log.csv`

Columns:

```
Timestamp, CPU%, RAM%, GPU%, GPU Mem MB, Upload KB/s, Download KB/s, Disk%, Disk Read KB/s, Disk Write KB/s, Battery%, Temps
```

---

## Requirements

* Python 3.13+
* `textual`
* `psutil`
* `pynvml` (optional for NVIDIA GPU stats)

---

## Notes

* Works on **Linux, Windows, macOS**.
* In **server mode**, ensure ICMP ping is allowed.
* Panel visibility toggles can be expanded for more customization.

---

