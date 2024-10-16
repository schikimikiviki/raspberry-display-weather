
import fcntl
import struct
import board
import digitalio
import requests
import time
import os.path
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from io import BytesIO
import cairosvg
import math  

# Set pins and initialize OLED
RESET_PIN = digitalio.DigitalInOut(board.D4)
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C, reset=RESET_PIN)

# Clear screen
oled.fill(0)
oled.show()

# Load fonts
font1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
font3 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)

def get_icon(id, size=32):
    path = f'./icons/{id}.svg'
    if os.path.isfile(path):
        return Image.open(
            BytesIO(cairosvg.svg2png(url=path))  # convert svg to png
        ).resize((size, size)).convert('1')  # return resized image
    else:
        return Image.new("1", (size, size))  # return empty image

def fetch_weather_data():
    try:
        # OpenWeather API request
        response = requests.get(
            url='https://api.openweathermap.org/data/2.5/onecall?appid=d3355b38ac0d56b2e91cefcd5fd744fb&units=metric&lang=de&lat=48.1833373&lon=16.2844278',
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f"Error getting weather data: {e}")
        return None

# Initialize variables
data = fetch_weather_data()
last_fetch_time = time.time()
fetch_interval_hours = 6  # Number of hours between each fetch
fetch_interval = fetch_interval_hours * 60 * 60  # Convert hours to seconds

while True:
    current_time = time.time()
    if current_time - last_fetch_time >= fetch_interval or data is None:
        data = fetch_weather_data()
        last_fetch_time = current_time

    if data:
        try:
            # Display hourly data
            for step in [
                {'title': 'Jetzt:', 'data': data['current']},
                {'title': 'in einer Stunde:', 'data': data['hourly'][1]},
                {'title': 'in 2 Stunden:', 'data': data['hourly'][2]},
                {'title': 'in 3 Stunden:', 'data': data['hourly'][3]},
                {'title': 'in 6 Stunden:', 'data': data['hourly'][6]},
            ]:
                image = Image.new("1", (oled.width, oled.height))
                draw = ImageDraw.Draw(image)

                draw.text((0, 0), step['title'], font=font3, fill=255)
                draw.text((0, 16), step['data']['weather'][0]['description'], font=font2, fill=255)
                # Use math.ceil to always round up the temperature
                temperature = math.ceil(step['data']['temp'])
                draw.text((48, 32), str(temperature) + '°C', font=font3, fill=255)
                draw.text((48, 48), str(step['data']['humidity']) + '%', font=font3, fill=255)
                image.paste(get_icon(step['data']['weather'][0]['icon']), (8, 32))

                oled.image(image)
                oled.show()
                time.sleep(4)

            image = Image.new("1", (oled.width, oled.height))
            draw = ImageDraw.Draw(image)

            draw.text((0, 0), 'nächste Tage', font=font3, fill=255)
            for i in range(1, 4):
                # Use math.ceil to always round up daily temperatures
                day_temp = math.ceil(data['daily'][i]['temp']['max'])
                night_temp = math.ceil(data['daily'][i]['temp']['min'])
                draw.text((24, 16 * i), str(day_temp) + '°C', font=font2, fill=255)
                draw.text((76, 16 * i), str(night_temp) + '°C', font=font2, fill=255)
                image.paste(get_icon(data['daily'][i]['weather'][0]['icon'], 16), (0, 16 * i))

            oled.image(image)
            oled.show()
            time.sleep(8)

        except Exception as e:
            print(f"Error displaying weather data: {e}")
    else:
        time.sleep(10)
