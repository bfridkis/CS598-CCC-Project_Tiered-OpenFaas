import json
import requests

def get_weather():
    # Enter your API key here
    api_key = "542e3e3340ebc8675a5cf8c8880ae3e3"

    # base_url variable to store url
    base_url = "http://pro.openweathermap.org/data/2.5/weather?"

    # Give city name
    city_name = 'Chicago'

    # complete_url variable to store
    # complete url address
    complete_url = base_url + "q=" + city_name + "&appid=" + api_key

    # get method of requests module
    # return response object
    response = requests.get(complete_url) 

    resp = response.json()

    # Check for 404 error, city not found
    if resp["cod"] == "404":
        print(" Weather Data Not Found ")
        return{} 
    else:
        return resp

def main():
    print(get_weather())
    
if __name__ == "__main__":
    main()