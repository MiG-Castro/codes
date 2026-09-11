// BNO units: Gyr = DPS, Acc = M/S2 (internamente se pasa a "g")

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
#include <condition_variable>
// Windows headers
#include <winsock2.h>
#include <windows.h>
#include <ws2tcpip.h>
// sonido
#include <mmsystem.h>
#pragma comment(lib, "winmm.lib")

// Incluir pesos de la red neuronal
#include "mlp_weights.h"

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
#define SP_MS_TO_WAIT 5 // Sleep time (ms) to wait for the receipt of new packages
#define IA_MS_TO_WAIT 40 // maximum waiting time (ms) to receive the samples of all nodes

#define NUM_PERIPHERALS 2
#define MAIN_SENSOR 0
#define BUFFER_SIZE 768
#define SAMPLES_PER_PACKET 3
#define NO_SAMPLES_ROT_MATX 60

#define PKT_START_BYTE 0x7E
#define PKT_END_BYTE   0x7F
#define MSG_TYPE_SENSOR_DATA 0x60

#define ACC_LSB_TO_MS2 100.0f
#define ACC_MS2_TO_G 9.80665f
#define ACC_RAW_TO_G 980.665f
#define GYRO_LSB_TO_DPS 16.0f

// RAW DATA!!!
struct IMUSample {
    uint32_t no_sample = 0; // Number of the sample
    int16_t quat[4] = {0};  // Raw quat data
    int16_t acc[3] = {0};   // Raw acc data
    int16_t gyro[3] = {0};  // Raw gyro data
    std::chrono::steady_clock::time_point rx_time;
    // bool valid;
};

// Process Data (units, filter ...)
struct ProcessedSample {
    uint32_t no_sample;
    float gyro[3] = {0};
    float acc[3] = {0};
    std::chrono::steady_clock::time_point rx_time;
};

// uint32 Last pkt & bool first_pkt
struct PacketTracker {
    uint32_t last_packet_num;
    bool first_packet;
    PacketTracker() : last_packet_num(0xFFFFFFFF), first_packet(true) {}
};

struct ExerciseDetected {
    uint32_t start_sample;
    uint32_t end_sample;
    int len;
};

// ID & no sample
struct rx_pkt {
    uint8_t p = 0;
    uint32_t no_sample = 0;
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
// DETECTOR Y CLASIFICADOR (Segmentación e IA)
// ============================================================================
class DetectorAndClassifier {
private:
    ProcessedSample (*processed_buffer)[BUFFER_SIZE];
    std::atomic<uint32_t>* latest_preprocessed;
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
    bool first_sample = true;
    bool first_cruce = true;
    bool in_threshold = false;
    bool was_in_threshold = false;
    float prev_value = 0.0f;

    // Variables and values for the exercise segmentation
    const int MIN_SEG_LEN = 20;      // 35;
    const int MAX_SEG_LEN = 130;
    const float MIN_AREA = 100.0f;   // 400.0f;
    const float MAX_AREA = 4000.0f;
    const int MIN_EXERCISE_LEN = 40; // 100;
    const int MAX_EXERCISE_LEN = 400;
    const float THRESHOLD = 5.0f;
    const int SEC_EJ[2] = {1, -1};

    ExerciseDetected exercice; // **************************************************
    bool ejercicio_pendiente = false; // *******************************************
    std::chrono::steady_clock::time_point last_chance; // ***************************

    double sigmoid(double x) {return 1.0 / (1.0 + exp(-x));}

    // Normalize the atributes for the ML
    double norm(double input, double min, double max) {
        // Protección para evitar división por cero
        if (max - min == 0) return 0.0;
        double resultado = 2.0 * ((input - min) / (max - min)) - 1.0;
        // En caso de valor maximo/minimo inesperado
        if (resultado > 1.0) resultado = 1.0;
        if (resultado < -1.0) resultado = -1.0;
        return resultado;
    }

public:
    DetectorAndClassifier(ProcessedSample (*buffer)[BUFFER_SIZE], std::atomic<uint32_t>* latest)
     : processed_buffer(buffer), latest_preprocessed(latest) {}

