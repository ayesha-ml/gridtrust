import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("EIA_API_KEY")
URL = "https://api.eia.gov/v2/electricity/rto/region-data/data/"

params = {
    "api_key": "oXdxf4ptc2enU9s4EMNdda7iPjBbSXvXV41Qw0TS",
    "frequency": "hourly",
    "data[0]": "value",
    "facets[respondent][]": "CISO",
    "facets[type][]": "D",
    "sort[0][column]": "period",
    "sort[0][direction]": "desc",
    "length": 5,
}

response = requests.get(URL, params=params)
print(response.status_code)
print(response.json())