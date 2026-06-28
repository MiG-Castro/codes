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
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.get_tk_widget().pack()

    # Variables para el cálculo de delay y jitter
    last_receive_time = time.time()  # Tiempo de recepcion del ultimo paquete
    max_delay = 0
    total_delay = 0
    total_jitter = 0
    num_samples = 0
    packets_lost = 0
    last_packet_number = 0
    all_jitters = []  # Lista para almacenar todos los jitter calculados
    all_delays = []  # Lista para almacenar todos los tiempos de delay calculados

    def update_plot():
        nonlocal last_receive_time, max_delay, total_delay, total_jitter, num_samples, packets_lost, last_packet_number

        try:
            data = q.get_nowait()
            if data != 'Q':
                N_pkt = data[0]
                lista_ecg = data[1]

                # Cálculo del delay y jitter
                current_time = time.time()  # Tiempo actual
                current_delay = current_time - last_receive_time  # Tiempo actual - Tiempo ultimo paquete
                last_receive_time = current_time  # Se actualiza
                max_delay = max(max_delay, current_delay)
                total_delay += current_delay
                num_samples += 1  # Cuenta de muestras recibidas
                if num_samples > 1:
                    jitter = abs(current_delay - (
                                total_delay / num_samples))  # Se calcula jitter como la diferencia de los paquetes y media de estos
                    total_jitter += jitter
                    all_jitters.append(jitter)
                    all_delays.append(current_delay)  # Añadir el tiempo de delay a la lista

                # Actualización de la gráfica
                ax.clear()
                ax.set_title('ECG')
                ax.set_xlabel("Muestras")
                ax.set_ylabel("Amplitud")
                # ax.set_ylim(0, 5000)
                ax.set_xlim(max(0, len(lista_ecg) - 600), len(lista_ecg))
                ax.grid()
                ax.plot(lista_ecg, 'r', linewidth=2)
                canvas.draw()

                # Actualiza la gráfica cada 100 ms
                window.after(50, update_plot)

                # Imprime el delay y jitter cada 10 muestras
            #  if num_samples % 1 == 0:
            # print(f"Media Delay: {(total_delay / num_samples * 1000):.6f} ms")
            # print(f"Jitter: {jitter * 1000:.6f} ms")

        except Empty:
            window.after(100, update_plot)

    window.after(100, update_plot)  # Inicia la actualización de la gráfica

    def on_closing():
        nonlocal packets_lost, all_jitters, total_delay, num_samples
        simulate.terminate()
        window.destroy()
        print("**********************************")

        print(f"Paquetes perdidos: {packets_lost}")

        # Calcular y mostrar el promedio de todos los jitter al finalizar
        if all_jitters:
            avg_jitter = mean(all_jitters) * 1000
            jitter_stdev = stdev(all_jitters) * 1000 if len(
                all_jitters) > 1 else 0  # Calcula la desviación estándar si hay más de una muestra, de lo contrario, establece en 0
            print(f"Promedio de Jitter: {avg_jitter:.6f} ms")
            print(f"Desviación estándar de Jitter: {jitter_stdev:.6f} ms")

        # Calcular y mostrar la media y desviación estándar del delay
        if num_samples > 0:
            avg_delay = total_delay / num_samples * 1000
            delay_stdev = stdev(
                all_delays) * 1000 if num_samples > 1 else 0  # Calcula la desviación estándar si hay más de una muestra, de lo contrario, establece en 0
            print(f"Average Delay: {avg_delay:.6f} ms")
            print(f"Desviación estándar de Delay: {delay_stdev:.6f} ms")

        print("**********************************")

    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()
    print('Done')


def simulation(q):
    # Listas para recibir datos
    N_pkt = []
    lista_ecg = []

    last_packet_number = 0
    packets_lost = 0

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

    while True:
        try:
            # Recibir datos del cliente
            data = conn.recv(200).decode("utf-8")

            # Procesar los datos recibidos
            for c in data:
                if c == i_paquete:
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
                        if len(datos_separados) > 0:  # Verificar que hay al menos un elemento (número de paquete)
                            packet_number = int(datos_separados[0])
                            if packet_number != last_packet_number + 1:
                                packets_lost += packet_number - last_packet_number - 1
                            last_packet_number = packet_number

                            N_pkt.append(packet_number)

                            # Agregar todos los valores después del número de paquete como una sola muestra continua
                            muestra_continua = [int(valor) for valor in datos_separados[1:]]

                            # Actualizar la lista de ECG con la muestra continua
                            lista_ecg.extend(muestra_continua)

                            # Limitar la lista a 1000 muestras
                            if len(lista_ecg) > 999:
                                lista_ecg = lista_ecg[-1000:]

                            q.put([N_pkt, lista_ecg])  # Mandamos la lista de las listas con la información

        except KeyboardInterrupt:
            sock.close()
            print("\n Socket TCP cerrado")
        except Exception as e:
            print("Error en recepcion:", e)


if __name__ == '__main__':
    main()
