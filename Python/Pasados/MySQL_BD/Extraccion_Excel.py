import openpyxl
import matplotlib.pyplot as plt
from openpyxl import Workbook
from numpy import linspace, arange

excel_document = openpyxl.load_workbook("Pruebas y datos.xlsx")
sheet = excel_document.get_sheet_by_name("FES2")
# sheet = excel_document.get_sheet_by_name("AAS2")
# sheet = excel_document.get_sheet_by_name('AAS3')

"""
INFORMACION Excel 

Datos de columna (D a QX -> AA AAM S3) y (D a QV -> AA AAM S2)
Señal de analisis Gy
[06] - Min      (Valor minimo de segmento negativo)
[07] - Max      (Valor maximo de segmento positivo)
[08] - PN01     (Pendiente negativa seccion 1/4)
[09] - PP02     (Pendiente positiva seccion 2/4)
[10] - PP03     (Pendiente positiva seccion 3/4)
[11] - PN04     (Pendiente positiva seccion 4/4)
[12] - SNP1     (Longitud parte negativo 1/2)
[13] - SNP2     (Longitud parte negativo 1/2)
[14] - SN       (Longitud parte negativo 2/2)
[15] - SS       (Longitud separacion de segmentos)
[16] - SP01     (Longitud parte positiva 1/2)
[17] - SP02     (Longitud parte positiva 1/2)
[18] - SP       (Longitud parte positiva 2/2)
[19] - Total    (Longitud total de ejercicio)
[20] - SN       (Area segmento negativo)
[21] - SP       (Area segmento positivo)
[22] - SN       (Energia segmento negativo)
[23] - SP       (Energia segmento positivo)
[24] - Total    (Energia total del ejercicio)

Datos de Columnas FE S2 (D -> PP)
Señal de analisis Ay (Ay = Ay - 1)
[06] V. Min
[07] PN01       (Pendiente Negativa Segmento 1/2)
[08] PP02       (Pendiente Positiva Segmento 1/2)
[09] SNP1       (Longitud Segmento 1/2)
[10] SNP2       (Longitud Segmento 1/2)
[11] SN         (Longitud TOTAL DEL SEGMENTO)
[12] Total      (Longitud TOTAL del Ejercicio)
[13] SN         (Area segmento)
[14] SN         (Energia Segmento)
[15] Total      (Energia TOTAL Ejercicio)
"""

titulo = "Energia Ejercicio"
colum = 15
fin = "PP"

Ini_Fin = ["D" + str(colum), fin + str(colum)]
multiple_cells = sheet[Ini_Fin[0]:Ini_Fin[1]]

intervalos = 20
datos_capturados = []

for row in multiple_cells:
    for cell in row:
        if cell.value is not None:
            datos_capturados.append(cell.value)

n, bins, patches = plt.hist(datos_capturados, intervalos, facecolor='g')
plt.subplots_adjust(left=0.04, bottom=0.07, right=0.98, top=0.9, wspace=0.15, hspace=0.12)

x = []
for k in arange(0, intervalos):
    x.append((bins[k] + bins[k + 1]) / 2)

for k in arange(0, intervalos):
    plt.text(x[k], n[k] + 1, str(int(n[k])))

plt.xlabel('Valores')
plt.ylabel('Frecuencia')
plt.title(titulo)
plt.xticks(bins)
plt.xlim([min(bins), max(bins)])
plt.grid(True)
plt.show()