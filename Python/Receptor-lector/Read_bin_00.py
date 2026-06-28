"""
PROGRAMA PARA LEER DATOS CAPTURADOS EN ARCHIVO .BIN
"""
Ftx = 30                                                    # Frec de Tx de paquetes
pkt_int16 = 13                                              # Variables in16 por paquete
muestras_x_pkt = 2                                          # Muestras x paquete
tamaño_pkt_bytes = 4 + (pkt_int16 * 2 * muestras_x_pkt)     # Tamaño del paquete
unpack = True                                               # Desglosar y guardar variables
imprimir = False                                            # Imprimir datos

# Archivo a leer
file = "2-XiaoTX[0f]_2025-03-27_01-36-21.bin"                
# Conversion bytes to units
u_acc = [100, 1]                # 1 m/s2 = 100 LSB, 1 mg = 1 LSB
u_gyr = [16, 900]               # 1 dps = 16 LSB, 1 rps = 900 LSB
u_mag = 16                      # 1uT = 16 LSB
u_qua = 16384                   # 1 Quat (Unit less) = 2^14
unit = [u_acc[0], u_gyr[1], u_mag, u_qua]   # 0:m/s2, 1:rps, 2:uT, 3:Quat

"""Variables de datos del captura"""
# Numero de paquetes
sec = []    
# Datos crudos (bytes)
raw_acc = []
raw_gyr = []
raw_mag = []
raw_qua = []
# Datos convertidos a sus unidades
acc = []
gyr = []
mag = []
qua = []

###########################################################################################################
# Lectura de archivo
###########################################################################################################

with open(file, 'rb') as f:
    data = f.read()

pkt_recibidos = len(data) / tamaño_pkt_bytes
print("\nArchivo:", file, "- Tamaño(Bytes):", len(data))
print("Tamaño de paquetes:", tamaño_pkt_bytes, ", Paquetes recibidos:", pkt_recibidos)

if unpack:
    for k in range(0, len(data), tamaño_pkt_bytes):
        temp = []

        sec.append(int.from_bytes(data[k: k + 4], byteorder='little', signed=False))
        if imprimir: print(sec[-1], end=",")
        for j in range(4, tamaño_pkt_bytes, 2):
            temp.append(int.from_bytes(data[k + j:k + j + 2], byteorder='little', signed=True))
            if imprimir: print(temp[-1], end=",")
        if imprimir: print("")
        
        for i in range(muestras_x_pkt):
            raw_qua.append([temp[0], temp[1], temp[2], temp[3]])
            raw_acc.append([temp[4], temp[5], temp[6]])
            raw_gyr.append([temp[7], temp[8], temp[9]])
            raw_mag.append([temp[10], temp[11], temp[12]])

            qua.append([temp[0] / unit[3], temp[1] / unit[3], temp[2] / unit[3], temp[3] / unit[3]])
            acc.append([temp[4] / unit[0], temp[5] / unit[0], temp[6] / unit[0]])
            gyr.append([temp[7] / unit[1], temp[8] / unit[1], temp[9] / unit[1]])
            mag.append([temp[10] / unit[2], temp[11] / unit[2], temp[12] / unit[2]])

        temp.clear()

    paquetes_sin_perdida = sec[-1] - sec[0] + 1
    print("Primer paquete:", sec[0], 
          "Ultimo paquete:", sec[-1],
          "Paquetes perdidos:", paquetes_sin_perdida - pkt_recibidos,
          "Tasa de exito:", (pkt_recibidos / paquetes_sin_perdida) * 100, "%")


"""
Formato 1: Acc, Gyr, Mag, Qua
    raw_acc.append([temp[0], temp[1], temp[2]])
    raw_gyr.append([temp[3], temp[4], temp[5]])
    raw_mag.append([temp[6], temp[7], temp[8]])
    raw_qua.append([temp[9], temp[10], temp[11], temp[12]])

    acc.append([temp[0] / unit[0], temp[1] / unit[0], temp[2] / unit[0]])
    gyr.append([temp[3] / unit[1], temp[4] / unit[1], temp[5] / unit[1]])
    mag.append([temp[6] / unit[2], temp[7] / unit[2], temp[8] / unit[2]])
    qua.append([temp[9] / unit[3], temp[10] / unit[3], temp[11] / unit[3], temp[12] / unit[3]])


Formato 2: Qua, Acc, Gyr, Mag
    raw_qua.append([temp[0], temp[1], temp[2], temp[3]])
    raw_acc.append([temp[4], temp[5], temp[6]])
    raw_gyr.append([temp[7], temp[8], temp[9]])
    raw_mag.append([temp[10], temp[11], temp[12]])

    qua.append([temp[0] / unit[3], temp[1] / unit[3], temp[2] / unit[3], temp[3] / unit[3]])
    acc.append([temp[4] / unit[0], temp[5] / unit[0], temp[6] / unit[0]])
    gyr.append([temp[7] / unit[1], temp[8] / unit[1], temp[9] / unit[1]])
    mag.append([temp[10] / unit[2], temp[11] / unit[2], temp[12] / unit[2]])
"""