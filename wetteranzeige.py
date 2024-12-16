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
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# import variables
key = os.getenv('KEY')
lon = os.getenv('LON')
lat = os.getenv('LAT')


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

def get_icon(icon_code, size=32):
    path = f'./icons/{icon_code}.svg'
    if os.path.isfile(path):
        return Image.open(
            BytesIO(cairosvg.svg2png(url=path))  # convert svg to png
        ).resize((size, size)).convert('1')  # return resized image
    else:
        return Image.new("1", (size, size))  # return empty image

session = requests.Session()

def fetch_weather_data():
    try:
        # Format the URL with proper values
        timestamp = int(time.time())
        url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={key}&lang=de&units=metric&_={timestamp}'
        
        # Set session-level headers to ensure no caching
        session.headers.update({
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # Send the GET request using the session
        response = session.get(url, timeout=10)
        
        # Print headers to verify caching control
        print("Response Headers: ", response.headers) 
        print("Date from headers: ", response.headers.get('Date'))
        
        # Raise an error for any unsuccessful responses
        response.raise_for_status() 
        
        # Return the parsed JSON response
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
            # Display current weather
            current_weather = data['weather'][0]['description']
            temp = math.ceil(data['main']['temp'])
   
            humidity = data['main']['humidity']
            icon_code = data['weather'][0]['icon']

            image = Image.new("1", (oled.width, oled.height))
            draw = ImageDraw.Draw(image)

            draw.text((0, 0), "Aktuelles Wetter:", font=font3, fill=255)
            draw.text((0, 16), current_weather, font=font2, fill=255)
            draw.text((48, 32), f"{temp}°C", font=font3, fill=255)
            draw.text((48, 48), f"{humidity}%", font=font3, fill=255)
            image.paste(get_icon(icon_code), (8, 32))

            oled.image(image)
            oled.show()
            time.sleep(4)

            # Clear display for time
            image = Image.new("1", (oled.width, oled.height))
            draw = ImageDraw.Draw(image)
            
            draw.text((0, 0), "Aktuelle Uhrzeit:", font=font3, fill=255)
            now = datetime.utcnow() 
            current_time = now.strftime("%H:%M:%S")
            draw.text((10, 20), current_time, font=font3, fill=255)
            day = now.strftime('%A')
            if day == "Monday":
                short = "Mo"
            elif day == "Tuesday":
                short = "Di"
            elif day == "Wednesday":
                short = "Mi"
            elif day == "Thursday": 
                short = "Do"
            elif day == "Friday": 
                short = "Fr"
            elif day == "Saturday": 
                short ="Sa"
            elif day == "Sunday": 
                short = "So"

            fulldate = '%s/%s' % (now.day, now.month)
            draw.text((10, 40), f'{short}, der {fulldate}', font=font3, fill=255)


            oled.image(image)
            oled.show()
            time.sleep(4) 



        except Exception as e:
            print(f"Error displaying weather data: {e}")
    else:
        time.sleep(10)

