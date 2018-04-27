#importo todas las librerías que voy a utilizar
import sys
import temperature
import threading
import time
import RPi.GPIO as GPIO
import json
from flask import Flask, render_template, request #importar todo lo refere
import http.client
import urllib.request
import urllib.parse
import datetime
import serial
global value # la nombro global para manejar datos de diferentes funciones

# Inicializo variables de los led y los buttons

PIN_REED=5
PIN_BUTTON1=13
PIN_BUTTON2=26
PIN_LED1=17
PIN_LED2=27
PIN_LED3=22

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_REED, GPIO.IN, pull_up_down=GPIO.PUD_UP)
state=GPIO.input(PIN_REED)
GPIO.setup(PIN_BUTTON1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BUTTON2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_LED1,GPIO.OUT)
GPIO.setup(PIN_LED2,GPIO.OUT)
GPIO.setup(PIN_LED3,GPIO.OUT)
GPIO.output(PIN_LED1, False)
GPIO.output(PIN_LED2, False)
GPIO.output(PIN_LED3, False)

a=0

#creo los 3 threads

class myThread (threading.Thread):
   def __init__(self, threadID, name, counter):
	   threading.Thread.__init__(self)
	   self.threadID = threadID
	   self.name = name
   def run(self):
	   print ("comenzar " + self.name)
	   monitorizar_hilo(self.name)
	   print (" Salir " + self.name)
class carriots(threading.Thread):
   def __init__(self, threadID, name):
      threading.Thread.__init__(self)
      self.threadID=threadID
      self.name=name
   def run(self):
      envio_carriots()
class ultrasonidos(threading.Thread):
   def __init__(self, threadID, name):
      threading.Thread.__init__(self)
      self.threadID=threadID
      self.name=name
   def run(self):
      distancia_ardui()

#función del threads de recoger del puerto serial la distancia tomada por el sensor de ultrasonidos

def distancia_ardui():
   while True:
      stateButton2 = GPIO.input(PIN_BUTTON2)
      # Retardo para establecer la conexión serial
      global getSerialValue
      arduinoPort = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
      time.sleep(0.5)
      getSerialValue = arduinoPort.readline()
      if stateButton2 == False:
          print ('\nValor retornado de Arduino: %s' % (getSerialValue))
   # Cerrando puerto serial
   arduinoPort.close()

# función del threads de envio a carriot si se pulsa button1
def envio_carriots():
   while True:
       stateButton1 = GPIO.input(PIN_BUTTON1)
       if stateButton1 == False:
           print('SUBIENDO A CARRIOTS...')
           api_url='http://api.carriots.com/streams'
           device='defaultDevice@Frutgan.Frutgan'
           api_key= '1c036214e9ec277d6880b11a8938360816e27ba3e6cffa1b59b9652564bc0ab5'
           content_type='application/json'
           timestamp = int(time.time())
           params={'protocol':'v2',
                   'device':device,
                   'at':timestamp,
                   'data':datos}
           binary_data=json.dumps(params).encode('ascii') # se utiliza json para el envioi a carriots
           header={'User-Agent':'raspberrycarriots','Content-Type':content_type,'carriots.apikey':api_key}
           req = urllib.request.Request(api_url,binary_data,header)
           f = urllib.request.urlopen(req)
           print(f.read().decode('utf-8'))
       time.sleep(5)
#funcion del threads para monitorizar en pantalla el string de valores recogidos de la placa
def monitorizar_hilo (threadName):
	if a:
		threadName.exit()
	while True:
			global temperatura
			global timeString
			global now
			global puerta
			global state
			global datos
			temperatura=temperature.read_temp()
			state= GPIO.input(PIN_REED)
			# La fecha/hora en formato timestamp
			timestamp = int(time.time())
			now = datetime.datetime.now()
			timeString = now.strftime("%Y-%m-%d %H:%M")
			if state == False:
				puerta=str("puerta abierta")
			else:
				puerta=str("puerta cerrada")
			datos= {"fecha": timeString,"Usuario": "Frutgan","placa": "Placa_Diego","temperatura": temperatura,"Puerta": puerta}
			print("informacion de la placa: " +str(datos))
			time.sleep(10)
        
##Ejecución de los threadas
def threads():
   threads = [] # Thread list
   threadLock = threading.Lock() # Con esto se anidan todos los hilos
   thread1 = myThread(1, "informacion actualizada", 1)
   thread1.start()
   threads.append(thread1)
   thread2= carriots(2, "enviar a carriots")
   thread2.start()
   threads.append(thread2)
   thread3=ultrasonidos(3, "distancia de ROBOTINHO2.0")
   thread3.start()
   threads.append(thread3)
