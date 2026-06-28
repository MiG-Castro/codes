import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, lfilter, freqz, filtfilt
import GestorBDD


save_path='/home/marisela/Documentos/Datosweka/'#ubicacion donde se guarda el archivo

def butter_lowpass(cutoff, fs, order=5):#filtro butterworth quinto orden
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def get_caracteristicas(ejercicio):
    b, a = butter_lowpass(3, 60, 5)
    try:
        id=[float(item) for item in ejercicio[4][1:-1].split(',')]
    except:
        print(ejercicio)
    gx = [float(item) for item in ejercicio[5][1:-1].split(',')]
    gy = [float(item) for item in ejercicio[6][1:-1].split(',')]
    gz = [float(item) for item in ejercicio[7][1:-1].split(',')]
    ax = [float(item) for item in ejercicio[8][1:-1].split(',')]
    ay = [float(item) for item in ejercicio[9][1:-1].split(',')]
    az = [float(item) for item in ejercicio[10][1:-1].split(',')]


    # try:
    #     gx = [float(item) for item in ejercicio[5][1:-1].split(',')]
    # except:
    #     print(gx)

    #Señales filtradas
    try:
        gxf = filtfilt(b, a, gx)
        gyf = filtfilt(b, a, gy)
        gzf = filtfilt(b, a, gz)
        axf = filtfilt(b, a, ax)
        ayf = filtfilt(b, a, ay)
        azf = filtfilt(b, a, az)


        #gxf = filtfilt(b, a, gx)
    except:
       print(ejercicio)

#obtencion de carcateristicas
    #Energia de la señal
    Egx = np.sum(gxf ** 2)
    Egy = np.sum(gyf ** 2)
    Egz = np.sum(gzf ** 2)
    Eax = np.sum(axf ** 2)
    Eay = np.sum(ayf ** 2)
    Eaz = np.sum(azf ** 2)

    #Media
    Mgx = np.mean(gxf)
    Mgy = np.mean(gyf)
    Mgz = np.mean(gzf)
    Max = np.mean(axf)
    May = np.mean(ayf)
    Maz = np.mean(azf)

    # Desviación estandar
    Dgx = np.std(gxf)
    Dgy = np.std(gyf)
    Dgz = np.std(gzf)
    Dax = np.std(axf)
    Day = np.std(ayf)
    Daz = np.std(azf)


    #Maximo
    maxgx = max(gxf)
    maxgy = max(gyf)
    maxgz = max(gzf)
    maxax = max(axf)
    maxay = max(ayf)
    maxaz = max(azf)

    # Minimo
    mingx = min(gxf)
    mingy = min(gyf)
    mingz = min(gzf)
    minax = min(axf)
    minay = min(ayf)
    minaz = min(azf)


    #Rango
    Rgx = maxgx - mingx
    Rgy = maxgy - mingy
    Rgz = maxgz - mingz
    Rax = maxax - minax
    Ray = maxay - minay
    Raz = maxaz - minaz


    #Duracion de la señal
    Duracion = id[-1]-id[0]


    #Pendiente

    P=Duracion/4
    Pendx= gxf[round(P)]
    if Pendx>0:
        Pendgx="Positiva"
    if Pendx<0:
        Pendgx="Negativa"

    Pendy = gyf[round(P)]
    if Pendy > 0:
        Pendgy = "Positiva"
    if Pendy < 0:
        Pendgy = "Negativa"

    Pendz = gzf[round(P)]
    if Pendz > 0:
        Pendgz = "Positiva"
    if Pendz< 0:
        Pendgz = "Negativa"

    Pendxa = axf[round(P)]
    if Pendxa > 0:
        Pendax = "Positiva"
    if Pendxa < 0:
        Pendax = "Negativa"

    Pendya = ayf[round(P)]
    if Pendya > 0:
        Penday = "Positiva"
    if Pendya < 0:
        Penday = "Negativa"

    Pendza= azf[round(P)]
    if Pendza > 0:
        Pendaz = "Positiva"
    if Pendza < 0:
        Pendaz = "Negativa"



    #recopilacion
    caracteristicas=[Egx,Egy,Egz,Eax,Eay,Eaz,Mgx,Mgy,Mgz,Max,May,Maz,Dgx,Dgy,Dgz,Dax,Day,Daz,maxgx,maxgy,maxgz,maxax,
                     maxay,maxaz,mingx,mingy,mingz,minax,minay,minaz,Rgx,Rgy,Rgz,Rax,Ray,Raz,Duracion,Pendgx,Pendgy,
                     Pendgz,Pendax,Penday,Pendaz]
    return caracteristicas
    #print(type(ejercicio[4]))

