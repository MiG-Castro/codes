/*
Paquetes de 56Bytes -> NoPkt + 2 muestras (Q + A + G + M)
Modo 9DOF (Para habilitar la fusion de sensores y el magnetometro) 
*/

/***************************************************************************************************
Librerias
***************************************************************************************************/
//Comunicacion con sensores
#include <Wire.h>
// Librerias BNO
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
//Librerias LSM-Xiao
#include <LSM6DS3.h>
//Librerias BLE
#include <ArduinoBLE.h>
// Librerias TIMER (INTERRUP)
#include "NRF52_MBED_TimerInterrupt.h"

/***************************************************************************************************
Variables - Configuracion
***************************************************************************************************/
/*//LSM-Xiao
LSM6DS3 LSM_IMU(I2C_MODE, 0x6A);    //I2C device address 0x6A
float aX, aY, aZ, gX, gY, gZ;
const float accelerationThreshold = 2.5; // threshold of significant in G's */

// BLUETOOTH 
#define Payload_bytes 56
char nombreBT[] = "XiaoTX[0f]"; // NOMBRE BLE
BLEService customService("180C");
BLECharacteristic customCharacteristic("2A56", BLENotify, Payload_bytes);  //BLEIndicate BLENotify
bool conectado = false;

// Timer: Determina el perido de muestreo -> Frecuencia de transmision = (Frec muestreo / 2)
#define TIMER0_INTERVAL_us          16666 //PERIOD DE MUESTREO (500000=Tx:1Hz, 50000=Tx:10Hz, 16666=Tx:30Hz)
#define TIMER_INTERRUPT_DEBUG       0
#define _TIMERINTERRUPT_LOGLEVEL_   3
volatile bool tic_timer = false;          // BANDERA TIMER!!!
bool led_OnOFF = true;                    // Control encendido LED's
uint32_t conteo_tics;                     // Conteo de interrupciones timer
uint32_t tics_segundo = 1000000 / TIMER0_INTERVAL_us;
NRF52_MBED_Timer ITimer0(NRF_TIMER_3);

// Transmision de datos y control
uint8_t tx_pkt[Payload_bytes] = {0};        // Paquete a transmitir
uint32_t sec_pkt = 0;                 // Numero de paquete
// EN CASO DE QUERER LIMITAR LOS PAQUETES A TRANSMITIR
bool limitar_Tx = true;              // Limitar el numero de paquetes a transmitir
uint32_t max_Txpkts = 18000;          // Numero total de paquetes a transmitir. 18000 = 10min a Tx:30Hz

// Impresion de datos en serial
bool  print_serial = false,       // Activar el uso del serial
      no_pkt = false,             // Imprimir no. de paquete
      print_completo = false,     // Imprimir data del sensor
      cali = false;               // Imprimir estado calibracion

// SENSOR BNO
// Adafruit_BNO055 BNO_IMU = Adafruit_BNO055(-1, 0x28, &Wire);  // ID, I2C address
// Datos sensor
bool load_cali = true;                                // True=LoadCalibration
uint8_t sistema, gyro, accel, mag, FullCalib = 3;     // Calibracion
int16_t qw, qx, qy, qz;                               // Cuaternion  
int16_t x, y, z;                                      // Ejes
uint8_t RawAcc[6], RawGyr[6], RawMag[6], RawQua[8];   // Datos crudos leidos del registro                

// CALIBRATION OFFSETS VALUES
#define OffSet_Ax -11
#define OffSet_Ay 15
#define OffSet_Az -34
#define OffSet_Gx 0
#define OffSet_Gy 0
#define OffSet_Gz -1
#define OffSet_Mx 341
#define OffSet_My -335
#define OffSet_Mz -172
#define OffSet_AR 1000
#define OffSet_MR 752

// Registros de interes
#define R_Acc 0x08 //Sensor data output Acc
#define R_Gyr 0x14 //Sensor data output Gyr
#define R_Mag 0x0E //Sensor data output Mag
#define R_Qua 0x20 //Sensor Fusion data output Quaternions
#define R_Uni 0x3B //Sensor unit selection 
#define R_PID 0x07 //Sensor page ID registers
#define R_OpM 0x3D //Sensor Operation Mode

