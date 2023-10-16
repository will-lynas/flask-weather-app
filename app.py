from flask import Flask
import requests
from flask_sqlalchemy import SQLAlchemy
import os
import time


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    temp = db.Column(db.Float, nullable=False)
    time = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.temp} {self.time}>"

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    last_result = db.session.query(WeatherData).order_by(WeatherData.time.desc()).first()
    if last_result:
        last_fetch = last_result.time
        last_fetch_delta = time.time() - last_fetch
        # Only fetch more frequently than once every cache_time seconds
        cache_time = 10 * 60
        if last_fetch_delta > cache_time:
            last_result = api_fetch("UK", "London")
            last_fetch_delta = 0
    else:
        last_result = api_fetch("UK", "London")
        last_fetch_delta = 0
    return f"Temperature: {last_result.temp} Time since updated: {last_fetch_delta}"


@app.route('/<country_name>/<city_name>')
def city_weather(country_name, city_name):
    last_result = db.session.query(WeatherData).filter(WeatherData.country.like(country_name), WeatherData.city.like(city_name)).order_by(WeatherData.time.desc()).first()
    if last_result:
        last_fetch = last_result.time
        last_fetch_delta = time.time() - last_fetch
        # Only fetch more frequently than once every cache_time seconds
        cache_time = 10
        if last_fetch_delta > cache_time:
            last_result = api_fetch(country_name, city_name)
            last_fetch_delta = 0
    else:
        last_result = api_fetch(country_name, city_name)
        last_fetch_delta = 0
    return f"Country: {country_name}. City: {city_name}. Temperature: {last_result.temp}. Time since updated: {last_fetch_delta}"


def api_fetch(country_name, city_name) -> WeatherData:
    with open('api_key.txt') as f:
        api_key = f.read().strip()
    params = {
            "q": f"{city_name}, {country_name}",
            "APPID": api_key,
            "units": "metric"
        }
    endpoint = "http://api.openweathermap.org/data/2.5/weather"
    response = requests.get(endpoint, params=params).json()
    weather_data = WeatherData(country=country_name, city=city_name, temp=response["main"]["temp"], time=time.time())
    db.session.add(weather_data)
    db.session.commit()
    return weather_data
