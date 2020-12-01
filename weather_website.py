import datetime
import json
import urllib.request

import datanews
import datetimerange
import ephem
import pytz
from flask import Flask, render_template, request
from flask_compress import Compress
from googletrans import Translator

import send_email
from run_sql import MySQL

hourly_images = []
daily_images = []
id_list = []
temp = ''
country = ''
main_list = []
alerts_image = ''
pop_list = []
city = ''
email = ''
lat = 0
lon = 0
data = {'city_name': 'Princeton', 'country_code': 'US'}

day_name = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
time_range = datetimerange.DateTimeRange("T5:00:00+0900", "T9:00:00+0900")


def send_emails_web():
    if str(datetime.datetime.today().hour) + ":00:00+0900" in time_range:
        global data_daily
        msg = "Hello, \nToday is " + data_daily['day_1_main'].lower()
        database = MySQL()
        all_emails = database.get_all()
        database.close()
        for row in all_emails:
            send_email.send_mail(row[0], row[1], msg, data_daily['day_1_temp'], ''.join([alerts_description,
                                                                                         alerts_description_2]), False)


def verify_icon(id_tag, it_is_day):
    id_tag_str = str(id_tag)
    id_list.append(id_tag)

    if id_tag in (200, 201, 202, 230, 231, 232):
        return 'static/icons/icon-11.svg'

    elif id_tag in (210, 211, 212, 221):
        return 'static/icons/icon-12.svg'

    elif id_tag_str[0] == '3':
        return 'static/icons/light_rain.svg'

    elif id_tag in (511, 520, 521, 522, 531):
        return 'static/icons/heavy_rain.svg'

    elif id_tag_str[0] == '6':
        return 'static/icons/icon-13.svg '

    elif id_tag_str[0] == '7':
        return 'static/icons/fog_2.svg'

    elif id_tag == 802:
        return 'static/icons/cloudy.svg'

    elif id_tag == 803:
        return 'static/icons/icon-6.svg'
    elif id_tag in (803, 804):
        return 'static/icons/icon-6.svg'

    if it_is_day:
        if id_tag == 800:
            return 'static/icons/sunny.svg'
        elif id_tag == 801:
            return 'static/icons/cloudy&sunny.svg'
        elif id_tag in (500, 501, 502, 503, 504):
            return 'static/icons/rain&sunny.svg'

    else:
        if id_tag == 800:
            return 'static/icons/clear_moon.webp'
        elif id_tag == 801:
            return 'static/icons/clouds_moon.webp'
        elif id_tag in (500, 501, 502, 503, 504):
            return 'static/icons/rain_moon.webp'

    return 'error'


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
COMPRESS_MIMETYPES = ['text/html', 'text/css', 'text/xml', 'application/json', 'application/javascript']
COMPRESS_LEVEL = 6
COMPRESS_MIN_SIZE = 500
Compress(app)

alerts_data = {}
alerts_description = ''
alerts_description_2 = ''
second_alert = False

data_daily = {}