// Configuraciones de interes
#define MConf 0x00 //Sensor mode configuration
#define M_9DF 0x0C //Sensor mode 9DOF (FUSION MODE)
#define M_IMU 0x08 //Sensor mode IMU  (FUSION MODE - A+G)
#define M_AMG 0x07 //Sensor mode AMG  (NO FUSION)
#define U_rad 0x86 //m/s2, rps, radians, °C, Android
#define U_Deg 0x80 //m/s2, dps, degrees, °C, Android (Default)

// Motion Data
uint16_t idx = 0;
int16_t motion_data[312] = {
	13924, -8583, -193, -914, 13959, -8528, -217, -906, 14001, -8459, -244, -895,
	14079, -8328, -323, -874, 14250, -8030, -411, -847, 14385, -7786, -435, -836, 
	14546, -7477, -507, -825, 14811, -6923, -692, -817, 15059, -6358, -756, -809,
	15287, -5800, -746, -739, 15608, -4891, -711, -638, 15823, -4153, -697, -588,
	15992, -3451, -713, -538, 16176, -2443, -749, -500, 16263, -1753, -802, -491,
	16320, -1092, -812, -498, 16356, -227, -784, -486, 16352, 480, -799, -438, 
	16311, 1246, -828, -386, 16207, 2216, -856, -357, 16096, 2918, -848, -364,
	15986, 3463, -853, -393, 15820, 4150, -867, -418, 15671, 4689, -831, -419,
	15387, 5564, -751, -411, 15094, 6318, -748, -345, 14776, 7033, -770, -222,
	14008, 8471, -674, -71, 14008, 8471, -674, -71, 13366, 9458, -579, 42,
	13025, 9919, -613, 129, 12678, 10364, -503, 173, 12229, 10898, -313, 160,
	11912, 11243, -308, 206, 11912, 11243, -308, 206, 11136, 12012, -172, 324,
	10756, 12352, -126, 406, 10446, 12612, -113, 483, 10316, 12718, -25, 522,
  10316, 12718, -25, 522, 10446, 12612, -113, 483, 10756, 12352, -126, 406, 
  11136, 12012, -172, 324, 11912, 11243, -308, 206, 11912, 11243, -308, 206,
  12229, 10898, -313, 160, 12678, 10364, -503, 173, 13025, 9919, -613, 129,
  13366, 9458, -579, 42, 14008, 8471, -674, -71, 14008, 8471, -674, -71,
  14776, 7033, -770, -222, 15094, 6318, -748, -345, 15387, 5564, -751, -411,
  15671, 4689, -831, -419, 15820, 4150, -867, -418, 15986, 3463, -853, -393,
  16096, 2918, -848, -364, 16207, 2216, -856, -357, 16311, 1246, -828, -386,
  16352, 480, -799, -438, 16356, -227, -784, -486, 16320, -1092, -812, -498,
  16263, -1753, -802, -491, 16176, -2443, -749, -500, 15992, -3451, -713, -538,
  15823, -4153, -697, -588, 15608, -4891, -711, -638, 15287, -5800, -746, -739,
  15059, -6358, -756, -809, 14811, -6923, -692, -817, 14546, -7477, -507, -825,
  14385, -7786, -435, -836, 14250, -8030, -411, -847, 14079, -8328, -323, -874,
  14001, -8459, -244, -895, 13959, -8528, -217, -906, 13924, -8583, -193, -914
};
uint8_t motion_pkt[624];

// FUNCION QUE SE LLAMA EN LA INTERRUMPCION
void TimerHandler0() {
  if (conectado){
    tic_timer = true;
  }
}

