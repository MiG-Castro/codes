import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
import struct
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
        
        # Variables para guardado de datos
        self.saving_data = False
        self.save_file = None
        
        # Control de scan
        self.scan_active = False
        
        self.setup_ui()
        self.update_ports()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuración de conexión (sin autoreconexión)
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
        
        # Guardado de datos
        save_subframe = ttk.LabelFrame(control_frame, text="Guardado", padding="3")
        save_subframe.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.save_btn = ttk.Button(save_subframe, text="Save bin", command=self.start_saving)
        self.save_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_save_btn = ttk.Button(save_subframe, text="End Save", command=self.stop_saving, state="disabled")
        self.stop_save_btn.grid(row=0, column=1)
        
        self.save_status_var = tk.StringVar(value="No guardando")
        ttk.Label(save_subframe, textvariable=self.save_status_var, font=('TkDefaultFont', 8)).grid(row=1, column=0, columnspan=2)
        
        # SECCIÓN PERIFÉRICOS con dos columnas
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
        
        # Área de logs expandida (más grande)
        logs_frame = ttk.LabelFrame(main_frame, text="Logs del Sistema", padding="10")
        logs_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.logs_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, state=tk.DISABLED, height=25)
        self.logs_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Button(logs_frame, text="Limpiar Logs", command=self.clear_logs).grid(row=1, column=0, pady=(5, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="Desconectado")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configurar pesos para redimensionamiento automático
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)  # Los logs se expanden más
        commands_frame.columnconfigure(0, weight=1)
        commands_frame.columnconfigure(1, weight=1)
        central_frame.columnconfigure(0, weight=1)
        central_frame.columnconfigure(1, weight=1)
        periph_frame.columnconfigure(0, weight=1)
        periph_frame.columnconfigure(1, weight=1)
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
        
        if self.serial_connection:
            self.serial_connection.close()
            
        self.connect_btn.config(text="Conectar")
        self.status_var.set("Desconectado")
        self.add_log("Conexión cerrada")
        
        # Detener guardado si está activo
        if self.saving_data:
            self.stop_saving()
        
    def read_serial_data(self):
        """Hilo simplificado para leer datos del puerto serie - imprime todo"""
        while not self.stop_reading and self.is_connected:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    # Leer todos los bytes disponibles
                    data = self.serial_connection.read(self.serial_connection.in_waiting or 1)
                    
                    # Guardar datos raw si está habilitado
                    if self.saving_data and self.save_file:
                        self.save_file.write(data)
                        self.save_file.flush()
                    
                    # Intentar mostrar como texto si es legible
                    try:
                        text_data = data.decode('utf-8', errors='ignore').strip()
                        if text_data and all(32 <= ord(c) <= 126 or c in '\r\n\t' for c in text_data):
                            self.add_log(f"{text_data}")
                    except:
                        pass
                    
                # time.sleep(0.01)
                
            except Exception as e:
                self.add_log(f"Error leyendo datos: {str(e)}")
                break
    
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
        """Inicia el guardado de datos en archivo binario"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".bin",
                filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
            )
            
            if filename:
                self.save_file = open(filename, 'wb')
                self.saving_data = True
                self.save_btn.config(state="disabled")
                self.stop_save_btn.config(state="normal")
                self.save_status_var.set(f"Guardando: {filename.split('/')[-1]}")
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