@app.route('/', methods=['POST', 'GET'])
def weather():
    global alerts_data, city, alerts_image, second_alert, pop_list, lat, lon, data_daily, alerts_description, \
        alerts_description_2, temp, country
    city = 'Princeton'
    state = 'newjersey'
    country = 'us'
    if request.method == 'POST':
        city = request.form['city'].title()
    # else:
    #     geoip = urllib.request.urlopen(
    #         'https://ip-geolocation.whoisxmlapi.com/api/v1?apiKey=at_7PwbMzdUGTjddKi5dhSUlOrzUEHhF&ipAddress').read()
    #     geo = json.loads(geoip)
    #     city = geo['location']['city']
    #     state = geo['location']['region']
    #     state = state.lower()
    #     state = state.replace(" ", "")
    #     print(city, state)
    new_city = city.strip()
    #
    # if ' ' in new_city:
    #     new_city = new_city.replace(' ', '+')

    # source contain json data from api
    temp = "imperial"
    symbol = 'F'
    isCelsius = False
    if isCelsius:
        temp = "metric"
        symbol = 'C'
    try:

        items = ['http://api.openweathermap.org/data/2.5/weather?q=', city, ",", state, ",", country,
                 '&units=', temp, '&appid=8a5edfd4d0e0f8953dbe82364cfc0b10']
        source = urllib.request.urlopen(''.join(items)).read()
        list_of_data = json.loads(source)

    except urllib.error.HTTPError:
        return render_template("404.html")

    main_data = {
        "country_code": str(list_of_data['sys']['country']),
        "city_name": str(city),
        "main": list_of_data['weather'][0]['main'],
        "description": list_of_data['weather'][0]['description'],
        "coordinate": str(list_of_data['coord']['lat']) + ',' + str(list_of_data['coord']['lon']),
        "temp": int(round(list_of_data['main']['temp'], 0)),
        "temp_min": int(round(list_of_data['main']['temp_min'])),
        "temp_max": int(round(list_of_data['main']['temp_max'])),
        "feels_like": int(round(list_of_data['main']['feels_like'])),
        "humidity": str(list_of_data['main']['humidity']),
        "wind_speed": list_of_data['wind']['speed'],
        'id': list_of_data['weather'][0]['id'],
        'sunrise': list_of_data['sys']['sunrise'],
        'sunset': list_of_data['sys']['sunset'],
        'offset': list_of_data['timezone']
    }
    lat = str(list_of_data['coord']['lat'])
    lon = str(list_of_data['coord']['lon'])

    # Sunrise and Sunset
    sunrise_time = main_data['sunrise'] + main_data['offset']
    sunset_time = main_data['sunset'] + main_data['offset']

    sunrise = datetime.datetime.fromtimestamp(sunrise_time, datetime.timezone.utc).strftime('%I:%M %p')
    sunset = datetime.datetime.fromtimestamp(sunset_time, datetime.timezone.utc).strftime('%I:%M %p')
    sun_time = [sunrise, sunset]

    items_hourly = ['https://api.openweathermap.org/data/2.5/onecall?lat=', lat, '&lon=', lon, '&units=', temp,
                    '&exclude=minutely,current&appid=8a5edfd4d0e0f8953dbe82364cfc0b10']
    # Hourly Weather
    hourly_source = urllib.request.urlopen(''.join(items_hourly)).read()
    hourly_data = json.loads(hourly_source)

    # Gets accurate hour, day and month for searched location
    tz = hourly_data['timezone']
    datetime_tz = datetime.datetime.now(pytz.timezone(tz))
    today_date = datetime_tz.day
    day = datetime_tz.today().weekday()

    # Gets day as a number
    day_2 = (datetime_tz + datetime.timedelta(days=1)).weekday()
    day_3 = (datetime_tz + datetime.timedelta(days=2)).weekday()
    day_4 = (datetime_tz + datetime.timedelta(days=3)).weekday()
    day_5 = (datetime_tz + datetime.timedelta(days=4)).weekday()
    day_6 = (datetime_tz + datetime.timedelta(days=5)).weekday()
    day_7 = (datetime_tz + datetime.timedelta(days=6)).weekday()

    list_of_days = [day, day_2, day_3, day_4, day_5, day_6, day_7]

    for i, val in enumerate(list_of_days):  # Converts number to day ( 1 = Monday 2 = Tuesday etc)
        list_of_days[i] = day_name[list_of_days[i]]

    month_name = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'June', 7: 'July', 8: 'Aug',
                  9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

    current_month = datetime_tz.month
    current_month = month_name[current_month]
    current_hour = int(datetime_tz.strftime("%H"))

    # Gets hour in 12 hour format (am/pm)
    list_of_hours = [current_hour, current_hour + 1, current_hour + 2, current_hour + 3, current_hour + 4,
                     current_hour + 5, current_hour + 6]

    for i, val in enumerate(list_of_hours):
        if list_of_hours[i] > 24:
            list_of_hours[i] -= 24
        if list_of_hours[i] > 12:
            list_of_hours[i] -= 12
            list_of_hours[i] = str(list_of_hours[i]) + ' pm'
        elif list_of_hours[i] == 0:
            list_of_hours[i] = 12
            list_of_hours[i] = str(list_of_hours[i]) + ' pm'
        else:
            list_of_hours[i] = str(list_of_hours[i]) + ' am'
    try:
        pop_list = []
        items_pop = ['http://dataservice.accuweather.com/locations/v1/cities/search?apikey='
                     '4zrGVjvJENvvA6SvIPA6hW1qUmtKqCcd&q=', new_city.lower(), '&details=false']
        get_id = urllib.request.urlopen(''.join(items_pop)).read()
    except:
        pop_list = ['N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A']

    else:
        city_id = json.loads(get_id)
        try:
            key = city_id[0]["Key"]
        except IndexError:
            return render_template("404.html")

        # get_pop = urllib.request.urlopen('http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/' + key +
        #                                  '?apikey=4zrGVjvJENvvA6SvIPA6hW1qUmtKqCcd&details=false').read()
        # pop_info = json.loads(get_pop)
        #
        # for i in range(0, 8):
        #     pop_num = pop_info[i]['PrecipitationProbability']
        #     pop_num = str(int(round(pop_num + 0.1, -1))) + '%'
        #     pop_list.append(pop_num)

    item_alerts = ['https://api.weatherbit.io/v2.0/alerts?lat=', lat, '&lon=', lon,
                   '&key=888c4677014d4578a511570492df67b0']
    alerts_api = urllib.request.urlopen(''.join(item_alerts)).read()
    alerts_store = json.loads(alerts_api)
    try:
        alerts_data = {
            'expires': alerts_store['alerts'][0]['expires_utc'],
            'effective': alerts_store['alerts'][0]['effective_local'],
            'description': alerts_store['alerts'][0]['description'],
            'effective_utc': alerts_store['alerts'][0]['effective_utc'],
            'severity': alerts_store['alerts'][0]['severity'],
            'title': alerts_store['alerts'][0]['title'], 'local_expire': alerts_store['alerts'][0]['expires_local']
        }

    except IndexError:
        alerts_description = 'No alerts in this area!'

    else:
        # translator = Translator()
        # alerts_description = translator.translate(alerts_data['description'])
        # alerts_description = alerts_description.text.replace('English: ', '')
        # alerts_description = alerts_description.replace('* WHAT...', 'What: ')
        # alerts_description = alerts_description.replace('* WHERE...', 'Where: ')
        # alerts_description = alerts_description.replace('* WHEN...', 'When: ')
        # alerts_description = alerts_description.replace('* IMPACTS...', 'Impacts: ')
        severity = alerts_data['severity']
        severity_switch = {'Warning': 'static/alerts/warning.png', 'Watch': 'static/alerts/watch.png',
                           'Extreme': 'static/alerts/extreme.png', 'Advisory': 'static/alerts/advisory.png'}

        alerts_image = severity_switch.get(severity, 'static/weather_icon-2.co')

        try:
            alerts_data_2 = {
                'expires': alerts_store['alerts'][1]['expires_utc'],
                'effective': alerts_store['alerts'][1]['effective_local'],
                'description': alerts_store['alerts'][1]['description'],
                'effective_utc': alerts_store['alerts'][1]['effective_utc'],
                'severity': alerts_store['alerts'][1]['severity'],
                'title': alerts_store['alerts'][1]['title'],
                'local_expire': alerts_store['alerts'][1]['expires_local']
            }
            second_alert = True

        except IndexError:
            second_alert = False

        else:
            pass
            # alerts_description_2 = translator.translate(alerts_data_2['description'])
            # alerts_description_2 = alerts_description_2.text.replace('English: ', '')
            # alerts_description_2 = alerts_description_2.replace('* WHAT...', 'What: ')
            # alerts_description_2 = alerts_description_2.replace('* WHERE...', 'Where: ')
            # alerts_description_2 = alerts_description_2.replace('* WHEN...', 'When: ')
            # alerts_description_2 = alerts_description_2.replace('* IMPACTS...', 'Impacts: ')

    # Hourly Weather stored in dictionary
    data_hourly = {
        'feels_like': int(round(hourly_data['hourly'][0]['feels_like'], 0)),
        'hour_1_temp': int(round(hourly_data['hourly'][0]['temp'], 0)),
        'hour_1_id': hourly_data['hourly'][0]['weather'][0]['id'],
        'hour_1_main': hourly_data['hourly'][0]['weather'][0]['main'],
        'hour_2_temp': int(round(hourly_data['hourly'][1]['temp'], 0)),
        'hour_2_id': hourly_data['hourly'][1]['weather'][0]['id'],
        'hour_2_main': hourly_data['hourly'][1]['weather'][0]['main'],
        'hour_3_temp': int(round(hourly_data['hourly'][2]['temp'], 0)),
        'hour_3_id': hourly_data['hourly'][2]['weather'][0]['id'],
        'hour_3_main': hourly_data['hourly'][2]['weather'][0]['main'],
        'hour_4_temp': int(round(hourly_data['hourly'][3]['temp'], 0)),
        'hour_4_id': hourly_data['hourly'][3]['weather'][0]['id'],
        'hour_4_main': hourly_data['hourly'][3]['weather'][0]['main'],
        'hour_5_temp': int(round(hourly_data['hourly'][4]['temp'], 0)),
        'hour_5_id': hourly_data['hourly'][4]['weather'][0]['id'],
        'hour_5_main': hourly_data['hourly'][4]['weather'][0]['main'],
        'hour_6_temp': int(round(hourly_data['hourly'][5]['temp'], 0)),
        'hour_6_id': hourly_data['hourly'][5]['weather'][0]['id'],
        'hour_6_main': hourly_data['hourly'][5]['weather'][0]['main'],
        'hour_7_temp': int(round(hourly_data['hourly'][6]['temp'], 0)),
        'hour_7_id': hourly_data['hourly'][6]['weather'][0]['id'],
        'hour_7_main': hourly_data['hourly'][6]['weather'][0]['main'],
        'hour_8_temp': int(round(hourly_data['hourly'][7]['temp'], 0)),
        'hour_8_id': hourly_data['hourly'][7]['weather'][0]['id'],
        'hour_8_main': hourly_data['hourly'][7]['weather'][0]['main'],
        'hour_9_temp': int(round(hourly_data['hourly'][8]['temp'], 0)),
        'hour_9_id': hourly_data['hourly'][8]['weather'][0]['id'],
        'hour_9_main': hourly_data['hourly'][8]['weather'][0]['main'],
        'hour_10_temp': int(round(hourly_data['hourly'][9]['temp'], 0)),
        'hour_10_id': hourly_data['hourly'][9]['weather'][0]['id'],
        'hour_10_main': hourly_data['hourly'][9]['weather'][0]['main'],
        'hour_11_temp': int(round(hourly_data['hourly'][10]['temp'], 0)),
        'hour_11_id': hourly_data['hourly'][10]['weather'][0]['id'],
        'hour_11_main': hourly_data['hourly'][10]['weather'][0]['main'],
        'hour_12_temp': int(round(hourly_data['hourly'][11]['temp'], 0)),
        'hour_12_id': hourly_data['hourly'][11]['weather'][0]['id'],
        'hour_12_main': hourly_data['hourly'][11]['weather'][0]['main'],
    }

    # Daily weather
    data_daily = {
        'day_1_temp': int(round(hourly_data['daily'][0]['temp']['day'], 0)),
        'day_1_max': int(round(hourly_data['daily'][0]['temp']['max'], 0)),
        'day_1_min': int(round(hourly_data['daily'][0]['temp']['min'], 0)),
        'day_1_main': hourly_data['daily'][0]['weather'][0]['main'],
        'day_1_id': hourly_data['daily'][0]['weather'][0]['id'],
        'day_2_temp': int(round(hourly_data['daily'][1]['temp']['day'], 0)),
        'day_2_max': int(round(hourly_data['daily'][1]['temp']['max'], 0)),
        'day_2_min': int(round(hourly_data['daily'][1]['temp']['min'], 0)),
        'day_2_main': hourly_data['daily'][1]['weather'][0]['main'],
        'day_2_id': hourly_data['daily'][1]['weather'][0]['id'],
        'day_3_temp': int(round(hourly_data['daily'][2]['temp']['day'], 0)),
        'day_3_max': int(round(hourly_data['daily'][2]['temp']['max'], 0)),
        'day_3_min': int(round(hourly_data['daily'][2]['temp']['min'], 0)),
        'day_3_main': hourly_data['daily'][2]['weather'][0]['main'],
        'day_3_id': hourly_data['daily'][2]['weather'][0]['id'],
        'day_4_temp': int(round(hourly_data['daily'][3]['temp']['day'], 0)),
        'day_4_max': int(round(hourly_data['daily'][3]['temp']['max'], 0)),
        'day_4_min': int(round(hourly_data['daily'][3]['temp']['min'], 0)),
        'day_4_main': hourly_data['daily'][3]['weather'][0]['main'],
        'day_4_id': hourly_data['daily'][3]['weather'][0]['id'],
        'day_5_temp': int(round(hourly_data['daily'][4]['temp']['day'], 0)),
        'day_5_max': int(round(hourly_data['daily'][4]['temp']['max'], 0)),
        'day_5_min': int(round(hourly_data['daily'][4]['temp']['min'], 0)),
        'day_5_main': hourly_data['daily'][4]['weather'][0]['main'],
        'day_5_id': hourly_data['daily'][4]['weather'][0]['id'],
        'day_6_temp': int(round(hourly_data['daily'][5]['temp']['day'], 0)),
        'day_6_max': int(round(hourly_data['daily'][5]['temp']['max'], 0)),
        'day_6_min': int(round(hourly_data['daily'][5]['temp']['min'], 0)),
        'day_6_main': hourly_data['daily'][5]['weather'][0]['main'],
        'day_6_id': hourly_data['daily'][5]['weather'][0]['id'],
        'day_7_temp': int(round(hourly_data['daily'][6]['temp']['day'], 0)),
        'day_7_max': int(round(hourly_data['daily'][6]['temp']['max'], 0)),
        'day_7_min': int(round(hourly_data['daily'][6]['temp']['min'], 0)),
        'day_7_main': hourly_data['daily'][6]['weather'][0]['main'],
        'day_7_id': hourly_data['daily'][6]['weather'][0]['id'],
        'uv': round(hourly_data['daily'][0]['uvi'])
    }
    first_hour = data_hourly['hour_1_main']
    if first_hour == 'Clear':
        bg_images = 'https://res.cloudinary.com/program-explorers/image/upload/v1600480831/Grand-Canyon-Destination' \
                    '-Page_mp557z.jpg '
    elif first_hour == 'Rain':
        bg_images = 'https://res.cloudinary.com/program-explorers/image/upload/v1600480866/2z1a5tixad121_ahwtn0.jpg'
    elif first_hour == 'Clouds':
        bg_images = 'https://res.cloudinary.com/program-explorers/image/upload/v1600480909' \
                    '/aAujKcEpiVcrqCCut2biNnG63S5fcwhRYcIb81Z0UnQ_yqq8iy.jpg '
    elif first_hour == 'Snow':
        bg_images = 'https://res.cloudinary.com/program-explorers/image/upload/v1600480952/GC_Winter_oan3zl.jpg'
    else:
        bg_images = 'https://res.cloudinary.com/program-explorers/image/upload/v1600480973/grand-canyon-sunset_c6yvay' \
                    '.jpg '

    user = ephem.Observer()
    user.lat = lat
    user.lon = lon
    next_sunrise_datetime = user.next_rising(ephem.Sun()).datetime()
    next_sunset_datetime = user.next_setting(ephem.Sun()).datetime()
    it_is_day = next_sunset_datetime < next_sunrise_datetime

    # Get icon for each hour
    for i in range(1, 13):
        hourly_images.append(verify_icon(data_hourly['hour_' + str(i) + '_id'], it_is_day))
        main_list.append(data_hourly['hour_' + str(i) + '_main'])
    for j in range(1, 8):
        daily_images.append(verify_icon(data_daily['day_' + str(j) + '_id'], True))

    id_tag = main_data['id']
    image = verify_icon(id_tag, it_is_day)

    send_emails_web()

    if alerts_description == alerts_description_2:
        alerts_description_2 = ''

    # symbol = 'F'
    # isCelsius = False
    # if isCelsius:
    #     main_data, data_hourly, data_daily = convert_to_c(main_data, data_hourly, data_daily)
    #     symbol = 'C'

    return render_template('home.html', data=main_data, image=image, hourly_images=hourly_images,
                           data_hourly=data_hourly, data_daily=data_daily, daily_images=daily_images,
                           days=list_of_days, sun_time=sun_time, list_of_hours=list_of_hours,
                           current_month=current_month, lat=lat, lon=lon, alerts_data=alerts_data,
                           alerts_image=alerts_image, new_des=alerts_description, pop_list=pop_list,
                           todays_date=today_date, bg_images=bg_images, symbol=symbol)


