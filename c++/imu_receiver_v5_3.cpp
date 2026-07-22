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

// Códigos de color ANSI
const std::string RST  = "\033[0m";
const std::string RED   = "\033[31m";
const std::string GRN  = "\033[32m";
const std::string YLL = "\033[33m";

// Habilitar soporte ANSI en la consola de Windows (llamar 1 vez al inicio del programa)
void habilitarANSI() {
    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
    DWORD dwMode = 0;
    GetConsoleMode(hOut, &dwMode);
    SetConsoleMode(hOut, dwMode | ENABLE_VIRTUAL_TERMINAL_PROCESSING);
}

// ============================================================================
// CONSTANTES Y ESTRUCTURAS
// ============================================================================
#define NUM_PERIPHERALS 4
#define MAIN_SENSOR 0
#define BUFFER_SIZE 768
#define SAMPLES_PER_PACKET 3
#define NO_SAMPLES_ROT_MATX 60

#define PKT_START_BYTE 0x7E
#define PKT_END_BYTE   0x7F
#define MSG_TYPE_SENSOR_DATA 0x60

#define ACC_LSB_TO_MS2 100.0f
#define GYRO_LSB_TO_DPS 16.0f

struct IMUSample {
    uint32_t no_sample = 0; // Number of the sample
    int16_t quat[4] = {0};  // Raw quat data
    int16_t acc[3] = {0};   // Raw acc data
    int16_t gyro[3] = {0};  // Raw gyro data
    // bool valid;
};

struct IMUSampleUDP {
    uint8_t peripheral_id;
    IMUSample sample;
};

struct ProcessedSampleUDP {
    uint32_t no_sample;   // Number of the sample
    float gyro[3];        // grados/s
    float acc[3];         // g
};

struct PacketTracker {
    uint32_t last_packet_num;
    bool first_packet;
    PacketTracker() : last_packet_num(0xFFFFFFFF), first_packet(true) {}
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

struct tm* localtime_compat(const time_t* timer) {return localtime(timer);}

FILE* fopen_compat(const char* filename, const char* mode) {return fopen(filename, mode);}

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
    double resultado = 2.0 * ((input - min) / (max - min)) - 1.0;
    // En caso de valor maximo/minimo inesperado
    if (resultado > 1.0) resultado = 1.0;
    if (resultado < -1.0) resultado = -1.0;
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
    struct TrackSample {
        uint32_t last; // last rx_sample processed
        bool first = true;
    };
    TrackSample tracker[NUM_PERIPHERALS];

    struct RotationMatrix {
        uint16_t rx_samples_count; // start in 0, "max" = NO_SAMPLES_ROT_MATX
        uint16_t list_no_samp[NO_SAMPLES_ROT_MATX];
        uint16_t raw_acc[3][NO_SAMPLES_ROT_MATX];   // Values to use in the rotation matrix
        float m[3][3];  // Rotation matrix
        bool ready;     // State of the rotation matrix, True=Matrix Ready
        RotationMatrix() : rx_samples_count(0), ready(false){}
    };
    RotationMatrix r_matrix[NUM_PERIPHERALS];

    // Variables and values for the exercise segmentation
    const int MIN_SEG_LEN = 20;      // 35;
    const int MAX_SEG_LEN = 130;
    const float MIN_AREA = 100.0f;   // 400.0f;
    const float MAX_AREA = 4000.0f;
    const int MIN_EXERCISE_LEN = 30; // 100;
    const int MAX_EXERCISE_LEN = 400;
    const float THRESHOLD = 5.0f;
    const int SEC_EJ[2] = {1, -1};
    
    struct IIRFilter {
        const float c[3] = {0.12915f, 0.12915f, 0.7417f};
        float x[2], y[2];
        IIRFilter() : x{0, 0}, y{0, 0} {} // inicializa el estado
        
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
        uint32_t no_sample;
        float gyro[3];
        float acc[3];
    };
    ProcessedSample processed_buffer[NUM_PERIPHERALS][BUFFER_SIZE];
    
    struct Segment {
        uint32_t start;
        uint32_t end;
        uint32_t len;
        float area;
        int sign;
        Segment() : start(0), end(0), len(0), area(0.0f), sign(0) {}
    };