     // Check one sensor signal to detect a possible exercice
    void automatic_seg(uint32_t idx, uint32_t no_sample, uint8_t p) {
        if (p != MAIN_SENSOR) return;

        float value = processed_buffer[p][idx].gyro[1]; // [0]=X, [1]=Y, [2]=Z
        bool cruce_detectado = false;

        // Are we in the THRESHOLD?
        in_threshold = (fabs(value) < THRESHOLD);
        
        // If this is not the firts sample
        if (!first_sample) {
            // If we traspass the THRESHOLD without touching it
            if (value*prev_value < -(THRESHOLD*THRESHOLD) && !in_threshold && !was_in_threshold) cruce_detectado = true;
            // If change from be in/out the threshold to out/in the threshold
            if (in_threshold != was_in_threshold) cruce_detectado = true;
        } else {
            // Primera muestra (o reinicio) -> reset de variables
            first_cruce = true;
            first_sample = false;
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

                // if(!v) std::cout << RED << "X" << RST << std::flush;
                // else {
                //     if (seg_actual.sign == 1) std::cout << GRN << "[+]" << RST << std::flush;
                //     else std::cout << GRN << "[-]" << RST << std::flush;
                // }

                // If is a valid segment
                if (v) {
                    // Check the secuence
                    if (seg_previo.area != 0 && // Si ya tenemos un segmento previo
                        seg_previo.sign == SEC_EJ[0] && // Y cumplimos la secuencia
                        seg_actual.sign == SEC_EJ[1]) {
                            
                            // VALIDACION FINAL!! - Calculate the total len
                            int tl = seg_actual.end - seg_previo.start + 1;
                            std::cout << "\nPE: " << std::flush;
                            // printf("Possible exercise [%d-%d l:%d] -> ", seg_previo.start, seg_actual.end, tl);

                            // EXERCISE DETECTED!!!!!!
                            if (tl >= MIN_EXERCISE_LEN && tl <= MAX_EXERCISE_LEN) {
                                // save the time window of the possible exercise
                                exercice.start_sample = seg_previo.start;
                                exercice.end_sample = seg_actual.end;
                                exercice.len = tl;
                                // verification procedure prior ML stage
                                last_chance = processed_buffer[p][idx].rx_time + std::chrono::milliseconds(IA_MS_TO_WAIT);
                                ejercicio_pendiente = true;
                                std::cout << exercice.start_sample << "-" << exercice.end_sample << "\n";
                                // if all samples ready -> pass to ML
                                // if (all_samples_ready()) machine_learning();
                                // else printf("X");
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

    // For the last Exercice detected: check if all samples from all sensor has all ready arrived
    bool all_samples_ready() {
        for (int i = 0; i < NUM_PERIPHERALS; i++) std::cout << latest_preprocessed[i].load() << "-";
        for (int i = 0; i < NUM_PERIPHERALS; i++) {
            if (latest_preprocessed[i].load() < exercice.end_sample) {
                std::cout << "False" << std::endl;
                return false;
            }
        }
        std::cout << "True"<<  std::endl;
        return true;
    }

    // Return if the system has an exercise pending to classify (if the system is waiting for all samples to arrive)
    bool has_pending_exercise() const { return ejercicio_pendiente; }

    // get the limit time for wait the arrive of all samples
    std::chrono::steady_clock::time_point get_timeout() const { return last_chance; }

    // For the last Exercice detected: Check if the time limit has passed
    bool check_timeout() {
        if (std::chrono::steady_clock::now() >= last_chance) {
            std::cout << RED << "T " << RST;
            return true;
        } else {
            std::cout << YLL << "t " << RST;
            return false;
        }
    }

    // get the attributes and classify the exercice
    void machine_learning() {
        ejercicio_pendiente = false;
        uint8_t p = MAIN_SENSOR;
        uint32_t start_pos = exercice.start_sample %  BUFFER_SIZE;
        uint32_t end_pos = exercice.end_sample %  BUFFER_SIZE;

        Attb sensor;
        sensor.NS = exercice.len;
        for (int i = 0; i < 3; i++) {sensor.SumEA[i] = 0; sensor.SumEG[i] = 0;}
        
        for (uint32_t s = start_pos; s != (end_pos + 1) % BUFFER_SIZE; s = (s + 1) % BUFFER_SIZE) {
            for (int i = 0; i < 3; i++) {
                sensor.SumEG[i] += processed_buffer[p][s].gyro[i] * processed_buffer[p][s].gyro[i];
                sensor.SumEA[i] += processed_buffer[p][s].acc[i] * processed_buffer[p][s].acc[i];
            }
        }

        if(mlp_classifier(sensor)) {
            PlaySound(TEXT("SystemNotification"), NULL, SND_ALIAS | SND_ASYNC);
            std::cout << GRN << "Well-performed\n" << RST << std::endl;
        } else {
            PlaySound(TEXT("SystemHand"), NULL, SND_ALIAS | SND_ASYNC);
            std::cout << YLL << "Poorly performed\n" << RST << std::endl;
        }
    }

    // MLP algorithm
    int mlp_classifier(Attb in) {
        // NORMALIZAR ENTRADAS (Rango -1 a 1)
        in.SumEG[0] = norm(in.SumEG[0], r.MinEG[0], r.MaxEG[0]);
        in.SumEG[1] = norm(in.SumEG[1], r.MinEG[1], r.MaxEG[1]);
        in.SumEG[2] = norm(in.SumEG[2], r.MinEG[2], r.MaxEG[2]);
        in.SumEA[0] = norm(in.SumEA[0], r.MinEA[0], r.MaxEA[0]);
        in.SumEA[1] = norm(in.SumEA[1], r.MinEA[1], r.MaxEA[1]);
        in.SumEA[2] = norm(in.SumEA[2], r.MinEA[2], r.MaxEA[2]);
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
};

// ============================================================================
// PRE-PROCESS (Convert to units, Rotation matrix, Filter, Interpolation ...)
// ============================================================================
class PreProcess {
private:
    ProcessedSample (*processed_buffer)[BUFFER_SIZE]; // Referencia al buffer global

    struct TrackSample {
        uint32_t last; // last rx_sample processed
        bool first = true;
    };
    TrackSample tracker[NUM_PERIPHERALS];

    struct RotationMatrix {
        uint16_t rx_samples_count; // start in 0, "max" = NO_SAMPLES_ROT_MATX
        uint16_t list_no_samp[NO_SAMPLES_ROT_MATX];
        int16_t raw_acc[3][NO_SAMPLES_ROT_MATX];   // Values to use in the rotation matrix
        float m[3][3];  // Rotation matrix
        bool ready;     // State of the rotation matrix, True=Matrix Ready
        RotationMatrix() : rx_samples_count(0), ready(false){}
    };
    RotationMatrix r_matrix[NUM_PERIPHERALS];
    
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
    
public:
    // Constructor recibe la dirección del buffer para escribir en él
    PreProcess(ProcessedSample (*buffer)[BUFFER_SIZE]) : processed_buffer(buffer) {}

    // Convierta a unidades, filtra, MR, rellena muestras perdidas y pasa las muestras listas a DetectorAndClassifier
    void process_sample(IMUSample* raw_buffers, uint32_t num_samp, uint8_t p, std::vector<rx_pkt>& ready_for_ia) {
        IMUSample& sample = raw_buffers[num_samp % BUFFER_SIZE];

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
                ready_for_ia.push_back({p, lost_sample});
                x++;
            }
        }

        // Pass to the DetectorAndClassifier
        ready_for_ia.push_back({p, sample.no_sample});
        tracker[p].last = sample.no_sample;
        tracker[p].first = false;
    }

private:
    // calcula matriz de rotacion. Toma como entrada el vector de valores promediados de try_calibrate
    void calculate_rotation_matrix(RotationMatrix& rm) {
        float acc_avg[3] = {0.0f}, k;
        int32_t acc_sum[3] = {0};

        k = (float)NO_SAMPLES_ROT_MATX * ACC_LSB_TO_MS2 * ACC_MS2_TO_G;
        for (int s = 0; s < NO_SAMPLES_ROT_MATX; s++) {for (int i = 0; i < 3; i++) acc_sum[i] += rm.raw_acc[i][s];}
        for (int i = 0; i < 3; i++) acc_avg[i] = (float)acc_sum[i] / k;
        
        double v_ini[3] = {(double)acc_avg[0], (double)acc_avg[1], (double)acc_avg[2]};
        double v_fin[3] = {0, 1, 0};
        double v_ini_norm = sqrt(v_ini[0]*v_ini[0] + v_ini[1]*v_ini[1] + v_ini[2]*v_ini[2]);
        
        // Eje de rotación: A = cross(v_ini, v_fin) (v_fin = [0, 1, 0])
        double A[3];
        A[0] = -v_ini[2];   // v_ini[1]*v_fin[2] - v_ini[2]*v_fin[1]; => v_ini[1]*0 - v_ini[2]*1 = -v_ini[2]
        A[1] = 0.0;         // v_ini[2]*v_fin[0] - v_ini[0]*v_fin[2]; => v_ini[2]*0 - v_ini[0]*0 = 0
        A[2] = v_ini[0];    // v_ini[0]*v_fin[1] - v_ini[1]*v_fin[0]; => v_ini[0]*1 - v_ini[1]*0 = v_ini[0]
        double A_norm = sqrt(A[0]*A[0] + A[2]*A[2]); // sqrt(A[0]*A[0] + A[1]*A[1] + A[2]*A[2]);
        
        const double A_norm_eps = 1e-9;
        if (A_norm < A_norm_eps) {
            printf("[RM]: A_norm ~ 0 (sensor ya alineado con eje Y). Se usa matriz identidad.\n");
            rm.m[0][0] = 1.0f; rm.m[0][1] = 0.0f; rm.m[0][2] = 0.0f;
            rm.m[1][0] = 0.0f; rm.m[1][1] = 1.0f; rm.m[1][2] = 0.0f;
            rm.m[2][0] = 0.0f; rm.m[2][1] = 0.0f; rm.m[2][2] = 1.0f;
            rm.ready = true;
            return;
        }

        double cos_alpha = v_ini[1] / v_ini_norm;
        if (cos_alpha > 1.0)  cos_alpha = 1.0;
        if (cos_alpha < -1.0) cos_alpha = -1.0;
        double alpha = acos(cos_alpha);
        
        double q0 = cos(alpha / 2.0);
        double q1 = sin(alpha / 2.0) * (A[0] / A_norm);
        double q2 = sin(alpha / 2.0) * (A[1] / A_norm);
        double q3 = sin(alpha / 2.0) * (A[2] / A_norm);
        
        rm.m[0][0] = (float)(1 - 2*(q2*q2 + q3*q3));
        rm.m[0][1] = (float)(2*(q1*q2 - q0*q3));
        rm.m[0][2] = (float)(2*(q0*q2 + q1*q3));
        
        rm.m[1][0] = (float)(2*(q1*q2 + q0*q3));
        rm.m[1][1] = (float)(1 - 2*(q1*q1 + q3*q3));
        rm.m[1][2] = (float)(2*(q2*q3 - q0*q1));
        
        rm.m[2][0] = (float)(2*(q1*q3 - q0*q2));
        rm.m[2][1] = (float)(2*(q0*q1 + q2*q3));
        rm.m[2][2] = (float)(1 - 2*(q1*q1 + q2*q2));

        rm.ready = true;
        printf("[PP] Rotation Matrix: Average Acc X=%.3f, Y=%.3f, Z=%.3f, \n", acc_avg[0], acc_avg[1], acc_avg[2]);
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
            acc[i] = sample.acc[i] / ACC_RAW_TO_G;
            // if (i==2) printf("%.2f, %.2f, %.2f\n", acc[0], acc[1], acc[2]);
        }
        
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

        p_sample.rx_time = sample.rx_time; // reception time (serial port)
        // p_sample.rx_time = std::chrono::steady_clock::now();
        
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
    // Apertura y configuracion de serial 230400
    SerialPort(const std::string& port, int baudrate = 1000000) : hSerial(INVALID_HANDLE_VALUE), port_name(port) {
        std::string full_port = "\\\\.\\" + port;
        hSerial = CreateFileA(full_port.c_str(), GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
        if (hSerial == INVALID_HANDLE_VALUE) {
            std::cerr << "[SP] Error(" << GetLastError() << "): unable to open port " << port << std::endl;
            return;
        }

        DCB dcbSerialParams;
        memset(&dcbSerialParams, 0, sizeof(dcbSerialParams));
        dcbSerialParams.DCBlength = sizeof(dcbSerialParams);

        if (!GetCommState(hSerial, &dcbSerialParams)) {
            std::cerr << "[SP] Error: Port info" << std::endl;
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
            std::cerr << "[SP] Error: Cofig Port" << std::endl;
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
            std::cerr << "[SP] Error: timeouts" << std::endl;
            CloseHandle(hSerial);
            hSerial = INVALID_HANDLE_VALUE;
            return;
        }

        std::cout << "[SP] " << port << " - baud rate " << baudrate << std::endl;
    }

    // Cierra el puerto serial
    ~SerialPort() {
        if (hSerial != INVALID_HANDLE_VALUE) {
            CloseHandle(hSerial);
            std::cout << "[SP] Serial port closed" << std::endl;
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
            std::cout << "[SP] TX: ";
            for (auto b : cmd) printf("%02X ", b);
            std::cout << std::endl;
        }
    }
};

// ============================================================================
// SISTEMA PRINCIPAL
// ============================================================================
class IMUReceiver {
private:
    SerialPort serial;
    
    IMUSample buffers[NUM_PERIPHERALS][BUFFER_SIZE];  // Raw-Data
    ProcessedSample processed_buffer[NUM_PERIPHERALS][BUFFER_SIZE]; // Processed Data (Global compartida)
    PacketTracker trackers[NUM_PERIPHERALS];
    std::atomic<uint32_t> latest_preprocessed[NUM_PERIPHERALS]; // rastreador maestro atómico
    
    // Instancias de clases de la tubería
    PreProcess pre_process;
    DetectorAndClassifier detector;

    std::atomic<bool> running;
    std::thread rx_thread;
    // std::thread udp_thread;
    std::thread process_thread;
    std::thread ia_thread;
    
    // cola para udp_thread
    std::queue<ProcessedSample> udp_queue;
    std::mutex udp_mutex;

    // Cola 1: RX a PreProcess
    std::queue<rx_pkt> process_queue;
    std::mutex process_mutex;
    std::condition_variable process_cv;
    
    // Cola 2: PreProcess a IA
    std::queue<rx_pkt> ia_queue;
    std::mutex ia_mutex;
    std::condition_variable ia_cv;

    FILE* bin_file;
    std::string bin_filename;
    bool save_to_bin;

    size_t MIN_PKT_LEN;
    uint32_t packets_received[NUM_PERIPHERALS] = {0};
    uint32_t packets_lost[NUM_PERIPHERALS] = {0};
    uint32_t total_packets_written = 0;

    std::chrono::steady_clock::time_point rx_time;

public:
    IMUReceiver(const std::string& port, bool save_bin = false, int baudrate = 1000000):
        serial(port, baudrate),
        running(false),
        bin_file(nullptr),
        save_to_bin(save_bin),
        pre_process(processed_buffer),
        detector(processed_buffer, latest_preprocessed)
        {
            for (int i = 0; i < NUM_PERIPHERALS; i++) latest_preprocessed[i].store(0);

            MIN_PKT_LEN = 3 + 4 + (SAMPLES_PER_PACKET * (4*2 + 3*2 + 3*2)); // (quat + acc + gyr)
            std::cout << "[IMU-R] Min PKT len: " <<(int)MIN_PKT_LEN << std::endl;
    } 

    ~IMUReceiver() {stop();}

    // Envia la secuencia de comandos de "start" al nodo central
    bool initialize() {
        if (!serial.is_open()) {
            std::cerr << "[IMU_R] Error: Serial port not available" << std::endl;
            return false;
        }

        std::cout << "\n[IMU-R] === TX START CMD's ===" << std::endl;
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
        ia_thread = std::thread(&IMUReceiver::ia_loop, this);
    }

    // Envia la secuencia de comandos de "stop" al nodo central y detiene hilos
    void stop() {
        if (!running) return;

        std::cout << "\n[IMU-R] TX STOPS CMD's" << std::endl;
        //                  Start,  len,  CMD, PAYLOAD........., end.
        serial.send_command({0x7E, 0x03, 0x00, 0xFF, 0x03, 0x00, 0x7F}); // Stop to all peripherals
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        serial.send_command({0x7E, 0x00, 0x16, 0x7F}); // UART TX Disable
        // std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        // serial.send_command({0x7E, 0x00, 0x19, 0x7F}); // Print logs/info ON

        std::cout << "\n[IMU-R] Stop threads..." << std::endl;
        running = false;
        process_cv.notify_all(); // despertar a los hilos para cerrarlos
        ia_cv.notify_all();

        if (rx_thread.joinable()) rx_thread.join();
        // if (udp_thread.joinable()) udp_thread.join();
        if (process_thread.joinable()) process_thread.join();
        if (ia_thread.joinable()) ia_thread.join();
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
        // std::cout << "[RX Thread] ON\n";
        if (save_to_bin) {
            bin_filename = generate_filename();
            bin_file = fopen_compat(bin_filename.c_str(), "wb");
            
            if (!bin_file) {
                std::cerr << "[RX Thread] Create/Open file error " << bin_filename << std::endl;
                return;
            } else std::cout << "[RX Thread] File open: " << bin_filename << "\n";
        }
        
        // Búfer local para leer bloques
        uint8_t temp_buffer[256], rx_buffer[256];
        size_t pos = 0;
        bool escape_next = false;

        while (running) {

            DWORD bytes_read = serial.read_bytes(temp_buffer, 256);
            if (bytes_read == 0) {
                std::this_thread::sleep_for(std::chrono::milliseconds(SP_MS_TO_WAIT));
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
                        if (save_to_bin && bin_file) {
                            fwrite(rx_buffer, pos, 1, bin_file);
                            total_packets_written++;
                        }
                        parse_packet(rx_buffer, pos);
                        process_cv.notify_one(); // Notify the process-thread --------------------------------
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

        if (save_to_bin && bin_file) fclose(bin_file);
        // std::cout << "[RX Thread] Closed\n";
    }

    // Detect gaps and save data in the raw struct -> send imu_data to pre-process
    void parse_packet(const uint8_t* pkt, size_t len) {
        if (len < MIN_PKT_LEN) return;
        
        rx_time = std::chrono::steady_clock::now();
        
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
            sample.rx_time = rx_time;
            
            // Pass the sample to the processing loop!!!
            rx_pkt sample_ready;
            sample_ready.p = peripheral_id;
            sample_ready.no_sample = sample.no_sample;
            {
                std::lock_guard<std::mutex> lock(process_mutex);
                process_queue.push(sample_ready);
            }
        }
    }

    // Preprocess data (units, rotation matrix, filter ...)
    void processing_loop() {
        // std::cout << "[Process Thread] ON\n";
        while (running) {
            std::vector<rx_pkt> batch;
            {
                std::unique_lock<std::mutex> lock(process_mutex);  // unique_lock
                process_cv.wait(lock, [this] { return !process_queue.empty() || !running; }); // Wait

                // Si el programa se detuvo y no hay datos, salir del loop
                if (!running && process_queue.empty()) break;

                size_t count = std::min(process_queue.size(), static_cast<size_t>(20));
                for (size_t i = 0; i < count; i++) {
                    batch.push_back(process_queue.front());
                    process_queue.pop();
                }
            }

            std::vector<rx_pkt> ready_for_ia;
            for (const rx_pkt& pkt : batch) {
                // envir las muestras raw recibidas a preprocesar
                pre_process.process_sample(buffers[pkt.p], pkt.no_sample, pkt.p, ready_for_ia);
            }

            // Pasar tickets al hilo de la IA
            if (!ready_for_ia.empty()) {
                std::lock_guard<std::mutex> lock(ia_mutex);
                for(const auto& item : ready_for_ia) {
                    ia_queue.push(item);
                    latest_preprocessed[item.p].store(item.no_sample);
                }
                ia_cv.notify_one();
            }
        }
        // std::cout << "[Process Thread] Closed\n";
    }

    void ia_loop() {
        // std::cout << "[IA Thread] ON - Automatic Segmentator & Neural Network\n";
        while (running) {
            std::vector<rx_pkt> batch;
            bool run_ml = false;
            {
                std::unique_lock<std::mutex> lock(ia_mutex);

                // Si hay un ejercicio "pendiente"
                if (detector.has_pending_exercise()) {
                    // Si ya tenemos todas las muestras o se llego al tiempo limite de espera -> activar clasificacion
                    if (detector.check_timeout()) run_ml = true;
                    if (detector.all_samples_ready()) run_ml = true;
                    // Si aun queda tiempo, esperamos
                    else ia_cv.wait_until(lock, detector.get_timeout(), [this] { return !ia_queue.empty() || !running; });
                
                // Si no hay ejercicio pendiente -> Esperemos nuevos datos
                } else ia_cv.wait(lock, [this] { return !ia_queue.empty() || !running; });

                // si no hay datos en la cola -> salimos
                if (!running && ia_queue.empty()) break; 

                // si hay datos los tomamos!
                size_t count = std::min(ia_queue.size(), static_cast<size_t>(20));
                for (size_t i = 0; i < count; i++) {
                    batch.push_back(ia_queue.front());
                    ia_queue.pop();
                }
            }

            if (run_ml) detector.machine_learning();
            
            // Procesar las muestras (si es que el hilo despertó por datos nuevos)
            for (const rx_pkt& pkt : batch) {
                uint32_t idx = pkt.no_sample % BUFFER_SIZE;
                detector.automatic_seg(idx, pkt.no_sample, pkt.p);
            }
        }
        // std::cout << "[IA Thread] Closed\n";
    }

    // void ia_loop() {
    //     std::cout << "[IA Thread] ON - Automatic Segmentator & Neural Network" << std::endl;
    //     while (running) {
    //         std::vector<rx_pkt> batch;
    //         {
    //             std::unique_lock<std::mutex> lock(ia_mutex);
    //             // Si hay un ejercicio "pendiente" y aun no llegan todas las muestras
    //             if (detector.has_pending_exercise() && !detector.all_samples_ready()) {
    //                 ia_cv.wait_until(lock, detector.get_timeout(), [this] { return !ia_queue.empty() || !running; });
    //             } else {
    //                 // Si no hay alarma, duerme indefinidamente hasta que lleguen datos
    //                 ia_cv.wait(lock, [this] { return !ia_queue.empty() || !running; });
    //             }

    //             // si no hay datos en la cola -> salimos
    //             if (!running && ia_queue.empty()) break; 

    //             // si hay datos los tomamos!
    //             size_t count = std::min(ia_queue.size(), static_cast<size_t>(20));
    //             for (size_t i = 0; i < count; i++) {
    //                 batch.push_back(ia_queue.front());
    //                 ia_queue.pop();
    //             }
    //         }
            
    //         // Procesar las muestras (si es que el hilo despertó por datos nuevos)
    //         for (const rx_pkt& pkt : batch) {
    //             uint32_t idx = pkt.no_sample % BUFFER_SIZE;
    //             detector.automatic_seg(idx, pkt.no_sample, pkt.p);
    //         }

    //         // Revisar en caso de que este pendiente un ejercicio
    //         detector.check_exercise_timeout();
    //     }
    //     std::cout << "[IA Thread] Closed" << std::endl;
    // }

    // // Exercise detection (signal segmentation) & classfication
    // void ia_loop() {
    //     std::cout << "[IA Thread] ON " << std::endl;
    //     while (running) {
    //         std::vector<rx_pkt> batch;
    //         {
    //             std::unique_lock<std::mutex> lock(ia_mutex);
    //             ia_cv.wait(lock, [this] { return !ia_queue.empty() || !running; });
    //             if (!running && ia_queue.empty()) break;

    //             size_t count = std::min(ia_queue.size(), static_cast<size_t>(20));
    //             for (size_t i = 0; i < count; i++) {
    //                 batch.push_back(ia_queue.front());
    //                 ia_queue.pop();
    //             }
    //         }
            
    //         for (const rx_pkt& pkt : batch) {
    //             uint32_t idx = pkt.no_sample % BUFFER_SIZE;
    //             detector.automatic_seg(idx, pkt.no_sample, pkt.p);
    //         }
    //     }
    //     std::cout << "[IA Thread] Closed" << std::endl;
    // }

    void print_statistics() {
        std::cout << "\n[IMU-R] === STATISTICS ===" << std::endl;
        if (save_to_bin) {
        std::cout << "File: " << bin_filename << std::endl;
        std::cout << "Write raw-pkts: " << total_packets_written << std::endl;
        }
        
        for (int i = 0; i < NUM_PERIPHERALS; i++) {
            std::cout<<"  P"<<i<<": "<<packets_received[i]<<" Rx-Pkts, "<<packets_lost[i]<<" lost";
            
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
    bool timer_resolution_ok = false;
    if (timeBeginPeriod(1) != TIMERR_NOERROR) std::cerr << "Error: timeBeginPeriod(1).\n";
    else timer_resolution_ok = true;

    std::string port = "COM7";
    bool save_bin = false;

    if (argc > 1) port = argv[1];
    if (argc > 2) { if (std::string(argv[2]) == "1") save_bin = true; }

    habilitarANSI();
    
    std::cout << "=== IMU Receiver - System (Windows/MinGW) ===" << std::endl;
    std::cout << "Sensor Nodes: " << NUM_PERIPHERALS << std::endl;
    std::cout << "Buffer: " << BUFFER_SIZE << " Samples per Sensor Node" << std::endl;
    // std::cout << "UDP: localhost:4000" << std::endl;
    std::cout << "Exercise:IAAC, Automatic-Segmentator: Sensor Node " << (int)MAIN_SENSOR << std::endl;
    std::cout << "============================================\n" << std::endl;

    IMUReceiver receiver(port, save_bin);
    if (!receiver.initialize()) {
        std::cout << "\nPress ENTER to stop and close..." << std::endl;
        std::cin.get();
        return 1;
    }

    receiver.start();
    std::cout << "Press ENTER to stop and close...\n" << std::endl;
    std::cin.get();
    receiver.stop();
    std::cout << "\nSystem closed." << std::endl;

    if (timer_resolution_ok) timeEndPeriod(1);
    return 0;
}