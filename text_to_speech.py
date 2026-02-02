import pyttsx3

def text_to_speech(text):
    try:
        engine = pyttsx3.init()

        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id)  # 0 for male, 1 for female (depends on system)
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)

        engine.say(text)
        engine.runAndWait()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    user_text = "hello".strip()
    if user_text:
        text_to_speech(user_text)
    else:
        print("No text entered.")
