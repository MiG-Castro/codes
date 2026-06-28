import asyncio
import bleak
import struct
import socket
from datetime import datetime
import time

# Caracterstica usada en codigo de Arduino
# characteristic_uuid = '00002A56-0000-1000-8000-00805F9B34FB'

# UUID Caracteristicas Perfil BLE IMU - Zephyr
c_uuid = ['5CF33501-538C-4DC9-B54B-0B102623558D',   # UUID Caracteristica Sensor Data
          '5CF33502-538C-4DC9-B54B-0B102623558D'    # UUID Caracteristica Exercice Detection
]

# REGISTRO DE DIRECCIONES DE DISPOSITIVOS BLUETOOTH
"""
# Addrs obtenidas al programar con arduino
xiao_0 = '3A:53:60:43:10:2F'   # XIAO BLE - case 00
xiao_1 = '3A:28:99:3C:D4:86'   # XIAO BLE - case 01
xiao_f = '95:4E:22:8F:E1:93'   # XIAO BLE - Falso contacto
xiao_m = 'DD:29:0E:DD:B7:54'   # XIAO BLE - mini-proto
"""
# Addrs "random-static" Zephyr
xiao_m = "E9:B6:1E:C5:C0:74"    # XIAO MORADO (Sin BNO)
xiao_0 = "FA:53:60:43:10:2F"    # XIAO - Case 00
xiao_1 = "FA:28:99:3C:D4:86"    # XIAO - Case 01

# Nombres BLE
nodo_0 = "MY_LBS2"

# VARIABLES DE CONFIGURACION
conectar = [xiao_0, xiao_1]         # Lista de dispositivos a conectar
ble_addresses = True        # True = Direcciones, False = Nombres
capturar = False            # Activar la captura de datos
UDP = True                 # Activar la transmision de datos por UDP
imprimir_pkt = True         # Activar la impresion de paquetes 

# NOTA: POR ALGUNA RAZON AHORA SOLO FUNCIONA USANDO ADDR'S Y NO CON NOMBRES!!!!