def filtrar_tuplas(ejercicios):
    tuplas=[]
    idusado=[]
    for i,ejercicio in enumerate(ejercicios):
        ejers=[]

        encontrado=False
        if(ejercicio[0] in idusado):
            continue
        ejers.append(ejercicio)
        #print(ejercicio)
        for ejer2 in ejercicios:
            if ejer2[2]==ejercicio[2] and ejercicio[3]!=ejer2[3] and not(ejer2[0] in idusado):
                ejers.append(ejer2)
                idusado.append(ejer2[0])
                idusado.append(ejercicio[0])
                #print(idusado)
                #print(ejer2[0],ejercicio[0])
                tuplas.append(ejers)
                break
        #ejers.pop(-1)
    #for tejers in tuplas:
        #print(tejers)
        #get_caracteristicas(ejercicio)
        #axs.flat[i].plot(id,gy)
        #axs.flat[i].plot(id, filtfilt(b,a,gy))
    #print(idusado)
    for ejercicio in ejercicios:
        if not ejercicio[0] in idusado:
            print(ejercicio)
    #print(len(ejers))
    print(len(tuplas))
    return tuplas


data=GestorBDD.DataBase()#Crea una instancia del manejador de la base de datos


condicop='WHERE Ejercicio="FE"'#jalamos los ejercicios de la base de datos
ejercicios=data.getSignals(condicop)
tuplasfe=filtrar_tuplas(ejercicios)

condicop='WHERE Ejercicio="FEM"'
ejercicios=data.getSignals(condicop)
tuplasfem=filtrar_tuplas(ejercicios)

#fig1, axs = plt.subplots(10,20)
#ejercaracteristicas=[]

