import os
import sys
import re
from time import time
from customtkinter import *
import yt_dlp
import ctypes
import win32gui
import win32con
import threading
import requests
import concurrent.futures
import socks
import socket
import traceback
import random
import urllib3
import time as time_module
import logging

logging.basicConfig(filename='app.log', level=logging.DEBUG)

# Funkcja do znajdowania ścieżki zasobów
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Wyłączenie ostrzeżeń o niezweryfikowanych certyfikatach SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Funkcja do znalezienia ścieżki do pliku zasobu
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Initialize all the settings
set_appearance_mode("System") # Setting the appearance mode to follow by the app: "System", "Light" or "Dark"
set_default_color_theme("green") # Setting the theme of the app to follow

if "youtube_downloads" not in os.listdir(os.getcwd()):
    os.mkdir("youtube_downloads")

# Function to validate YouTube URL
def is_valid_youtube_url(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    youtube_regex_match = re.match(youtube_regex, url)
    return youtube_regex_match is not None

def test_proxy_speed(proxy):
    try:
        start_time = time()  # Użyj time() zamiast time.time()
        socks5_address, socks5_port = proxy.split(':')
        socks.set_default_proxy(socks.SOCKS5, socks5_address, int(socks5_port))
        socket.socket = socks.socksocket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(5)
        test_socket.connect(('www.youtube.com', 80))
        test_socket.close()
        end_time = time()  # Użyj time() zamiast time.time()
        return proxy, int((end_time - start_time) * 1000)  # Czas w milisekundach
    except Exception as e:
        print(f"Błąd podczas testowania proxy {proxy}: {str(e)}")
        return proxy, None

def get_fast_proxy(num_proxies=5):
    try:
        response = requests.get('https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all')
        proxies = response.text.split('\r\n')
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(test_proxy_speed, proxies[:50]))  # Testujemy pierwsze 50 proxy
        
        fast_proxies = sorted([r for r in results if r[0]], key=lambda x: x[1])[:num_proxies]
        return [proxy for proxy, _ in fast_proxies]
    except Exception as e:
        print(f"Błąd podczas pobierania proxy: {str(e)}")
        return None

def get_socks5_proxy():
    proxy_sources = [
        'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all',
        'https://www.proxy-list.download/api/v1/get?type=socks5',
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
        'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt'
    ]
    
    # Dodajemy nową listę proxy
    custom_proxies = [
         "121.129.47.25:1080", "46.101.159.153:52570", "54.38.151.84:56789",
        "104.255.170.63:60899",
        "23.19.244.109:1080", "31.170.22.127:1080", "72.167.46.207:1080",
        "198.12.250.231:7684", "139.198.120.15:29527", "154.12.253.232:61015",
        "161.97.163.52:59510", "185.82.218.146:1080", "45.138.87.238:1080",
        # Dodajemy nowe proxy
        "92.204.135.37:59092", "34.124.190.108:8080", "163.172.146.42:16379"
    ]
    
    random.shuffle(proxy_sources)
    
    for source in proxy_sources:
        try:
            response = requests.get(source, timeout=10, verify=False)
            if response.status_code == 200:
                proxies = [proxy.strip() for proxy in response.text.split('\n') if proxy.strip()]
                if proxies:
                    return random.choice(proxies)
        except Exception as e:
            print(f"Błąd podczas pobierania proxy z {source}: {str(e)}")
    
    # Jeśli nie udało się pobrać proxy z zewnętrznych źródeł, użyj własnej listy
    if custom_proxies:
        return random.choice(custom_proxies)
    
    print("Nie udało się pobrać żadnego proxy z dostępnych źródeł.")
    return None

def test_proxy(proxy):
    try:
        socks5_address, socks5_port = proxy.split(':')
        socks.set_default_proxy(socks.SOCKS5, socks5_address, int(socks5_port))
        socket.socket = socks.socksocket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(5)
        test_socket.connect(('www.youtube.com', 80))
        test_socket.close()
        return True
    except Exception as e:
        print(f"Błąd podczas testowania proxy {proxy}: {str(e)}")
        return False