    Segment seg_actual;
    Segment seg_previo;
    bool first_cruce = true;
    bool in_threshold = false;
    bool was_in_threshold = false;
    float prev_value = 0.0f;

public:
    // Detecta muestras perdidas y rellena con interpolacion lineal
    // Llama a prepross_ufrm para "convertir a unidades, filtrar y aplicar MR" la muestra recibida
    // Llama a automatic_se para detectar ejercicios
    void process_sample(IMUSample buffers[BUFFER_SIZE], uint32_t num_samp, uint8_t p) {
        IMUSample& sample = buffers[num_samp % BUFFER_SIZE];

        // If the rotation matriz is not ready
        if (!r_matrix[p].ready) {
            RotationMatrix& rm = r_matrix[p];
            if (rm.rx_samples_count < NO_SAMPLES_ROT_MATX) {
                // Save the "no_sample" and value of the acc
                rm.list_no_samp[rm.rx_samples_count] = sample.no_sample;
                for (int i = 0; i < 3; i++) rm.raw_acc[i][rm.rx_samples_count] = sample.acc[i];
                rm.rx_samples_count++;
            } else {
                // Enough samples -> calculate the rotation matrix!
                calculate_rotation_matrix(rm);
                std::cout<< "[ED] P"<<(int)p<<" Rot-Matrix Ready" << std::endl;
            }
            return;
        }

        uint32_t new_idx = sample.no_sample % BUFFER_SIZE;   // Get the index of the new sample
        prepross_ufrm(sample, p);                   // Preprocess the sample (acc & gyr)

        // If they are lost samples -> lineal interpolation
        if (!tracker[p].first && sample.no_sample > tracker[p].last + 1) {
            int lost_samples = sample.no_sample - tracker[p].last - 1;
            int last_idx = tracker[p].last % BUFFER_SIZE;
            
            // Calculate m & b
            // Para simplificar el calculo -> la ultima muestra es x = 0, de esta forma y1 = b
            float gyr_m[3], gyr_b[3], acc_m[3], acc_b[3];
            for (int j = 0; j < 3; j++) {
                gyr_b[j] = processed_buffer[p][last_idx].gyro[j];
                acc_b[j] = processed_buffer[p][last_idx].acc[j];
                // m = (y2 - y1) / ("pasos")
                gyr_m[j] = (processed_buffer[p][new_idx].gyro[j] - gyr_b[j]) / (lost_samples + 1);
                acc_m[j] = (processed_buffer[p][new_idx].acc[j] - acc_b[j]) / (lost_samples + 1);
            }

            // For eache lost sample
            uint32_t lost_idx, x = 1;
            for (uint32_t lost_sample = tracker[p].last + 1; lost_sample < sample.no_sample; lost_sample++){
                lost_idx = lost_sample % BUFFER_SIZE; // real buffer index 
                // For eache sensor
                for (int j = 0; j < 3; j++){
                    // y = m *x + b
                    processed_buffer[p][lost_idx].gyro[j] = gyr_m[j] * x + gyr_b[j];
                    processed_buffer[p][lost_idx].acc[j] = acc_m[j] * x + acc_b[j];
                }
                if (p == MAIN_SENSOR) automatic_seg(lost_idx, lost_sample, p); // LOST SAMPLES TO AUTO-SEG
                x++;
            }
        }

        // Pass to the Automatic Seg
        if (p == MAIN_SENSOR) automatic_seg(new_idx, sample.no_sample, p);
        tracker[p].last = sample.no_sample;
        tracker[p].first = false;
    }

private:
    // calcula matriz de rotacion. Toma como entrada el vector de valores promediados de try_calibrate
    void calculate_rotation_matrix(RotationMatrix& rm) {
        float acc_sum[3] = {0}, acc_avg[3] = {0};

        for (int s = 0; s < NO_SAMPLES_ROT_MATX; s++) {
            for (int i = 0; i < 3; i++) acc_sum[i] += rm.raw_acc[i][s] / (float)ACC_LSB_TO_MS2;
        }
        for (int i = 0; i < 3; i++) acc_avg[i] = acc_sum[i] / (float)NO_SAMPLES_ROT_MATX;

        float v_ini[3] = {acc_avg[0], acc_avg[1], acc_avg[2]};
        float v_fin[3] = {0, 1, 0};
        
        float v_ini_norm = sqrt(v_ini[0]*v_ini[0] + v_ini[1]*v_ini[1] + v_ini[2]*v_ini[2]);
        // if (v_ini_norm < 0.1f) v_ini_norm = 1.0f; // vectores casi palalelos
        
        // Eje de rotación: A = cross(v_ini, v_fin)
        // v_fin = [0, 1, 0]
        float A[3];
        A[0] = -v_ini[2]; // v_ini[1]*v_fin[2] - v_ini[2]*v_fin[1];  // = v_ini[1]*0 - v_ini[2]*1 = -v_ini[2]
        A[1] = 0;         // v_ini[2]*v_fin[0] - v_ini[0]*v_fin[2];  // = v_ini[2]*0 - v_ini[0]*0 = 0
        A[2] = v_ini[0];  // v_ini[0]*v_fin[1] - v_ini[1]*v_fin[0];  // = v_ini[0]*1 - v_ini[1]*0 = v_ini[0]
        
        float A_norm = sqrt(A[0]*A[0] + A[2]*A[2]); // sqrt(A[0]*A[0] + A[1]*A[1] + A[2]*A[2]);
        // if (A_norm < 0.001f) {
        //     rm.m[0][0] = 1; rm.m[0][1] = 0; rm.m[0][2] = 0;
        //     rm.m[1][0] = 0; rm.m[1][1] = 1; rm.m[1][2] = 0;
        //     rm.m[2][0] = 0; rm.m[2][1] = 0; rm.m[2][2] = 1;
        //     return;
        // }
        
        float alpha = acos(v_ini[1] / v_ini_norm);
        
        float q0 = cos(alpha / 2.0f);
        float q1 = sin(alpha / 2.0f) * (A[0] / A_norm);
        float q2 = sin(alpha / 2.0f) * (A[1] / A_norm);
        float q3 = sin(alpha / 2.0f) * (A[2] / A_norm);
        
        rm.m[0][0] = 1 - 2*(q2*q2 + q3*q3);
        rm.m[0][1] = 2*(q1*q2 - q0*q3);
        rm.m[0][2] = 2*(q0*q2 + q1*q3);
        
        rm.m[1][0] = 2*(q1*q2 + q0*q3);
        rm.m[1][1] = 1 - 2*(q1*q1 + q3*q3);
        rm.m[1][2] = 2*(q2*q3 - q0*q1);
        
        rm.m[2][0] = 2*(q1*q3 - q0*q2);
        rm.m[2][1] = 2*(q0*q1 + q2*q3);
        rm.m[2][2] = 1 - 2*(q1*q1 + q2*q2);

        rm.ready = true;
    }
    