threads()
#creación de la aplicacion Flask

app = Flask(__name__)

@app.route("/maqueta") #para generar la aplicacion flask con la plantilla creada para la pag principal
def hello():
   now = datetime.datetime.now()
   timeString = now.strftime("%Y-%m-%d %H:%M")
   templateData = {
	  'title' : 'Robotinho 2.0',
	  'time': timeString,
          }
   return render_template('main.html', **templateData)

@app.route("/maqueta/datosplaca", methods=['GET'])    #otro apartado de la aplicacion flask get para ver el string de datos de la placa a flask
def hello_uno():
   return "datos de la placa actualizados: " +str(datos)
@app.route("/maqueta/robot", methods=['GET'])    #otro apartado de la aplicacion flask para visualizar los datos del sensor de proximidad
def hello_tres():
   now = datetime.datetime.now()
   timeString = now.strftime("%Y-%m-%d %H:%M")
   templateData3 = {
	  'title' : 'Robotinho 2.0',
	  'time': timeString,
          'getSerialValue': getSerialValue,
          }
   return render_template('main_2.html', **templateData3)

@app.route("/maqueta/carriot", methods=['GET'])    #otro apartado de la aplicacion flask para visualizar el ultimo envio a carriots
def hello_dos():
   now = datetime.datetime.now()
   timeString = now.strftime("%Y-%m-%d %H:%M")
   api_url = "http://api.carriots.com/streams"
   #recojo de carriot el ultimo dato
   api_key = '1c036214e9ec277d6880b11a8938360816e27ba3e6cffa1b59b9652564bc0ab5'
   header = {"carriots.apikey": api_key}
   req = urllib.request.Request(api_url,None,header)
   f = urllib.request.urlopen(req)
   data=json.loads(f.read().decode('utf-8'))
   cod_id=data['result'][int(data['total_documents'])-1]['id_developer']
   print(cod_id)
   #el ultimo dato enviado a carriot se quiere visualizar en flask
   api_url = "http://api.carriots.com/streams/"+cod_id+"/"
   api_key = '1c036214e9ec277d6880b11a8938360816e27ba3e6cffa1b59b9652564bc0ab5'
   params = {"protocol": "v2"}
   binary_data = json.dumps(params).encode('ascii')
   header = {"carriots.apikey": api_key}
   req = urllib.request.Request(api_url,binary_data,header)
   req.get_method = lambda: "GET"
   f = urllib.request.urlopen(req)
   data=json.loads(f.read().decode('utf-8')) 
   almacenados=json.dumps(data,indent=4,sort_keys=True)
   templateData1 = {
       'title' : 'Robotinho 2.0',
       'time': timeString,
       'almacenados': almacenados,
       }
   return render_template('main_1.html', **templateData1)

@app.route("/maqueta/led_rojo/<int:pin>", methods=['POST']) #parte del post led rojo a traves de postman
def setPin(pin):

	value = request.form['value']
	# value puede ser 0 o 1 para establecerlo a bajo/alto
	try:
		GPIO.setup(pin, GPIO.OUT)
		if int(value) == 1:
			GPIO.output(pin, True)
			return "led_rojo encendido" 

		elif int(value) == 0:
			GPIO.output(pin, False)
			return "led_rojo apagado" 
	except:
		return "There was an error setting pin " + str(pin) + " to ." + str(value)
@app.route("/maqueta/led_verde/<int:pin>", methods=['POST']) #parte del post led verde a travéss de postman
def setPin1(pin):
	value1 = request.form['value']
	# value puede ser 0 o 1 para establecerlo a bajo/alto
	try:
		GPIO.setup(pin, GPIO.OUT)
		if int(value1) == 1:
			GPIO.output(pin, True)
		elif int(value1) == 0:
			GPIO.output(pin, False)

		return "OK"
	except:
		return "There was an error setting pin " + str(pin) + " to ." + str(value)
@app.route("/maqueta/led_amarillo/<int:pin>", methods=['POST']) #parte del post led  amarillo a través de postman
def setPin2(pin):
	value2 = request.form['value']
	# value puede ser 0 o 1 para establecerlo a bajo/alto
	try:
		GPIO.setup(pin, GPIO.OUT)
		if int(value2) == 1:
			GPIO.output(pin, True)
		elif int(value2) == 0:
			GPIO.output(pin, False)

		return "OK"
	except:
		return "There was an error setting pin " + str(pin) + " to ." + str(value)
if __name__ == "__main__":
   app.run(host='0.0.0.0', port=8080, debug=True)


