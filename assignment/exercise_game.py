"""
Response time - single-threaded
"""

from machine import Pin
import time
import random
import json
import network
import urequests

N: int = 10
sample_ms = 10.0
on_ms = 500

# Wifi Credentials
SSID = "BU Guest (unencrypted)"
PASSWORD = ""

# Adafruit IO details
ADAFRUITIOUSERNAME = 'USERNAME' # Replace with Adafruit io username
ADAFRUITIOKEY = 'APIKEY' # Replace with Adafruit io Key
FEEDKEY = 'FEEDKEY'  # Replace with your feed key

def random_time_interval(tmin: float, tmax: float) -> float:
    """return a random time interval between max and min"""
    return random.uniform(tmin, tmax)


def blinker(N: int, led: Pin) -> None:
    # %% let user know game started / is over

    for _ in range(N):
        led.high()
        time.sleep(0.1)
        led.low()
        time.sleep(0.1)


def write_json(json_filename: str, data: dict) -> None:
    """Writes data to a JSON file.

    Parameters
    ----------

    json_filename: str
        The name of the file to write to. This will overwrite any existing file.

    data: dict
        Dictionary data to write to the file.
    """

    with open(json_filename, "w") as f:
        json.dump(data, f)


def scorer(t: list[int | None]) -> None:
    # %% collate results
    misses = t.count(None)
    print(f"You missed the light {misses} / {len(t)} times")

    t_good = [x for x in t if x is not None]
    
    print(t_good)

    # add key, value to this dict to store the minimum, maximum, average response time
    # and score (non-misses / total flashes) i.e. the score a floating point number
    # is in range [0..1]

    score  = ((N-int(misses))/len(t))
    data = {"Minimum": min(t_good), "Maximum": max(t_good), "Average Response Time": sum(t_good)/len(t_good), "Score": score}
    
    # %% make dynamic filename and write JSON
    
    now: tuple[int] = time.localtime()

    now_str = "-".join(map(str, now[:3])) + "T" + "_".join(map(str, now[3:6]))
    filename = f"score-{now_str}.json"

    print("write", filename)

    write_json(filename, data)
    
    upload_data(data)
    

# Upload data to Adafruit IO
def upload_data(data):
    url = f'https://io.adafruit.com/api/v2/{ADAFRUITIOUSERNAME}/feeds/{FEEDKEY}/data'
    headers = {'X-AIO-Key': ADAFRUITIOKEY, 'Content-Type': 'application/json'}
    data_to_send = {'value': json.dumps(data)}
    try:
        response = urequests.post(url, json=data_to_send, headers=headers)
        print("Data sent to Adafruit IO:", response.json())
        response.close()
    except Exception as e:
        print("Failed to send data:", e)
    
    


if __name__ == "__main__":
    # using "if __name__" allows us to reuse functions in other script files
    
    # Initialize the Wi-Fi in station mode
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    # Wait for connection
    print("Connecting to Wi-Fi", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(1)

    print("\nConnected to Wi-Fi")
    print("IP address:", wlan.ifconfig()[0])

    led = Pin("LED", Pin.OUT)
    button = Pin(16, Pin.IN, Pin.PULL_UP)

    t: list[int | None] = []

    blinker(3, led)

    for i in range(N):
        time.sleep(random_time_interval(0.5, 5.0))

        led.high()

        tic = time.ticks_ms()
        t0 = None
        while time.ticks_diff(time.ticks_ms(), tic) < on_ms:
            if button.value() == 0:
                t0 = time.ticks_diff(time.ticks_ms(), tic)
                led.low()
                break
        t.append(t0)

        led.low()

    blinker(5, led)

    scorer(t)