    // Devuelve el vector rotado segun la matriz de rotacion
    void apply_rotation(float vec[3], float result[3], uint8_t p) {
        result[0] = r_matrix[p].m[0][0]*vec[0] + r_matrix[p].m[0][1]*vec[1] + r_matrix[p].m[0][2]*vec[2];
        result[1] = r_matrix[p].m[1][0]*vec[0] + r_matrix[p].m[1][1]*vec[1] + r_matrix[p].m[1][2]*vec[2];
        result[2] = r_matrix[p].m[2][0]*vec[0] + r_matrix[p].m[2][1]*vec[1] + r_matrix[p].m[2][2]*vec[2];
    }
    
    // RawData -> Units -> Aplica Filtro -> Aplica MR (acc & gyr)
    void prepross_ufrm(const IMUSample& sample, uint8_t p) {
        ProcessedSample& p_sample = processed_buffer[p][sample.no_sample % BUFFER_SIZE];
        // Convertir a unidades físicas
        float gyro[3], acc[3];
        for (int i = 0; i < 3; i++) {
            gyro[i] = sample.gyro[i] / GYRO_LSB_TO_DPS;
            acc[i] = sample.acc[i] / ACC_LSB_TO_MS2;
        }

        // std::cout << pos << " ";
        // for (int i = 0; i < 3; i++) printf("%.2f ", gyro[i]);
        // for (int i = 0; i < 3; i++) printf("%.2f ", acc[i]);
        // std::cout << std::endl;
        
        // Aplicar filtro IIR
        for (int i = 0; i < 3; i++) {
            gyro[i] = filter_gyro[i].apply(gyro[i], tracker[p].first);
            acc[i] = filter_acc[i].apply(acc[i], tracker[p].first);
        }
        
        // Aplicar matriz de rotación
        float gyro_rotated[3], acc_rotated[3];
        apply_rotation(gyro, gyro_rotated, p);
        apply_rotation(acc, acc_rotated, p);
        
        // Save the processed sample in the processed_buffer
        for (int i = 0; i < 3; i++) {
            p_sample.gyro[i] = gyro_rotated[i];
            p_sample.acc[i] = acc_rotated[i];
        }
    }
    
