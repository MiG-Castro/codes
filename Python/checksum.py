# Formato comando I+LenP + T + P + C + F
# check sum sobre T & P
# start_scan 7E 00 20 20 7F
# STOP_SCAN 7E 00 21 21 7F
# send_cmd (inicio al cero) 7E 02 30 00 AA 9A 7F
# send_cmd (detener todos) 7E 02 30 FF FF 30 7F

# disconnect 0 -> 7E 01 22 00 22 7F

# 0x7E, 0x01, 0x22, 0x00
b = 0x00
a = [0x22, 0x00]
for k in a:
    b ^= k
print(f'{b:02X}')

a = 1
print(f'{a:02X}')

# def calculate_checksum(data: list[int] | bytes | bytearray) -> int:
#     """Calcula un checksum de 8 bits para una secuencia de bytes usando XOR."""
#     checksum = 0
#     for byte in data:
#         checksum ^= byte
#     return checksum

# # --- 1. Definir las constantes de nuestro protocolo ---
# PKT_START_BYTE = 0x7E
# PKT_END_BYTE   = 0x7F
# CMD_TYPE_SEND_CMD = 0x30

# # --- 2. Definir los datos específicos del comando ---
# peripheral_index = 0x00
# command_byte     = 0xAA

# # --- 3. Construir las partes del paquete ---
# # El PAYLOAD contiene el índice y el comando
# payload = [peripheral_index, command_byte]

# # La LONGITUD es solo la longitud del PAYLOAD
# length = len(payload)

# # Los datos sobre los que se calcula el checksum son TIPO + PAYLOAD
# data_for_checksum = [CMD_TYPE_SEND_CMD] + payload

# # --- 4. Calcular el checksum ---
# checksum = calculate_checksum(data_for_checksum)

# # --- 5. Ensamblar el paquete final ---
# # Estructura: [START] [LEN] [TIPO] [PAYLOAD] [CHECKSUM] [END]
# packet_list = [PKT_START_BYTE]
# packet_list.append(length)
# packet_list.extend(data_for_checksum) # .extend() añade todos los elementos de una lista
# packet_list.append(checksum)
# packet_list.append(PKT_END_BYTE)

# # --- 6. Verificar y Enviar ---

# # Imprimir los resultados para verificar
# print(f"Datos para checksum: {[hex(b) for b in data_for_checksum]}") # -> ['0x30', '0x0', '0xaa']
# print(f"Checksum calculado: {hex(checksum)}") # -> 0x9a

# print("\n--- Paquete Final ---")
# print(f"Como lista de enteros: {packet_list}")
# # Convertir a formato hexadecimal para fácil lectura
# print(f"Como lista hexadecimal: {[hex(b) for b in packet_list]}")

# # Esta es la secuencia que enviarías con VSC Serial Monitor
# # 7E 02 30 00 AA 9A 7F
# print(f"String hexadecimal: {' '.join(f'{b:02X}' for b in packet_list)}")

# # Finalmente, para enviarlo con la librería pyserial, lo convertirías a un objeto 'bytes'
# bytes_to_send = bytes(packet_list)
# print(f"Objeto bytes para enviar: {bytes_to_send}")

# Ejemplo de cómo se enviaría con pyserial (no ejecutar sin la librería)
# import serial
# ser = serial.Serial('COMx', 115200)
# ser.write(bytes_to_send)
# ser.close()