void setup(void) {
  // Convertir arreglo int16 -> uint8 (le)
  for (int i = 0; i < 312; i++) {
    motion_pkt[i * 2]     = lowByte(motion_data[i]);
    motion_pkt[i * 2 + 1] = highByte(motion_data[i]);
  }


  // COnfiguramos LED's y encedemos el rojo
  pinMode(LEDB,  OUTPUT);
  pinMode(LEDG,  OUTPUT);
  pinMode(LEDR,  OUTPUT);
  digitalWrite(LEDB,  1);   // OFF
  digitalWrite(LEDG,  1);   // OFF
  digitalWrite(LEDR,  0);   // ON

  // CONFIGURACION DE SENSOR BNO
  // Inicializacion
  // if(!BNO_IMU.begin()) {
  //   Serial.print("BNO055 NO DETECTED");
  //   while(1);
  // }
  // delay(50);
  // BNO_IMU.setExtCrystalUse(true);
  // delay(50);

  // Carga de calibracion guardada
  // if (load_cali) {
  //   adafruit_bno055_offsets_t calibrationData;
  //   calibrationData.accel_offset_x  = OffSet_Ax;
  //   calibrationData.accel_offset_y  = OffSet_Ay;
  //   calibrationData.accel_offset_z  = OffSet_Az;
  //   calibrationData.gyro_offset_x   = OffSet_Gx;
  //   calibrationData.gyro_offset_y   = OffSet_Gy;
  //   calibrationData.gyro_offset_z   = OffSet_Gz;
  //   calibrationData.mag_offset_x    = OffSet_Mx;
  //   calibrationData.mag_offset_y    = OffSet_My;
  //   calibrationData.mag_offset_z    = OffSet_Mz;
  //   calibrationData.accel_radius    = OffSet_AR;
  //   calibrationData.mag_radius      = OffSet_MR;
  //   BNO_IMU.setSensorOffsets(calibrationData);
  // }
  // delay(500);
  
  // // MODO DE OPERACION y SELECCION DE UNIDADES
  // BNO_IMU.setMode(OPERATION_MODE_CONFIG);                                 // Set Modo Configuracion
  // BNO_IMU.write8((Adafruit_BNO055::adafruit_bno055_reg_t)R_PID, 0x00);    // Seleccion de Page_ID de Registro
  // BNO_IMU.write8((Adafruit_BNO055::adafruit_bno055_reg_t)R_Uni, 0x86);    // Seleccion de unidades 0x86[m/s2, rps, radians, °C, Android]
  // BNO_IMU.setMode(OPERATION_MODE_NDOF);                                   // Set Modo de Operacion 9DOF
  // delay(30);

  // CONFIGURACION BLUETOOTH
  // Inicializacion
  if (!BLE.begin()) {
    while (1);
  }

  // Servicio y caracteristicas
  BLE.setConnectionInterval(0x0006, 0x0006);                      // Interval 7.5ms
  BLE.setLocalName(nombreBT);                                     // Nombre de Bluetooth device
  BLE.setAdvertisedService(customService);                        
  customService.addCharacteristic(customCharacteristic);
  BLE.addService(customService);
  uint8_t initialValue[Payload_bytes] = {0};
  customCharacteristic.writeValue(initialValue, Payload_bytes);
  BLE.advertise();

  if (print_serial) {
    Serial.begin(115200);
    while (!Serial);  // wait for serial port to open!

    // Nombre y MAC XIAO-Bluetooth
    Serial.print(nombreBT);
    Serial.print(", ");
    Serial.println(BLE.address());
  }

  // INTERRUPCION
  ITimer0.attachInterruptInterval(TIMER0_INTERVAL_us, TimerHandler0);

  // APAGAMOS LED ROJO = FIN DE CONFIGURACION INICIAL
  digitalWrite(LEDR, 1);
}

