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
        self.root.geometry("900x700")
        
        # Variables de conexión
        self.serial_connection = None
        self.is_connected = False
        self.reading_thread = None
        self.stop_reading = False
        
        # Variables para guardado de datos
        self.saving_data = False
        self.save_file = None
        
        self.setup_ui()
        self.update_ports()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuración de conexión
        conn_frame = ttk.LabelFrame(main_frame, text="Configuración de Conexión", padding="10")
        conn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
        
        ttk.Button(conn_frame, text="Actualizar Puertos", command=self.update_ports).grid(row=0, column=5, padx=(5, 0))
        
        # Frame expandido de envío de comandos
        send_frame = ttk.LabelFrame(main_frame, text="Comandos WSN", padding="10")
        send_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Comando manual
        manual_frame = ttk.LabelFrame(send_frame, text="Comando Manual", padding="5")
        manual_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(manual_frame, text="Tipo (hex):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.cmd_type_var = tk.StringVar()
        cmd_type_entry = ttk.Entry(manual_frame, textvariable=self.cmd_type_var, width=10)
        cmd_type_entry.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(manual_frame, text="Payload (hex):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.payload_var = tk.StringVar()
        payload_entry = ttk.Entry(manual_frame, textvariable=self.payload_var, width=30)
        payload_entry.grid(row=0, column=3, padx=(0, 10))
        
        ttk.Button(manual_frame, text="Enviar", command=self.send_command).grid(row=0, column=4)
        
        # Botones de scan
        scan_frame = ttk.LabelFrame(send_frame, text="Control de Scan", padding="5")
        scan_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(scan_frame, text="Start Scan", command=self.start_scan).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(scan_frame, text="Stop Scan", command=self.stop_scan).grid(row=0, column=1)
        
        # Disconnect con textbox
        disconnect_frame = ttk.LabelFrame(send_frame, text="Disconnect", padding="5")
        disconnect_frame.grid(row=1, column=2, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10), padx=(10, 0))
        
        ttk.Label(disconnect_frame, text="Valor (hex):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.disconnect_var = tk.StringVar()
        disconnect_entry = ttk.Entry(disconnect_frame, textvariable=self.disconnect_var, width=10)
        disconnect_entry.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(disconnect_frame, text="Disconnect", command=self.send_disconnect).grid(row=0, column=2)
        
        # Configuración PHY
        phy_frame = ttk.LabelFrame(send_frame, text="Configuración PHY", padding="5")
        phy_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # PHY (1 byte)
        ttk.Label(phy_frame, text="PHY:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.phy_var = tk.StringVar()
        ttk.Entry(phy_frame, textvariable=self.phy_var, width=8).grid(row=0, column=1, padx=(0, 10))
        
        # Connection Interval (2 bytes)
        ttk.Label(phy_frame, text="Conn Interval:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.conn_interval_var = tk.StringVar()
        ttk.Entry(phy_frame, textvariable=self.conn_interval_var, width=8).grid(row=0, column=3, padx=(0, 10))
        
        # Latency (2 bytes)
        ttk.Label(phy_frame, text="Latency:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.latency_var = tk.StringVar()
        ttk.Entry(phy_frame, textvariable=self.latency_var, width=8).grid(row=0, column=5, padx=(0, 10))
        
        # Time Out (2 bytes)
        ttk.Label(phy_frame, text="Time Out:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.timeout_var = tk.StringVar()
        ttk.Entry(phy_frame, textvariable=self.timeout_var, width=8).grid(row=1, column=1, padx=(0, 10))
        
        # Data Length (2 bytes)
        ttk.Label(phy_frame, text="Data Length:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.data_length_var = tk.StringVar()
        ttk.Entry(phy_frame, textvariable=self.data_length_var, width=8).grid(row=1, column=3, padx=(0, 10))
        
        # Tx/Rx Time (2 bytes)
        ttk.Label(phy_frame, text="Tx/Rx Time:").grid(row=1, column=4, sticky=tk.W, padx=(0, 5))
        self.txrx_time_var = tk.StringVar()
        ttk.Entry(phy_frame, textvariable=self.txrx_time_var, width=8).grid(row=1, column=5, padx=(0, 10))
        
        # Botón para enviar configuración PHY
        ttk.Button(phy_frame, text="Enviar Config PHY", command=self.send_phy_config).grid(row=2, column=0, columnspan=6, pady=(10, 0))
        
        # Botones de guardado
        save_frame = ttk.LabelFrame(send_frame, text="Guardado de Datos", padding="5")
        save_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.save_btn = ttk.Button(save_frame, text="Save bin", command=self.start_saving)
        self.save_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_save_btn = ttk.Button(save_frame, text="End Save", command=self.stop_saving, state="disabled")
        self.stop_save_btn.grid(row=0, column=1)
        
        self.save_status_var = tk.StringVar(value="No guardando")
        ttk.Label(save_frame, textvariable=self.save_status_var).grid(row=0, column=2, padx=(20, 0))
        
        # Área expandida de logs (eliminando datos binarios)
        logs_frame = ttk.LabelFrame(main_frame, text="Logs del Sistema", padding="10")
        logs_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.logs_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD)
        self.logs_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Button(logs_frame, text="Limpiar Logs", command=self.clear_logs).grid(row=1, column=0, pady=(5, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="Desconectado")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configurar pesos para redimensionamiento automático
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # Los logs se expanden
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
                timeout=0.1
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
        """Hilo para leer datos del puerto serie continuamente"""
        buffer = b''
        
        while not self.stop_reading and self.is_connected:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    buffer += data
                    
                    # Guardar datos raw si está habilitado
                    if self.saving_data and self.save_file:
                        self.save_file.write(data)
                        self.save_file.flush()
                    
                    # Procesar buffer para mostrar logs
                    buffer = self.process_buffer(buffer)
                    
                time.sleep(0.01)  # Pequeña pausa para no saturar CPU
                
            except Exception as e:
                self.add_log(f"Error leyendo datos: {str(e)}")
                break
                
    def process_buffer(self, buffer):
        """Procesa el buffer separando logs de datos binarios"""
        remaining_buffer = b''
        i = 0
        
        while i < len(buffer):
            # Buscar inicio de mensaje binario (0x7E)
            if buffer[i] == 0x7E:
                # Intentar parsear mensaje binario
                msg_end = self.find_binary_message_end(buffer[i:])
                if msg_end != -1:
                    binary_msg = buffer[i:i+msg_end+1]
                    self.process_binary_message(binary_msg)
                    i += msg_end + 1
                else:
                    # Mensaje incompleto, guardar para siguiente iteración
                    remaining_buffer = buffer[i:]
                    break
            else:
                # Buscar línea de log (texto terminado en \n o \r\n)
                line_end = self.find_line_end(buffer[i:])
                if line_end != -1:
                    try:
                        log_line = buffer[i:i+line_end].decode('utf-8', errors='ignore')
                        if log_line.strip():  # Solo mostrar líneas no vacías
                            self.add_log(log_line.strip())
                        i += line_end + 1
                    except:
                        i += 1
                else:
                    # Línea incompleta, guardar para siguiente iteración
                    remaining_buffer = buffer[i:]
                    break
                    
        return remaining_buffer
        
    def find_binary_message_end(self, data):
        """Encuentra el final de un mensaje binario (0x7F)"""
        if len(data) < 2:
            return -1
            
        try:
            # Verificar que tenemos al menos: inicio + len + tipo + checksum + fin
            if len(data) < 5:
                return -1
                
            payload_len = data[1]  # Segundo byte es la longitud del payload
            expected_total_len = 5 + payload_len  # inicio + len + tipo + payload + checksum + fin
            
            if len(data) >= expected_total_len and data[expected_total_len-1] == 0x7F:
                return expected_total_len - 1
                
        except:
            pass
            
        return -1
        
    def find_line_end(self, data):
        """Encuentra el final de una línea de texto"""
        for i, byte in enumerate(data):
            if byte in [ord('\n'), ord('\r')]:
                return i
        return -1
        
    def process_binary_message(self, msg):
        """Procesa un mensaje binario completo y lo muestra como log"""
        if len(msg) < 5:
            return
            
        try:
            start_byte = msg[0]
            payload_len = msg[1]
            cmd_type = msg[2]
            payload = msg[3:3+payload_len]
            checksum = msg[3+payload_len]
            end_byte = msg[3+payload_len+1]
            
            # Verificar checksum
            calculated_checksum = cmd_type
            for byte in payload:
                calculated_checksum ^= byte
                
            checksum_status = "✓" if calculated_checksum == checksum else "✗"
            
            # Mostrar en logs como mensaje binario recibido
            hex_msg = ' '.join([f'{b:02X}' for b in msg])
            log_info = f"[BINARY] Tipo: 0x{cmd_type:02X}, Payload: {payload.hex().upper()}, Checksum: {checksum_status} | Raw: {hex_msg}"
            self.add_log(log_info)
            
        except Exception as e:
            self.add_log(f"Error procesando mensaje binario: {str(e)}")
    
    def hex_to_bytes(self, hex_string):
        """Convierte string hex a bytes"""
        hex_string = hex_string.replace(' ', '').replace('0x', '')
        return bytes.fromhex(hex_string)
    
    def send_raw_hex(self, hex_message):
        """Envía un mensaje hex directo"""
        if not self.is_connected:
            messagebox.showwarning("Advertencia", "No hay conexión establecida")
            return
            
        try:
            message = self.hex_to_bytes(hex_message)
            self.serial_connection.write(message)
            self.add_log(f"Enviado: {hex_message}")
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando mensaje: {str(e)}")
    
    def start_scan(self):
        """Envía comando Start Scan"""
        self.send_raw_hex("7E 00 20 20 7F")
        
    def stop_scan(self):
        """Envía comando Stop Scan"""
        self.send_raw_hex("7E 00 21 21 7F")
        
    def send_disconnect(self):
        """Envía comando Disconnect con valor del textbox"""
        try:
            hex_value = self.disconnect_var.get().strip()
            if not hex_value:
                messagebox.showwarning("Advertencia", "Debe especificar un valor hex")
                return
                
            # Remover 0x si existe
            hex_value = hex_value.replace('0x', '')
            
            # Calcular checksum: 22 XOR hex_value
            value_byte = int(hex_value, 16)
            checksum = 0x22 ^ value_byte
            
            message = f"7E 01 22 {value_byte:02X} {checksum:02X} 7F"
            self.send_raw_hex(message)
            
        except ValueError:
            messagebox.showerror("Error", "Valor hex inválido")
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando disconnect: {str(e)}")
    
    def send_phy_config(self):
        """Envía configuración PHY con formato little endian"""
        try:
            # Validar que todos los campos tengan valores
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
            
            # Convertir valores a enteros
            phy = int(self.phy_var.get())
            conn_interval = int(self.conn_interval_var.get())
            latency = int(self.latency_var.get())
            timeout = int(self.timeout_var.get())
            data_length = int(self.data_length_var.get())
            txrx_time = int(self.txrx_time_var.get())
            
            # Validar rangos
            if not (0 <= phy <= 255):
                raise ValueError("PHY debe estar entre 0-255")
            if not all(0 <= val <= 65535 for val in [conn_interval, latency, timeout, data_length, txrx_time]):
                raise ValueError("Los valores de 2 bytes deben estar entre 0-65535")
            
            # Construir payload en little endian
            payload = struct.pack('<BHHHHH', phy, conn_interval, latency, timeout, data_length, txrx_time)
            
            # Calcular checksum
            checksum = 0x23  # Tipo de comando
            for byte in payload:
                checksum ^= byte
            
            # Construir mensaje completo
            message = bytes([0x7E, 0x0B, 0x23]) + payload + bytes([checksum, 0x7F])
            
            # Enviar
            self.serial_connection.write(message)
            
            hex_msg = ' '.join([f'{b:02X}' for b in message])
            self.add_log(f"Config PHY enviada: {hex_msg}")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Error en valores: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando configuración PHY: {str(e)}")
            
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
                
            # Convertir tipo de comando (acepta hex directamente)
            cmd_type_str = cmd_type_str.replace('0x', '')
            cmd_type = int(cmd_type_str, 16)
            
            # Convertir payload
            if payload_str:
                payload_str = payload_str.replace('0x', '').replace(' ', '')
                payload = bytes.fromhex(payload_str)
            else:
                payload = b''
                
            # Construir mensaje
            payload_len = len(payload)
            checksum = cmd_type
            for byte in payload:
                checksum ^= byte
                
            message = bytes([0x7E, payload_len, cmd_type]) + payload + bytes([checksum, 0x7F])
            
            # Enviar mensaje
            self.serial_connection.write(message)
            
            # Log del envío
            hex_msg = ' '.join([f'{b:02X}' for b in message])
            self.add_log(f"Comando enviado: {hex_msg}")
            
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
                self.save_status_var.set(f"Guardando en: {filename}")
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
        """Agrega un mensaje al área de logs"""
        def update_logs():
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.logs_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.logs_text.see(tk.END)
            
        self.root.after(0, update_logs)
        
    def clear_logs(self):
        """Limpia el área de logs"""
        self.logs_text.delete(1.0, tk.END)
        
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