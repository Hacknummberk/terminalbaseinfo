import psutil, time, csv, subprocess, sys
from datetime import datetime
from threading import Thread
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button
from textual.containers import Grid
from textual.reactive import reactive

# GPU info
try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except:
    NVML_AVAILABLE = False

LOG_FILE = "system_dashboard_log.csv"

# Initialize CSV
with open(LOG_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Timestamp", "CPU%", "RAM%", "GPU%", "GPU Mem MB",
        "Upload KB/s", "Download KB/s", "Disk%", "Disk Read KB/s", "Disk Write KB/s",
        "Battery%", "Temps"
    ])

def make_bar(percent: float, length=20) -> str:
    filled = int(length * percent / 100)
    empty = length - filled
    if percent < 50: color = "green"
    elif percent < 80: color = "yellow"
    else: color = "red"
    return f"[{color}]{'█'*filled}[grey37]{'░'*empty}[/{color}] {percent:.1f}%"

def sparkline(data: list[float], length=20) -> str:
    if not data: return ""
    data = data[-length:]
    max_val = max(data) or 1
    chars = "▁▂▃▄▅▆▇█"
    return "".join(chars[int((val/max_val)*(len(chars)-1))] for val in data)

class Panel(Static):
    def __init__(self, title: str, **kwargs):
        super().__init__(**kwargs)
        self.title = title
    def render(self) -> str:
        return f"[b]{self.title}[/b]\n{self.renderable}"