# Globalna zmienna do przechowywania aktualnego proxy
current_proxy = None

# Dodaj tę zmienną globalną
format_var = None

# Zmodyfikuj funkcję download_video
def download_video():
    url = entry.get()
    if not is_valid_youtube_url(url):
        show_error("Nieprawidłowy link YouTube")
        return

    progress_bar.pack(pady=10)
    progress_bar.set(0)

    def download_thread():
        try:
            start_time = time()
            download_location = "youtube_downloads/"
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    p = d.get('_percent_str', '0%')
                    p = p.replace('%','').strip()
                    try:
                        progress = float(p) / 100
                        master.after(0, lambda: progress_bar.set(progress))
                    except ValueError:
                        print(f"Nie można przekonwertować na float: {p}")

            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
            ]

            ydl_opts = {
                'outtmpl': os.path.join('youtube_downloads', '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'user-agent': random.choice(user_agents),
                'cookiefile': cookies_path
            }

            if format_var.get() == "mp3":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            else:  # mp4
                ydl_opts.update({
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                })
            
            if vpn_enabled and current_proxy:
                print(f"Używam SOCKS5 proxy: {current_proxy}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                print(f"Tytuł wideo: {info['title']}")
                ydl.download([url])
            
            end_time = time()
            master.after(0, lambda: show_success(f"Pobieranie zakończone!\nCałkowity czas: {round(end_time-start_time,3)} sekund"))
        except Exception as e:
            print(f"Wystąpił błąd: {str(e)}")
            master.after(0, lambda: show_error(f"Wystąpił błąd podczas pobierania: {str(e)}"))
        finally:
            master.after(0, lambda: progress_bar.pack_forget())

        time_module.sleep(random.uniform(1, 3))  # Losowe opóźnienie między 1 a 3 sekundy

    threading.Thread(target=download_thread, daemon=True).start()

def show_success(message):
    popup = CTkToplevel(master)
    popup.title("Status pobierania")
    popup.geometry("300x100")
    CTkLabel(popup, text=message).pack(pady=10)
    CTkButton(popup, text="OK", command=popup.destroy).pack()

def show_error(message):
    popup = CTkToplevel(master)
    popup.title("Błąd")
    popup.geometry("300x100")
    CTkLabel(popup, text=message).pack(pady=10)
    CTkButton(popup, text="OK", command=popup.destroy).pack()

def show_info(message):
    popup = CTkToplevel(master)
    popup.title("Informacja")
    popup.geometry("300x100")
    CTkLabel(popup, text=message).pack(pady=10)
    CTkButton(popup, text="OK", command=popup.destroy).pack()

def set_taskbar_icon(root, icon_path):
    myappid = 'mycompany.myproduct.subproduct.version'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    root.iconbitmap('icon.ico')
   
    hwnd = win32gui.GetParent(root.winfo_id())
    icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
    try:
        hicon = win32gui.LoadImage(win32gui.GetModuleHandle(None), icon_path,
                                   win32con.IMAGE_ICON, 0, 0, icon_flags)
        win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)
    except:
        pass

# Nowa funkcja do wyświetlania listy proxy
def show_proxy_list():
    proxy_window = CTkToplevel(master)
    proxy_window.title("Lista proxy")
    proxy_window.geometry("400x300")

    proxy_frame = CTkScrollableFrame(proxy_window)
    proxy_frame.pack(fill="both", expand=True, padx=10, pady=10)

    custom_proxies = [
        "121.129.47.25:1080", "46.101.159.153:52570", "54.38.151.84:56789",
        "104.255.170.63:60899",
        "23.19.244.109:1080", "31.170.22.127:1080", "72.167.46.207:1080",
        "198.12.250.231:7684", "139.198.120.15:29527", "154.12.253.232:61015",
        "161.97.163.52:59510", "185.82.218.146:1080", "45.138.87.238:1080",
        # Dodajemy nowe proxy
        "92.204.135.37:59092", "34.124.190.108:8080", "163.172.146.42:16379"
    ]

    def select_proxy(proxy):
        global current_proxy
        current_proxy = proxy
        vpn_button.configure(text=f"VPN: Włączony ({proxy})")
        proxy_window.destroy()

    def test_and_add_proxy(proxy):
        proxy, response_time = test_proxy_speed(proxy)
        if response_time is not None:
            button_text = f"{proxy} ({response_time} ms)"
        else:
            button_text = f"{proxy} (niedostępny)"
        return (proxy, button_text)

    # Używamy ThreadPoolExecutor do równoległego testowania proxy
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_proxy = {executor.submit(test_and_add_proxy, proxy): proxy for proxy in custom_proxies}
        for future in concurrent.futures.as_completed(future_to_proxy):
            proxy, button_text = future.result()
            CTkButton(proxy_frame, text=button_text, command=lambda p=proxy: select_proxy(p)).pack(pady=5)

    if not proxy_frame.winfo_children():
        CTkLabel(proxy_frame, text="Brak dostępnych proxy").pack(pady=10)

# Modyfikacja funkcji toggle_vpn
def toggle_vpn():
    global vpn_enabled, current_proxy
    vpn_enabled = not vpn_enabled
    if vpn_enabled:
        show_proxy_list()
    else:
        socks.set_default_proxy()
        socket.socket = socket._socketobject
        vpn_button.configure(text="VPN: Wyłączony")
        current_proxy = None
        show_info("VPN wyłączony")

# Initializing the layout of the app
master = CTk()
master.title("Pobieranie yt beta")
master.geometry("350x350")  # Zwiększamy wysokość okna

if os.path.exists("icon.ico"):
    master.wm_iconbitmap("icon.ico")
    master.iconbitmap("icon.ico")
    set_taskbar_icon(master, "icon.ico")

frame = CTkFrame(master)
frame.pack(pady=20, padx=20, fill="both", expand=True)

label = CTkLabel(frame, text="Wklej link do filmu YouTube:")
label.pack(pady=10)

entry = CTkEntry(frame, width=300)
entry.pack(pady=10)

# Dodajemy wybór formatu
format_var = StringVar(value="mp3")
format_frame = CTkFrame(frame)
format_frame.pack(pady=10)

CTkRadioButton(format_frame, text="MP3", variable=format_var, value="mp3").pack(side="left", padx=10)
CTkRadioButton(format_frame, text="MP4", variable=format_var, value="mp4").pack(side="left", padx=10)

button = CTkButton(frame, text="Pobierz", command=download_video)
button.pack(pady=10)

progress_bar = CTkProgressBar(frame, width=300)

# Dodajemy przycisk do włączania/wyłączania trybu VPN
vpn_enabled = False

# Modyfikacja przycisku VPN
vpn_button = CTkButton(frame, text="VPN: Wyłączony", command=toggle_vpn)
vpn_button.pack(pady=10)

icon_path = resource_path('icon.ico')
cookies_path = resource_path('cookies.txt')

try:
    # Twój główny kod aplikacji
    master.mainloop()
except Exception as e:
    logging.error(f"Wystąpił błąd: {str(e)}")
    logging.error(traceback.format_exc())
    show_error(f"Wystąpił nieoczekiwany błd: {str(e)}")
    show_error(f"Wystąpił nieoczekiwany błd: {str(e)}")
    show_error(f"Wystąpił nieoczekiwany błd: {str(e)}")
    show_error(f"Wystąpił nieoczekiwany błd: {str(e)}")
    show_error(f"Wystąpił nieoczekiwany błd: {str(e)}")
    show_error(f"Wystąpił nieoczekiwany błd: {str(e)}")
    show_error(f"Wystąpił nieoczekiwany błd: {str(e)}")