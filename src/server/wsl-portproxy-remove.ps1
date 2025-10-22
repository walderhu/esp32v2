param(
    [int]$ListenPort = 8081,
    [string]$RuleName = "WSL Port 8081"
)

netsh interface portproxy delete v4tov4 listenport=$ListenPort listenaddress=0.0.0.0
netsh advfirewall firewall delete rule name="$RuleName" protocol=TCP localport=$ListenPort

netsh interface portproxy show all
Write-Output "Удалено."
