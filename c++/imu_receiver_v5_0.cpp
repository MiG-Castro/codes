#include <iostream>
#include <thread>
#include <mutex>
#include <queue>
#include <vector>
#include <cstring>
#include <atomic>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <ctime>
#include <cmath>
#include <cstdio>
// Windows headers
#include <winsock2.h>
#include <windows.h>
#include <ws2tcpip.h>

// ============================================================================
// CONSTANTES Y ESTRUCTURAS
// ============================================================================
#define NUM_PERIPHERALS 4
#define BUFFER_SIZE 768
#define SAMPLES_PER_PACKET 3

#define PKT_START_BYTE 0x7E
#define PKT_END_BYTE   0x7F
#define MSG_TYPE_SENSOR_DATA 0x60

#define ACC_LSB_TO_MS2 100.0f
#define GYRO_LSB_TO_DPS 16.0f

struct IMUSample {
    int16_t quat[4];
    int16_t acc[3];
    int16_t gyro[3];
    bool valid;
};

struct IMUSampleUDP {
    uint8_t peripheral_id;
    uint16_t sample_num;
    IMUSample sample;
};

struct ProcessedSampleUDP {
    int sample_num;       // Usamos int para el índice global
    float gyro[3];        // Ya en grados/s o rad/s
    float acc[3];         // Ya en m/s2 o g
};

struct PacketTracker {
    uint8_t last_packet_num;
    bool first_packet;
    PacketTracker() : last_packet_num(255), first_packet(true) {}
};

// ============================================================================
// FUNCIONES AUXILIARES
// ============================================================================
int inet_pton_compat(int af, const char* src, void* dst) {
    if (af == AF_INET) {
        unsigned long addr = inet_addr(src);
        if (addr == INADDR_NONE) return 0;
        memcpy(dst, &addr, sizeof(addr));
        return 1;
    }
    return -1;
}

struct tm* localtime_compat(const time_t* timer) {
    return localtime(timer);
}

FILE* fopen_compat(const char* filename, const char* mode) {
    return fopen(filename, mode);
}

// ============================================================================
// Perceptron Multicapa
// ============================================================================
typedef struct {
    double SumEG[3];
    double SumEA[3];
    double NS;
} Attb;

typedef struct {
    double MinEG[3];
    double MaxEG[3];
    double MinEA[3];
    double MaxEA[3];
    double MinNS;
    double MaxNS;
} MinMax;

const MinMax r = {
    .MinEG = {1121, 102463, 2398},
    .MaxEG = {882866, 1737554, 423835},
    .MinEA = {0.03, 23.99, 0.13},
    .MaxEA = {112.77, 279.07, 56.48},
    .MinNS = 32.0,
    .MaxNS = 302.0
};

double sigmoid(double x) {return 1.0 / (1.0 + exp(-x));}

double norm(double input, double min, double max) {
    // Protección para evitar división por cero
    if (max - min == 0) return 0.0;
    double resultado = 2.0f * ((input - min) / (max - min)) - 1.0;
    // En caso de valor maximo/minimo inesperado
    if (resultado > 1.0f) resultado = 1.0f;
    if (resultado < -1.0f) resultado = -1.0f;
    return resultado;
}

const double Em_to_Eg = 1.0/ (9.81*9.81);

// bien_realizado - Node 0, mal_realizado - Node 1: Threshold, n2, n3, n4, n5
const double n0[5] = {-4.6128596494187395, 7.271962069696998, 9.391451037779122, -13.609032353445063, -15.442785307567272};
const double n1[5] = {4.6128596494187395, -7.271962069696998, -9.391451037779122, 13.609032353445063, 15.442785307567272};

// PESOS - NODES
const double n02_Th = -4.044551371029093;
const double n02_EG[3] = {-1.9533412516657682, 2.1117797732832364, 3.7008738089473177};
const double n02_EA[3] = {-4.05613984365648, -9.417971488447751, -0.22316064148245005};
const double n02_NS = 17.39799805351816;

const double n03_Th = -10.648564467740147;
const double n03_EG[3] = {-3.029163894460441, 11.538919737723264, 7.246293988389006};
const double n03_EA[3] = {-13.618617921939457, -2.711086966758214, -11.505836577972191};
const double n03_NS = 13.127867959396218;

const double n04_Th = 7.7168417583773765;
const double n04_EG[3] = {-5.558649228752904, 12.61148100606476, 6.910973683412792};
const double n04_EA[3] = {9.284871254321937, -2.9550209742199423, -5.512144389008965};
const double n04_NS = 0.454554356133417;

const double n05_Th = 7.715367362971807;
const double n05_EG[3] = {4.568097192057056, 11.140464063583996, -10.895180368580245};
const double n05_EA[3] = {7.02440611674875, -1.1960592176519014, 5.185917103657688};
const double n05_NS = 7.081514573276;

