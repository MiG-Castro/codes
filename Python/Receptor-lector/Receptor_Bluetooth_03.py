import asyncio
import bleak
import struct
import socket
from datetime import datetime
import time

# UUID Caracteristicas Perfil BLE IMU - Zephyr
c_uuid = ['5CF33501-538C-4DC9-B54B-0B102623558D',    # UUID Caracteristica Sensor Data
          '5CF33502-538C-4DC9-B54B-0B102623558D']    # UUID Caracteristica Exercice Detection

# VARIABLES DE CONFIGURACION
conectar = ["C6:9B:47:DE:A4:AF"]    # Lista de dispositivos a conectar addrs
imprimir_pkt = True                 # Activar la impresion de paquetes 

class BLEDataCollector:
    def __init__(self, characteristic_uuid, device_addresses, imprimir=False):
        self.device_addresses = device_addresses                            # lista dispositivos a conectar (addresses or ble name)
        self.characteristic_uuid = characteristic_uuid                      # Caracteristicas
        self.subscribed = [False] * len(device_addresses)                   # Bandera dispositivos suscritos
        self.imprimir = imprimir                                            # Activar la impresion de paquetes

    async def notification_handler(self, sender, data, device_index):
        """Recepcion y manejo de datos"""
        if self.imprimir: print(f"[{datetime.now().strftime('%H-%M-%S')}] N[{device_index}]-{len(data)}B. Rx ", end="")

        # REVISION DE PERDIDA DE PAQUETES ####################################################################
        no_pkt = struct.unpack('<I', data[0:4])[0]
        gyr_raw = struct.unpack('<3h', data[4:10])
        acc_raw = struct.unpack('<3h', data[10:16])
        
        # Conversion a unidades
        g = [v * 0.00875 for v in gyr_raw] 
        a = [v * 0.000061 for v in acc_raw]

        # IMPRESION DE DATOS ##################################################################################
        if self.imprimir:
            print(f"{no_pkt} Gyr x:{g[0]:.3f} y:{g[1]:.3f} z:{g[2]:.3f} dps. Acc x:{a[0]:.3f} y:{a[1]:.3f} z:{a[2]:.3f} g")

    # CONEXION A DISPOSITIVOS
    async def connect_device(self, address):
        connection_attempts = 0
        while True:
            try:
                device = await bleak.BleakScanner.find_device_by_address(address, timeout=10.0)
                if device:
                    async with bleak.BleakClient(device, timeout=20.0) as client:
                        # Índice del dispositivo
                        device_index = self.device_addresses.index(address)

                        # ----> DEFINICIÓN DE LOS HANDLERS DENTRO <-----
                        async def on_notification_internal(sender, data):
                            await self.notification_handler(sender, data, device_index)

                        connection_attempts = 0
                        notify_success = False
                        subscription_attempts = 0
                        while not notify_success and subscription_attempts < 5: # Reintentar hasta 5 veces
                            try:
                                await client.start_notify(self.characteristic_uuid[0], on_notification_internal)
                                notify_success = True
                            except Exception as e:
                                subscription_attempts += 1
                                print(f"Fallo al suscribir a NOTIFY en {address} (intento {subscription_attempts}): {e}")
                                await asyncio.sleep(1) # Esperar 1 segundo antes de reintentar
                        
                        # La caracteristica de mayor importancia es la de recepcion de datos ...
                        if notify_success:
                            self.subscribed[device_index] = True

                            # Marcar dispositivo como suscrito
                            self.subscribed[device_index] = True
                            print(f"{datetime.now().strftime('%H-%M-%S')} conectado y suscrito a: {device.name}->{device.address}-{device_index}")

                            # Mantiene la conexión activa
                            while client.is_connected:
                                await asyncio.sleep(1)
                            print(f"{datetime.now().strftime('%H-%M-%S')} Desconexion inesperada de: {device.name}->{device.address}-{device_index}")
                        else: 
                            print(f"No se pudo suscribir a la caracteristica Notify de {address}. Desconectando.")
                            break
                else: 
                    print(f"Dispositivo {address} no encontrado. Reintentando...")
                    await asyncio.sleep(min(10, 2 ** connection_attempts))
                    connection_attempts += 1
                    continue 

            except Exception as e:
                print(f"Error de conexión con {address}: {e}")
                # Backoff exponencial
                await asyncio.sleep(min(10, 2 ** connection_attempts))
                connection_attempts += 1
            finally:
                device_index = self.device_addresses.index(address)

                # INFORME DE DESCONEXION
                if self.subscribed[device_index]:
                    print(f"{datetime.now().strftime('%H-%M-%S')} - Desconectado de: {address}-{device_index},")
                
                # RESET DE VARIABLES
                self.subscribed[device_index] = False

    async def main(self):
        # Crear tareas de conexión para todos los dispositivos al mismo tiempo
        connection_tasks = [self.connect_device(address) for address in self.device_addresses]
        await asyncio.gather(*connection_tasks)


collector = BLEDataCollector(c_uuid, conectar, imprimir=imprimir_pkt)
asyncio.run(collector.main())