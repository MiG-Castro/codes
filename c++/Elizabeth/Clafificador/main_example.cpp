// main_example.cpp
// Ejemplo de cómo integrar RehabInterface en tu aplicación existente.
#include "RehabInterface.hpp"

// #include "TuSensor.hpp"   // tu header con la lectura de sensor y mlp_classifier(...)

int main() {
    RehabInterface interfaz("KinderMove - Apoyo en Rehabilitacion");
    if (!interfaz.Init()) {
        return -1;
    }

    bool running = true;
    while (running /* && tu condicion original para seguir leyendo el sensor */) {
        // --- tu lógica existente ---
        // Sensor sensor = leerSensor();
        bool ejercicioOk = true; // = mlp_classifier(sensor);

        // Antes:
        //   if (mlp_classifier(sensor)) std::cout << GRN << "Well-performed\n" << RST << std::endl;
        //   else std::cout << YLL << "Poorly performed\n" << RST << std::endl;
        //
        // Ahora, una sola línea reemplaza ambas ramas:
        running = interfaz.ShowFeedback(ejercicioOk);
    }

    return 0;
}
