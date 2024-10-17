# Ustaw kodowanie na UTF-8 BOM
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# Ścieżka do środowiska wirtualnego (dostosuj do swojej konfiguracji)
$venvPath = "c:\Users\kpanfiluk\Documents\plsteraz\.venv"

# Ścieżka do pyinstaller
$pyinstallerPath = Join-Path $venvPath "Scripts\pyinstaller.exe"

# Ścieżka do customtkinter
$customtkinterPath = Join-Path $venvPath "Lib\site-packages\customtkinter"

# Kompilacja
& $pyinstallerPath --onefile --windowed `
    --add-data "$customtkinterPath;customtkinter" `
    --add-data "icon.ico;." `
    --add-data "cookies.txt;." `
    --hidden-import "win32gui" `
    --hidden-import "win32con" `
    --hidden-import "ctypes" `
    --hidden-import "yt_dlp" `
    --hidden-import "requests" `
    --hidden-import "concurrent.futures" `
    --hidden-import "socks" `
    --hidden-import "urllib3" `
    --icon="icon.ico" `
    --name "YouTube Downloader" `
    python.py

# Kopiowanie pliku exe do głównego katalogu
Move-Item -Path "dist\YouTube Downloader.exe" -Destination "YouTube Downloader.exe" -Force

# Usuwanie tymczasowych folderów
Remove-Item -Path "build" -Recurse -Force
Remove-Item -Path "dist" -Recurse -Force
Remove-Item -Path "YouTube Downloader.spec" -Force

# Użyj Write-Output zamiast Write-Host
Write-Output "Kompilacja zakonczona. Plik wykonywalny: YouTube Downloader.exe"