    // logica Segmentador automatico
    void automatic_seg(uint32_t idx, uint32_t no_sample, uint8_t p) {
        float value = processed_buffer[p][idx].gyro[1]; // [0]=X, [1]=Y, [2]=Z
        bool cruce_detectado = false;

        // Are we in the THRESHOLD?
        in_threshold = (fabs(value) < THRESHOLD);
        
        // If this is not the firts sample
        if (!tracker[p].first) {
            // If we traspass the THRESHOLD without touching it
            if (value*prev_value < -(THRESHOLD*THRESHOLD) && !in_threshold && !was_in_threshold) cruce_detectado = true;
            // If change from be in/out the threshold to out/in the threshold
            if (in_threshold != was_in_threshold) cruce_detectado = true;
        } else {
            // Primera muestra (o reinicio) -> reset de variables
            first_cruce = true;
            memset(&seg_actual, 0, sizeof(seg_actual));
            memset(&seg_previo, 0, sizeof(seg_previo));
        }
        
        // loop over the values
        was_in_threshold = in_threshold;
        prev_value = value;

        // If we are in a open segment -> calculate the area
        if (!cruce_detectado && !first_cruce) seg_actual.area += value;
        else {
            // Start of the first segment!
            if (first_cruce) {
                seg_actual.start = no_sample;
                seg_actual.area = value;
                first_cruce = false;
            } else {
                // End of a segment
                seg_actual.area += value;
                seg_actual.end = no_sample;

                // Get the segment len, area and sign
                seg_actual.len = seg_actual.end - seg_actual.start + 1;
                seg_actual.sign = (seg_actual.area > 0) ? 1 : -1;
                float a = fabs(seg_actual.area);

                // printf("P%d-%d l:%d\n", seg_actual.start, seg_actual.end, seg_actual.len);
                
                // Check if is a valid segment
                bool v = true;
                if (seg_actual.len < MIN_SEG_LEN || seg_actual.len > MAX_SEG_LEN) v = false;
                if (a < MIN_AREA || a > MAX_AREA) v = false;

                if(!v) std::cout << RED << "X" << RST << std::flush;
                else {
                    if (seg_actual.sign == 1) std::cout << GRN << "[+]" << RST << std::flush;
                    else std::cout << GRN << "[-]" << RST << std::flush;
                }

                // If is a valid segment
                if (v) {
                    // Check the secuence
                    if (seg_previo.area != 0 && // Si ya tenemos un segmento previo
                        seg_previo.sign == SEC_EJ[0] && // Y cumplimos la secuencia
                        seg_actual.sign == SEC_EJ[1]) {
                            
                            // VALIDACION FINAL!! - Calculate the total len
                            int tl = seg_actual.end - seg_previo.start + 1;
                            // printf("P[%d-%d l:%d] -> ", seg_previo.start, seg_actual.end, tl);
                            // printf("Possible Exercise -> ");
                            std::cout << "\nPossible exercise: " << std::flush;
                            // If the total len is ok
                            if (tl >= MIN_EXERCISE_LEN && tl <= MAX_EXERCISE_LEN) {
                                uint32_t start_idx = seg_previo.start % BUFFER_SIZE;
                                // printf("Possible exercise [%d-%d l:%d] -> ", seg_previo.start, seg_actual.end, tl);
                                // printf("Possible exercise: ");
                                get_attributes(start_idx, idx, tl, p);
                            } else std::cout << RED << " Out of range\n" << RST << std::endl;
                            
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
                seg_actual.start = no_sample;
                seg_actual.area = value;
            }
        }
    }

    // Obtiene los atributos y llama a mlp_classifier
    void get_attributes(uint32_t start_pos, uint32_t end_pos, int l, uint8_t p) {
        Attb sensor;
        sensor.NS = l;
        for (int i = 0; i < 3; i++) {sensor.SumEA[i] = 0; sensor.SumEG[i] = 0;}
        
        for (uint32_t s = start_pos; s != (end_pos + 1) % BUFFER_SIZE; s = (s + 1) % BUFFER_SIZE) {
            for (int i = 0; i < 3; i++) {
                sensor.SumEG[i] += processed_buffer[p][s].gyro[i] * processed_buffer[p][s].gyro[i];
                sensor.SumEA[i] += processed_buffer[p][s].acc[i] * processed_buffer[p][s].acc[i];
            }
        }
        if(mlp_classifier(sensor)) std::cout << GRN << "Well-performed\n" << RST << std::endl;
        else std::cout << YLL << "Poorly performed\n" << RST << std::endl;
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
    // Apertura y configuracion de serial
    SerialPort(const std::string& port, int baudrate = 230400) : hSerial(INVALID_HANDLE_VALUE), port_name(port) {
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

    // Cierra el puerto serial
    ~SerialPort() {
        if (hSerial != INVALID_HANDLE_VALUE) {
            CloseHandle(hSerial);
            std::cout << "Puerto serial cerrado" << std::endl;
        }
    }

    // Regresa true si el puerto/handle es válido
    bool is_open() const {return hSerial != INVALID_HANDLE_VALUE;}

    // Escribe "len" bytes en el serial
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

    // Lee hasta "len" bytes disponibles
    DWORD read_bytes(uint8_t* buffer, DWORD len) {
        if (!is_open()) return 0;
        DWORD bytes_read = 0;
        // Regresa los bytes que tenga
        if (!ReadFile(hSerial, buffer, len, &bytes_read, NULL)) {return 0;}// Hubo un error
        return bytes_read; // Devuelve 0 si hubo timeout
    }

    // Envia los comandos (arreglos de bytes) por serial port
    void send_command(const std::vector<uint8_t>& cmd) {
        if (write_bytes(cmd.data(), cmd.size())) {
            std::cout << "TX-CMD: ";
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
        int sent = sendto(sockfd, (const char*)&sample, sizeof(sample), 0, (struct sockaddr*)&server_addr, sizeof(server_addr));
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
    
    // arreglo de buffers (datos crudos) para los nodos sensores
    IMUSample buffers[NUM_PERIPHERALS][BUFFER_SIZE];
    PacketTracker trackers[NUM_PERIPHERALS];
    
    std::atomic<bool> running;
    std::thread rx_thread;
    std::thread udp_thread;
    std::thread process_thread;
    
    // cola para udp_thread
    std::queue<IMUSampleUDP> udp_queue;
    std::mutex udp_mutex;

    struct rx_pkt {
        uint8_t p = 0;
        uint32_t no_sample = 0;
    };
    size_t MIN_PKT_LEN;
    
    // cola para process_thread
    std::queue<rx_pkt> process_queue;
    std::mutex process_mutex;
    
    FILE* bin_file;
    std::string bin_filename;
    
    uint32_t packets_received[NUM_PERIPHERALS] = {0};
    uint32_t packets_lost[NUM_PERIPHERALS] = {0};
    uint32_t total_packets_written = 0;
    
    EventDetector event_detector;

public:
    IMUReceiver(const std::string& port, int baudrate = 230400):
        serial(port, baudrate),
        running(false),
        bin_file(nullptr)
        {
            MIN_PKT_LEN = 3 + 4 + (SAMPLES_PER_PACKET * (4*2 + 3*2 + 3*2)); // (quat + acc + gyr)
            std::cout << "Min PKT len: " <<(int)MIN_PKT_LEN << std::endl;
    } 

    ~IMUReceiver() {stop();}

    // Envia la secuencia de comandos de "start" al nodo central
    bool initialize() {
        if (!serial.is_open()) {
            std::cerr << "Error: Puerto serial no disponible" << std::endl;
            return false;
        }

        std::cout << "\n=== TX START CMD's ===" << std::endl;
        // std::this_thread::sleep_for(std::chrono::milliseconds(5000));
        serial.send_command({0x7E, 0x00, 0x18, 0x7F}); // Print logs/info OFF
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
        serial.send_command({0x7E, 0x00, 0x17, 0x7F}); // UART TX Eneable
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
        serial.send_command({0x7E, 0x03, 0x00, 0xFF, 0x03, 0x01, 0x7F}); // Start to all peripherals
        return true;
    }

    // Inicia los hilos
    void start() {
        if (running) return;
        running = true;
        rx_thread = std::thread(&IMUReceiver::reception_loop, this);
        // udp_thread = std::thread(&IMUReceiver::udp_loop, this);
        process_thread = std::thread(&IMUReceiver::processing_loop, this);
        std::cout << "Threads iniciados (RX + Process)" << std::endl;
    }

    // Envia la secuencia de comandos de "stop" al nodo central y detiene hilos
    void stop() {
        if (!running) return;

        std::cout << "\nTX STOPS CMD's" << std::endl;
        //                  Start,  len,  CMD, PAYLOAD........., end.
        serial.send_command({0x7E, 0x03, 0x00, 0xFF, 0x03, 0x00, 0x7F}); // Stop to all peripherals
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        serial.send_command({0x7E, 0x00, 0x16, 0x7F}); // UART TX Disable
        // std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        // serial.send_command({0x7E, 0x00, 0x19, 0x7F}); // Print logs/info ON

        std::cout << "\nStop threads..." << std::endl;
        running = false;
        if (rx_thread.joinable()) rx_thread.join();
        // if (udp_thread.joinable()) udp_thread.join();
        if (process_thread.joinable()) process_thread.join();
        print_statistics();
    }

private:
    // Get the time and convert to string
    std::string generate_filename() {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        struct tm* tm_ptr = localtime_compat(&time_t);
        char buffer[64];
        strftime(buffer, sizeof(buffer), "%Y-%m-%d_%H-%M-%S.bin", tm_ptr);
        return std::string(buffer);
    }

    // Creat bin file and pkt's reconstruction
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

                // lógica de máquina de estados
                if (byte == PKT_START_BYTE) {
                    pos = 0;
                    // rx_buffer[pos++] = byte;
                    continue;
                } else {
                    if (byte == PKT_END_BYTE && pos > 0) {
                        // for (int i = 0; i < pos; i++) printf("%02X ", rx_buffer[i]);
                        // printf("[%zu]\n\n", pos);
                        fwrite(rx_buffer, pos, 1, bin_file);
                        total_packets_written++;
                        parse_packet(rx_buffer, pos);
                        // in_packet = false;
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

    // Detect gaps and save data in the raw struct -> send imu_data to process_loop
    void parse_packet(const uint8_t* pkt, size_t len) {
        if (len < MIN_PKT_LEN) return;
        
        // uint8_t pkt_len = pkt[0];
        // uint8_t msg_type = pkt[1];
        uint8_t peripheral_id = pkt[2];
        
        // if (msg_type != MSG_TYPE_SENSOR_DATA) return;
        if (peripheral_id >= NUM_PERIPHERALS) return;
        
        const uint8_t* payload = &pkt[3];
        uint32_t packet_num = payload[0] | (payload[1] << 8) | (payload[2] << 16) | (payload[3] << 24); // Little-Endian
        // std::cout <<(int)peripheral_id<<" "<<(int)len<<" "<<(int)packet_num<< std::endl;

        // Deteccion de paquetes perdidos
        PacketTracker& tracker = trackers[peripheral_id];
        if (!tracker.first_packet) {
            uint32_t expected = tracker.last_packet_num + 1;
            if (packet_num > expected) {
                uint32_t lost_count = packet_num - expected;
                packets_lost[peripheral_id] += lost_count;
                std::cout <<"P"<<(int)peripheral_id<<"-LP="<<(int)lost_count
                <<" "<<(int)tracker.last_packet_num<<"-"<<(int)packet_num<< std::endl;
                
                // // En caso de perdidas marcar "valid" como falso e indicar el numero de muestra
                // uint32_t lost_sample = expected * SAMPLES_PER_PACKET;
                // uint32_t lost_sample_idx = lost_sample % BUFFER_SIZE;
                // for (uint32_t i = 0; i < (lost_count * SAMPLES_PER_PACKET); i++) {
                //     if (i >= BUFFER_SIZE) break;
                //     // buffers[peripheral_id][lost_sample_idx].no_sample = lost_sample;
                //     buffers[peripheral_id][lost_sample_idx].valid = false;
                //     lost_sample++;
                //     lost_sample_idx = lost_sample % BUFFER_SIZE;
                // }
            }
        }
        
        tracker.last_packet_num = packet_num;
        tracker.first_packet = false;
        packets_received[peripheral_id]++;
        
        const uint8_t* data = &payload[4];
        for (int i = 0; i < SAMPLES_PER_PACKET; i++) {
            IMUSample& sample = buffers[peripheral_id][(packet_num * SAMPLES_PER_PACKET + i) % BUFFER_SIZE];
            sample.no_sample = packet_num * SAMPLES_PER_PACKET + i;
            
            for (int j = 0; j < 4; j++) {
                sample.quat[j] = (int16_t)((uint16_t)data[0] | ((uint16_t)data[1] << 8));
                data += 2;
            }
            for (int j = 0; j < 3; j++) {
                sample.acc[j] = (int16_t)((uint16_t)data[0] | ((uint16_t)data[1] << 8));
                data += 2;
            }
            for (int j = 0; j < 3; j++) {
                sample.gyro[j] = (int16_t)((uint16_t)data[0] | ((uint16_t)data[1] << 8));
                data += 2;
            }

            // IMUSampleUDP udp_sample;
            // udp_sample.peripheral_id = peripheral_id;
            // udp_sample.sample_num = sample_num;
            // udp_sample.sample = sample;
            // {
            //     std::lock_guard<std::mutex> lock(udp_mutex);
            //     udp_queue.push(udp_sample);
            // }
            
            // Pass the sample to the processing loop!!!
            rx_pkt sample_ready;
            sample_ready.p = peripheral_id;
            sample_ready.no_sample = sample.no_sample;
            std::lock_guard<std::mutex> lock(process_mutex);
            process_queue.push(sample_ready);
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

    // Calculate rotation_matrix & 
    void processing_loop() {
        std::cout << "[Process Thread] Iniciado - Segmentador IAAC Periferico 0" << std::endl;
        while (running) {
            std::vector<rx_pkt> batch;
            {
                std::lock_guard<std::mutex> lock(process_mutex);
                size_t count = std::min(process_queue.size(), static_cast<size_t>(20));
                for (size_t i = 0; i < count; i++) {
                    batch.push_back(process_queue.front());
                    process_queue.pop();
                }
            }
            if (batch.empty()) std::this_thread::sleep_for(std::chrono::milliseconds(20));
            else {for (const rx_pkt& pkt : batch) {event_detector.process_sample(buffers[pkt.p], pkt.no_sample, pkt.p);}}
        }
        std::cout << "[Process Thread] Terminado" << std::endl;
    }

    void print_statistics() {
        std::cout << "\n=== ESTADISTICAS ===" << std::endl;
        std::cout << "Archivo: " << bin_filename << std::endl;
        std::cout << "Paquetes raw escritos: " << total_packets_written << std::endl;
        
        for (int i = 0; i < NUM_PERIPHERALS; i++) {
            std::cout<<"  P"<<i<<": "<<packets_received[i]<<" paquetes recibidos, "<<packets_lost[i]<<" perdidos";
            
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
    habilitarANSI();
    
    std::cout << "=== IMU Receiver System (Windows/MinGW) ===" << std::endl;
    std::cout << "Puerto: " << port << std::endl;
    std::cout << "Baudrate: 230400" << std::endl;
    std::cout << "Perifericos: " << NUM_PERIPHERALS << std::endl;
    std::cout << "Buffer: " << BUFFER_SIZE << " muestras/periferico" << std::endl;
    // std::cout << "UDP: localhost:4000" << std::endl;
    std::cout << "Segmentador: IAAC en Nodo " << (int)MAIN_SENSOR << std::endl;
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