int mlp_classifier(Attb in) {
    // NORMALIZAR ENTRADAS (Rango -1 a 1)
    in.SumEG[0] = norm(in.SumEG[0], r.MinEG[0], r.MaxEG[0]);
    in.SumEG[1] = norm(in.SumEG[1], r.MinEG[1], r.MaxEG[1]);
    in.SumEG[2] = norm(in.SumEG[2], r.MinEG[2], r.MaxEG[2]);
    in.SumEA[0] = norm(in.SumEA[0] * Em_to_Eg, r.MinEA[0], r.MaxEA[0]);
    in.SumEA[1] = norm(in.SumEA[1] * Em_to_Eg, r.MinEA[1], r.MaxEA[1]);
    in.SumEA[2] = norm(in.SumEA[2] * Em_to_Eg, r.MinEA[2], r.MaxEA[2]);
    in.NS = norm(in.NS, r.MinNS, r.MaxNS);

    double out02 = in.SumEG[0]*n02_EG[0] + in.SumEG[1]*n02_EG[1] + in.SumEG[2]*n02_EG[2]
                 + in.SumEA[0]*n02_EA[0] + in.SumEA[1]*n02_EA[1] + in.SumEA[2]*n02_EA[2] 
                 + in.NS*n02_NS + n02_Th;
    out02 = sigmoid(out02);

    double out03 = in.SumEG[0]*n03_EG[0] + in.SumEG[1]*n03_EG[1] + in.SumEG[2]*n03_EG[2]
                 + in.SumEA[0]*n03_EA[0] + in.SumEA[1]*n03_EA[1] + in.SumEA[2]*n03_EA[2]
                 + in.NS*n03_NS + n03_Th;
    out03 = sigmoid(out03);
    
    double out04 = in.SumEG[0]*n04_EG[0] + in.SumEG[1]*n04_EG[1] + in.SumEG[2]*n04_EG[2]
                 + in.SumEA[0]*n04_EA[0] + in.SumEA[1]*n04_EA[1] + in.SumEA[2]*n04_EA[2]
                 + in.NS*n04_NS + n04_Th;
    out04 = sigmoid(out04);

    double out05 = in.SumEG[0]*n05_EG[0] + in.SumEG[1]*n05_EG[1] + in.SumEG[2]*n05_EG[2]
                 + in.SumEA[0]*n05_EA[0] + in.SumEA[1]*n05_EA[1] + in.SumEA[2]*n05_EA[2]
                 + in.NS*n05_NS + n05_Th;
    out05 = sigmoid(out05);
    
    double prob_b = sigmoid(n0[0] + out02*n0[1] + out03*n0[2] + out04*n0[3] + out05*n0[4]);
    double prob_m = sigmoid(n1[0] + out02*n1[1] + out03*n1[2] + out04*n1[3] + out05*n1[4]);
    
    if (prob_b > prob_m) return 1;  // Bien Realizado
    else return 0;                  // Mal Realizado
}

// ============================================================================
// DETECTOR DE EVENTOS
// ============================================================================
class EventDetector {
private:
    bool calibrated;
    int calibration_count;
    float acc_sum[3];
    float rotation_matrix[3][3];
    
    bool first_cruce;
    const int MIN_SEG_LEN = 15;      // 35;
    const int MAX_SEG_LEN = 130;
    const float MIN_AREA = 100.0f;   // 400.0f;
    const float MAX_AREA = 4000.0f;
    const int MIN_EXERCISE_LEN = 30; // 100;
    const int MAX_EXERCISE_LEN = 400;
    const float THRESHOLD = 5.0f;
    
    const int SEC_EJ[2] = {1, -1};
    
    struct IIRFilter {
        const float c[3] = {0.12915f, 0.12915f, 0.7417f};
        float x[2];
        float y[2];
        
        IIRFilter() : x{0, 0}, y{0, 0} {}
        
        float apply(float input, bool first) {
            if (first) {y[0] = input; x[0] = input;}
            float output = c[0]*input + c[1]*x[0] + c[2]*y[0];
            x[0] = input;
            y[0] = output;
            return output;
        }
    };
    
    IIRFilter filter_gyro[3];
    IIRFilter filter_acc[3];
    
    struct ProcessedSample {
        float gyro[3];
        float acc[3];
        bool valid;
    };
    
    std::vector<ProcessedSample> processed_buffer;
    
    struct Segment {
        int start;
        int end;
        int len;
        float area;
        int sign;
    };
    
    Segment seg_actual;
    Segment seg_previo;
    int total_length_counter;
    bool in_threshold;
    bool was_in_threshold;
    float prev_value;
    int last_processed_idx;

public:
    EventDetector():
        calibrated(false),
        calibration_count(0),
        first_cruce(true),
        total_length_counter(0),
        in_threshold(true),
        was_in_threshold(true), 
        prev_value(0),
        last_processed_idx(-1)
        {
            processed_buffer.resize(BUFFER_SIZE);
            for (int i = 0; i < BUFFER_SIZE; i++) {processed_buffer[i].valid = false;}
            memset(acc_sum, 0, sizeof(acc_sum));
            memset(&seg_actual, 0, sizeof(seg_actual));
            memset(&seg_previo, 0, sizeof(seg_previo));
        }
    
    bool is_calibrated() const { return calibrated; }
    
