// RehabInterface.hpp
//
// Interfaz gráfica (Dear ImGui + GLFW) para reemplazar la salida por consola
// de una app de apoyo en rehabilitación infantil ("KinderMove").
//
// Tiene 3 pantallas:
//   - "Bien hecho"           (verde)  -> cuando mlp_classifier(sensor) da true
//   - "Sigamos practicando"  (amarillo) -> cuando da false
//   - "Tu turno"             (azul)   -> pantalla de espera, aparece sola
//                                        unos segundos despues del resultado,
//                                        invitando a repetir el ejercicio.
//
// Uso, en el loop principal (SIEMPRE en el hilo principal, GLFW/ImGui no son
// thread-safe y en macOS es obligatorio):
//
//      RehabInterface interfaz;
//      interfaz.Init();
//      while (running) {
//          if (hay_resultado_nuevo) interfaz.ShowResult(mlp_classifier(sensor));
//          running = interfaz.Tick();
//      }
//
#pragma once
#include <string>
#include <chrono>
#include <iostream>

struct GLFWwindow;

class RehabInterface {
public:
    explicit RehabInterface(const std::string& appName = "KinderMove - Apoyo en Rehabilitacion");
    ~RehabInterface();

    // Crea la ventana y el contexto de ImGui. Se puede llamar explícitamente
    // o se invoca sola la primera vez que se llama a Tick().
    bool Init(int width = 480, int height = 360);

    // Llamar cuando llega un resultado nuevo (wellPerformed = mlp_classifier(sensor)).
    // Muestra la carita de "bien hecho" / "sigamos practicando" por
    // GetFeedbackDuration() segundos y despues vuelve sola a la pantalla de espera.
    void ShowResult(bool wellPerformed);

    // Llamar una vez por iteración del loop principal. Dibuja el estado actual
    // (resultado o pantalla de espera) y procesa eventos de la ventana.
    // Devuelve false si el usuario cerró la ventana (usarlo para cortar el loop).
    bool Tick();

    // Segundos que se muestra el resultado antes de volver a la pantalla de espera.
    void SetFeedbackDuration(float seconds) { m_displaySeconds = seconds; }
    float GetFeedbackDuration() const { return m_displaySeconds; }

    void Shutdown();

private:
    enum class State { Waiting, Good, Bad };

    GLFWwindow* m_window = nullptr;
    std::string m_appName;
    bool m_initialized = false;

    State m_state = State::Waiting;
    std::chrono::steady_clock::time_point m_resultTime{};
    float m_displaySeconds = 3.0f; // cuanto tiempo se queda la carita de bien/mal antes de pasar a "esperando"

    void RenderFrame();
};