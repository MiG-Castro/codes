import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import multiprocessing
from tkinter import *
from queue import Empty
import time
import socket
from statistics import mean, stdev  # Funciones para el cálculo de la media y desviación estándar



def main():
    global all_jitters, packets_lost, N_pkt
    # Se crea una cola para compartir información entre procesos
    q = multiprocessing.Queue()

    # Se crea e inicia el proceso de simulación
    simulate = multiprocessing.Process(target=simulation, args=(q,))
    simulate.start()

    # Genera la ventana
    window = Tk()
    window.title("ECG Viewer")

    # Genera la gráfica
    fig = plt.Figure(figsize=(8, 6), dpi=100)
    ax = fig.add_subplot(111)
    ax.get_xaxis().set_visible(False)
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.get_tk_widget().pack()

    def update_plot():
        try:
            data = q.get_nowait()
            if data != 'Q':
                x = data[0][0:-60]
                lista_ecg = data[1][0:-60]

                # Actualización de la gráfica
                ax.clear()
                ax.set_title('ECG')
                ax.set_xlabel("Muestras")
                ax.set_ylabel("Amplitud")
                ax.set_ylim(0, 3.5)
                # ax.set_xlim(x[0], x[-1]len(lista_ecg))
                # ax.grid()
                ax.plot(x, lista_ecg, 'r', linewidth=2)
                canvas.draw()

        except Empty:
            A = "No hace nada jaja"
        # Actualiza la gráfica cada 100 ms
        window.after(30, update_plot)

    window.after(30, update_plot)  # Inicia la actualización de la gráfica

    def on_closing():
        data = q.get_nowait()
        N_pkt = data[2]
        packets_lost = data[3]
        all_jitters = data[4]
        all_jitters[0] = 110

        simulate.terminate()
        window.destroy()

        print("**********************************")
        print(f"Paquetes perdidos: {packets_lost}, TPP = {((packets_lost / (N_pkt[-1] - N_pkt[0] + 1)) * 100)}%")
        if len(all_jitters) > 1:
            print(f"Jitter promedio: {mean(all_jitters):.6f}ms, std: {(stdev(all_jitters)):.6f}ms")
            print(f"Retardo maximo: {max(all_jitters):.6f}ms, retardo minimo: {min(all_jitters):.6f}ms")
            for k in range(len(all_jitters)):
                all_jitters[k] = all_jitters[k] - 100
            print(f"Retardo promedio: {mean(all_jitters):.6f}ms")
        print("**********************************")

    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()
    print('Done')


def simulation(q):
    # Listas para recibir datos
    lista_ecg = []
    eje_x = []

    all_jitters = []
    N_pkt = []
    packets_lost = 0

    last_packet_number = - 1

    # Crear un socket TCP -> SOCK_STREAM
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Enlazar el socket a la dirección IP y puerto
    puerto = 3333
    ip = "192.168.10.132"
    sock.bind((ip, puerto))

    # Escuchar conexiones entrantes
    sock.listen()

    # Aceptar una conexión, obtener el socket y definir el timeout
    conn, addr = sock.accept()
    conn.settimeout(20)

    i_paquete = "p"  # Indicador de inicio y fin de paquete
    f_paquete = "."  # Indicador de fin de paquete
    paquete_actual = ""  # Variable para almacenar el paquete actual

    last_receive_time = time.time()  # Tiempo actual

    while True:
        try:
            # Recibir datos del cliente
            data = conn.recv(200).decode("utf-8")

            # Procesar los datos recibidos
            for c in data:
                if c == i_paquete:
                    # Jitter!
                    current_time = time.time()
                    all_jitters.append((current_time - last_receive_time) * 1000)
                    last_receive_time = current_time
                    # Se inicia un nuevo paquete
                    paquete_actual = i_paquete

                else:
                    paquete_actual += c

                # Verificar si hay un paquete completo
                if c == f_paquete:
                    if paquete_actual[0] == i_paquete:
                        # Paquete completo encontrado ******************************************************************
                        datos_separados = paquete_actual[1:-1].split(',')
                        paquete_actual = ""  # Reset de variable temporal

                        # Procesamiento
                        tam_pqt = len(datos_separados)
                        if tam_pqt > 0:  # Verificar que hay al menos un elemento (número de paquete)
                            packet_number = int(datos_separados[0])

                            # DETECCION Y CONTEO DE PERDIDA DE PAQUETES
                            if packet_number != last_packet_number + 1:
                                packets_lost += packet_number - last_packet_number - 1
                            last_packet_number = packet_number
                            N_pkt.append(packet_number)

                            # Expansion de eje X
                            for k in range(tam_pqt - 1):
                                    eje_x.append(((packet_number * (tam_pqt - 1)) + k) * 0.005)

                            # Agregar todos los valores después del número de paquete como una sola muestra continua
                            muestra_continua = [(3.3 * int(valor))/4095 for valor in datos_separados[1:]]
                            # Actualizar la lista de ECG con la muestra continua
                            lista_ecg.extend(muestra_continua)

                            # Limitar la lista a 600 muestras
                            if len(lista_ecg) > 600:
                                lista_ecg = lista_ecg[-600:]
                                eje_x = eje_x[-600:]

                            q.put([eje_x, lista_ecg, N_pkt, packets_lost, all_jitters])  # Mandamos la lista de las listas con la información

        except KeyboardInterrupt:
            sock.close()
            print("\n Socket TCP cerrado")
        except Exception as e:
            print("Error en recepcion:", e)


if __name__ == '__main__':
    main()