    void try_calibrate(IMUSample buffers[BUFFER_SIZE]) {
        if (calibrated) return;
        
        // Reset to not count double
        calibration_count = 0;
        memset(acc_sum, 0, sizeof(acc_sum));

        for (int s = 0; s < BUFFER_SIZE && calibration_count < 60; s++) {
            if (buffers[s].valid) {
                for (int i = 0; i < 3; i++) {
                    acc_sum[i] += buffers[s].acc[i] / ACC_LSB_TO_MS2;
                }
                calibration_count++;
            }
        }
        
        if (calibration_count == 60) {
            float acc_avg[3];
            for (int i = 0; i < 3; i++) {
                acc_avg[i] = acc_sum[i] / 60.0f;
            }
            
            calculate_rotation_matrix(acc_avg);
            calibrated = true;
            
            std::cout << "[ED] Rot-Matriz Ready" << std::endl;
        }
    }
    
    void process_sample(IMUSample buffers[BUFFER_SIZE], int sample_idx) {
        if (!calibrated) return;
        
        int pos = sample_idx % BUFFER_SIZE;
        
        // process the valid sample (convert to units -> filter -> rotation matrix)
        prepross_ufrm(buffers, pos);

        // Detectar gap
        if (last_processed_idx >= 0 && sample_idx != last_processed_idx + 1) {
            int lost_samples = sample_idx - last_processed_idx - 1;
            int last_pos = last_processed_idx % BUFFER_SIZE;
            
            // Calculate m & b
            float gyr_m[3], gyr_b[3], acc_m[3], acc_b[3];
            for (int j = 0; j < 3; j++) {
                // b = y1
                gyr_b[j] = processed_buffer[last_pos].gyro[j];
                acc_b[j] = processed_buffer[last_pos].acc[j];

                // m = (y2 - y1) / ("pasos")
                gyr_m[j] = (processed_buffer[pos].gyro[j] - gyr_b[j]) / (lost_samples + 1);
                acc_m[j] = (processed_buffer[pos].acc[j] - acc_b[j]) / (lost_samples + 1);
            }

            // For eache lost sample
            int i, x = 1;
            for (int i_global = last_processed_idx + 1; i_global < sample_idx; i_global++){
                i = i_global % BUFFER_SIZE; // real buffer index 
                // For eache sensor
                for (int j = 0; j < 3; j++){
                    // y = m *x + b
                    processed_buffer[i].gyro[j] = gyr_m[j] * x + gyr_b[j];
                    processed_buffer[i].acc[j] = acc_m[j] * x + acc_b[j];
                }
                processed_buffer[i].valid = true;
                automatic_seg(i, i_global); // LOST SAMPLES TO AUTO-SEG
                x++;
            }
        }

        // Pass to the Automatic Seg
        automatic_seg(pos, sample_idx);
        last_processed_idx = sample_idx;
    }

private:
    void calculate_rotation_matrix(float acc_avg[3]) {
        float v_ini[3] = {acc_avg[0], acc_avg[1], acc_avg[2]};
        float v_fin[3] = {0, 1, 0};
        
        float v_ini_norm = sqrt(v_ini[0]*v_ini[0] + v_ini[1]*v_ini[1] + v_ini[2]*v_ini[2]);
        // if (v_ini_norm < 0.1f) v_ini_norm = 1.0f;
        
        // Eje de rotación: A = cross(v_ini, v_fin)
        // v_fin = [0, 1, 0]
        float A[3];
        A[0] = -v_ini[2]; // v_ini[1]*v_fin[2] - v_ini[2]*v_fin[1];  // = v_ini[1]*0 - v_ini[2]*1 = -v_ini[2]
        A[1] = 0;         // v_ini[2]*v_fin[0] - v_ini[0]*v_fin[2];  // = v_ini[2]*0 - v_ini[0]*0 = 0
        A[2] = v_ini[0];  // v_ini[0]*v_fin[1] - v_ini[1]*v_fin[0];  // = v_ini[0]*1 - v_ini[1]*0 = v_ini[0]
        
        float A_norm = sqrt(A[0]*A[0] + A[2]*A[2]); // sqrt(A[0]*A[0] + A[1]*A[1] + A[2]*A[2]);
        // if (A_norm < 0.001f) {
        //     rotation_matrix[0][0] = 1; rotation_matrix[0][1] = 0; rotation_matrix[0][2] = 0;
        //     rotation_matrix[1][0] = 0; rotation_matrix[1][1] = 1; rotation_matrix[1][2] = 0;
        //     rotation_matrix[2][0] = 0; rotation_matrix[2][1] = 0; rotation_matrix[2][2] = 1;
        //     return;
        // }
        
        float alpha = acos(v_ini[1] / v_ini_norm);
        
        float q0 = cos(alpha / 2.0f);
        float q1 = sin(alpha / 2.0f) * (A[0] / A_norm);
        float q2 = sin(alpha / 2.0f) * (A[1] / A_norm);
        float q3 = sin(alpha / 2.0f) * (A[2] / A_norm);
        
        rotation_matrix[0][0] = 1 - 2*(q2*q2 + q3*q3);
        rotation_matrix[0][1] = 2*(q1*q2 - q0*q3);
        rotation_matrix[0][2] = 2*(q0*q2 + q1*q3);
        
        rotation_matrix[1][0] = 2*(q1*q2 + q0*q3);
        rotation_matrix[1][1] = 1 - 2*(q1*q1 + q3*q3);
        rotation_matrix[1][2] = 2*(q2*q3 - q0*q1);
        
        rotation_matrix[2][0] = 2*(q1*q3 - q0*q2);
        rotation_matrix[2][1] = 2*(q0*q1 + q2*q3);
        rotation_matrix[2][2] = 1 - 2*(q1*q1 + q2*q2);
    }
    
