import time

ejercicio = "04-09-2024_13-33-22_IAAC_s2.txt"  # "24-01-2022_16-46-07_IAAM_s3.txt"
f = open(ejercicio, "r")

while True:
        line = f.readline()
        line.replace(" ", "")
        print(line, end="")
        time.sleep(1)


