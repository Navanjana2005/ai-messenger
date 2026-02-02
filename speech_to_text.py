import speech_recognition as sr

r = sr.Recognizer()

def speech_recognition():
    with sr.Microphone() as mic_source:
        print("Tell youe message")
        audio_text = r.listen(mic_source)

        try:
            message = r.recognize_google(audio_text)
            print("Message = " + message)
        except:
            print("Sorry, I did not get that")
    return message

# if __name__ == "__main__":
#     speech_to_text()