    void apply_rotation(float vec[3], float result[3]) {
        result[0] = rotation_matrix[0][0]*vec[0] + rotation_matrix[0][1]*vec[1] + rotation_matrix[0][2]*vec[2];
        result[1] = rotation_matrix[1][0]*vec[0] + rotation_matrix[1][1]*vec[1] + rotation_matrix[1][2]*vec[2];
        result[2] = rotation_matrix[2][0]*vec[0] + rotation_matrix[2][1]*vec[1] + rotation_matrix[2][2]*vec[2];
    }
    
    void prepross_ufrm(IMUSample buffers[BUFFER_SIZE], int pos) {
        // Si no es válida ??? - TODOS SIN VALIDOS!!!
        // if (!buffers[pos].valid) 
        
        // Convertir a unidades físicas
        float gyro[3], acc[3];
        for (int i = 0; i < 3; i++) {
            gyro[i] = buffers[pos].gyro[i] / GYRO_LSB_TO_DPS;
            acc[i] = buffers[pos].acc[i] / ACC_LSB_TO_MS2;
        }

        // std::cout << pos << " ";
        // for (int i = 0; i < 3; i++) printf("%.2f ", gyro[i]);
        // for (int i = 0; i < 3; i++) printf("%.2f ", acc[i]);
        // std::cout << std::endl;
        
        // Aplicar filtro IIR
        bool first_sample = false;
        if (last_processed_idx == -1) first_sample = true;
        for (int i = 0; i < 3; i++) {
            gyro[i] = filter_gyro[i].apply(gyro[i], first_sample);
            acc[i] = filter_acc[i].apply(acc[i], first_sample);
        }
        
        // Aplicar matriz de rotación
        float gyro_rotated[3], acc_rotated[3];
        apply_rotation(gyro, gyro_rotated);
        apply_rotation(acc, acc_rotated);
        
        // Guardar
        for (int i = 0; i < 3; i++) {
            processed_buffer[pos].gyro[i] = gyro_rotated[i];
            processed_buffer[pos].acc[i] = acc_rotated[i];
        }
        processed_buffer[pos].valid = true;
    }
    
    void automatic_seg(int pos, int global_counter) {
        float value = processed_buffer[pos].gyro[1];
        bool cruce_detectado = false;

        // Are we in the THRESHOLD?
        in_threshold = (fabs(value) < THRESHOLD);
        
        // If this is not the firts sample
        if (last_processed_idx != -1) {
            // If we traspass the THRESHOLD without touching it
            if (value * prev_value < -(THRESHOLD*THRESHOLD) 
                && !in_threshold && !was_in_threshold) cruce_detectado = true;
            
            // If change from be in/out the threshold to out/in the threshold
            if (in_threshold != was_in_threshold) cruce_detectado = true;
        }
        
        // loop over the values
        was_in_threshold = in_threshold;
        prev_value = value;

        // If we are in a open segment -> calculate the area
        if (!cruce_detectado && !first_cruce) seg_actual.area += value;
        else {
            // Start of the first segment!
            if (first_cruce) {
                seg_actual.start = global_counter;
                seg_actual.area = value;
                first_cruce = false;
            } else {
                // End of a segment
                seg_actual.area += value;
                seg_actual.end = global_counter;

                // Get the segment len, area and sign
                seg_actual.len = seg_actual.end - seg_actual.start + 1;
                seg_actual.sign = (seg_actual.area > 0) ? 1 : -1;
                float a = fabs(seg_actual.area);
                
                // Check if is a valid segment
                bool v = true;
                if (seg_actual.len < MIN_SEG_LEN || seg_actual.len > MAX_SEG_LEN) v = false;
                if (a < MIN_AREA || a > MAX_AREA) v = false;

                // If is a valid segment
                if (v) {
                    // Check the secuence
                    if (seg_previo.area != 0 && // Si ya tenemos un segmento previo
                        seg_previo.sign == SEC_EJ[0] && // Y cumplimos la secuencia
                        seg_actual.sign == SEC_EJ[1]) {
                        
                            // VALIDACION FINAL!! - Calculate the total len
                            int tl = seg_actual.end - seg_previo.start + 1;
                            // If the total len is ok
                            if (tl >= MIN_EXERCISE_LEN && tl <= MAX_EXERCISE_LEN) {
                                 int start_pos = seg_previo.start % 768;
                                printf("Possible exercise [%d-%d l:%d] -> ", seg_previo.start, seg_actual.end, tl);
                                get_attributes(start_pos, pos, tl);
                            }
                        // Secuence ok -> Reset prev
                        memset(&seg_previo, 0, sizeof(seg_previo));
                    } else {
                        // If the secuence is wrong or prev is cero
                        // If actual seg is the first seg secuence -> Save
                        if (seg_actual.sign == SEC_EJ[0]) seg_previo = seg_actual;
                        else memset(&seg_previo, 0, sizeof(seg_previo));
                    }
                }
                // printf("SEG[%d]: A=%.2f L=%d, S=%d\n", v, seg_actual.area, seg_actual.len, seg_actual.sign);
                // Reset -> Start of the next segment
                memset(&seg_actual, 0, sizeof(seg_actual));
                seg_actual.start = global_counter;
                seg_actual.area = value;
            }
        }
    }

