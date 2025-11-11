**ISS Sighting Notifier**

---

The **ISS Sighting Notifier** is an automated script that alerts you to ideal viewing opportunities for the International Space Station (ISS) from your specific location.

This project is designed to be a “set it and forget it” service. It runs automatically once per day using a serverless cloud function. The script gathers data on upcoming ISS passes, filters them based on optimal viewing conditions, and sends a verbal announcement to all Alexa devices in your home if a “good” sighting is happening that night.

The script’s “smart filtering” is designed to find only the best viewing opportunities, defined by:



* **Nighttime:** The pass must occur after sunset
* **Before Bedtime:** The pass must occur before a user-defined “bedtime” (e.g., 9:00 PM) to avoid middle-of-the-night announcements.
* **Clear Skies:** The script checks a weather forecast and will only send an alert if cloud cover is below a set threshold (e.g., 25%)
* **High Visibility:** The pass must be bright enough to be easily seen (based on its “magnitude” rating)

The alert message is designed to be engaging, including the exact time, duration, and direction of the pass, as well as a fun fact: the names of the astronauts currently on board the station.


---

**Services & API Accounts**

To run this project, you will need to sign up for several free (or “freemium”) services and collect the necessary API keys and credentials.



* **[N2YO.com](N2YO.com)**
    * **Purpose:** Provides the 10-day forecast for ISS visual passes over a specific location. This is our primary data source for pass time, duration, and brightness.
    * **Account:** This requires a free account to get an API key.
* **[OpenWeatherMap](https://openweathermap.org/api/one-call-api)**
    * **Purpose:** Provides detailed hourly weather forecast data, specifically the cloud cover percentage (clouds) and sunset time (sunset) for your location.
    * **Account:** Requires a free account. You will need to subscribe to the “One Call API 3.0” (which has a generous free tier) to get an API key.
* **[Open Notify](http://open-notify.org/Open-Notify-API/People-In-Space/)**
    * **Purpose:** A simple, open API used to fetch the number and names of the astronauts currently in space.
    * **Account:** No account or API key is required.
* **Amazon / Alexa**
    * **Purpose:** Used to send the final notification as a verbal announcement on your Echo devices.
    * **Account:** You will need your standard Amazon login credentials. We will use a Python library (alexapy) to handle authentication and send the announcement command.
* **Cloud Provider (AWS)**
    * **Purpose:** To host and automate the script to run on a daily schedule without needing a dedicated computer.
    * **Account:** I recommend AWS for this project. You can create a free tier account. We will use two of their services:
        * AWS Lambda: To host our serverless Python function.
        * Amazon EventBridge: To create a daily “cron” schedule that triggers the Lambda function.


---

**Dependencies & Tech Stack**

This project is written in **Python 3.9** (or newer). The following Python libraries will be required.

* **requests**
* **python-dateutil**
* **alexapy**
