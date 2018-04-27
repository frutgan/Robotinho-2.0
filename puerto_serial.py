#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
import time
import serial
import RPi.GPIO as GPIO

# Iniciando conexión serial
arduinoPort = serial.Serial('/dev/ttyACM1', 9600, timeout=1)
flagCharacter = 'k'
PIN_BUTTON2=26
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_BUTTON2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
while True:
    # Retardo para establecer la conexión serial
    time.sleep(0.5)
    #arduinoPort.write(flagCharacter)
    getSerialValue = arduinoPort.readline()
    #getSerialValue = arduinoPort.read()
    #getSerialValue = arduinoPort.read(50)
    print ('\nValor retornado de Arduino: %s' % (getSerialValue))

# Cerrando puerto serial
arduinoPort.close()
