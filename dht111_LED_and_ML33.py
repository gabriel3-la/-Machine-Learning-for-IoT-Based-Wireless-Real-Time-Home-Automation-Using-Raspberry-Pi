import RPi.GPIO as GPIO
import time
import requests
import adafruit_dht
import board


# Set GPIO mode (choose BOARD or BCM)
GPIO.setmode(GPIO.BCM)  # or GPIO.setmode(GPIO.BCM)

# GPIO pin for LED
LED_PIN = 12
# GPIO pin for LDR
LDR_PIN = 4
# GPIO pin for relay control
RELAY_PIN = 16

# ThingSpeak channel settings
THINGSPEAK_API_KEY = '0B0Q4AO540ESZKQI'
THINGSPEAK_URL = f'https://api.thingspeak.com/update?api_key={THINGSPEAK_API_KEY}'

# Initialize DHT11 sensor
dht_device = adafruit_dht.DHT11(board.D11)

# Set up GPIO for LED, LDR, and Relay

GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(LDR_PIN, GPIO.IN)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Machine Learning Parameters
HIGH_LDR_THRESHOLD = 800  # Adjust this threshold based on your LDR sensor readings

def predict_light_status(ldr_value):
    """Predict light status ('dark' or 'bright') based on LDR value"""
    if ldr_value > HIGH_LDR_THRESHOLD:
        return 'bright'
    else:
        return 'dark'

def control_relay(light_status):
    """Control relay based on predicted light status"""
    if light_status == 'bright':
        GPIO.output(RELAY_PIN, GPIO.HIGH)  # Turn on relay
    else:
        GPIO.output(RELAY_PIN, GPIO.LOW)  # Turn off relay

try:
    while True:
        # Read DHT11 temperature and humidity
        temperature_c = dht_device.temperature
        humidity = dht_device.humidity

        # Read LDR sensor value
        GPIO.setup(LDR_PIN, GPIO.OUT)
        GPIO.output(LDR_PIN, GPIO.LOW)
        time.sleep(0.1)
        GPIO.setup(LDR_PIN, GPIO.IN)
        start_time = time.time()
        while GPIO.input(LDR_PIN) == GPIO.LOW:
            pass
        end_time = time.time()
        ldr_value = int((end_time - start_time) * 1000)  # LDR value in milliseconds

        print("Temp: {:.1f} C / Humidity: {}% / LDR: {}".format(temperature_c, humidity, ldr_value))

        # Send data to ThingSpeak
        payload = {'field1': temperature_c, 'field2': humidity, 'field3': ldr_value}
        response = requests.get(THINGSPEAK_URL, params=payload)

        if response.status_code == 200:
            print("Data sent to ThingSpeak successfully")
        else:
            print(f"Failed to send data to ThingSpeak (HTTP {response.status_code})")

        # Predict light status
        light_status = predict_light_status(ldr_value)

        # Control relay based on predicted light status
        control_relay(light_status)

        # Predict temperature status (you can add this back if needed)
        # temperature_status = predict_temperature_status(temperature_c)
        # Control LED based on temperature status prediction
        # if temperature_status == 'high':
        #     GPIO.output(LED_PIN, GPIO.HIGH)  # Turn on LED
        # else:
        #     GPIO.output(LED_PIN, GPIO.LOW)  # Turn off LED

        time.sleep(15)  # Adjust the interval (in seconds) based on ThingSpeak rate limits

except RuntimeError as err:
    print(f"Error reading DHT sensor: {err}")

finally:
    # Clean up GPIO
    GPIO.cleanup()