@app.route('/news/')
def news():
    global country
    datanews.api_key = '04loc6feus33veq8swg615d7w'

    response = datanews.headlines(q="earthquakes, rain, showers, snow, sunny, thunderstorm, clear, night, day," +
                                    " morning, evening, raining, wind, cold"
                                  , country=country,
                                  language=['en'], sortBy="relevance")
    articles = response['hits']
    article_data = {
        'article1_title': articles[0]['title'],
        'article1_content': articles[0]['content'],
        'article1_img': articles[0]['imageUrl'],
        'article1_url': articles[0]['url'],
        'article2_title': articles[1]['title'],
        'article2_content': articles[1]['content'],
        'article2_img': articles[1]['imageUrl'],
        'article2_url': articles[1]['url'],
        'article3_title': articles[2]['title'],
        'article3_content': articles[2]['content'],
        'article3_img': articles[2]['imageUrl'],
        'article3_url': articles[2]['url'],
        'article4_title': articles[3]['title'],
        'article4_content': articles[3]['content'],
        'article4_img': articles[3]['imageUrl'],
        'article4_url': articles[3]['url'],
        'article5_title': articles[4]['title'],
        'article5_content': articles[4]['content'],
        'article5_img': articles[4]['imageUrl'],
        'article5_url': articles[4]['url'],
    }
    return render_template("news.html", article_data=article_data)