#Encabezado del formato de archivo para WEKA
encabezado=["@relation ejercicio_FE",
            "@attribute 'Energx' numeric",
            "@attribute 'Energy' numeric",
            "@attribute 'Energz' numeric",
            "@attribute 'Enerax' numeric",
            "@attribute 'Eneray' numeric",
            "@attribute 'Eneraz' numeric",
            "@attribute 'Mediagx' numeric",
            "@attribute 'Mediagy' numeric",
            "@attribute 'Mediagz' numeric",
            "@attribute 'Mediaax' numeric",
            "@attribute 'Mediaay' numeric",
            "@attribute 'Mediaaz' numeric",
            "@attribute 'STDgx' numeric",
            "@attribute 'STDgy' numeric",
            "@attribute 'STDgz' numeric",
            "@attribute 'STDax' numeric",
            "@attribute 'STDay' numeric",
            "@attribute 'STDaz' numeric",
            "@attribute 'Maximogx' numeric",
            "@attribute 'Maximogy' numeric",
            "@attribute 'Maximogz' numeric",
            "@attribute 'Maximoax' numeric",
            "@attribute 'Maximoay' numeric",
            "@attribute 'Maximoaz' numeric",
            "@attribute 'Minimogx' numeric",
            "@attribute 'Minimogy' numeric",
            "@attribute 'Minimogz' numeric",
            "@attribute 'Minimoax' numeric",
            "@attribute 'Minimoay' numeric",
            "@attribute 'Minimoaz' numeric",
            "@attribute 'Rangogx' numeric",
            "@attribute 'Rangogy' numeric",
            "@attribute 'Rangogz' numeric",
            "@attribute 'Rangoax' numeric",
            "@attribute 'Rangoay' numeric",
            "@attribute 'Rangoaz' numeric",
            "@attribute 'Duracion' numeric",
            "@attribute 'Pendgx' {Positiva, Negativa}",
            "@attribute 'Pendgy' {Positiva, Negativa}",
            "@attribute 'Pendgz' {Positiva, Negativa}",
            "@attribute 'Pendax' {Positiva, Negativa}",
            "@attribute 'Penday' {Positiva, Negativa}",
            "@attribute 'Pendaz' {Positiva, Negativa}",
            "@attribute 'Energxs3' numeric",
            "@attribute 'Energys3' numeric",
            "@attribute 'Energzs3' numeric",
            "@attribute 'Eneraxs3' numeric",
            "@attribute 'Enerays3' numeric",
            "@attribute 'Enerazs3' numeric",
            "@attribute 'Mediagxs3' numeric",
            "@attribute 'Mediagys3' numeric",
            "@attribute 'Mediagzs3' numeric",
            "@attribute 'Mediaaxs3' numeric",
            "@attribute 'Mediaays3' numeric",
            "@attribute 'Mediaazs3' numeric",
            "@attribute 'STDgxs3' numeric",
            "@attribute 'STDgys3' numeric",
            "@attribute 'STDgzs3' numeric",
            "@attribute 'STDaxs3' numeric",
            "@attribute 'STDays3' numeric",
            "@attribute 'STDazs3' numeric",
            "@attribute 'Maximogxs3' numeric",
            "@attribute 'Maximogys3' numeric",
            "@attribute 'Maximogzs3' numeric",
            "@attribute 'Maximoaxs3' numeric",
            "@attribute 'Maximoays3' numeric",
            "@attribute 'Maximoazs3' numeric",
            "@attribute 'Minimogxs3' numeric",
            "@attribute 'Minimogys3' numeric",
            "@attribute 'Minimogzs3' numeric",
            "@attribute 'Minimoaxs3' numeric",
            "@attribute 'Minimoays3' numeric",
            "@attribute 'Minimoazs3' numeric",
            "@attribute 'Rangogxs3' numeric",
            "@attribute 'Rangogys3' numeric",
            "@attribute 'Rangogzs3' numeric",
            "@attribute 'Rangoaxs3' numeric",
            "@attribute 'Rangoays3' numeric",
            "@attribute 'Rangoazs3' numeric",
            "@attribute 'Duracions3' numeric",
            "@attribute 'Pendgxs3' {P, N}",
            "@attribute 'Pendgys3' {P, N}",
            "@attribute 'Pendgzs3' {P, N}",
            "@attribute 'Pendaxs3' {P, N}",
            "@attribute 'Pendays3' {P, N}",
            "@attribute 'Pendazs3' {P, N}",
            "@attribute 'class' {bien_realizado, mal_realizado}",
            "@data"]

#global save_path
FEfile= open(save_path+"FEpend.arff","w+")#nombre del archivo donde se guardan los datos
#archivo=open("ejercicio", "w+")
FEfile.writelines(["%s\n" % item for item in encabezado])

for fet in tuplasfe:
    caracts2=get_caracteristicas(fet[0])
    caracts3 = get_caracteristicas(fet[1])
    linea=','.join([str(elem) for elem in caracts2])+','+','.join([str(elem) for elem in caracts3])+',bien_realizado\n'
    FEfile.writelines(linea)
    #print(linea)

for fet in tuplasfem:
    caracts2=get_caracteristicas(fet[0])
    caracts3 = get_caracteristicas(fet[1])
    linea=','.join([str(elem) for elem in caracts2])+','+','.join([str(elem) for elem in caracts3])+',mal_realizado\n'
    FEfile.writelines(linea)
    #print(linea)


FEfile.close()
#archivo.write(caracteristicas)
plt.show()
#print(len(ejercicios))