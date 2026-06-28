S_xx = []
S2_xx = []
S_Loss = 0
S2_Loss = 0
LossPkt = [0, 0, 0]
lengthVector = 100

Total_Error = "Conteo Errores: S3 = 0, S4 = 0, Total = 0"
f = open("26-11-2021_16-45-17_E2B-s3.txt", "r")

while True:
    try:
        line = f.readline()
        if not line:
            print("FIN")
            break
        try:
            line_list = line.split(".")
            if len(line_list) == 20:
                if line_list[0] == "3":
                    # Conversion bytes a enteros
                    S_xx.append(int(line_list[1]) + 1)
                    S_xx = S_xx[-lengthVector:]

                    if len(S_xx) > 1 and S_xx[-1] != (S_xx[-2] + 1):
                        S_Loss = S_Loss + 1
                        LossPkt[1] = LossPkt[1] + S_xx[-1] - S_xx[-2] - 1
                        LossPkt[2] = LossPkt[0] + LossPkt[1]
                        Total_Error = "Discontinuidades: S3 = " + str(S_Loss) + ", S2 = " + str(S2_Loss) + \
                                      ", Total = " + str(S_Loss + S2_Loss)
                        print(Total_Error)
                        print("Error en S3, ultimo paquete = ", S_xx[-2], ", Nuevo paquete = ", S_xx[-1],
                              ", Perdidos = ", (S_xx[-1] - S_xx[-2] - 1))
                        print("Paquetes perdidos: S3 = ", LossPkt[1], ", S2 = ", LossPkt[0], "Total = ", LossPkt[2], "\n")
                    #else:
                        #print("S3, Muestra: ", S_xx[-1], ", Bien. ", Total_Error)

                elif line_list[0] == "2":
                    # Conversion bytes a enteros
                    S2_xx.append(int(line_list[1]))

                    # Ajuste de tamaño de variables
                    S2_xx = S2_xx[-lengthVector:]

                    if len(S2_xx) > 1 and S2_xx[-1] != (S2_xx[-2] + 1):
                        S2_Loss = S2_Loss + 1
                        LossPkt[0] = LossPkt[0] + S2_xx[-1] - S2_xx[-2] - 1
                        LossPkt[2] = LossPkt[0] + LossPkt[1]
                        Total_Error = "Discontinuidades: S3 = " + str(S_Loss) + ", S2 = " + str(S2_Loss) + \
                                      ", Total = " + str(S_Loss + S2_Loss)
                        print(Total_Error)
                        print("Error en S2, Ultima paquete = ", S2_xx[-2], ", Nuevo paquete = ", S2_xx[-1],
                              ", Perdidos = ", (S2_xx[-1] - S2_xx[-2] - 1))
                        print("Paquetes perdidos: S3 = ", LossPkt[1], ", S2 = ", LossPkt[0], "Total = ", LossPkt[2], "\n")

                    #else:
                        #print("S2, Muestra: ", S2_xx[-1], ", Bien. ", Total_Error)
        except:
            print("Error al separar/convertir linea, Linea recibida: ", line)
    except:
        print("Algo salio mal al leer")