from flask import Flask, render_template, request, jsonify
import pyttsx3
import datetime as dt
import pywhatkit as pk
import wikipedia as wiki
import threading
import queue
import os
import requests
import json
import random
import schedule
import time

app = Flask(__name__)

# Thread-safe speech queue
speech_queue = queue.Queue()
va_name = 'KIWI'

# Configuration (Add your API keys here)
WEATHER_API_KEY = 'bd5e378503939ddaee76f12ad7a97608'
NEWS_API_KEY = 'your_newsapi_key'

# Jokes database
JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "What do you call fake spaghetti? An impasta!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "How do you organize a space party? You planet!"
]


# Speech worker thread
def speech_worker():
    while True:
        text = speech_queue.get()
        if text is None:
            break
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('voice', engine.getProperty('voices')[0].id)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"Speech error: {e}")
        finally:
            speech_queue.task_done()


# Start speech thread
speech_thread = threading.Thread(target=speech_worker)
speech_thread.start()


# Additional Command Handlers
def get_weather(city):
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(complete_url)
    data = response.json()
    if data["cod"] != "404":
        main = data["main"]
        weather = data["weather"][0]
        return f"Current temperature in {city} is {main['temp']}°C with {weather['description']}"
    return "City not found"


def get_news():
    news_url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
    response = requests.get(news_url)
    news_data = response.json()
    articles = news_data["articles"][:3]  # Get top 3 news
    news = []
    for article in articles:
        news.append(f"{article['title']}. Published by {article['source']['name']}")
    return "Here are the top news headlines: " + ". ".join(news)


def set_reminder(reminder_text, minutes):
    def reminder():
        speech_queue.put(f"Reminder: {reminder_text}")

    schedule.every(minutes).minutes.do(reminder)
    return f"Reminder set for {minutes} minutes from now"


def tell_joke():
    return random.choice(JOKES)


def system_command(command):
    if 'SHUTDOWN' in command:
        os.system("shutdown /s /t 1")
        return "Shutting down system"
    elif 'RESTART' in command:
        os.system("shutdown /r /t 1")
        return "Restarting system"
    return "System command not recognized"


def send_email(receiver, subject, body):
    # You'll need to configure your email settings
    # This is a placeholder function
    return f"Email to {receiver} with subject {subject} sent successfully"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/command', methods=['POST'])
def handle_command():
    user_command = request.form['command'].upper()
    response = ""

    try:
        if 'STOP' in user_command:
            response = 'Goodbye! Have a great day!'

        elif 'TIME' in user_command:
            response = dt.datetime.now().strftime('Current time is %I:%M %p')

        elif 'PLAY' in user_command:
            song = user_command.replace('PLAY ', '')
            pk.playonyt(song)
            response = f'Playing {song} on YouTube'

        elif 'SEARCH' in user_command or 'FIND' in user_command:
            query = user_command.replace('SEARCH ', '').replace('FIND ', '')
            pk.search(query)
            response = f'Searching web for {query}'

        elif 'WHO IS' in user_command:
            person = user_command.replace('WHO IS ', '')
            info = wiki.summary(person, sentences=2)
            response = info

        elif 'WEATHER' in user_command:
            city = user_command.replace('WEATHER ', '').replace(' IN ', '')
            response = get_weather(city)

        elif 'NEWS' in user_command:
            response = get_news()

        elif 'REMIND' in user_command:
            parts = user_command.split(' IN ')
            reminder_text = parts[0].replace('REMIND ME TO ', '')
            minutes = int(parts[1].replace(' MINUTES', ''))
            response = set_reminder(reminder_text, minutes)

        elif 'JOKE' in user_command:
            response = tell_joke()

        elif 'SHUTDOWN' in user_command or 'RESTART' in user_command:
            response = system_command(user_command)

        elif 'E-MAIL' in user_command:
            # Example command: "EMAIL TO JOHN SUBJECT MEETING BODY LET'S MEET TOMORROW"
            parts = user_command.split(' SUBJECT ')
            receiver = parts[0].replace('EMAIL TO ', '')
            subject_body = parts[1].split(' BODY ')
            subject = subject_body[0]
            body = subject_body[1]
            response = send_email(receiver, subject, body)

        elif 'CALCULATE' in user_command:
            # Example: "CALCULATE 125 PLUS 369" or "CALCULATE 45 TIMES 12"
            expression = user_command.replace('CALCULATE ', '')
            response = calculate_expression(expression)

        elif 'WHO ARE YOU' in user_command:
            response = f'I am {va_name}, your personal voice assistant'

        else:
            response = 'Sorry, I didn\'t understand that. Please try again.'

    except Exception as e:
        print(f"Command error: {e}")
        response = 'Oops! Something went wrong. Please try again.'

    speech_queue.put(response)
    return jsonify({'response': response})


def calculate_expression(expression):
    expression = expression.lower() \
        .replace('plus', '+') \
        .replace('minus', '-') \
        .replace('times', '*') \
        .replace('divided by', '/')
    try:
        result = eval(expression)
        return f"The result is {result}"
    except:
        return "Could not calculate that expression"


# Scheduler thread for reminders
def reminder_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


reminder_thread = threading.Thread(target=reminder_scheduler)
reminder_thread.daemon = True
reminder_thread.start()

if __name__ == '__main__':
    app.run(debug=True)
    speech_queue.put(None)  # Cleanup
    speech_thread.join()