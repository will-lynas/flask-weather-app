from flask import Flask, redirect, render_template
import requests
from flask_sqlalchemy import SQLAlchemy
import os
import time


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class CityNotFoundError(Exception):
    def __init__(self):
        super().__init__("City not found")

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    temp = db.Column(db.Float, nullable=False)
    time = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.temp} {self.time} {self.country} {self.city}>"



with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return redirect('/UK/London')


@app.route('/<country_name>/<city_name>')
def city_weather(country_name, city_name): 
    try:
        city_weather = api_fetch(country_name, city_name)
    except CityNotFoundError:
        return 'City not Found', 404
    time_since_updated = time.time() - city_weather.time
    return render_template('city_weather.html', city_weather=city_weather, time_since_updated=time_since_updated)


def api_fetch(country_name, city_name) -> WeatherData:
    last_result = db.session.query(WeatherData).filter(WeatherData.country == country_name, WeatherData.city == city_name).order_by(WeatherData.time.desc()).first()
    if last_result:
        last_fetch = last_result.time
        last_fetch_delta = time.time() - last_fetch
        cache_time = 10
        if last_fetch_delta <= cache_time:
            return last_result

    with open('api_key.txt') as f:
        api_key = f.read().strip()
    params = {
            "q": f"{city_name}, {country_name}",
            "APPID": api_key,
            "units": "metric"
        }
    endpoint = "http://api.openweathermap.org/data/2.5/weather"
    response = requests.get(endpoint, params=params)
    if not response:
        raise CityNotFoundError
    response_json = response.json()
    weather_data = WeatherData(country=country_name, city=city_name, temp=response_json["main"]["temp"], time=time.time())
    db.session.add(weather_data)
    db.session.commit()
    return weather_data
