import speech_recognition as sr
import time
from openai import OpenAI
import os 
from gtts import gTTS # Online Text-to-Speech library
import tempfile # Temporary file handle karne ke liye

# --- API CONFIGURATION ---
# WARNING: Please keep your API key secret and do not share it publicly.
OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY_HERE"

# OpenRouter client initialization
llm_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

LLM_MODEL = "mistralai/mistral-7b-instruct-v0.2"

# --- TTS INITIALIZATION (gTTS is used here, no need for engine init) ---
print("TTS Engine: gTTS (Online) is active.")

# 1. JARVIS ka Bolne ka Function (Updated for gTTS)
def speak(text):
    """JARVIS jo bhi text diya jayega use bol kar sunayega (Online TTS)."""
    # Yeh line terminal me text dikhati hai
    print(f"JARVIS: {text}") 
    
    # gTTS ka use karke Text-to-Speech karein
    try:
        # LLM reply multilingual hota hai, 'en' lang code set karne par bhi 
        # gTTS Indian languages (Hindi, etc.) ko theek se process kar leta hai.
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Temporary file path create karna (output.mp3 har baar overwrite hoga)
        filename = "output.mp3"
        
        # Audio file save karna
        tts.save(filename)
        
        # Audio file play karna (Windows ke liye 'start' command)
        os.system(f"start {filename}")
        
        # Zaroori: Audio ko poora play hone ka waqt dena. Ye 'runAndWait' ki jagah kaam karta hai.
        # Ye delay LLM replies ke liye bahut zaruri hai.
        time.sleep(1 + len(text) * 0.015) 
        
        # File delete karna taaki directory saaf rahe
        if os.path.exists(filename):
            os.remove(filename)
            
    except Exception as e:
        print(f"TTS Playback Error (gTTS): {e}")


# 2. LLM Processing Function (No change needed here)
def process_with_llm(user_prompt):
    """OpenRouter API ka use karke user prompt ko process karta hai aur multilingual reply deta hai."""
    try:
        system_message = (
            "You are JARVIS, a helpful, advanced AI assistant. "
            "You must automatically detect the user's language (Hindi, English, Punjabi, etc.) "
            "and respond politely, professionally, and fluently in the SAME language. "
            "Keep answers concise. If the user asks you to say goodbye, respond appropriately without mentioning sleep mode."
        )
        
        response = llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7, 
            max_tokens=200
        )

        llm_response = response.choices[0].message.content
        return llm_response

    except Exception as e:
        print(f"LLM API Error: {e}")
        return "Sorry Sir, I ran into a technical error while processing your request through the AI model."


# 3. JARVIS ka Wake Word Sunne ka Function (No change needed here)
def listen_wake_word():
    """Microphone se input leta hai aur check karta hai ki kya 'Jarvis' bola gaya hai."""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        
        recognizer.adjust_for_ambient_noise(source, duration=1.5) 
        print("Listening for 'Jarvis'...")
        
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            word = recognizer.recognize_google(audio, language='en-in') 
            
            if "jarvis" in word.lower():
                return True
            else:
                print(f"Heard (but ignoring): {word}")
                return False
                
        except sr.WaitTimeoutError:
            return False
        
        except sr.UnknownValueError:
            return False
            
        except Exception as e:
            return False

# 4. JARVIS ka Command Sunne ka Function (No change needed here)
def take_command():
    """Wake word sunne ke baad user ka command sunne ke liye function."""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.5)
        print("\nListening for command...")
        
        try:
            audio_command = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio_command, language='en-in')
            print(f"User Command: {command}")
            return command
            
        except sr.WaitTimeoutError:
            print("No speech detected during command phase.")
            return "timeout"
            
        except sr.UnknownValueError:
            print("Could not understand command.")
            return "unrecognized"
            
        except Exception as e:
            print(f"An error occurred during command listening: {e}")
            return "error"


# --- MAIN PROGRAM LOOP ---

if __name__ == "__main__":
    speak("System starting. Waiting for your command.")
    
    while True:
        try:
            is_awake = listen_wake_word()
            
            if is_awake:
                print("\n*** WAKE WORD DETECTED ***")
                speak("Yes Sir, I am here. How may I help you?")
                
                while True:
                    user_command = take_command()
                    
                    # 1. Sleep/Exit Command
                    if "goodbye" in user_command.lower() or "bye" in user_command.lower() or "sleep" in user_command.lower():
                        speak("Goodbye Sir. Have a nice day. I am going into sleep mode.")
                        break 
                    
                    # 2. Silent Listening (Timeout or Unrecognized) - JARVIS chuppi sadhega
                    elif user_command in ["timeout", "unrecognized"]:
                        if user_command == "timeout":
                            print("System Log: No command detected. Listening again...")
                        elif user_command == "unrecognized":
                            print("System Log: Command unrecognizable. Listening again...")
                        
                        continue # Turant wapas listening par
                        
                    # 3. Critical Error
                    elif user_command == "error":
                        speak("A critical processing error occurred. Please repeat your command.")
                        
                    # 4. Actual Command Processing using LLM 
                    else:
                        # Acknowledgement bolna zaroori hai
                        speak("Processing your request.") 
                        
                        # LLM se reply generate karna
                        llm_reply = process_with_llm(user_command)
                        
                        # ZAROORI FIX: LLM se aaye hue reply ko speak() function mein bhejna
                        if llm_reply:
                            speak(llm_reply)
                            # time.sleep(0.5) ki zaroorat nahi hai kyunki speak function mein hi delay hai.
                        else:
                            speak("I received an empty response from the AI model.")
                        
        except KeyboardInterrupt:
            print("\nProgram stopped by user.")
            break