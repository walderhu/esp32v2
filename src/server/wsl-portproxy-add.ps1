# wsl-portproxy-add.ps1
param(
    [int]$ListenPort = 8081,
    [int]$ConnectPort = 8081,
    [string]$RuleName = "WSL Port 8081"
)

# Получаем первый IP WSL (hostname -I)
$wslIpsRaw = wsl hostname -I 2>$null
if (-not $wslIpsRaw) {
    Write-Error "Не удалось получить IP WSL. Убедись, что WSL запущен."
    exit 1
}
$wslIp = $wslIpsRaw.Split()[0]

Write-Output "WSL IP: $wslIp"

# Удаляем старый проброс (если есть)
netsh interface portproxy delete v4tov4 listenport=$ListenPort listenaddress=0.0.0.0 2>$null

# Добавляем новый
netsh interface portproxy add v4tov4 listenport=$ListenPort listenaddress=0.0.0.0 connectport=$ConnectPort connectaddress=$wslIp

# Разрешаем в фаерволе (если правило уже есть, будет дубликат — нормально)
netsh advfirewall firewall add rule name="$RuleName" dir=in action=allow protocol=TCP localport=$ListenPort

# Вывод
netsh interface portproxy show all
Write-Output "Готово. Открой http://<WINDOWS_IP>:$ListenPort"
