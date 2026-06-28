import openpyxl
import matplotlib.pyplot as plt
from numpy import arange

"""
INFORMACION EXCEL 
Nombre de archivo: Recopilacion

-----------------------------------------------------------------
Nombre de hoja: IAACD_2. Datos de columna C -> BJ
[01]    Sensor 2 - IAACD. BD NA (Umbral +-5). Forma de -Seno en Gy.
[02]	No. Python
[03]	ID Ejercicio
[04]	V. Min
[05]	V. Max
[06]	PN01    (Pendiente P1)
[07]	PP02    (Pendiente P2)
[08]	PP03    (Pendiente P3)
[09]	PN04    (Pendiente P4)
[10]	SNP1    (No. Muestras Seg Neg P1)
[11]	SNP2    (No. Muestras Seg Neg P2)
[12]	SN      (No. Muestras Seg Neg Completo)
[13]	SS      (No. Muestras Sep Seg)
[14]	SP01    (No. Muestras Seg Pos P1)
[15]	SP02    (No. Muestras Seg Pos P2)
[16]	SP      (No. Muestras Seg Pos Completo)
[17]	Total   (No. Muestras total)
[18]	SN      (Area Seg Neg)
[19]	SP      (Area Seg Pos)
[20]	SN      (Energia Seg Neg)
[21]	SP      (Energia Seg Pos)
[22]	Total   (Energia Ejercicio Completo)

-----------------------------------------------------------------
Nombre de hoja: IAACI_2. Datos de columna C -> AR
[01]    Sensor 2 - IAACI. BD NA (Umbral +-5). Forma de +Seno en Gy.
[02]	No. Python
[03]	ID Ejercicio
[04]	V. Max
[05]	V. Min
[06]	PP01    (Pendiente P1)
[07]	PN02    (Pendiente P2)
[08]	PN03    (Pendiente P3)
[09]	PP04    (Pendiente P4)
[10]	SP01    (No. Muestras Seg Pos P1)
[11]	SP02    (No. Muestras Seg Pos P2)
[12]	SP      (No. Muestras Seg Pos Completo)
[13]	SS      (No. Muestras Sep Seg)
[14]	SN01    (No. Muestras Seg Neg P1)
[15]	SN02    (No. Muestras Seg Neg P2)
[16]	SN      (No. Muestras Seg Neg Completo)
[17]	Total   (No. Muestras total)
[18]	SP      (Area Seg Pos)
[19]	SN      (Area Seg Neg)
[20]	SP      (Energia Seg Pos)
[21]	SN      (Energia Seg Neg)
[22]	Total   (Energia Ejercicio Completo)

-----------------------------------------------------------------
Nombre de hoja: IAACD_3. Datos de columna C -> BJ
[01]    Sensor 3 - IAACD. BD NA (Umbral +-5). Forma de -Seno en Gy.
[02]	No. Python
[03]	ID Ejercicio
[04]	V. Min
[05]	V. Max
[06]	PN01    (Pendiente P1)
[07]	PP02    (Pendiente P2)
[08]	PP03    (Pendiente P3)
[09]	PN04    (Pendiente P4)
[10]	SNP1    (No. Muestras Seg Neg P1)
[11]	SNP2    (No. Muestras Seg Neg P2)
[12]	SN      (No. Muestras Seg Neg Completo)
[13]	SS      (No. Muestras Sep Seg)
[14]	SP01    (No. Muestras Seg Pos P1)
[15]	SP02    (No. Muestras Seg Pos P2)
[16]	SP      (No. Muestras Seg Pos Completo)
[17]	Total   (No. Muestras total)
[18]	SN      (Area Seg Neg)
[19]	SP      (Area Seg Pos)
[20]	SN      (Energia Seg Neg)
[21]	SP      (Energia Seg Pos)
[22]	Total   (Energia Ejercicio Completo)

-----------------------------------------------------------------
Nombre de hoja: IAACI_3. Datos de columna C -> AQ
[01]    Sensor 3 - IAACI. BD NA (Umbral +-5). Forma de +Seno en Gy.
[02]	No. Python
[03]	ID Ejercicio
[04]	V. Max
[05]	V. Min
[06]	PP01    (Pendiente P1)
[07]	PN02    (Pendiente P2)
[08]	PN03    (Pendiente P3)
[09]	PP04    (Pendiente P4)
[10]	SP01    (No. Muestras Seg Pos P1)
[11]	SP02    (No. Muestras Seg Pos P2)
[12]	SP      (No. Muestras Seg Pos Completo)
[13]	SS      (No. Muestras Sep Seg)
[14]	SN01    (No. Muestras Seg Neg P1)
[15]	SN02    (No. Muestras Seg Neg P2)
[16]	SN      (No. Muestras Seg Neg Completo)
[17]	Total   (No. Muestras total)
[18]	SP      (Area Seg Pos)
[19]	SN      (Area Seg Neg)
[20]	SP      (Energia Seg Pos)
[21]	SN      (Energia Seg Neg)
[22]	Total   (Energia Ejercicio Completo)

-----------------------------------------------------------------
Nombre de hoja: IFER_2. Datos de columna C -> CZ
[01]    Sensor 2 - IFER. BD NA (Umbral +-5). Forma de +Seno en Gz.
[02]	No. Python
[03]	ID Ejercicio
[04]	V. Max
[05]	V. Min
[06]	PP01    (Pendiente P1)
[07]	PN02    (Pendiente P2)
[08]	PN03    (Pendiente P3)
[09]	PP04    (Pendiente P4)
[10]	SP01    (No. Muestras Seg Pos P1)
[11]	SP02    (No. Muestras Seg Pos P2)
[12]	SP      (No. Muestras Seg Pos Completo)
[13]	SS      (No. Muestras Sep Seg)
[14]	SN01    (No. Muestras Seg Neg P1)
[15]	SN02    (No. Muestras Seg Neg P2)
[16]	SN      (No. Muestras Seg Neg Completo)
[17]	Total   (No. Muestras total)
[18]	SP      (Area Seg Pos)
[19]	SN      (Area Seg Neg)
[20]	SP      (Energia Seg Pos)
[21]	SN      (Energia Seg Neg)
[22]	Total   (Energia Ejercicio Completo)

-----------------------------------------------------------------
Nombre de hoja: IFEC_3. Datos de columna C -> CX
[01]    Sensor 3 - IFEC. BD NA (Umbral +-0.05 / offset -1G Ay). Forma de +U en Ay.
[02]	No. Python
[03]	ID Ejercicio
[04]	V. Min
[05]	PN01    (Pendiente P1)
[06]	PP02    (Pendiente P2)
[07]	SNP1    (No. Muestras Seg Neg P1)
[08]	SNP2    (No. Muestras Seg Neg P1)
[09]	SN      (No. Muestras Seg Neg Completo)
[10]	Total   (No. Muestras Total)
[11]	SN      (Area Seg Neg)
[12]	SN      (Energia Seg Neg)
[13]	Total   (Energia Ejerccicio Completo)

INFORMACION EXCEL 
Nombre de archivo: IFERN_2

Nombre de hoja: IFERN_2. Datos de columna C -> CG

[01]    Sensor 2 - IFER. BD NA (Umbral +-5). Forma de +Seno en Gz.
[02]	No. Python
[03]	ID Ejercicio
[04]	V. Max
[05]	V. Min
[06]	PP01    (Pendiente P1)
[07]	PN02    (Pendiente P2)
[08]	PN03    (Pendiente P3)
[09]	PP04    (Pendiente P4)
[10]	SP01    (No. Muestras Seg Pos P1)
[11]	SP02    (No. Muestras Seg Pos P2)
[12]	SP      (No. Muestras Seg Pos Completo)
[13]	SS      (No. Muestras Sep Seg)
[14]	SN01    (No. Muestras Seg Neg P1)
[15]	SN02    (No. Muestras Seg Neg P2)
[16]	SN      (No. Muestras Seg Neg Completo)
[17]	Total   (No. Muestras total)
[18]	SP      (Area Seg Pos)
[19]	SN      (Area Seg Neg)
[20]	SP      (Energia Seg Pos)
[21]	SN      (Energia Seg Neg)
[22]	Total   (Energia Ejercicio Completo)
"""

excel_document = openpyxl.load_workbook("IFERN_2.xlsx")
sheet = excel_document["IFERN_2"]

titulo = "IFERN 2. Energia Ejercicio"
colum = 22
fin = "CG"

Ini_Fin = ["C" + str(colum), fin + str(colum)]
multiple_cells = sheet[Ini_Fin[0]:Ini_Fin[1]]

intervalos = 20
datos_capturados = []

for row in multiple_cells:
    for cell in row:
        if cell.value is not None:
            datos_capturados.append(cell.value)

n, bins, patches = plt.hist(datos_capturados, intervalos, facecolor='g')
plt.subplots_adjust(left=0.03, bottom=0.06, right=0.98, top=0.95)

x = []
for k in arange(0, intervalos):
    x.append((bins[k] + bins[k + 1]) / 2)

for k in arange(0, intervalos):
    plt.text(x[k], n[k] + 0.1, str(int(n[k])))

plt.xlabel('Valores')
plt.ylabel('Frecuencia')
plt.title(titulo)
plt.xticks(bins)
plt.xlim([min(bins), max(bins)])
plt.grid(True)
plt.show()