void loop(void) {
  /*
  // Revision del estado de calibracion
  BNO_IMU.getCalibration(&sistema, &gyro, &accel, &mag);
  if (gyro == FullCalib &&  accel == FullCalib) digitalWrite(LEDG, 0);  // VERDE -> ON 
  else digitalWrite(LEDG, 1);                                           // VERDE -> OFF
  delay(20);
  */

  // Reset de variables de conteo
  // sec_pkt = 0;
  conteo_tics = 0;
  conectado = false;

  // Turn OFF LED´s indicadores
  digitalWrite(LEDB, 1);
  digitalWrite(LEDR, 1);
  digitalWrite(LEDR, 1);

  BLEDevice central = BLE.central();
  if (central) {
    while (central.connected() && customCharacteristic.subscribed()) {
      
      // Si ya esta conectado -> Habilitamos bandera del timer
      if (!conectado){
        conectado = true;
        digitalWrite(LEDB, 0);    // Prendemos el led AZUL para indicar el inicio del proceso
      }

      if (tic_timer) {
        tic_timer = false;

        // LECTURA DE SENSOR
        // BNO_IMU.readLen((Adafruit_BNO055::adafruit_bno055_reg_t)R_Acc, RawAcc, 6);
        // BNO_IMU.readLen((Adafruit_BNO055::adafruit_bno055_reg_t)R_Gyr, RawGyr, 6);
        // BNO_IMU.readLen((Adafruit_BNO055::adafruit_bno055_reg_t)R_Mag, RawMag, 6);
        // BNO_IMU.readLen((Adafruit_BNO055::adafruit_bno055_reg_t)R_Qua, RawQua, 8);
        
        // Formacion del paquete & TRANSMICION
        if (conteo_tics % 2 == 0) {
          // PRIMERA_CAPTURA
          // 1er slot (4bytes) -> Secuencia/No de pkt [0:3]
          tx_pkt[0] = sec_pkt & 0xFF;           // Byte menos significativo
          tx_pkt[1] = (sec_pkt >> 8) & 0xFF;    // Segundo byte
          tx_pkt[2] = (sec_pkt >> 16) & 0xFF;   // Tercer byte
          tx_pkt[3] = (sec_pkt >> 24) & 0xFF;   // Byte más significativo

          /* BLOQUE MUESTRA 1 */
          // 2do slot (8bytes) -> Data Quat[4:11]
          tx_pkt[4] = motion_pkt[idx];    // Quat_w[4:5]
          tx_pkt[5] = motion_pkt[idx + 1]; 
          tx_pkt[6] = motion_pkt[idx + 2];    // Quat_x[6:7]
          tx_pkt[7] = motion_pkt[idx + 3];
          tx_pkt[8] = motion_pkt[idx + 4];    // Quat_y[8:9]
          tx_pkt[9] = motion_pkt[idx + 5];          
          tx_pkt[10] = motion_pkt[idx + 6];   // Quat_z[10:11]
          tx_pkt[11] = motion_pkt[idx + 7];
          idx = idx + 8;
          if (idx >= 624) idx = 0;
          
          // /* BLOQUE MUESTRA 1 */
          // // 2do slot (8bytes) -> Data Quat[4:11]
          // tx_pkt[4] = RawQua[0];    // Quat_w[4:5]
          // tx_pkt[5] = RawQua[1]; 
          // tx_pkt[6] = RawQua[2];    // Quat_x[6:7]
          // tx_pkt[7] = RawQua[3];
          // tx_pkt[8] = RawQua[4];    // Quat_y[8:9]
          // tx_pkt[9] = RawQua[5];          
          // tx_pkt[10] = RawQua[6];   // Quat_z[10:11]
          // tx_pkt[11] = RawQua[7];
          // // 3er slot (6bytes) -> Data Acc[12:15]
          // tx_pkt[12] = RawAcc[0];   // Acc_x[12:13]        
          // tx_pkt[13] = RawAcc[1];
          // tx_pkt[14] = RawAcc[2];   // Acc_y[14:15] 
          // tx_pkt[15] = RawAcc[3];
          // tx_pkt[16] = RawAcc[4];   // Acc_z[16:17] 
          // tx_pkt[17] = RawAcc[5];
          // // 4to slot (6bytes) -> Data Gyr[16:21]
          // tx_pkt[18] = RawGyr[0];   // Gyr_x[18:19]               
          // tx_pkt[19] = RawGyr[1];
          // tx_pkt[20] = RawGyr[2];   // Gyr_y[20:21]
          // tx_pkt[21] = RawGyr[3];
          // tx_pkt[22] = RawGyr[4];   // Gyr_z[22:23]
          // tx_pkt[23] = RawGyr[5];
          // // 5to slot (6bytes) -> Data Mag[16:21]
          // tx_pkt[24] = RawMag[0];   // Mag_x[24:25]
          // tx_pkt[25] = RawMag[1];
          // tx_pkt[26] = RawMag[2];   // Mag_x[26:27]
          // tx_pkt[27] = RawMag[3];
          // tx_pkt[28] = RawMag[4];   // Mag_x[28:29]
          // tx_pkt[29] = RawMag[5];

        } else {  // SEGUNDA_CAPTURA & TRANSMISION
          /* BLOQUE MUESTRA 2 */
          // 6to slot (8bytes) -> Data Quat[30:37]
          // tx_pkt[30] = RawQua[0];
          // tx_pkt[31] = RawQua[1];
          // tx_pkt[32] = RawQua[2];
          // tx_pkt[33] = RawQua[3];
          // tx_pkt[34] = RawQua[4];
          // tx_pkt[35] = RawQua[5];
          // tx_pkt[36] = RawQua[6];
          // tx_pkt[37] = RawQua[7];
          // // 7mo slot (6bytes) -> Data Acc[38:43]
          // tx_pkt[38] = RawAcc[0];
          // tx_pkt[39] = RawAcc[1];
          // tx_pkt[40] = RawAcc[2];
          // tx_pkt[41] = RawAcc[3];
          // tx_pkt[42] = RawAcc[4];
          // tx_pkt[43] = RawAcc[5];
          // // 8vo slot (6bytes) -> Data Mag[44:49]
          // tx_pkt[44] = RawGyr[0];
          // tx_pkt[45] = RawGyr[1];
          // tx_pkt[46] = RawGyr[2];
          // tx_pkt[47] = RawGyr[3];
          // tx_pkt[48] = RawGyr[4];
          // tx_pkt[49] = RawGyr[5];
          // // 9no slot (8bytes) -> Data Quat[50:55]
          // tx_pkt[50] = RawMag[0];
          // tx_pkt[51] = RawMag[1];
          // tx_pkt[52] = RawMag[2];
          // tx_pkt[53] = RawMag[3];
          // tx_pkt[54] = RawMag[4];
          // tx_pkt[55] = RawMag[5];

          // Limitacion de paquetes a transmitir (para pruebas)
          if (limitar_Tx && sec_pkt == max_Txpkts) {
            central.disconnect();   // Nos desconectamos
            digitalWrite(LEDG, 1);  // VERDE -> OFF
            digitalWrite(LEDB, 1);  // VERDE -> OFF 
            digitalWrite(LEDR, 1);  // VERDE -> O
            while(1)  delay(1000);  // HACEMOS NADA C:          
          }

          // ENVIO DE PAQUETE
          customCharacteristic.writeValue(tx_pkt, sizeof(tx_pkt));
          // IMRPESION DE PAQUETE EN SERIAL
          if (print_serial) {
            if (no_pkt) Serial.print(sec_pkt);
            if (print_completo) {
              for (int k = 4; k < Payload_bytes; k += 2) {
                Serial.print(",");
                x = (int16_t)((uint16_t)tx_pkt[k] | ((uint16_t)tx_pkt[k + 1] << 8));
                Serial.print(x);
              }
            }
            if (no_pkt || print_completo) Serial.println("");
          }
          // Aumento en el contero de numero de paquete
          sec_pkt++;
        }
        // Contamos los tic's de la interrupcion
        conteo_tics++;

        // APAGADO-ENCENDIDO DE LED's
        if (conteo_tics % tics_segundo == 0) {
          if (led_OnOFF) {
            digitalWrite(LEDB, 0);    // AZUL -> ON
            digitalWrite(LEDG, 1);    // VERDE -> OFF 
            digitalWrite(LEDR, 1);    // ROJO  -> OFF
          } else {
            digitalWrite(LEDB, 1);    // AZUL -> OFF
            // Revision del estado de calibracion
            // BNO_IMU.getCalibration(&sistema, &gyro, &accel, &mag);
            // if (gyro == FullCalib &&  accel == FullCalib) {
            //   digitalWrite(LEDG, 0);  // VERDE -> ON 
            //   digitalWrite(LEDR, 1);  // ROJO  -> OFF
            // } else {
            //   digitalWrite(LEDG, 1);  // VERDE -> OFF
            //   digitalWrite(LEDR, 0);  // ROJO  -> ON
            // }

            // IMPRESION DE ESTADO CALIBRACION
            if (print_serial && cali) {
              Serial.print("g:");
              Serial.println(gyro);
              Serial.print(", a:");
              Serial.println(accel);
            }
          }
          led_OnOFF = !led_OnOFF;
        }
      }
    }
  }
}