class SystemDashboardApp(App):
    CSS_PATH = None

    cpu_history: list[float] = reactive([])
    ram_history: list[float] = reactive([])
    gpu_history: list[float] = reactive([])
    net_history: list[tuple[int,int]] = reactive([])
    disk_history: list[tuple[int,int]] = reactive([])
    ping_logs: list[str] = reactive([])

    show_cpu: reactive[bool] = reactive(True)
    show_ram: reactive[bool] = reactive(True)
    show_gpu: reactive[bool] = reactive(True)
    show_net: reactive[bool] = reactive(True)
    show_disk: reactive[bool] = reactive(True)
    show_batt: reactive[bool] = reactive(True)
    show_temps: reactive[bool] = reactive(True)
    show_console: reactive[bool] = reactive(False)

    server_mode: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if len(sys.argv) > 1 and sys.argv[1].lower() == "server":
            self.server_mode = True
            self.show_console = True

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        grid = Grid()
        grid.styles.grid_template_columns = "1fr 1fr"
        grid.styles.grid_gap = 1

        # Panels
        self.cpu_panel = Panel("CPU Usage")
        self.ram_panel = Panel("RAM Usage")
        self.disk_panel = Panel("Disk Partitions")
        self.gpu_panel = Panel("GPU Usage")
        self.net_panel = Panel("Network")
        self.batt_panel = Panel("Battery")
        self.temps_panel = Panel("Temperatures")
        self.console_panel = Panel("Console Log")

        panels = [
            self.cpu_panel, self.ram_panel, self.disk_panel,
            self.gpu_panel, self.net_panel, self.batt_panel, self.temps_panel
        ]

        for p in panels:
            grid.mount(p)

        yield grid
        yield Button("Settings", id="settings_btn")
        if self.server_mode:
            yield self.console_panel
        yield Footer()

    def on_mount(self):
        self.prev_net = psutil.net_io_counters()
        self.prev_disk = psutil.disk_io_counters()
        Thread(target=self.update_stats, daemon=True).start()
        if self.server_mode:
            Thread(target=self.ping_loop, daemon=True).start()

    def update_stats(self):
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cpu_percent = psutil.cpu_percent(interval=1)
            ram_percent = psutil.virtual_memory().percent

            self.cpu_history.append(cpu_percent)
            self.cpu_history = self.cpu_history[-50:]
            self.ram_history.append(ram_percent)
            self.ram_history = self.ram_history[-50:]

            # Temps
            temps_data = psutil.sensors_temperatures()
            temp_str = ""
            for key, entries in temps_data.items():
                for entry in entries:
                    color = "red" if entry.current > 80 else "green"
                    temp_str += f"[{color}]{entry.label or key}: {entry.current}°C[/{color}] "

            # GPU
            gpu_str = ""
            gpu_percent = 0
            gpu_mem = 0
            if NVML_AVAILABLE:
                for i in range(pynvml.nvmlDeviceGetCount()):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle).decode()
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
                    mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu_percent = util
                    gpu_mem = mem.used // 1024**2
                    self.gpu_history.append(gpu_percent)
                    self.gpu_history = self.gpu_history[-50:]
                    gpu_str += f"{name}: {util}% / {gpu_mem}MB  "
            else:
                gpu_str = "No GPU info"

            # Network
            net = psutil.net_io_counters()
            up_speed = (net.bytes_sent - self.prev_net.bytes_sent)/1024
            down_speed = (net.bytes_recv - self.prev_net.bytes_recv)/1024
            self.prev_net = net
            self.net_history.append((up_speed, down_speed))
            self.net_history = self.net_history[-50:]
            net_str = f"Up: {up_speed:.1f} KB/s | Down: {down_speed:.1f} KB/s " \
                      f"{sparkline([u for u,d in self.net_history])} {sparkline([d for u,d in self.net_history])}"

            # Disk Partitions
            disk_str = ""
            for part in psutil.disk_partitions(all=False):
                usage = psutil.disk_usage(part.mountpoint)
                disk_str += f"{part.device}: {make_bar(usage.percent)} {usage.free//1024//1024}MB free\n"

            # Battery
            if psutil.sensors_battery():
                batt_percent = psutil.sensors_battery().percent
                batt_str = f"{batt_percent:.1f}%"
            else:
                batt_str = "No battery"

            # Update panels
            if self.show_cpu: self.cpu_panel.update(make_bar(cpu_percent) + " " + sparkline(self.cpu_history))
            if self.show_ram: self.ram_panel.update(make_bar(ram_percent) + " " + sparkline(self.ram_history))
            if self.show_gpu: self.gpu_panel.update(make_bar(gpu_percent) + " " + sparkline(self.gpu_history) if NVML_AVAILABLE else gpu_str)
            if self.show_net: self.net_panel.update(net_str)
            if self.show_disk: self.disk_panel.update(disk_str)
            if self.show_batt: self.batt_panel.update(batt_str)
            if self.show_temps: self.temps_panel.update(temp_str)
            if self.show_console:
                # Show last 20 ping logs
                self.console_panel.update("\n".join(self.ping_logs[-20:]))

            # Log CSV
            with open(LOG_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, cpu_percent, ram_percent, gpu_str, gpu_mem,
                    up_speed, down_speed, "N/A", 0, 0,
                    batt_str, temp_str
                ])
            time.sleep(1)

    def ping_loop(self):
        host = "8.8.8.8"
        while True:
            try:
                output = subprocess.run(["ping", "-c", "1", "-W", "1", host],
                                        capture_output=True, text=True)
                if output.returncode == 0:
                    line = output.stdout.splitlines()[1]
                else:
                    line = f"{datetime.now().strftime('%H:%M:%S')} Ping failed"
            except Exception as e:
                line = f"{datetime.now().strftime('%H:%M:%S')} Ping error: {e}"
            self.ping_logs.append(line)
            self.ping_logs = self.ping_logs[-100:]
            time.sleep(1)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "settings_btn":
            # Toggle all panel
            self.show_cpu = not self.show_cpu
            self.show_ram = not self.show_ram
            self.show_gpu = not self.show_gpu
            self.show_net = not self.show_net
            self.show_disk = not self.show_disk
            self.show_batt = not self.show_batt
            self.show_temps = not self.show_temps

if __name__ == "__main__":
    SystemDashboardApp().run()
