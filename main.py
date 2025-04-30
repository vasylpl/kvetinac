import network
import socket
import time

# Wi-Fi připojení
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("vasyl", "vasyl000")

    timeout = 10  # čekat max 10 sekund
    while not wlan.isconnected() and timeout > 0:
        print("⏳ Připojuji se k Wi-Fi...")
        time.sleep(1)
        timeout -= 1

    if wlan.isconnected():
        print("✅ Připojeno:", wlan.ifconfig())
        return wlan.ifconfig()[0]
    else:
        print("❌ Nepodařilo se připojit k Wi-Fi.")
        return "0.0.0.0"  # Vrátí IP 0.0.0.0, pokud není připojeno

# Minimalistický web server
def simple_web_server(ip):
    addr = socket.getaddrinfo(ip, 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print("🌐 Server běží na http://", ip)

    while True:
        try:
            cl, addr = s.accept()
            print("🔗 Připojeno od", addr)
            request = cl.recv(1024).decode()
            print("📩 Request:", request)

            # Zjednodušená odpověď
            response = """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
            <html><body><h1>Hello, World!</h1></body></html>"""
            cl.send(response)
            cl.close()

        except Exception as e:
            print("💥 Chyba:", e)

# Připojení k Wi-Fi
ip = connect_wifi()

# Spuštění webového serveru
if ip != "0.0.0.0":
    simple_web_server(ip)