    void get_attributes(int start_pos, int end_pos, int l) {
        Attb sensor;
        sensor.NS = l;
        for (int i = 0; i < 3; i++) {sensor.SumEA[i] = 0; sensor.SumEG[i] = 0;}
        
        for (int s = start_pos; s != (end_pos + 1); s = (s + 1) % 768) {
            for (int i = 0; i < 3; i++) {
                sensor.SumEG[i] += processed_buffer[s].gyro[i] * processed_buffer[s].gyro[i];
                sensor.SumEA[i] += processed_buffer[s].acc[i] * processed_buffer[s].acc[i];
            }
        }
        if(mlp_classifier(sensor)) std::cout << "Well-performed" << std::endl;
        else std::cout << "Poorly performed" << std::endl;
    }
};

// ============================================================================
// PUERTO SERIAL
// ============================================================================
class SerialPort {
private:
    HANDLE hSerial;
    std::string port_name;

public:
    SerialPort(const std::string& port, int baudrate = 230400) 
        : hSerial(INVALID_HANDLE_VALUE), port_name(port) {
        
        std::string full_port = "\\\\.\\" + port;
        hSerial = CreateFileA(
            full_port.c_str(),
            GENERIC_READ | GENERIC_WRITE,
            0, NULL, OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL, NULL
        );

        if (hSerial == INVALID_HANDLE_VALUE) {
            std::cerr << "Error: No se pudo abrir " << port << std::endl;
            std::cerr << "Codigo de error: " << GetLastError() << std::endl;
            return;
        }

        DCB dcbSerialParams;
        memset(&dcbSerialParams, 0, sizeof(dcbSerialParams));
        dcbSerialParams.DCBlength = sizeof(dcbSerialParams);

        if (!GetCommState(hSerial, &dcbSerialParams)) {
            std::cerr << "Error obteniendo estado del puerto" << std::endl;
            CloseHandle(hSerial);
            hSerial = INVALID_HANDLE_VALUE;
            return;
        }

        dcbSerialParams.BaudRate = baudrate;
        dcbSerialParams.ByteSize = 8;
        dcbSerialParams.StopBits = ONESTOPBIT;
        dcbSerialParams.Parity = NOPARITY;
        dcbSerialParams.fDtrControl = DTR_CONTROL_ENABLE;

        if (!SetCommState(hSerial, &dcbSerialParams)) {
            std::cerr << "Error configurando puerto" << std::endl;
            CloseHandle(hSerial);
            hSerial = INVALID_HANDLE_VALUE;
            return;
        }

        COMMTIMEOUTS timeouts;
        memset(&timeouts, 0, sizeof(timeouts));
        timeouts.ReadIntervalTimeout = 1;
        timeouts.ReadTotalTimeoutConstant = 1;
        timeouts.ReadTotalTimeoutMultiplier = 0;
        timeouts.WriteTotalTimeoutConstant = 50;
        timeouts.WriteTotalTimeoutMultiplier = 10;

        if (!SetCommTimeouts(hSerial, &timeouts)) {
            std::cerr << "Error configurando timeouts" << std::endl;
            CloseHandle(hSerial);
            hSerial = INVALID_HANDLE_VALUE;
            return;
        }

        std::cout << "Puerto serial " << port << " abierto a " << baudrate << " baud" << std::endl;
    }

    ~SerialPort() {
        if (hSerial != INVALID_HANDLE_VALUE) {
            CloseHandle(hSerial);
            std::cout << "Puerto serial cerrado" << std::endl;
        }
    }

    bool is_open() const { 
        return hSerial != INVALID_HANDLE_VALUE; 
    }

    bool write_bytes(const uint8_t* data, size_t len) {
        if (!is_open()) return false;
        
        DWORD bytes_written;
        return WriteFile(hSerial, data, (DWORD)len, &bytes_written, NULL) && bytes_written == len;
    }

    // bool read_byte(uint8_t* byte) {
    //     if (!is_open()) return false;
    //     DWORD bytes_read;
    //     if (ReadFile(hSerial, byte, 1, &bytes_read, NULL) && bytes_read == 1) {
    //         return true;
    //     }
    //     return false;
    // }

    DWORD read_bytes(uint8_t* buffer, DWORD len) {
        if (!is_open()) return 0;
        
        DWORD bytes_read = 0;
        
        // Regresa los bytes que tenga
        if (!ReadFile(hSerial, buffer, len, &bytes_read, NULL)) {
            return 0; // Hubo un error
        }
        
        return bytes_read; // Devuelve 0 si hubo timeout
    }

    void send_command(const std::vector<uint8_t>& cmd) {
        if (write_bytes(cmd.data(), cmd.size())) {
            std::cout << "CMD enviado: ";
            for (auto b : cmd) printf("%02X ", b);
            std::cout << std::endl;
        }
    }
};

