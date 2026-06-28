from openpyxl import Workbook

book = Workbook()
sheet = book.active

sheet['A1'] = 5
sheet['A2'] = 10

sheet['B1'] = 'rango'

sheet.cell(row=1, column=10).value = "1_10"

book.save('prueba_escritura.xlsx')