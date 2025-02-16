from flask import Flask, render_template, request, jsonify
import pyttsx3
import datetime as dt
import pywhatkit as pk
import wikipedia as wiki
import threading
import queue
import random
import schedule
import time

from pyaudio import paFramesPerBufferUnspecified

app = Flask(__name__)

# Thread-safe speech queue
speech_queue = queue.Queue()
va_name = 'KIWI'

# Jokes database
JOKES = [
    "Why don’t skeletons fight each other? They don’t have the guts!",
    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
    "Why don’t eggs tell jokes? Because they might crack up!",
    "What do you call fake spaghetti? An impasta!",
    "I told my computer I needed a break, and now it won’t stop sending me Kit-Kats.",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "I’m reading a book about anti-gravity. It’s impossible to put down!",
    "Did you hear about the restaurant on the moon? Great food, no atmosphere!",
    "What do you get if you cross a snowman and a vampire? Frostbite!",
    "I’m on a whiskey diet. I’ve lost three days already.",
    "Why was the math book sad? It had too many problems.",
    "Why don’t oysters share their pearls? Because they’re shellfish!",
    "I used to play piano by ear, but now I use my hands.",
    "Why did the bicycle fall over? It was two-tired.",
    "I’m terrified of elevators, so I’m taking steps to avoid them.",
    "Why do cows have hooves instead of feet? Because they lactose!",
    "What did one ocean say to the other ocean? Nothing, they just waved.",
    "I once got into a fight with a broken pencil. It was pointless.",
    "Why don’t skeletons ever use cell phones? They’re always dead to the world.",
    "I couldn’t figure out how to put my seatbelt on. Then it clicked.",
    "What do you call a pile of cats? A meow-tain.",
    "Why do bananas never get lonely? Because they hang in bunches.",
    "What did one wall say to the other wall? I’ll meet you at the corner.",
    "Why are frogs so happy? Because they eat whatever bugs them!",
    "What do you call cheese that isn’t yours? Nacho cheese!",
    "Why did the tomato turn red? Because it saw the salad dressing!",
    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
    "Why did the computer go to the doctor? It had a virus!",
    "I can’t believe I got fired from the calendar factory. All I did was take a day off!",
    "What’s orange and sounds like a parrot? A carrot!",
    "Why did the chicken join a band? Because it had drumsticks!",
    "Why don’t skeletons ever tell secrets? They don’t have the guts to.",
    "What did the coffee say to the sugar? You’re sweet!",
    "Why don’t programmers like nature? It has too many bugs.",
    "I’m writing a book about reverse psychology. Don’t buy it!",
    "Why don’t you ever see elephants hiding in trees? Because they’re really good at it.",
    "What’s the best way to watch a fly fishing tournament? Live stream.",
    "Why did the golfer bring two pairs of pants? In case he got a hole in one!",
    "How do cows stay up to date with current events? They read the moos-paper!",
    "I used to play piano by ear, but now I use my hands.",
    "What did one plate say to the other plate? Lunch is on me!",
    "Why don’t you ever see hippos hiding in trees? Because they’re really good at it!",
    "What do you call an alligator in a vest? An investigator!",
    "I couldn’t figure out why I was getting strange messages on my phone, but then it dawned on me.",
    "What’s a skeleton’s least favorite room? The living room.",
    "I used to be addicted to soap, but I’m clean now.",
    "What’s brown and sticky? A stick!",
    "Why do cows wear bells? Because their horns don’t work!",
    "I told my computer I needed a break, and now it won’t stop sending me Kit-Kats.",
    "Why don’t scientists trust atoms? Because they make up everything!"
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

def set_reminder(reminder_text, minutes):
    def reminder():
        speech_queue.put(f"Reminder: {reminder_text}")

    schedule.every(minutes).minutes.do(reminder)
    return f"Reminder set for {minutes} minutes from now"


def tell_joke():
    return random.choice(JOKES)


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

        elif 'REMIND' in user_command:
            parts = user_command.split(' IN ')
            reminder_text = parts[0].replace('REMIND ME ', '')
            minutes = int(parts[1].replace(' MINUTES', ''))
            response = set_reminder(reminder_text, minutes)

        elif 'JOKE' in user_command:
            response = tell_joke()

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
    expression = expression.lower().replace('plus', '+') .replace('minus', '-') .replace('multiples of', '*') .replace('divided by', '/')
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