// ============================================================================
// UDP SENDER
// ============================================================================
class UDPSender {
private:
    SOCKET sockfd;
    struct sockaddr_in server_addr;
    bool initialized;

public:
    UDPSender(const std::string& ip = "127.0.0.1", int port = 4000):
    initialized(false) {
        WSADATA wsaData;
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
            std::cerr << "Error: WSAStartup fallo" << std::endl;
            return;
        }

        sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
        if (sockfd == INVALID_SOCKET) {
            std::cerr << "Error: No se pudo crear socket UDP" << std::endl;
            WSACleanup();
            return;
        }

        memset(&server_addr, 0, sizeof(server_addr));
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(port);
        
        if (inet_pton_compat(AF_INET, ip.c_str(), &server_addr.sin_addr) <= 0) {
            std::cerr << "Error: Direccion IP invalida" << std::endl;
            closesocket(sockfd);
            WSACleanup();
            return;
        }

        initialized = true;
        std::cout << "UDP Sender configurado para " << ip << ":" << port << std::endl;
    }

    ~UDPSender() {
        if (initialized) {
            closesocket(sockfd);
            WSACleanup();
        }
    }

    bool is_initialized() const { return initialized; }

    bool send_sample(const IMUSampleUDP& sample) {
        if (!initialized) return false;
        
        int sent = sendto(sockfd, (const char*)&sample, sizeof(sample), 0,
                         (struct sockaddr*)&server_addr, sizeof(server_addr));
        return sent > 0;
    }
};

// ============================================================================
// SISTEMA PRINCIPAL
// ============================================================================
class IMUReceiver {
private:
    SerialPort serial;
    UDPSender udp_sender;
    
    IMUSample buffers[NUM_PERIPHERALS][BUFFER_SIZE];
    PacketTracker trackers[NUM_PERIPHERALS];
    
    std::atomic<bool> running;
    std::thread rx_thread;
    std::thread udp_thread;
    std::thread process_thread;
    
    std::queue<IMUSampleUDP> udp_queue;
    std::mutex udp_mutex;
    
    std::queue<int> process_queue;
    std::mutex process_mutex;
    
    FILE* bin_file;
    std::string bin_filename;
    
    uint32_t packets_received[NUM_PERIPHERALS];
    uint32_t packets_lost[NUM_PERIPHERALS];
    uint32_t total_packets_written;
    
    EventDetector event_detector;
    int global_sample_index;

public:
    IMUReceiver(const std::string& port, int baudrate = 230400):
        serial(port, baudrate),
        running(false),
        bin_file(nullptr), 
        total_packets_written(0),
        global_sample_index(-1)
        {
        
        for (int i = 0; i < NUM_PERIPHERALS; i++) {
            packets_received[i] = 0;
            packets_lost[i] = 0;
        }
        
        for (int p = 0; p < NUM_PERIPHERALS; p++) {
            for (int s = 0; s < BUFFER_SIZE; s++) {
                memset(&buffers[p][s], 0, sizeof(IMUSample));
                buffers[p][s].valid = false;
            }
        }
    }

    ~IMUReceiver() {
        stop();
    }

    bool initialize() {
        if (!serial.is_open()) {
            std::cerr << "Error: Puerto serial no disponible" << std::endl;
            return false;
        }

        // std::cout << "\n=== CONFIGURACION INICIAL ===" << std::endl;
        // std::this_thread::sleep_for(std::chrono::milliseconds(500));
        // serial.send_command({0x7E, 0x00, 0x18, 0x7F}); // Print logs/info OFF
        // std::this_thread::sleep_for(std::chrono::milliseconds(500));
        // serial.send_command({0x7E, 0x00, 0x17, 0x7F}); // UART TX Eneable
        // std::this_thread::sleep_for(std::chrono::milliseconds(500));
        // serial.send_command({0x7E, 0x03, 0x10, 0xFF, 0x01, 0x01, 0x7F}); // Start to all peripherals
        // // std::this_thread::sleep_for(std::chrono::milliseconds(100));
        std::cout << "\n=== TX START CMD's ===" << std::endl;
        // std::this_thread::sleep_for(std::chrono::milliseconds(5000));
        serial.send_command({0x7E, 0x00, 0x18, 0x7F}); // Print logs/info OFF
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
        serial.send_command({0x7E, 0x00, 0x17, 0x7F}); // UART TX Eneable
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
        serial.send_command({0x7E, 0x03, 0x00, 0xFF, 0x03, 0x01, 0x7F}); // Start to all peripherals
        std::cout << "=== CONFIGURACION COMPLETA ===\n" << std::endl;
        return true;
    }

    void start() {
        if (running) return;
        
        running = true;
        rx_thread = std::thread(&IMUReceiver::reception_loop, this);
        // udp_thread = std::thread(&IMUReceiver::udp_loop, this);
        process_thread = std::thread(&IMUReceiver::processing_loop, this);
        
        std::cout << "Threads iniciados (RX + UDP + Procesamiento)" << std::endl;
    }

