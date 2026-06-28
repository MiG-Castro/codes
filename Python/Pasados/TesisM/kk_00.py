import struct
original_data = b'\x00' * 69  # Datos originales de 69 bytes
print(len(original_data))  # Esto imprimirá 13

device_index = 5  # Por ejemplo
original_data = struct.pack('B', device_index) + original_data[0:12]
print(len(original_data))  # Esto imprimirá 13