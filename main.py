import requests
import config
import json
import datetime
from dateutil import tz


def get_local_time(utc_timestamp):
    """Converts a UTC timestamp into a timezone-aware local datetime object."""
    utc_time = datetime.datetime.fromtimestamp(utc_timestamp, tz=tz.tzutc())
    return utc_time.astimezone(tz.tzlocal())


def get_iss_passes():
    """
    Fetches the 10-day visual pass forecast for the ISS from the N2YO API.
    """
    print("Connecting to N2YO API to fetch ISS pass data...")

    # N2YO's endpoint for "Visual Passes"
    # We are asking for passes for satellite #25544 (the ISS)
    # for our specific location (lat, long, alt)
    # for the next 10 days
    # with a minimum visibility of 0 degrees
    N2YO_URL = f"https://api.n2yo.com/rest/v1/satellite/visualpasses/25544/{config.MY_LAT}/{config.MY_LONG}/{config.MY_ALT}/10/0/&apiKey={config.N2YO_API_KEY}"

    try:
        response = requests.get(N2YO_URL)
        response.raise_for_status()
        data = response.json()

        if 'passes' in data:
            print(f"Successfully fetched {data['info']['passescount']} potential passes.")
            return data['passes']
        else:
            print("No 'passes' data found in N2YO API response.")
            return []

    except requests.exceptions.RequestException as e:
        print(f"N2YO API Error: {e}")
        return None
    

def get_weather_and_sunset():
    """
    Fetches the 48-hour hourly forescast and today's sunset time from OpenWeatherMap.
    """
    print("Connecting to OpenWeatherMap API...")

    OWM_URL = f"https://api.openweathermap.org/data/3.0/onecall?lat={config.MY_LAT}&lon={config.MY_LONG}&exclude=minutely,daily&appid={config.OWM_API_KEY}&units=imperial"

    try:
        response = requests.get(OWM_URL)
        response.raise_for_status()
        data = response.json()

        if 'hourly' in data and 'current' in data and 'sunset' in data['current']:
            hourly_forecast = data['hourly']

            sunset_timestamp = data['current']['sunset']
            sunset_time = datetime.datetime.fromtimestamp(sunset_timestamp, tz=tz.tzlocal())

            print(f"Successfully fetched wather. Today's sunset is at: {sunset_time.strftime('%I:%M %p')}")
            return hourly_forecast, sunset_time

        else:
            print("No 'hourly' or 'current' data found in OpenWeatherMap API response.")
            return None, None
        
    except requests.exceptions.RequestException as e:
        print(f"OpenWeatherMap API Error: {e}")
        return None, None
    

def get_astronauts():
    """
    Fetches the names of the astronauts currently on the ISS.
    """
    print("Connecting to Open Notify API...")

    ASTROS_URL = "http://api.open-notify.org/astros.json"

    try:
        response = requests.get(ASTROS_URL)
        response.raise_for_status()
        data = response.json()

        iss_crew = [person['name'] for person in data['people'] if person['craft'] == 'ISS']
        print(f"Successfully fetched {len(iss_crew)} astronauts on the ISS.")
        return iss_crew
    
    except requests.exceptions.RequestException as e:
        print(f"Open Notify API Error: {e}")
        return None
    

def find_best_sighting(passes, hourly_weather, sunset_time):
    """
    Filters the list of passes to find the first "good" sighting.
    Returns a dictionary of the sighting details if one is found, else None.
    """
    print("\n--- Filtering Sighting Opportunities ---")

    try:
        bedtime_hour, bedtime_minute = map(int, config.BEDTIME.split(":"))
        today_bedtime = datetime.datetime.now(tz=tz.tzlocal()).replace(
            hour=bedtime_hour,
            minute=bedtime_minute,
            second=0,
            microsecond=0
        )
    except ValueError:
        print("Invalid bedtime format. Please use HH:MM format.")
        return None
    
    for p in passes:
        pass_start_time = get_local_time(p['startUTC'])

        if p['mag'] > config.MIN_BRIGHTNESS:
            print(f"-> Skipping pass at {pass_start_time.strftime('%I:%M %p')} because it is too dim (Mag: {p['mag']})")
            continue

        if pass_start_time < sunset_time:
            print(f"-> Skipping pass at {pass_start_time.strftime('%I:%M %p')} because it is before sunset")
            continue

        if pass_start_time.date() == today_bedtime.date():
            if pass_start_time > today_bedtime:
                print(f"-> Skipping pass at {pass_start_time.strftime('%I:%M %p')} because it is after bedtime")
                continue

        try:
            forecast = next(h for h in hourly_weather if h['dt'] > pass_start_time.timestamp())
        except StopIteration:
            print(f"-> Skipping pass at {pass_start_time.strftime('%I:%M %p')} because no forecast data is available")
            continue

        cloud_cover = forecast['clouds']
        if cloud_cover > config.MAX_CLOUD_COVER:
            print(f"-> Skipping pass at {pass_start_time.strftime('%I:%M %p')} because it has too much cloud cover (Cloud Cover: {cloud_cover})")
            continue

        print(f"*** Found a good sighting at {pass_start_time.strftime('%I:%M %p')}! ***")
        return {
            "start_time": pass_start_time,
            "duration": p['duration'],
            "brightness": p['mag'],
            "start_az": p['startAzCompass'],
            "end_az": p['endAzCompass'],
            "cloud_cover": cloud_cover
        }
    
    print("--- No good sightings found in the next 10 days. ---")
    return None


def build_notification_message(sighting_details, crew):
    """
    Creates a natural language string for the Alexa notification.
    """
    sighting_time = sighting_details['start_time'].strftime('%I:%M %p').lstrip('0')

    duration_min = round(sighting_details['duration'] / 60)
    duration_str = f"{duration_min} minute"
    if duration_min > 1:
        duration_str += "s"

    if crew:
        first_names = [name.split(' ')[0] for name in crew]
        
        if len(first_names) == 1:
            names_str = first_names[0]
        elif len(first_names) == 2:
            names_str = f"{first_names[0]} and {first_names[1]}"
        else:
            names_str = f"{', '.join(first_names[:-1])}, and {first_names[-1]}"
            
        crew_str = f"Right now, {len(crew)} astronauts are on board, including {names_str}."
    else:
        crew_str = "Right now, astronauts are living and working onboard."

    message = f"""
    Get ready! There is a fantastic, bright pass of the International Space Station tonight.
    Look up at {sighting_time}.
    It will be visible for about {duration_str} starting in the {sighting_details['start_az']}
    and ending in the {sighting_details['end_az']}.
    The sky is forecasted to be clear.
    {crew_str}
    Enjoy the show!
    """

    return " ".join(message.split())


if __name__ == "__main__":
    print(f"--- ISS Sighting Notifier (Running at {datetime.datetime.now()}) ---")
    
    passes = get_iss_passes()
    hourly_data, sunset = get_weather_and_sunset()
    
    if passes and hourly_data:
        good_sighting = find_best_sighting(passes, hourly_data, sunset)
        
        if good_sighting:
            print("\n--- !!! ALERT: Good Sighting Found !!! ---")
            print(json.dumps(good_sighting, indent=2, default=str))
            
            print("Fetching crew data to build notification...")
            crew = get_astronauts()
            
            notification_message = build_notification_message(good_sighting, crew)
            print("\n--- Notification Message ---")
            print(notification_message)
            
            # 3. Send Notification
            # TODO
            
        else:
            print("No suitable ISS sightings found matching your criteria.")
            
    else:
        print("Failed to get data from APIs. Exiting.") 