    void stop() {
        if (!running) return;

        std::cout << "\nTX STOPS CMD's" << std::endl;
        //                  Start,  len,  CMD, PAYLOAD........., end.
        serial.send_command({0x7E, 0x03, 0x00, 0xFF, 0x03, 0x00, 0x7F}); // Stop to all peripherals
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        serial.send_command({0x7E, 0x00, 0x16, 0x7F}); // UART TX Disable

        std::cout << "\nDeteniendo threads..." << std::endl;
        running = false;
        
        if (rx_thread.joinable()) rx_thread.join();
        // if (udp_thread.joinable()) udp_thread.join();
        if (process_thread.joinable()) process_thread.join();
        
        print_statistics();
    }

private:
    std::string generate_filename() {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        
        struct tm* tm_ptr = localtime_compat(&time_t);
        
        char buffer[64];
        strftime(buffer, sizeof(buffer), "%Y-%m-%d_%H-%M-%S.bin", tm_ptr);
        
        return std::string(buffer);
    }

    void reception_loop() {
        bin_filename = generate_filename();
        bin_file = fopen_compat(bin_filename.c_str(), "wb");
        
        if (!bin_file) {
            std::cerr << "[RX] Error: no se pudo crear archivo " << bin_filename << std::endl;
            return;
        }
        
        std::cout << "[RX Thread] Iniciado" << std::endl;
        std::cout << "[RX] Archivo abierto: " << bin_filename << std::endl;
        
        // Búfer local para leer bloques
        uint8_t temp_buffer[256];
        uint8_t rx_buffer[256];
        size_t pos = 0;
        bool escape_next = false;
        bool in_packet = false;


        while (running) {

            DWORD bytes_read = serial.read_bytes(temp_buffer, 256);
            if (bytes_read == 0) {
                std::this_thread::sleep_for(std::chrono::milliseconds(5));
                continue;
            }

            for (DWORD i = 0; i < bytes_read; i++) {
                uint8_t byte = temp_buffer[i]; // El byte actual del bloque

                // (Esta es tu lógica de máquina de estados exacta de antes)
                if (byte == PKT_START_BYTE) {
                    pos = 0;
                    in_packet = true;
                    escape_next = false;
                    continue;
                }

                if ( in_packet) {
                    if (byte == PKT_END_BYTE && pos > 0) {
                        fwrite(rx_buffer, pos, 1, bin_file);
                        total_packets_written++;
                        parse_packet(rx_buffer, pos);
                        
                        // print len + Pid + No.Pkt
                        // std::cout << +pos << "-" << +rx_buffer[0] << "-" << +rx_buffer[2] << "-" << +rx_buffer[3] << std::endl;
                        
                        in_packet = false;
                        pos = 0;
                        
                        continue;
                    }

                    if (byte == 0x7D) { // Byte de escape detectado
                        escape_next = true;
                        continue; // No guardamos este byte, esperamos al siguiente
                    }

                    if (escape_next) {
                        byte = byte ^ 0x20; // Recuperar valor original
                        escape_next = false;
                    }

                    if (pos < 256) rx_buffer[pos++] = byte;
                }
            }
        }

        std::cout << "[RX] Cerrando archivo..." << std::endl;
        fclose(bin_file);
        std::cout << "[RX] Archivo cerrado: " << total_packets_written << " paquetes escritos" << std::endl;
        std::cout << "[RX Thread] Terminado" << std::endl;
    }

    void parse_packet(const uint8_t* pkt, size_t len) {
        if (len < 5) return;
        
        // uint8_t pkt_len = pkt[0];
        // uint8_t msg_type = pkt[1];
        uint8_t peripheral_id = pkt[2];
        
        // if (msg_type != MSG_TYPE_SENSOR_DATA) return;
        if (peripheral_id >= NUM_PERIPHERALS) return;
        
        const uint8_t* payload = &pkt[3];
        uint8_t packet_num = payload[0];
        
        PacketTracker& tracker = trackers[peripheral_id];
        
        if (!tracker.first_packet && event_detector.is_calibrated()) {
            uint8_t expected = (tracker.last_packet_num + 1) % 256;
            
            if (packet_num != expected) {
                uint8_t lost_count = (packet_num - expected + 256) % 256;
                packets_lost[peripheral_id] += lost_count;
                
                std::cout << "[P" << (int)peripheral_id << "] Gap:"
                          << " ultimo=" << (int)tracker.last_packet_num
                          << " esperado=" << (int)expected 
                          << " recibido=" << (int)packet_num
                          << " perdidos=" << (int)lost_count << " paquetes" << std::endl;
                
                for (uint8_t p = expected; p != packet_num; p = (p + 1) % 256) {
                    for (int offset = 0; offset < SAMPLES_PER_PACKET; offset++) {
                        uint16_t sample_num = (p * SAMPLES_PER_PACKET + offset) % BUFFER_SIZE;
                        buffers[peripheral_id][sample_num].valid = false;
                    }
                }
                // Count the lost samples in global_sample_index!!!
                if (peripheral_id == 0 && global_sample_index != -1) global_sample_index += lost_count * SAMPLES_PER_PACKET;
            }
        }
        
        tracker.last_packet_num = packet_num;
        tracker.first_packet = false;
        packets_received[peripheral_id]++;

        const uint8_t* data = &payload[1];
        
        for (int i = 0; i < SAMPLES_PER_PACKET; i++) {
            uint16_t sample_num = (packet_num * SAMPLES_PER_PACKET + i) % BUFFER_SIZE;
            IMUSample& sample = buffers[peripheral_id][sample_num];
            
            for (int j = 0; j < 4; j++) {
                sample.quat[j] = data[0] | (data[1] << 8);
                data += 2;
            }
            
            for (int j = 0; j < 3; j++) {
                sample.acc[j] = data[0] | (data[1] << 8);
                data += 2;
            }
            
            for (int j = 0; j < 3; j++) {
                sample.gyro[j] = data[0] | (data[1] << 8);
                data += 2;
            }
            
            sample.valid = true;
            
            // IMUSampleUDP udp_sample;
            // udp_sample.peripheral_id = peripheral_id;
            // udp_sample.sample_num = sample_num;
            // udp_sample.sample = sample;
            
            // {
            //     std::lock_guard<std::mutex> lock(udp_mutex);
            //     udp_queue.push(udp_sample);
            // }
            
            // Use the queue until the calibration is done
            if (peripheral_id == 0 && event_detector.is_calibrated()) {
                std::lock_guard<std::mutex> lock(process_mutex);
                // If this is the first sample -> Sync with global_sample
                if (global_sample_index == -1) global_sample_index = sample_num;
                // printf("%u - %d\n", sample_num, global_sample_index);
                process_queue.push(global_sample_index++);
            }
        }
    }

