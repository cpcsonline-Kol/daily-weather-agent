import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

# 1. Configuration: 3 Canadian and 3 US Cities
CITIES = [
    {"name": "Toronto, ON", "lat": 43.6532, "lon": -79.3832},
    {"name": "Vancouver, BC", "lat": 49.2827, "lon": -123.1207},
    {"name": "Montreal, QC", "lat": 45.5017, "lon": -73.5673},
    {"name": "New York, NY", "lat": 40.7128, "lon": -74.0060},
    {"name": "Los Angeles, CA", "lat": 34.0522, "lon": -118.2437},
    {"name": "Chicago, IL", "lat": 41.8781, "lon": -87.6298},
]

# Weather code mapping (WMO standards used by Open-Meteo)
WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 61: "Slight rain",
    63: "Moderate rain", 65: "Heavy rain", 71: "Slight snow", 73: "Moderate snow",
    75: "Heavy snow", 95: "Thunderstorm"
}

def fetch_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        f"&timezone=auto&forecast_days=1"
    )
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()["daily"]

    code = data["weather_code"][0]
    return {
        "date": data["time"][0],
        "condition": WEATHER_CODES.get(code, f"Code {code}"),
        "temp_max": data["temperature_2m_max"][0],
        "temp_min": data["temperature_2m_min"][0],
        "precip_prob": data["precipitation_probability_max"][0],
    }

def generate_recommendation(weather):
    tips = []
    if weather["precip_prob"] >= 40:
        tips.append("Bring an umbrella.")
    if weather["temp_min"] <= 2:
        tips.append("Near/below freezing—bundle up.")
    elif weather["temp_max"] >= 25:
        tips.append("Warm—stay hydrated.")
    if not tips:
        tips.append("Comfortable weather ahead.")
    return " ".join(tips)

def build_html_interface(weather_data_list):
    """Generates a multi-city dashboard HTML page."""
    cards_html = ""
    for item in weather_data_list:
        city = item["city"]
        w = item["weather"]
        advice = item["advice"]
        
        cards_html += f"""
        <div class="card">
            <h2>{city}</h2>
            <div class="temp">{w['temp_min']}°C – {w['temp_max']}°C</div>
            <p><strong>Condition:</strong> {w['condition']}</p>
            <p><strong>Precipitation:</strong> {w['precip_prob']}%</p>
            <div class="advice"><strong>Tip:</strong> {advice}</div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Multi-City Weather Dashboard</title>
<style>
body {{ font-family: system-ui, sans-serif; background: #f4f7f6; padding: 40px; margin: 0; }}
h1 {{ text-align: center; color: #1e293b; margin-bottom: 30px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; max-width: 1000px; margin: 0 auto; }}
.card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
.card h2 {{ margin-top: 0; font-size: 1.25rem; color: #0284c7; }}
.temp {{ font-size: 1.8rem; font-weight: bold; color: #0f172a; margin: 8px 0; }}
.advice {{ background: #e0f2fe; padding: 10px; border-radius: 6px; color: #0369a1; font-size: 0.9rem; margin-top: 12px; }}
.meta {{ text-align: center; font-size: 0.85rem; color: #64748b; margin-top: 40px; }}
</style>
</head>
<body>
<h1>North American Weather Dashboard</h1>
<div class="grid">
{cards_html}
</div>
<div class="meta">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</div>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    return html

def send_email(html_content):
    sender = os.environ["SENDER_EMAIL"]
    password = os.environ["EMAIL_PASSWORD"]
    recipient = os.environ["RECIPIENT_EMAIL"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Multi-City Weather Briefing - {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = sender
    msg["To"] = recipient

    msg.attach(MIMEText(html_content, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

if __name__ == "__main__":
    all_weather_data = []
    
    for city_info in CITIES:
        w_data = fetch_weather(city_info["lat"], city_info["lon"])
        advice = generate_recommendation(w_data)
        all_weather_data.append({
            "city": city_info["name"],
            "weather": w_data,
            "advice": advice
        })
    
    html_output = build_html_interface(all_weather_data)
    send_email(html_output)
    print("Multi-city weather dashboard generated and email sent successfully.")