@app.route('/subscribe/', methods=['POST', 'GET'])
def send_mail():
    global email
    email = request.form['subscribe']
    message = "Please confirm the information below, or edit"
    message2 = ""

    return render_template("subscribe.html", message=message, message2=message2, email=email, city=city)


@app.route('/subscribe/edit', methods=['POST', 'GET'])
def edit():
    return render_template('edit.html')


@app.route('/subscribe/done', methods=['POST', 'GET'])
def update_mail_loc():
    global email, city, data_daily
    msg = "Thank you for subscribing to Weather Website by Program Explorers!"
    alerts_email = alerts_description + alerts_description_2

    try:
        email = request.form['update_email']
        city = request.form['update_location']
    except:
        pass
    is_email_sent = send_email.send_mail(email, city, msg, data_daily['day_1_temp'], alerts_email, True)

    if is_email_sent:
        message = "Thank You For Subscribing!"

    else:
        message = 'Invalid email try again'

    data_base = MySQL()
    data_base.insert(email=email, location=city)
    data_base.commit()
    data_base.close()

    return render_template('done.html', message=message)


@app.route('/alerts')
def alerts():
    return render_template('alerts.html', des=alerts_description, des2=alerts_description, city=city)


if __name__ == '__main__':
    app.run(debug=True)
