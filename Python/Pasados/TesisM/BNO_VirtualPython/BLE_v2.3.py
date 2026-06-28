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
xiao = ["DD:29:0E:DD:B7:54",  # mini-proto
        "95:4E:22:8F:E1:93",  # Falso contacto
        "3A:53:60:43:10:2F"   # XIAO (soldado a BNO)
        ]
address = xiao[1]
# UUID de la característica que vamos a suscribir para recibir notificaciones
characteristic_uuid = "00002A56-0000-1000-8000-00805f9b34fb"


async def notification_handler(sender, data):
    global first_reading, activar3D, calib

    if activar3D:
        # Desglose de paquete
        # No = int.from_bytes(data[0:4], byteorder='little', signed=False)
        q0 = int.from_bytes(data[4:6], byteorder='little', signed=True) / 10000.0
        q1 = int.from_bytes(data[6:8], byteorder='little', signed=True) / 10000.0
        q2 = int.from_bytes(data[8:10], byteorder='little', signed=True) / 10000.0
        q3 = int.from_bytes(data[10:12], byteorder='little', signed=True) / 10000.0

        """
        cal_s = data[12]
        cal_g = data[13]
        cal_a = data[14]
        cal_m = data[15]
        """

        """
        print(f'Pkt: {No}, '
              f'Q(w,x,y,z): {q0:.5f}, {q1:.5f}, {q2:.5f}, {q3:.5f}, '
              f'C(S,G,A,M): {cal_s}, {cal_g}, {cal_a}, {cal_m}')
        """
        # print(f'{q0:.5f}, {q1:.5f}, {q2:.5f}, {q3:.5f}')

        roll = -math.atan2(2 * (q0 * q1 + q2 * q3), 1 - 2 * (q1 * q1 + q2 * q2))
        pitch = math.asin(2 * (q0 * q2 - q3 * q1))
        yaw = -math.atan2(2 * (q0 * q3 + q1 * q2), 1 - 2 * (q2 * q2 + q3 * q3)) - np.pi / 2

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
