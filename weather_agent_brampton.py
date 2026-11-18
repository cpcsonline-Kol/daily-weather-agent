import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

# 1. Configuration (Example: Brampton, ON coordinates)
LATITUDE = 43.7315
LONGITUDE = -79.7624
CITY_NAME = "Bramladesh, ON"

# Weather code mapping (WMO standards used by Open-Meteo)
WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 61: "Slight rain",
    63: "Moderate rain", 65: "Heavy rain", 71: "Slight snow", 73: "Moderate snow",
    75: "Heavy snow", 95: "Thunderstorm"
}

def fetch_weather():
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LATITUDE}&longitude={LONGITUDE}"
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
    """Simple rule-based agent logic for daily advice."""
    tips = []
    if weather["precip_prob"] >= 40:
        tips.append("Bring an umbrella or rain jacket.")
    if weather["temp_min"] <= 2:
        tips.append("Its that time again! Bundle up—temperatures are near or below freezing.")
    elif weather["temp_max"] >= 25:
        tips.append("Stay hydrated and wear light clothing.")
    if not tips:
        tips.append("Comfortable weather ahead—no special gear needed.")
    return " ".join(tips)

def build_html_interface(weather, advice):
    """Generates a simple, clean static web interface."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Weather Agent - {CITY_NAME}</title>
<style>
body {{ font-family: system-ui, sans-serif; background: #f4f7f6; display: flex; justify-content: center; padding: 40px; }}
.card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 400px; width: 100%; }}
h1 {{ margin-top: 0; font-size: 1.5rem; color: #1e293b; }}
.temp {{ font-size: 2.2rem; font-weight: bold; color: #0284c7; margin: 10px 0; }}
.advice {{ background: #e0f2fe; padding: 12px; border-radius: 8px; color: #0369a1; margin-top: 15px; }}
.meta {{ font-size: 0.85rem; color: #64748b; margin-top: 20px; }}
</style>
</head>
<body>
<div class="card">
<h1>{CITY_NAME} Weather</h1>
<p><strong>Date:</strong> {weather['date']}</p>
<div class="temp">{weather['temp_min']}°C – {weather['temp_max']}°C</div>
<p><strong>Condition:</strong> {weather['condition']}</p>
<p><strong>Chance of Precipitation:</strong> {weather['precip_prob']}%</p>
<div class="advice"><strong>Agent Tip:</strong> {advice}</div>
<div class="meta">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</div>
</div>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    return html

def send_email(html_content, weather):
    sender = os.environ["SENDER_EMAIL"]
    password = os.environ["EMAIL_PASSWORD"]
    recipient = os.environ["RECIPIENT_EMAIL"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"7 AM Weather Briefing ({CITY_NAME}): {weather['condition']}, High {weather['temp_max']}°C"
    msg["From"] = sender
    msg["To"] = recipient

    msg.attach(MIMEText(html_content, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

if __name__ == "__main__":
    weather_data = fetch_weather()
    agent_advice = generate_recommendation(weather_data)
    html_output = build_html_interface(weather_data, agent_advice)
    send_email(html_output, weather_data)
    print("Weather interface updated and email sent successfully.")
