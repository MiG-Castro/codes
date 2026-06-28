import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
import struct
import socket
from datetime import datetime

class WSNInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Interfaz WSN - Nodo Central")
        self.root.geometry("1400x900")
        
        # Variables de conexión
        self.serial_connection = None
        self.is_connected = False
        self.reading_thread = None
        self.stop_reading = False
        self.printLogs = True
        
        # Variables para guardado de datos
        self.saving_data = False
        self.save_file = None
        
        # Control de scan
        self.scan_active = False
        
        # Variables para parsing de paquetes
        self.packet_buffer = bytearray()
        self.packet_state = 0  # 0: buscando inicio, 1: leyendo paquete
        self.expected_packet_size = 50
        
        # Variables para estadísticas por sensor (0, 1, 2)
        self.last_packet_numbers = [None, None, None]  # Último número de paquete recibido
        self.lost_packets_count = [0, 0, 0]  # Contador de paquetes perdidos
        
        # Variables para localhost
        self.sending_to_localhost = False
        self.localhost_thread = None
        self.stop_localhost_thread = False
        self.sensor_fragments = [bytearray(13), bytearray(13), bytearray(13)]  # Fragmentos de 13 bytes por sensor
        self.sensor_data_received = [False, False, False]  # Flag para saber si hemos recibido datos
        self.udp_socket = None
        
        # Variables para actualización de estadísticas
        self.stats_update_counter = 0
        self.stop_pkt_no = 0
        
        self.setup_ui()
        self.update_ports()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuración de conexión
        conn_frame = ttk.LabelFrame(main_frame, text="Configuración de Conexión", padding="10")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(conn_frame, text="Puerto:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=15)
        self.port_combo.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(conn_frame, text="Baudrate:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.baud_var = tk.StringVar(value="115200")
        baud_combo = ttk.Combobox(conn_frame, textvariable=self.baud_var, width=10)
        baud_combo['values'] = ('9600', '19200', '38400', '57600', '115200', '230400')
        baud_combo.grid(row=0, column=3, padx=(0, 10))
        
        self.connect_btn = ttk.Button(conn_frame, text="Conectar", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=4, padx=(10, 0))
        
        ttk.Button(conn_frame, text="Actualizar", command=self.update_ports).grid(row=0, column=5, padx=(5, 0))
        
        # Frame de comandos en dos secciones principales
        commands_frame = ttk.Frame(main_frame)
        commands_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # SECCIÓN CENTRAL con dos columnas
        central_frame = ttk.LabelFrame(commands_frame, text="Central", padding="10")
        central_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 10))
        
        # Columna 1 de Central
        central_col1 = ttk.Frame(central_frame)
        central_col1.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 10))
        
        # Comando manual
        manual_frame = ttk.LabelFrame(central_col1, text="Comando Manual", padding="5")
        manual_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(manual_frame, text="Tipo (hex):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.cmd_type_var = tk.StringVar()
        ttk.Entry(manual_frame, textvariable=self.cmd_type_var, width=8).grid(row=0, column=1, padx=(0, 5))
        
        ttk.Label(manual_frame, text="Payload (hex):").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.payload_var = tk.StringVar()
        ttk.Entry(manual_frame, textvariable=self.payload_var, width=20).grid(row=1, column=1, padx=(0, 5))
        
        ttk.Button(manual_frame, text="Enviar", command=self.send_command).grid(row=2, column=0, columnspan=2, pady=(5, 0))
        
        # Configuración de Parámetros
        params_frame = ttk.LabelFrame(central_col1, text="Configuración Parámetros", padding="5")
        params_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Fila 1 parámetros
        ttk.Label(params_frame, text="PHY:").grid(row=0, column=0, sticky=tk.W, padx=(0, 2))
        self.phy_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.phy_var, width=6).grid(row=0, column=1, padx=(0, 5))
        
        ttk.Label(params_frame, text="Conn Int:").grid(row=0, column=2, sticky=tk.W, padx=(0, 2))
        self.conn_interval_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.conn_interval_var, width=6).grid(row=0, column=3)
        
        # Fila 2 parámetros
        ttk.Label(params_frame, text="Latency:").grid(row=1, column=0, sticky=tk.W, padx=(0, 2))
        self.latency_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.latency_var, width=6).grid(row=1, column=1, padx=(0, 5))
        
        ttk.Label(params_frame, text="Timeout:").grid(row=1, column=2, sticky=tk.W, padx=(0, 2))
        self.timeout_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.timeout_var, width=6).grid(row=1, column=3)
        
        # Fila 3 parámetros
        ttk.Label(params_frame, text="Data Len:").grid(row=2, column=0, sticky=tk.W, padx=(0, 2))
        self.data_length_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.data_length_var, width=6).grid(row=2, column=1, padx=(0, 5))
        
        ttk.Label(params_frame, text="Tx/Rx:").grid(row=2, column=2, sticky=tk.W, padx=(0, 2))
        self.txrx_time_var = tk.StringVar()
        ttk.Entry(params_frame, textvariable=self.txrx_time_var, width=6).grid(row=2, column=3)
        
        ttk.Button(params_frame, text="Enviar", command=self.send_params_config).grid(row=3, column=0, columnspan=4, pady=(5, 0))
        
        # Columna 2 de Central - Sección Control
        control_frame = ttk.LabelFrame(central_frame, text="Control", padding="5")
        control_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N))
        
        # Control de Scan (toggle)
        self.scan_btn = ttk.Button(control_frame, text="Start Scan", command=self.toggle_scan)
        self.scan_btn.grid(row=0, column=0, columnspan=2, pady=(0, 5), sticky=(tk.W, tk.E))
        
        # Disconnect
        ttk.Label(control_frame, text="Disconnect:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.disconnect_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.disconnect_var, width=8).grid(row=2, column=0, padx=(0, 5))
        ttk.Button(control_frame, text="Disconnect", command=self.send_disconnect).grid(row=2, column=1)
        
        # Botones de control sistema
        ttk.Button(control_frame, text="PrintLogs", command=self.send_print_logs).grid(row=3, column=0, pady=(5, 2), sticky=(tk.W, tk.E))
        ttk.Button(control_frame, text="TxUART", command=self.send_tx_uart).grid(row=3, column=1, pady=(5, 2), sticky=(tk.W, tk.E))
        
        # Control de envío a localhost
        localhost_frame = ttk.LabelFrame(control_frame, text="Localhost", padding="3")
        localhost_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.localhost_btn = ttk.Button(localhost_frame, text="Start Localhost", command=self.toggle_localhost)
        self.localhost_btn.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Guardado de datos
        save_subframe = ttk.LabelFrame(control_frame, text="Guardado", padding="3")
        save_subframe.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.save_btn = ttk.Button(save_subframe, text="Save bin", command=self.start_saving)
        self.save_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_save_btn = ttk.Button(save_subframe, text="End Save", command=self.stop_saving, state="disabled")
        self.stop_save_btn.grid(row=0, column=1)
        
        self.save_status_var = tk.StringVar(value="No guardando")
        ttk.Label(save_subframe, textvariable=self.save_status_var, font=('TkDefaultFont', 8)).grid(row=1, column=0, columnspan=2)
        
        # SECCIÓN PERIFÉRICOS
        periph_frame = ttk.LabelFrame(commands_frame, text="Periféricos", padding="10")
        periph_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N))
        
        # Columna 1 de Periféricos
        periph_col1 = ttk.Frame(periph_frame)
        periph_col1.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 10))
        
        # IDX del periférico
        idx_frame = ttk.LabelFrame(periph_col1, text="ID Periférico", padding="5")
        idx_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(idx_frame, text="IDX (hex):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.periph_idx_var = tk.StringVar()
        ttk.Entry(idx_frame, textvariable=self.periph_idx_var, width=10).grid(row=0, column=1)
        ttk.Label(idx_frame, text="(vacío = 0xFF)", font=('TkDefaultFont', 8)).grid(row=1, column=0, columnspan=2)
        
        # Control de muestreo expandido
        sampling_control_frame = ttk.LabelFrame(periph_col1, text="Control de Muestreo", padding="5")
        sampling_control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(sampling_control_frame, text="Start", command=self.start_sampling).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(sampling_control_frame, text="Stop", command=self.stop_sampling).grid(row=0, column=1)
        
        # StopPkt
        ttk.Label(sampling_control_frame, text="StopPkt:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.stop_pkt_var = tk.StringVar()
        ttk.Entry(sampling_control_frame, textvariable=self.stop_pkt_var, width=12).grid(row=2, column=0, padx=(0, 5))
        ttk.Button(sampling_control_frame, text="Enviar", command=self.send_stop_pkt).grid(row=2, column=1)
        
        # Columna 2 de Periféricos
        periph_col2 = ttk.Frame(periph_frame)
        periph_col2.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N))
        
        # Configuración muestreo
        sampling_config_frame = ttk.LabelFrame(periph_col2, text="Configuración Muestreo", padding="5")
        sampling_config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(sampling_config_frame, text="Fs (Hz):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.fs_var = tk.StringVar()
        ttk.Entry(sampling_config_frame, textvariable=self.fs_var, width=8).grid(row=0, column=1)
        
        ttk.Label(sampling_config_frame, text="Start Delay:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.start_delay_var = tk.StringVar()
        ttk.Entry(sampling_config_frame, textvariable=self.start_delay_var, width=8).grid(row=1, column=1)
        
        ttk.Button(sampling_config_frame, text="Enviar", command=self.send_sampling_config).grid(row=2, column=0, columnspan=2, pady=(5, 0))
        
        # Control características
        features_frame = ttk.LabelFrame(periph_col2, text="Control Características", padding="5")
        features_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Sensor Data
        sensor_frame = ttk.LabelFrame(features_frame, text="Sensor Data", padding="3")
        sensor_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(sensor_frame, text="ON", command=lambda: self.send_feature_control(0x01)).grid(row=0, column=0, padx=(0, 2))
        ttk.Button(sensor_frame, text="OFF", command=lambda: self.send_feature_control(0x02)).grid(row=0, column=1)
        
        # Exercise Detection
        exercise_frame = ttk.LabelFrame(features_frame, text="Exercise Detection", padding="3")
        exercise_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(exercise_frame, text="ON", command=lambda: self.send_feature_control(0x03)).grid(row=0, column=0, padx=(0, 2))
        ttk.Button(exercise_frame, text="OFF", command=lambda: self.send_feature_control(0x04)).grid(row=0, column=1)
        
        # Frame de estadísticas de sensores
        stats_frame = ttk.LabelFrame(main_frame, text="Estadísticas de Sensores", padding="10")
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Estadísticas por sensor en columnas
        for i in range(3):
            sensor_col = ttk.Frame(stats_frame)
            sensor_col.grid(row=0, column=i, sticky=(tk.W, tk.E, tk.N), padx=(0, 20))
            
            ttk.Label(sensor_col, text=f"Sensor {i}", font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=0, pady=(0, 5))
            
            ttk.Label(sensor_col, text="Último paquete:").grid(row=1, column=0, sticky=tk.W)
            setattr(self, f"last_packet_label_{i}", tk.StringVar(value="N/A"))
            ttk.Label(sensor_col, textvariable=getattr(self, f"last_packet_label_{i}")).grid(row=1, column=1, sticky=tk.W, padx=(5, 0))
            
            ttk.Label(sensor_col, text="Perdidos:").grid(row=2, column=0, sticky=tk.W)
            setattr(self, f"lost_packets_label_{i}", tk.StringVar(value="0"))
            ttk.Label(sensor_col, textvariable=getattr(self, f"lost_packets_label_{i}")).grid(row=2, column=1, sticky=tk.W, padx=(5, 0))
        
        # Botón para resetear contadores
        reset_btn_frame = ttk.Frame(stats_frame)
        reset_btn_frame.grid(row=0, column=3, sticky=(tk.W, tk.E, tk.N), padx=(20, 0))
        ttk.Button(reset_btn_frame, text="Resetear\nContadores", command=self.reset_counters).grid(row=0, column=0)
        
        # Área de logs expandida
        logs_frame = ttk.LabelFrame(main_frame, text="Logs del Sistema", padding="10")
        logs_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.logs_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, state=tk.DISABLED, height=20)
        self.logs_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Button(logs_frame, text="Limpiar Logs", command=self.clear_logs).grid(row=1, column=0, pady=(5, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="Desconectado")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configurar pesos para redimensionamiento automático
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)  # Los logs se expanden más
        commands_frame.columnconfigure(0, weight=1)
        commands_frame.columnconfigure(1, weight=1)
        central_frame.columnconfigure(0, weight=1)
        central_frame.columnconfigure(1, weight=1)
        periph_frame.columnconfigure(0, weight=1)
        periph_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def update_ports(self):
        """Actualiza la lista de puertos serie disponibles"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)
            
    def toggle_connection(self):
        """Conecta o desconecta del puerto serie"""
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()
            
    def connect(self):
        """Establece conexión con el puerto serie"""
        try:
            port = self.port_var.get()
            baud = int(self.baud_var.get())
            
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.005
            )
            
            self.is_connected = True
            self.connect_btn.config(text="Desconectar")
            self.status_var.set(f"Conectado a {port} @ {baud} baud")
            
            # Iniciar hilo de lectura
            self.stop_reading = False
            self.reading_thread = threading.Thread(target=self.read_serial_data, daemon=True)
            self.reading_thread.start()
            
            self.add_log("Conexión establecida correctamente")
            
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar: {str(e)}")
            
    def disconnect(self):
        """Cierra la conexión serie"""
        self.stop_reading = True
        self.is_connected = False
        
        # Detener localhost si está activo
        if self.sending_to_localhost:
            self.toggle_localhost()
        
        if self.serial_connection:
            self.serial_connection.close()
            
        self.connect_btn.config(text="Conectar")
        self.status_var.set("Desconectado")
        self.add_log("Conexión cerrada")
        
        # Detener guardado si está activo
        if self.saving_data:
            self.stop_saving()
        
    def read_serial_data(self):
        """Hilo para leer datos del puerto serie con parsing de paquetes"""
        while not self.stop_reading and self.is_connected:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    # Leer todos los bytes disponibles
                    data = self.serial_connection.read(self.serial_connection.in_waiting or 1)
                    
                    # Guardar datos raw si está habilitado
                    if self.saving_data and self.save_file:
                        self.save_file.write(data)
                        self.save_file.flush()
                    
                    # Procesar bytes para parsing de paquetes
                    for byte in data:
                        self.process_byte(byte)
                    
                    # Mostrar como texto si es legible (mantener funcionalidad original)
                    if self.printLogs:
                        try:
                            text_data = data.decode('utf-8', errors='ignore').strip()
                            if text_data and all(32 <= ord(c) <= 126 or c in '\r\n\t' for c in text_data):
                                self.add_log(f"{text_data}")
                        except:
                            pass
                    
            except Exception as e:
                self.add_log(f"Error leyendo datos: {str(e)}")
                break

    def process_byte(self, byte):
        """Procesa un byte para el parsing de paquetes"""
        if self.packet_state == 0:  # Buscando byte de inicio
            if byte == 0x7E:
                self.packet_buffer = bytearray([byte])
                self.packet_state = 1
        elif self.packet_state == 1:  # Leyendo paquete
            self.packet_buffer.append(byte)
            
            # Si tenemos el paquete completo
            if len(self.packet_buffer) == self.expected_packet_size:
                # Verificar byte de fin
                if byte == 0x7F:
                    self.process_complete_packet(self.packet_buffer)
                else:
                    # Paquete inválido, buscar nuevo inicio desde el segundo byte
                    self.search_new_start()
                self.packet_state = 0
                self.packet_buffer.clear()
            elif len(self.packet_buffer) > self.expected_packet_size:
                # Buffer demasiado grande, buscar nuevo inicio
                self.search_new_start()
                self.packet_state = 0
                self.packet_buffer.clear()

    def search_new_start(self):
        """Busca un nuevo byte de inicio en el buffer actual"""
        for i in range(1, len(self.packet_buffer)):
            if self.packet_buffer[i] == 0x7E:
                self.packet_buffer = self.packet_buffer[i:]
                self.packet_state = 1
                return
        # No se encontró nuevo inicio
        self.packet_buffer.clear()
        self.packet_state = 0

    def process_complete_packet(self, packet):
        """Procesa un paquete completo válido"""
        try:
            if len(packet) != 50:
                return
                
            # Extraer campos del paquete
            # [0x7E][Len][Tipo][Nodo][Payload 40 bytes][Checksum][0x7F]
            node_id = packet[3]
            
            # Validar que sea un nodo válido (0x00, 0x01, 0x02)
            if node_id not in [0x00, 0x01, 0x02]:
                return
            
            # Extraer número de paquete (primeros 4 bytes del payload en little endian)
            payload_start = 4
            packet_number = struct.unpack('<I', packet[payload_start:payload_start + 4])[0]
            
            # Actualizar estadísticas
            self.update_packet_stats(node_id, packet_number)
            
            # Si está activo el envío a localhost, guardar fragmento
            if self.sending_to_localhost:
                # Fragmento: [Nodo][4 bytes No.Paquete][8 bytes variables] = 13 bytes
                fragment = bytearray()
                fragment.append(node_id)  # Byte nodo
                fragment.extend(packet[payload_start:payload_start + 12])  # 4 bytes paquete + 8 bytes variables
                
                # self.sensor_fragments[node_id] = fragment
                # self.sensor_data_received[node_id] = True
                if self.sending_to_localhost:
                    self.udp_socket.sendto(fragment, ('localhost', 4000))

        except Exception as e:
            self.add_log(f"Error procesando paquete: {str(e)}")

    def update_packet_stats(self, node_id, packet_number):
        """Actualiza estadísticas de paquetes por sensor"""
        try:
            # Si es el primer paquete de este sensor
            if self.last_packet_numbers[node_id] is None:
                self.last_packet_numbers[node_id] = packet_number
            else:
                # Calcular paquetes perdidos
                expected = (self.last_packet_numbers[node_id] + 1) & 0xFFFFFFFF
                if packet_number != expected:
                    if packet_number > expected:
                        lost = packet_number - expected
                    else:
                        # Handle rollover
                        lost = (0xFFFFFFFF - expected) + packet_number + 1
                    self.lost_packets_count[node_id] += lost
                
                self.last_packet_numbers[node_id] = packet_number

                if packet_number == self.stop_pkt_no: self.add_log(f"Fin {node_id}")
                
        except Exception as e:
            self.add_log(f"Error actualizando estadísticas: {str(e)}")

    def toggle_localhost(self):
        """Toggle para activar/desactivar envío a localhost"""
        if not self.sending_to_localhost:
            self.start_localhost()
        else:
            self.stop_localhost()

    def start_localhost(self):
        """Inicia el envío de datos a localhost"""
        try:
            # Crear socket UDP
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            self.sending_to_localhost = True
            self.localhost_btn.config(text="Stop Localhost")
            
            # Iniciar hilo de envío a localhost
            self.stop_localhost_thread = False
            # self.localhost_thread = threading.Thread(target=self.localhost_sender_thread, daemon=True)
            # self.localhost_thread.start()
            
            self.add_log("Envío a localhost:4001 activado")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error iniciando localhost: {str(e)}")
            self.sending_to_localhost = False

    def stop_localhost(self):
        """Detiene el envío de datos a localhost"""
        self.stop_localhost_thread = True
        self.sending_to_localhost = False
        self.localhost_btn.config(text="Start Localhost")
        
        if self.udp_socket:
            self.udp_socket.close()
            self.udp_socket = None
            
        self.add_log("Envío a localhost detenido")

    def localhost_sender_thread(self):
        """Hilo que envía datos a localhost a 30Hz"""
        last_stats_update = time.time()
        
        while not self.stop_localhost_thread and self.sending_to_localhost:
            try:
                start_time = time.time()
                
                # Verificar si tenemos al menos un sensor con datos
                if any(self.sensor_data_received):
                    # Crear paquete de 39 bytes concatenando los 3 fragmentos
                    packet = bytearray()
                    
                    for i in range(3):
                        if self.sensor_data_received[i]:
                            packet.extend(self.sensor_fragments[i])
                        else:
                            # Rellenar con ceros si no hay datos del sensor
                            packet.extend(bytearray(13))  # 13 bytes de ceros
                    
                    # Enviar por UDP a localhost:4001
                    if self.udp_socket and len(packet) == 39:
                        self.udp_socket.sendto(packet, ('localhost', 4000))
                
                # Actualizar estadísticas cada segundo
                current_time = time.time()
                if current_time - last_stats_update >= 1.0:
                    self.update_stats_display()
                    last_stats_update = current_time
                
                # Mantener 30Hz (33.33ms por iteración)
                elapsed = time.time() - start_time
                sleep_time = max(0, 1.0/30.0 - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                self.add_log(f"Error en hilo localhost: {str(e)}")
                break

    def update_stats_display(self):
        """Actualiza las estadísticas en la interfaz"""
        def update_ui():
            for i in range(3):
                # Actualizar último número de paquete
                last_packet = self.last_packet_numbers[i]
                if last_packet is not None:
                    getattr(self, f"last_packet_label_{i}").set(str(last_packet))
                else:
                    getattr(self, f"last_packet_label_{i}").set("N/A")
                
                # Actualizar paquetes perdidos
                getattr(self, f"lost_packets_label_{i}").set(str(self.lost_packets_count[i]))
        
        self.root.after(0, update_ui)

    def reset_counters(self):
        """Resetea los contadores de paquetes perdidos"""
        for i in range(3):
            self.lost_packets_count[i] = 0

        self.last_packet_numbers = [None, None, None]  # Último número de paquete recibido
        self.sensor_data_received = [False, False, False] # Flag para saber si hemos recibido datos

        self.update_stats_display()
        self.add_log("Contadores de paquetes perdidos reseteados")
    
    def get_periph_idx(self):
        """Obtiene el IDX del periférico (0xFF si está vacío)"""
        idx_str = self.periph_idx_var.get().strip()
        if not idx_str:
            return 0xFF
        
        idx_str = idx_str.replace('0x', '')
        return int(idx_str, 16) & 0xFF
    
    def send_raw_hex(self, hex_message):
        """Envía un mensaje hex directo"""
        if not self.is_connected:
            messagebox.showwarning("Advertencia", "No hay conexión establecida")
            return
            
        try:
            hex_message = hex_message.replace(' ', '').replace('0x', '')
            message = bytes.fromhex(hex_message)
            self.serial_connection.write(message)
            hex_display = ' '.join([f'{b:02X}' for b in message])
            self.add_log(f"[TX] {hex_display}")
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando mensaje: {str(e)}")
    
    def toggle_scan(self):
        """Toggle del control de scan"""
        if not self.scan_active:
            self.send_raw_hex("7E 00 20 20 7F")
            self.scan_btn.config(text="Stop Scan")
            self.scan_active = True
        else:
            self.send_raw_hex("7E 00 21 21 7F")
            self.scan_btn.config(text="Start Scan")
            self.scan_active = False
        
    def send_disconnect(self):
        """Envía comando Disconnect (0xFF si está vacío)"""
        try:
            hex_value = self.disconnect_var.get().strip()
            if not hex_value:
                value_byte = 0xFF
            else:
                hex_value = hex_value.replace('0x', '')
                value_byte = int(hex_value, 16) & 0xFF
            
            checksum = 0x22 ^ value_byte
            message = f"7E 01 22 {value_byte:02X} {checksum:02X} 7F"
            self.send_raw_hex(message)
            
        except ValueError:
            messagebox.showerror("Error", "Valor hex inválido")
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando disconnect: {str(e)}")
    
    def send_params_config(self):
        """Envía configuración de parámetros"""
        try:
            fields = [
                (self.phy_var.get(), "PHY"),
                (self.conn_interval_var.get(), "Connection Interval"),
                (self.latency_var.get(), "Latency"),
                (self.timeout_var.get(), "Time Out"),
                (self.data_length_var.get(), "Data Length"),
                (self.txrx_time_var.get(), "Tx/Rx Time")
            ]
            
            for value, name in fields:
                if not value.strip():
                    messagebox.showwarning("Advertencia", f"Debe llenar el campo {name}")
                    return
            
            phy = int(self.phy_var.get()) & 0xFF
            conn_interval = int(self.conn_interval_var.get()) & 0xFFFF
            latency = int(self.latency_var.get()) & 0xFFFF
            timeout = int(self.timeout_var.get()) & 0xFFFF
            data_length = int(self.data_length_var.get()) & 0xFFFF
            txrx_time = int(self.txrx_time_var.get()) & 0xFFFF
            
            payload = struct.pack('<BHHHHH', phy, conn_interval, latency, timeout, data_length, txrx_time)
            
            checksum = 0x23
            for byte in payload:
                checksum ^= byte
            
            message = bytes([0x7E, 0x0B, 0x23]) + payload + bytes([checksum, 0x7F])
            self.serial_connection.write(message)
            
            hex_msg = ' '.join([f'{b:02X}' for b in message])
            self.add_log(f"[TX] Config Parámetros: {hex_msg}")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Error en valores: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando configuración: {str(e)}")
    
    def send_print_logs(self):
        """Envía comando PrintLogs (0x19)"""
        self.send_raw_hex("7E 00 19 19 7F")
        if self.printLogs: self.printLogs = False
        else: self.printLogs = True
    
    def send_tx_uart(self):
        """Envía comando TxUART (0x18)"""
        self.send_raw_hex("7E 00 18 18 7F")
    
    def start_sampling(self):
        """Envía comando Start Sampling a periférico"""
        try:
            idx = self.get_periph_idx()
            checksum = 0x30 ^ idx ^ 0xAA
            message = f"7E 02 30 {idx:02X} AA {checksum:02X} 7F"
            self.send_raw_hex(message)
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando start sampling: {str(e)}")
    
    def stop_sampling(self):
        """Envía comando Stop Sampling a periférico"""
        try:
            idx = self.get_periph_idx()
            checksum = 0x30 ^ idx ^ 0xFF
            message = f"7E 02 30 {idx:02X} FF {checksum:02X} 7F"
            self.send_raw_hex(message)
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando stop sampling: {str(e)}")
    
    def send_stop_pkt(self):
        """Envía comando StopPkt con formato 7E 05 25 [idx StopPkt-4B] CheckSum 7F"""
        try:
            stop_pkt_str = self.stop_pkt_var.get().strip()
            if not stop_pkt_str:
                messagebox.showwarning("Advertencia", "Debe especificar StopPkt")
                return
            
            idx = self.get_periph_idx()
            self.stop_pkt_no = int(stop_pkt_str)
            stop_pkt = int(stop_pkt_str) & 0xFFFFFFFF  # uint32
            
            # Payload: idx (1B) + StopPkt (4B) en little endian
            payload = struct.pack('<BI', idx, stop_pkt)
            
            checksum = 0x25
            for byte in payload:
                checksum ^= byte
            
            message = bytes([0x7E, 0x05, 0x25]) + payload + bytes([checksum, 0x7F])
            self.serial_connection.write(message)
            
            hex_msg = ' '.join([f'{b:02X}' for b in message])
            self.add_log(f"[TX] StopPkt: {hex_msg}")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Error en valor StopPkt: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando StopPkt: {str(e)}")
    
    def send_sampling_config(self):
        """Envía configuración de muestreo a periférico"""
        try:
            fs_str = self.fs_var.get().strip()
            delay_str = self.start_delay_var.get().strip()
            
            if not fs_str or not delay_str:
                messagebox.showwarning("Advertencia", "Debe llenar Fs y Start Delay")
                return
            
            idx = self.get_periph_idx()
            fs = int(fs_str) & 0xFFFF
            start_delay = int(delay_str) & 0xFFFF
            
            # Payload en little endian: idx + fs(2B) + start_delay(2B)
            payload = struct.pack('<BHH', idx, fs, start_delay)
            
            checksum = 0x24
            for byte in payload:
                checksum ^= byte
            
            message = bytes([0x7E, 0x05, 0x24]) + payload + bytes([checksum, 0x7F])
            self.serial_connection.write(message)
            
            hex_msg = ' '.join([f'{b:02X}' for b in message])
            self.add_log(f"[TX] Config Muestreo: {hex_msg}")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Error en valores: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando config muestreo: {str(e)}")
    
    def send_feature_control(self, command):
        """Envía comando de control de características a periférico"""
        try:
            idx = self.get_periph_idx()
            checksum = 0x30 ^ idx ^ command
            message = f"7E 02 30 {idx:02X} {command:02X} {checksum:02X} 7F"
            self.send_raw_hex(message)
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando control de características: {str(e)}")
            
    def send_command(self):
        """Envía un comando manual en hex"""
        if not self.is_connected:
            messagebox.showwarning("Advertencia", "No hay conexión establecida")
            return
            
        try:
            cmd_type_str = self.cmd_type_var.get().strip()
            payload_str = self.payload_var.get().strip()
            
            if not cmd_type_str:
                messagebox.showwarning("Advertencia", "Debe especificar el tipo de comando en hex")
                return
                
            cmd_type_str = cmd_type_str.replace('0x', '')
            cmd_type = int(cmd_type_str, 16) & 0xFF
            
            if payload_str:
                payload_str = payload_str.replace('0x', '').replace(' ', '')
                payload = bytes.fromhex(payload_str)
            else:
                payload = b''
                
            payload_len = len(payload)
            checksum = cmd_type
            for byte in payload:
                checksum ^= byte
                
            message = bytes([0x7E, payload_len, cmd_type]) + payload + bytes([checksum, 0x7F])
            self.serial_connection.write(message)
            
            hex_msg = ' '.join([f'{b:02X}' for b in message])
            self.add_log(f"[TX] Comando manual: {hex_msg}")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Error en formato hex: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando comando: {str(e)}")
    
    def start_saving(self):
        """Inicia el guardado de datos en archivo binario con timestamp"""
        try:
            # Generar nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{timestamp}.bin"
            
            self.save_file = open(filename, 'wb')
            self.saving_data = True
            self.save_btn.config(state="disabled")
            self.stop_save_btn.config(state="normal")
            self.save_status_var.set(f"Guardando: {filename}")
            self.add_log(f"Iniciado guardado en: {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error iniciando guardado: {str(e)}")
    
    def stop_saving(self):
        """Detiene el guardado de datos"""
        if self.saving_data and self.save_file:
            self.save_file.close()
            self.save_file = None
            
        self.saving_data = False
        self.save_btn.config(state="normal")
        self.stop_save_btn.config(state="disabled")
        self.save_status_var.set("No guardando")
        self.add_log("Guardado de datos detenido")
            
    def add_log(self, message):
        """Agrega un mensaje al área de logs (no editable)"""
        def update_logs():
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.logs_text.config(state=tk.NORMAL)
            self.logs_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.logs_text.see(tk.END)
            self.logs_text.config(state=tk.DISABLED)
            
        self.root.after(0, update_logs)
        
    def clear_logs(self):
        """Limpia el área de logs"""
        self.logs_text.config(state=tk.NORMAL)
        self.logs_text.delete(1.0, tk.END)
        self.logs_text.config(state=tk.DISABLED)
        
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        if self.sending_to_localhost:
            self.stop_localhost()
        if self.is_connected:
            self.disconnect()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = WSNInterface(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()