    void udp_loop() {
        std::cout << "[UDP Thread] Iniciado" << std::endl;
        
        while (running) {
            IMUSampleUDP sample;
            bool has_data = false;
            
            {
                std::lock_guard<std::mutex> lock(udp_mutex);
                if (!udp_queue.empty()) {
                    sample = udp_queue.front();
                    udp_queue.pop();
                    has_data = true;
                }
            }
            
            if (has_data) {
                udp_sender.send_sample(sample);
            } else {
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
        }
        
        std::cout << "[UDP Thread] Terminado" << std::endl;
    }

    void processing_loop() {
        std::cout << "[Process Thread] Iniciado - Segmentador IAAC Periferico 0" << std::endl;
        
        while (running) {
            if (!event_detector.is_calibrated()) {
                event_detector.try_calibrate(buffers[0]);
                std::this_thread::sleep_for(std::chrono::milliseconds(50));
            } else {
                std::vector<int> batch;
                {
                    std::lock_guard<std::mutex> lock(process_mutex);
                    int count = std::min((int)process_queue.size(), 20);
                    for (int i = 0; i < count; i++) {
                        batch.push_back(process_queue.front());
                        process_queue.pop();
                    }
                }
                if (batch.empty()) std::this_thread::sleep_for(std::chrono::milliseconds(50));
                else {for (int sample_idx : batch) {event_detector.process_sample(buffers[0], sample_idx);}}
            }
        }
        std::cout << "[Process Thread] Terminado" << std::endl;
    }

    void print_statistics() {
        std::cout << "\n=== ESTADISTICAS ===" << std::endl;
        std::cout << "Archivo: " << bin_filename << std::endl;
        std::cout << "Paquetes raw escritos: " << total_packets_written << std::endl;
        std::cout << "\nPor periferico:" << std::endl;
        
        for (int i = 0; i < NUM_PERIPHERALS; i++) {
            std::cout << "  P" << i << ": "
                      << packets_received[i] << " paquetes recibidos, "
                      << packets_lost[i] << " perdidos";
            
            if (packets_received[i] > 0) {
                float loss_rate = (float)packets_lost[i] / (packets_received[i] + packets_lost[i]) * 100.0f;
                std::cout << " (" << std::fixed << std::setprecision(2) << loss_rate << "%)";
            }
            std::cout << std::endl;
        }
    }
};

// ============================================================================
// MAIN
// ============================================================================
int main(int argc, char** argv) {
    std::string port = "COM7";
    
    if (argc > 1) port = argv[1];
    
    std::cout << "=== IMU Receiver System (Windows/MinGW) ===" << std::endl;
    std::cout << "Puerto: " << port << std::endl;
    std::cout << "Baudrate: 230400" << std::endl;
    std::cout << "Perifericos: " << NUM_PERIPHERALS << std::endl;
    std::cout << "Buffer: " << BUFFER_SIZE << " muestras/periferico" << std::endl;
    std::cout << "UDP: localhost:4000" << std::endl;
    std::cout << "Segmentador: IAAC en Periferico 0" << std::endl;
    std::cout << "============================================\n" << std::endl;

    IMUReceiver receiver(port);
    
    if (!receiver.initialize()) {
        std::cout << "\nPresiona ENTER para salir..." << std::endl;
        std::cin.get();
        return 1;
    }

    receiver.start();

    std::cout << "\n=== Sistema en ejecucion ===" << std::endl;
    std::cout << "Presiona ENTER para detener y cerrar archivo..." << std::endl;
    std::cin.get();

    receiver.stop();
    
    std::cout << "\nSistema detenido. Archivo cerrado." << std::endl;

    return 0;
}