import openai
import streamlit as st
import datetime
import pytz
from skyfield.api import load, wgs84
from skyfield.data import mpc
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# OpenAI API 키 설정
openai_api_key = st.secrets["OPENAI_API_KEY"]
if not openai_api_key:
    raise ValueError("OpenAI API key is not set. Please set it in the .env file or as an environment variable.")

client = openai.OpenAI(api_key=openai_api_key)

def get_zodiac_sign(month, day):
    zodiac_signs = [
        ("염소자리", (1, 1), (1, 19)),
        ("물병자리", (1, 20), (2, 18)),
        ("물고기자리", (2, 19), (3, 20)),
        ("양자리", (3, 21), (4, 19)),
        ("황소자리", (4, 20), (5, 20)),
        ("쌍둥이자리", (5, 21), (6, 20)),
        ("게자리", (6, 21), (7, 22)),
        ("사자자리", (7, 23), (8, 22)),
        ("처녀자리", (8, 23), (9, 22)),
        ("천칭자리", (9, 23), (10, 22)),
        ("전갈자리", (10, 23), (11, 21)),
        ("사수자리", (11, 22), (12, 21)),
        ("염소자리", (12, 22), (12, 31))
    ]

    for sign, start, end in zodiac_signs:
        if (month, day) >= start and (month, day) <= end:
            return sign
    return "알 수 없음"


def get_coordinates(place):
    geolocator = Nominatim(user_agent="astrology_app")
    try:
        location = geolocator.geocode(place)
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except (GeocoderTimedOut, GeocoderUnavailable):
        return None


def get_planet_positions(birth_date, birth_time, lat, lon):
    ts = load.timescale()
    birth_datetime = datetime.datetime.combine(birth_date, birth_time)
    utc = pytz.utc
    birth_datetime_utc = birth_datetime.replace(tzinfo=utc)

    t = ts.utc(birth_datetime_utc.year, birth_datetime_utc.month, birth_datetime_utc.day,
               birth_datetime_utc.hour, birth_datetime_utc.minute, birth_datetime_utc.second)

    eph = load('de421.bsp')
    earth = eph['earth']

    planets = {
        'sun': eph['sun'],
        'moon': eph['moon'],
        'mercury': eph['mercury'],
        'venus': eph['venus'],
        'mars': eph['mars'],
        'jupiter': eph['jupiter barycenter'],
        'saturn': eph['saturn barycenter']
    }

    positions = {}

    for planet, body in planets.items():
        astrometric = earth.at(t).observe(body)
        ra, dec, _ = astrometric.apparent().radec()
        positions[planet] = f"RA: {ra.hours:.2f}h, Dec: {dec.degrees:.2f}°"

    return positions

def get_current_planet_positions(lat, lon):
    ts = load.timescale()
    t = ts.now()

    eph = load('de421.bsp')
    earth = eph['earth']

    planets = {
        'sun': eph['sun'],
        'moon': eph['moon'],
        'mercury': eph['mercury'],
        'venus': eph['venus'],
        'mars': eph['mars'],
        'jupiter': eph['jupiter barycenter'],
        'saturn': eph['saturn barycenter']
    }

    positions = {}

    for planet, body in planets.items():
        astrometric = earth.at(t).observe(body)
        ra, dec, _ = astrometric.apparent().radec()
        positions[planet] = f"RA: {ra.hours:.2f}h, Dec: {dec.degrees:.2f}°"

    return positions


def determine_fortune(planet_positions):
    prompts = {
        "재정 운": f"Given the positions of Jupiter (RA: {planet_positions['jupiter']}) and Venus (RA: {planet_positions['venus']}), evaluate the financial fortune, assign a score out of 100, and provide the result in Korean.",
        "애정 운": f"Given the positions of Mars (RA: {planet_positions['mars']}) and Venus (RA: {planet_positions['venus']}), evaluate the love fortune, assign a score out of 100, and provide the result in Korean.",
        "건강 운": f"Given the position of the Moon (RA: {planet_positions['moon']}), evaluate the health fortune, assign a score out of 100, and provide the result in Korean.",
        "직업 운": f"Given the positions of Mercury (RA: {planet_positions['mercury']}) and Jupiter (RA: {planet_positions['jupiter']}), evaluate the career fortune, assign a score out of 100, and provide the result in Korean."
    }

    fortune_messages = {}

    for key, prompt in prompts.items():
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides astrology fortune readings. Please answer in Korean."},
                {"role": "user", "content": prompt}
            ],
        )
        fortune_messages[key] = response.choices[0].message.content.strip()

    return fortune_messages


st.title('향상된 점성술 앱')

# Separate inputs for year, month, and day
current_year = datetime.datetime.now().year
birth_year = st.number_input("태어난 연도를 입력하세요", min_value=1900, max_value=current_year, value=1990)
birth_month = st.number_input("태어난 월을 입력하세요", min_value=1, max_value=12, value=1)
birth_day = st.number_input("태어난 일을 입력하세요", min_value=1, max_value=31, value=1)

# Validate the date
try:
    birth_date = datetime.date(birth_year, birth_month, birth_day)
except ValueError:
    st.error("잘못된 날짜입니다. 입력을 확인하세요.")
    st.stop()

birth_time = st.time_input("태어난 시간을 입력하세요")
birth_place = st.text_input("태어난 장소를 입력하세요 (도시, 국가)")

if st.button('점성술 정보 얻기'):
    zodiac_sign = get_zodiac_sign(birth_date.month, birth_date.day)
    st.write(f"당신의 별자리는: {zodiac_sign}")

    coordinates = get_coordinates(birth_place)
    if coordinates:
        lat, lon = coordinates
        st.write(f"태어난 장소의 좌표: 위도 {lat:.4f}, 경도 {lon:.4f}")

        planet_positions = get_planet_positions(birth_date, birth_time, lat, lon)
        st.write("태어난 때의 행성 위치:")
        for planet, position in planet_positions.items():
            st.write(f"{planet.capitalize()}: {position}")

        current_planet_positions = get_current_planet_positions(lat, lon)
        st.write("현재 행성 위치:")
        for planet, position in current_planet_positions.items():
            st.write(f"{planet.capitalize()}: {position}")

        current_fortune = determine_fortune(current_planet_positions)
        st.write("현재 운세:")
        for key, message in current_fortune.items():
            st.write(message)

    else:
        st.write("입력한 태어난 장소의 좌표를 찾을 수 없습니다. 기본 위치(서울시)를 사용합니다.")
        lat, lon = 37.5665, 126.9780  # 서울시 좌표
        planet_positions = get_planet_positions(birth_date, birth_time, lat, lon)
        st.write("태어난 때의 행성 위치 (기본 위치 기반):")
        for planet, position in planet_positions.items():
            st.write(f"{planet.capitalize()}: {position}")

        birth_fortune = determine_fortune(planet_positions)
        st.write("당신의 운세 (기본 위치 기반):")
        for key, message in birth_fortune.items():
            st.write(message)

        current_planet_positions = get_current_planet_positions(lat, lon)
        st.write("현재 행성 위치 (기본 위치 기반):")
        for planet, position in current_planet_positions.items():
            st.write(f"{planet.capitalize()}: {position}")

        current_fortune = determine_fortune(current_planet_positions)
        st.write("현재 운세 (기본 위치 기반):")
        for key, message in current_fortune.items():
            st.write(message)

    st.write("""
    참고: 이 앱은 오락 목적으로 점성술 정보를 제공합니다. 
    점성술은 과학적인 학문으로 간주되지 않으며 중요한 결정을 내리는 데 사용되지 않아야 합니다.
    20240703 1257
    """)
