import network
import socket
import time
from machine import Pin, ADC
import dht

# Wi-Fi připojení
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("vasyl", "vasyl000")

    timeout = 10
    while not wlan.isconnected() and timeout > 0:
        print("⏳ Připojuji se k Wi-Fi...")
        time.sleep(1)
        timeout -= 1

    if wlan.isconnected():
        print("✅ Připojeno:", wlan.ifconfig())
        return wlan.ifconfig()[0]
    else:
        print("❌ Nepodařilo se připojit k Wi-Fi.")
        return "0.0.0.0"

# Inicializace komponent
sensor = dht.DHT11(Pin(15))
moisture = ADC(Pin(26))
relay = Pin(16, Pin.OUT)
relay.off()

# Parametry
auto_watering = True
THRESHOLD_PERCENT = 30  # pod touto hodnotou se spustí automatické zalévání

# HTML stránka
def web_page(temp, hum, soil_percent, auto):
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: sans-serif; text-align: center; background: #f5f5f5; }}
        .box {{ background: white; border-radius: 8px; box-shadow: 0 0 10px #ccc; padding: 20px; margin: 20px auto; width: 90%; max-width: 400px; }}
        button {{ padding: 10px 20px; font-size: 16px; border: none; background: #4CAF50; color: white; border-radius: 5px; cursor: pointer; }}
        button:hover {{ background: #45a049; }}
    </style>
</head>
<body>
    <h1>🌿 Chytrý květináč</h1>
    <div class="box">
        🌡️ <strong>Teplota:</strong> {temp}°C<br>
        💧 <strong>Vlhkost vzduchu:</strong> {hum}%<br>
        🌱 <strong>Vlhkost půdy:</strong> {soil_percent}%<br>
        🤖 <strong>Automatické zalévání:</strong> {"ANO" if auto else "NE"}
    </div>
    <form action="/water" method="get">
        <button type="submit">💦 Zalít nyní</button>
    </form>
    <form action="/toggle_auto" method="get">
        <button type="submit">🔁 Přepnout automatiku</button>
    </form>
</body>
</html>"""

# Spuštění webserveru
ip = connect_wifi()
addr = socket.getaddrinfo(ip, 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print("🌐 Server běží na http://", ip)

# Hlavní smyčka
while True:
    try:
        cl, addr = s.accept()
        print("🔗 Připojeno od", addr)
        request = cl.recv(1024).decode()
        print("📩 Request:", request)

        # Čtení DHT11
        try:
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
        except Exception as e:
            temp = "N/A"
            hum = "N/A"
            print("❌ Chyba čtení DHT11:", e)

        # Vlhkost půdy v procentech
        soil_raw = moisture.read_u16()
        soil_percent = 100 - int((soil_raw / 65535) * 100)
        print(f"📊 Půdní vlhkost: {soil_percent}% ({soil_raw})")

        # Ruční zalévání
        if "/water" in request:
            print("💧 Ruční zalévání...")
            relay.on()
            time.sleep(2)
            relay.off()

        # Přepínání automatiky
        if "/toggle_auto" in request:
            auto_watering = not auto_watering
            print("🔁 Automatické zalévání:", "Zapnuto" if auto_watering else "Vypnuto")

        # Automatické zalévání
        if auto_watering and isinstance(soil_percent, int) and soil_percent < THRESHOLD_PERCENT:
            print("⚠️ Sucho! Zalévám automaticky.")
            relay.on()
            time.sleep(2)
            relay.off()

        # Odpověď (HTML)
        response = web_page(temp, hum, soil_percent, auto_watering)
        cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        cl.send(response)
        cl.close()

    except Exception as e:
        print("💥 Chyba:", e)
