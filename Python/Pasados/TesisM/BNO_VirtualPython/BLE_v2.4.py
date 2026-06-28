"""
Autor: Miguel Castro - 2024
CICESE - Laboratorio ARTS
Pruebas con Sensor -> Bluetooth -> Representacion3D

###################################################################
# RECEPCION DE DATOS DE NODO BLUETOOTH Y REPRESENTACION 3D
###################################################################

Uso de Virtual Python
Usar el mouse (click derecho) para ajustar la perspectiva
Formato esperado de paquete: NoPkt, Q0(W,X,Y,Z), Q1(W,X,Y,Z)
###################################################################
"""

import asyncio
from bleak import BleakClient, BleakScanner, BleakError
from vpython import *
import numpy as np
import math
import threading

# Escena Vpython #######################################################################################################
scene.range = 5
scene.background = color.white
scene.forward = vector(0, -1, 1)
scene.width = 1500
scene.height = 900

# Texto
titulo = text(text="CICESE - Laboratorio ARTS\nPrueba de rotación", align='center', height=0.5, depth=0.01,
              color=color.black, pos=vector(0, 3.5, 0), billboard=True, emissive=True)

# Flechas
# xarrow = arrow(lenght=8, shaftwidth=0.1, color=color.blue, axis=vector(-1, 0, 0))
yarrow = arrow(lenght=8, shaftwidth=0.1, color=color.green, axis=vector(0, 1, 0))
# zarrow = arrow(lenght=8, shaftwidth=0.1, color=color.red, axis=vector(0, 0, 1))

# Objeto 3D
placa = box(length=3, width=2, height=.2, opacity=1, pos=vector(0, 0, 0, ), color=color.cyan)
bno05 = box(length=0.9, width=.75, height=.1, pos=vector(1, .15, 0), color=color.black)
xiao_ = box(length=0.9, width=.6, height=.3, pos=vector(-1, .15, 0), color=color.white)

myObj = compound([placa, bno05, xiao_])

# Calculos/banderas ####################################################################################################
first_reading = True
activar3D = True
calib = 0

toRad = 2 * np.pi / 360
toDeg = 1 / toRad

# BLUETOOTH ############################################################################################################
# Dirección del dispositivo Arduino BLE (debes reemplazar con la dirección correcta)
xiao = ["DD:29:0E:DD:B7:54",  # [0] mini-proto
        "95:4E:22:8F:E1:93",  # [1] Falso contacto
        "3A:53:60:43:10:2F",  # [2] XIAO (soldado a BNO - 00)
        "3A:28:99:3C:D4:86"   # [3] XIAO (soldado a BNO - 01)
        ]
address = xiao[1]
# UUID de la característica que vamos a suscribir para recibir notificaciones
characteristic_uuid = "00002A56-0000-1000-8000-00805f9b34fb"


async def notification_handler(sender, data):
    global first_reading, activar3D, calib

    if activar3D:
        # Desglose de paquete
        No = int.from_bytes(data[0:4], byteorder='little', signed=False)
        q00 = int.from_bytes(data[4:6], byteorder='little', signed=True) / 10000.0
        q01 = int.from_bytes(data[6:8], byteorder='little', signed=True) / 10000.0
        q02 = int.from_bytes(data[8:10], byteorder='little', signed=True) / 10000.0
        q03 = int.from_bytes(data[10:12], byteorder='little', signed=True) / 10000.0

        print(f'Pkt: {No}, '
              f'Q0: {q00:.5f}, {q01:.5f}, {q02:.5f}, {q03:.5f}.')
        """
        q10 = int.from_bytes(data[12:14], byteorder='little', signed=True) / 10000.0
        q11 = int.from_bytes(data[14:16], byteorder='little', signed=True) / 10000.0
        q12 = int.from_bytes(data[16:18], byteorder='little', signed=True) / 10000.0
        q13 = int.from_bytes(data[18:20], byteorder='little', signed=True) / 10000.0
        
        print(f'Pkt: {No}, '
              f'Q0: {q00:.5f}, {q01:.5f}, {q02:.5f}, {q03:.5f}.'
              f'Q1: {q10:.5f}, {q11:.5f}, {q12:.5f}, {q13:.5f}.')
        """

        roll = -math.atan2(2 * (q00 * q01 + q02 * q03), 1 - 2 * (q01 * q01 + q02 * q02))
        pitch = math.asin(2 * (q00 * q02 - q03 * q01))
        yaw = -math.atan2(2 * (q00 * q03 + q01 * q02), 1 - 2 * (q02 * q02 + q03 * q03)) - np.pi / 2

        # rate(20)
        k = vector(cos(yaw) * cos(pitch), sin(pitch), sin(yaw) * cos(pitch))
        y = vector(0, 1, 0)
        s = cross(k, y)
        v = cross(s, k)
        vrot = v * cos(roll) + cross(k, v) * sin(roll)

        myObj.axis = k
        myObj.up = vrot


async def ble_main():
    global activar3D, calib
    try:
        print("Escaneando dispositivos Bluetooth...\n")
        devices = await BleakScanner.discover()

        if not devices:
            print("No se encontraron dispositivos.")
            return

        for device in devices:
            print(f"Dispositivo encontrado: {device.name} ({device.address})")

            if device.address == address:
                print(f"\nDispositivo Arduino encontrado: {device.name} ({device.address})")
                try:
                    # Intentamos conectarnos al dispositivo Arduino
                    async with BleakClient(device, timeout=20.0) as client:  # Ajusta el timeout según sea necesario
                        print("Conectado al dispositivo Arduino")
                        try:
                            # Suscribirse a las notificaciones de la característica deseada
                            await client.start_notify(characteristic_uuid, notification_handler)
                            print("Suscrito a las notificaciones")
                            activar3D = True
                            print("3D ON!!!")

                            # Mantener la conexión activa
                            while True:
                                await asyncio.sleep(1)

                        except BleakError as e:
                            print(f"Error de Bleak: {e}")
                        except Exception as e:
                            print(f"Error al suscribirse a las notificaciones: {e}")

                except BleakError as e:
                    print(f"Error de Bleak: {e}")
                except Exception as e:
                    print(f"Error al conectarse al dispositivo: {e}")

    except BleakError as e:
        print(f"Error de Bleak: {e}")
    except Exception as e:
        print(f"Otro error: {e}")


def run_ble_loop():
    asyncio.run(ble_main())


# Ejecutar la función BLE en un hilo separado
ble_thread = threading.Thread(target=run_ble_loop)
ble_thread.start()