class BLEDataCollector:
    def __init__(self, characteristic_uuid, device_addresses, addresses=True, save_bin=False, capture_path=None, tx_udp=False,
                 udp_ip='127.0.0.1', udp_port=4000, timer_s=0.016, imprimir=False):
        
        self.addresses = addresses                                          # if True, use addresses, if False, use names
        self.device_addresses = device_addresses                            # lista dispositivos a conectar (addresses or ble name)
        self.characteristic_uuid = characteristic_uuid                      # Caracteristicas

        self.last_pkt = [-1] * len(device_addresses)                        # Numero del ultimo pkt recibido
        self.pkt_loss = [0] * len(device_addresses)                         # Numero de pkts perdidos
        self.last_data = [None] * len(device_addresses)                     # ultimo pkt recibido
        self.subscribed = [False] * len(device_addresses)                   # Bandera dispositivos suscritos

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Creacion de UDP Socket
        self.tx_udp = tx_udp                                                # Activar la transmision de datos por UDP
        self.udp_ip = udp_ip                                                # IP destino
        self.udp_port = udp_port                                            # Puerto destino
        self.timer_s = timer_s                                              # Periodo trasmision UDP

        self.save_bin = save_bin                                            # Activar la captura de datos
        self.capture_files = [None] * len(device_addresses)                 # Archivo por cada dispositivo
        self.is_capturing = [False] * len(device_addresses)                 # Bandera de archivos-dispositivos

        self.imprimir = imprimir                                            # Activar la impresion de paquetes

    async def start_data_capture(self, device_index, name):
        """Inicia la captura de datos para un dispositivo específico"""
        # Nombre de archivo con indice y nombre del dispositivo + timestamp
        filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{name}-{device_index}.bin"
        # Abre archivo en modo binario de escritura en la ubicación actual
        self.capture_files[device_index] = open(filename, 'wb')
        self.is_capturing[device_index] = True
        print(f"Archivo {filename} creado")

    async def stop_data_capture(self, device_index):
        """Detiene la captura de datos para un dispositivo específico"""
        self.subscribed[device_index] = False
        if self.capture_files[device_index]:
            self.capture_files[device_index].close()
            self.is_capturing[device_index] = False
            print(f"Deteniendo captura para {device_index}")

    async def notification_handler(self, sender, data, device_index):
        """Recepcion y manejo de datos"""
        # if self.imprimir: print(f"[{datetime.now().strftime('%H-%M-%S')}] N[{device_index}]-{len(data)}B")

        # REVISION DE PERDIDA DE PAQUETES ####################################################################
        # no_pkt_rx = struct.unpack('<I', data[0:4])[0]                   # Extraemos el numero de paquete recibido

        # pkt_loss = 0                                                    # Inicializamos el contador de paquetes perdidos
        # if self.last_pkt[device_index] == -1:                           # Si es el primer paquete recibido
        #     if no_pkt_rx > 0:                                           # Y no es el pkt 0
        #       pkt_loss = no_pkt_rx + 1                                  # paquetes perdidos = recibidos + 1
        # else:                                                           # De lo contrario
        #     pkt_loss = no_pkt_rx - self.last_pkt[device_index] - 1      # Perdida de paquetes respecto al ultimo recibido

        # if pkt_loss > 0:                                                # Imprimimos perdidas en caso de que haya
        #     self.pkt_loss[device_index] += pkt_loss
        #     #print(f'Nodo[{device_index}] Pkt perdidos: {pkt_loss} ({self.last_pkt[device_index]}->{no_pkt_rx}),' 
        #     #      f'Total: {self.pkt_loss[device_index]}, Tasa de perdida = {((self.pkt_loss[device_index] / no_pkt_rx) * 100):.2f}%')
        # self.last_pkt[device_index] = no_pkt_rx                         # ACTUALIZAMOS -> Paquete recibido = Ultimo paquete

        # IMPRESION DE DATOS ##################################################################################
        # if self.imprimir:                                               # En caso de activar la impresion de paquetes
        #     data_txt = str(no_pkt_rx)
        #     for k in range(4, len(data), 2):
        #         data_txt = data_txt + "," + str(struct.unpack('<h', data[k:k + 2])[0])
        #     print(data_txt)

        # CAPTURA DE DATOS ####################################################################################
        if self.save_bin and self.is_capturing[device_index]:           # En caso de activar la captura de paquetes
            try:
                self.capture_files[device_index].write(data)            # Guardamos el paquete en .bin
                self.capture_files[device_index].flush()                # Forzamos el guardado inmediato
            except Exception as e:
                print(f"Error capturando datos del dispositivo {device_index}: {e}")

        # ENVIO DE DATOS POR UDP ################################################################################
        if self.tx_udp:                                                 # En caso de activar la Tx por UDP
            # pkt = struct.pack('B', device_index) + data[0:12]          # pkt = id + no_pkt[4B] + Qwxyz[8B]
            pkt = struct.pack('B', device_index) + data                 # pkt = id + Qwxyz[8B]
            if sum(self.subscribed) > 1:                                # Si hay mas de uno suscrito
                self.last_data[device_index] = pkt                      # Actualizamos ultimo paquete recibido
            else:                                                       # De lo contrario → envio directo por UDP
                try:
                    self.udp_socket.sendto(pkt, (self.udp_ip, self.udp_port))
                except Exception as e:
                    print(f"Error al enviar los datos de {device_index}, por UDP: {e}")
    
    # Recepcion de datos por Indication
    async def indication_handler(self, sender, data, device_index):
        print(f"[{datetime.now().strftime('%H-%M-%S')}] INDICATE from {device_index}: {data[0]} (len={len(data)})")

    # CONEXION A DISPOSITIVOS
    async def connect_device(self, address):
        connection_attempts = 0
        while True:
            try:
                
                if self.addresses:  # Si se usa direcciones
                    device = await bleak.BleakScanner.find_device_by_address(address, timeout=10.0)
                else:  # Si se usa nombres
                    device = await bleak.BleakScanner.find_device_by_name(address, timeout=10.0)
                
                if device:
                    async with bleak.BleakClient(device, timeout=20.0) as client:
                        # Índice del dispositivo
                        device_index = self.device_addresses.index(address)

                        # ----> DEFINICIÓN DE LOS HANDLERS DENTRO <-----
                        async def on_notification_internal(sender, data):
                            await self.notification_handler(sender, data, device_index)

                        # async def on_indication_internal(sender, data):
                        #     await self.indication_handler(sender, data, device_index)

                        # Inicializacion Captura de datos
                        if self.save_bin:
                            await self.start_data_capture(device_index, device.name)

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
                        
                        # indicate_success = False
                        # subscription_attempts = 0
                        # while not indicate_success and subscription_attempts < 5: # Reintentar hasta 5 veces
                        #     try:
                        #         await client.start_notify(self.characteristic_uuid[1], on_indication_internal)
                        #         indicate_success = True
                        #     except Exception as e:
                        #         subscription_attempts += 1
                        #         print(f"Fallo al suscribir a INDICATE en {address} (intento {subscription_attempts}): {e}")
                        #         await asyncio.sleep(1) # Esperar 1 segundo antes de reintentar
                        
                        # Prueba para verificar las indicaciones
                        # if indicate_success:
                        #     # Envio de un comando de prueba
                        #     command_to_send = bytearray([0xAA])
                        #     await client.write_gatt_char(self.characteristic_uuid[1], command_to_send, response=True)
                        
                        # if notify_success and indicate_success:
                        #     print(f"{datetime.now().strftime('%H-%M-%S')} suscripción Notify&Indicate de: {address}")
                        # elif notify_success: print(f"{datetime.now().strftime('%H-%M-%S')} suscripción a Notify de: {address}")
                        
                        # La caracteristica de mayor importancia es la de recepcion de datos ...
                        if notify_success:
                            self.subscribed[device_index] = True
                            # print(f"{datetime.now().strftime('%H-%M-%S')} suscripción a Notify de: {address}")

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
                if self.last_pkt[device_index] != -1 and self.subscribed[device_index]:
                    print(f"{datetime.now().strftime('%H-%M-%S')} - Desconectado de: {address}-{device_index},"
                        f" pkt loss = {self.pkt_loss[device_index]}")
                
                # Detener la captura de datos si está activa
                if self.is_capturing[device_index]:
                    await self.stop_data_capture(device_index)
                    self.last_pkt[device_index] = -1
                    self.pkt_loss[device_index] = 0
                
                # RESET DE VARIABLES
                self.subscribed[device_index] = False
                
    async def timer_send_to_udp(self):
        """Tarea de agregación y envío de datos"""
        while self.tx_udp:
            if sum(self.subscribed) <= 1:                   # Si no hay dispositivos suscritos -> dormir
                await asyncio.sleep(1)
                continue

            start_time = time.perf_counter()                # Iniciamos el conteo de tiempo
            await asyncio.sleep(self.timer_s)               # Dormimos el periodo asignado
            elapsed = time.perf_counter() - start_time      # Verificamos el tiempo

            if elapsed < 0.01:                              # Si el tiempo fue mucho menor -> volver a dormir
                await asyncio.sleep(self.timer_s)

            data_block = b''
            for packet in self.last_data:                   # Formamos el bloque de paquetes
                if packet is not None:
                    data_block += packet

            if data_block:                                  # Si hay datos -> Envio por UDP
                self.udp_socket.sendto(data_block, (self.udp_ip, self.udp_port))

    async def main(self):
        # Crear tareas de conexión para todos los dispositivos al mismo tiempo
        connection_tasks = [self.connect_device(address) for address in self.device_addresses]
        await asyncio.gather(*connection_tasks, self.timer_send_to_udp())


collector = BLEDataCollector(c_uuid, conectar, save_bin=capturar, tx_udp=UDP, imprimir=imprimir_pkt)
asyncio.run(collector.main())