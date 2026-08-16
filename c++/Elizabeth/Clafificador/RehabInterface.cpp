// RehabInterface.cpp
#include "RehabInterface.hpp"

#include "imgui.h"
#include "backends/imgui_impl_glfw.h"
#include "backends/imgui_impl_opengl3.h"

// imgui_impl_opengl3.h ya incluye su propio loader minimo (no hace falta gl3w/glad).
#include <GLFW/glfw3.h>

#include <cmath>
#include <chrono>

namespace {

constexpr float kPi = 3.14159265358979323846f;

// Dibuja una carita simple: contenta (sonrisa) o animosa/neutra (para "sigamos practicando").
// Se dibuja con primitivas de ImGui para no depender de archivos de imagen externos;
// se puede reemplazar fácilmente por ImGui::Image(...) si se prefieren íconos/PNG reales.
void DrawFace(ImDrawList* dl, ImVec2 center, float radius, ImU32 skinColor, bool happy) {
    dl->AddCircleFilled(center, radius, skinColor, 64);
    dl->AddCircle(center, radius, IM_COL32(60, 60, 60, 120), 64, 3.0f);

    float eyeDX = radius * 0.32f;
    float eyeDY = radius * 0.18f;
    float eyeR  = radius * 0.09f;
    ImU32 eyeColor = IM_COL32(50, 50, 50, 255);
    dl->AddCircleFilled(ImVec2(center.x - eyeDX, center.y - eyeDY), eyeR, eyeColor);
    dl->AddCircleFilled(ImVec2(center.x + eyeDX, center.y - eyeDY), eyeR, eyeColor);

    ImU32 mouthColor = IM_COL32(60, 60, 60, 255);
    if (happy) {
        // Sonrisa grande (arco tipo "U")
        ImVec2 mouthCenter(center.x, center.y + radius * 0.05f);
        float mouthRadius = radius * 0.5f;
        dl->PathArcTo(mouthCenter, mouthRadius, kPi * 0.15f, kPi * 0.85f, 24);
        dl->PathStroke(mouthColor, 0, 5.0f);
    } else {
        // Expresión neutra/animosa (nunca triste): evita desalentar al niño/a.
        float w = radius * 0.4f;
        float y = center.y + radius * 0.35f;
        dl->AddLine(ImVec2(center.x - w, y), ImVec2(center.x - w * 0.3f, y + radius * 0.05f), mouthColor, 5.0f);
        dl->AddLine(ImVec2(center.x - w * 0.3f, y + radius * 0.05f), ImVec2(center.x + w * 0.3f, y + radius * 0.05f), mouthColor, 5.0f);
        dl->AddLine(ImVec2(center.x + w * 0.3f, y + radius * 0.05f), ImVec2(center.x + w, y), mouthColor, 5.0f);
    }
}

// Estrellita decorativa para cuando el ejercicio salió bien.
void DrawStarBadge(ImDrawList* dl, ImVec2 center, float radius, ImU32 color) {
    const int points = 5;
    ImVec2 outer[points], inner[points];
    float rotation = -kPi / 2.0f;
    for (int i = 0; i < points; i++) {
        float aOuter = rotation + i * 2.0f * kPi / points;
        float aInner = aOuter + kPi / points;
        outer[i] = ImVec2(center.x + cosf(aOuter) * radius, center.y + sinf(aOuter) * radius);
        inner[i] = ImVec2(center.x + cosf(aInner) * radius * 0.45f, center.y + sinf(aInner) * radius * 0.45f);
    }
    dl->PathClear();
    for (int i = 0; i < points; i++) {
        dl->PathLineTo(outer[i]);
        dl->PathLineTo(inner[i]);
    }
    dl->PathFillConvex(color);
}

// Tres puntitos animados (typing dots) debajo del texto, para reforzar
// visualmente que la pantalla de "esperando" esta viva, no trabada.
void DrawWaitingDots(ImDrawList* dl, ImVec2 center, float spacing, float baseRadius, float time, ImU32 color) {
    for (int i = 0; i < 3; i++) {
        float phase = time * 4.0f - i * 0.6f;
        float bounce = (sinf(phase) + 1.0f) * 0.5f; // 0..1
        float r = baseRadius * (0.6f + 0.4f * bounce);
        ImVec2 p(center.x + (i - 1) * spacing, center.y);
        dl->AddCircleFilled(p, r, color, 16);
    }
}

} // namespace

RehabInterface::RehabInterface(const std::string& appName) : m_appName(appName) {}

RehabInterface::~RehabInterface() {
    Shutdown();
}

bool RehabInterface::Init(int width, int height) {
    if (m_initialized) return true;
    if (!glfwInit()) return false;

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
#ifdef __APPLE__
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
#endif

    m_window = glfwCreateWindow(width, height, m_appName.c_str(), nullptr, nullptr);
    if (!m_window) {
        glfwTerminate();
        return false;
    }
    glfwMakeContextCurrent(m_window);
    glfwSwapInterval(1);

    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    (void)io;

    ImGui::StyleColorsLight();
    ImGuiStyle& style = ImGui::GetStyle();
    style.WindowRounding = 0.0f;

    ImGui_ImplGlfw_InitForOpenGL(m_window, true);
    ImGui_ImplOpenGL3_Init("#version 330");

    m_initialized = true;
    m_state = State::Waiting;
    m_resultTime = std::chrono::steady_clock::now();
    return true;
}

void RehabInterface::ShowResult(bool wellPerformed) {
    m_state = wellPerformed ? State::Good : State::Bad;
    m_resultTime = std::chrono::steady_clock::now();
}

bool RehabInterface::Tick() {
    if (!m_initialized && !Init()) return false;
    if (glfwWindowShouldClose(m_window)) return false;

    // Si ya pasaron 'm_displaySeconds' desde el ultimo resultado, volvemos
    // solos a la pantalla de espera invitando a repetir el ejercicio.
    if (m_state != State::Waiting) {
        float elapsed = std::chrono::duration<float>(std::chrono::steady_clock::now() - m_resultTime).count();
        if (elapsed >= m_displaySeconds) m_state = State::Waiting;
    }

    RenderFrame();

    return !glfwWindowShouldClose(m_window);
}

void RehabInterface::RenderFrame() {
    glfwPollEvents();

    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();

    ImGuiIO& io = ImGui::GetIO();
    ImGui::SetNextWindowPos(ImVec2(0, 0));
    ImGui::SetNextWindowSize(io.DisplaySize);

    ImVec4 bgColor;
    const char* title;
    const char* subtitle;
    bool happyFace;
    bool showStar = false;
    bool showDots = false;

    switch (m_state) {
        case State::Good:
            bgColor  = ImVec4(0.16f, 0.62f, 0.35f, 1.0f); // verde (GRN)
            title    = "Ejercicio bien hecho!";
            subtitle = "Excelente trabajo, segue así";
            happyFace = true;
            showStar = true;
            break;
        case State::Bad:
            bgColor  = ImVec4(0.95f, 0.75f, 0.15f, 1.0f); // amarillo (YLL)
            title    = "Sigamos practicando!";
            subtitle = "Casi lo logras, intentalo de nuevo";
            happyFace = false;
            break;
        case State::Waiting:
        default:
            bgColor  = ImVec4(0.30f, 0.47f, 0.85f, 1.0f); // azul
            title    = "Tu turno!";
            subtitle = "Repite el ejercicio cuando estés listo/a";
            happyFace = true;
            showDots = true;
            break;
    }

    ImGui::PushStyleColor(ImGuiCol_WindowBg, bgColor);
    ImGui::Begin("##RehabFeedback", nullptr,
        ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoResize |
        ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoScrollbar |
        ImGuiWindowFlags_NoCollapse);

    ImDrawList* dl = ImGui::GetWindowDrawList();
    ImVec2 winPos = ImGui::GetWindowPos();
    ImVec2 winSize = ImGui::GetWindowSize();
    ImVec2 center(winPos.x + winSize.x * 0.5f, winPos.y + winSize.y * 0.42f);
    float faceRadius = winSize.y * 0.22f;
    float t = (float)ImGui::GetTime();

    // En "esperando" la carita respira suavemente, para que se note que la
    // pantalla esta viva y no trabada.
    if (m_state == State::Waiting) {
        faceRadius *= 1.0f + 0.06f * sinf(t * 2.5f);
    }

    DrawFace(dl, center, faceRadius, IM_COL32(255, 255, 255, 255), happyFace);

    if (showStar) {
        ImVec2 badgeCenter(center.x + faceRadius * 1.3f, center.y - faceRadius * 1.1f);
        DrawStarBadge(dl, badgeCenter, faceRadius * 0.35f, IM_COL32(255, 215, 0, 255));
    }

    if (showDots) {
        ImVec2 dotsCenter(center.x, center.y + 130.0f);
        DrawWaitingDots(dl, dotsCenter, faceRadius * 0.22f, faceRadius * 0.08f, t, IM_COL32(255, 255, 255, 220));
    }

    ImGui::SetWindowFontScale(2.0f);
    ImVec2 titleSize = ImGui::CalcTextSize(title);
    ImGui::SetCursorPos(ImVec2((winSize.x - titleSize.x) * 0.5f, winSize.y * 0.68f));
    ImGui::TextColored(ImVec4(1, 1, 1, 1), "%s", title);

    ImGui::SetWindowFontScale(1.2f);
    ImVec2 subSize = ImGui::CalcTextSize(subtitle);
    ImGui::SetCursorPos(ImVec2((winSize.x - subSize.x) * 0.5f, winSize.y * 0.82f));
    ImGui::TextColored(ImVec4(1, 1, 1, 0.9f), "%s", subtitle);
    ImGui::SetWindowFontScale(1.0f);

    ImGui::End();
    ImGui::PopStyleColor();

    ImGui::Render();
    int display_w, display_h;
    glfwGetFramebufferSize(m_window, &display_w, &display_h);
    glViewport(0, 0, display_w, display_h);
    glClearColor(bgColor.x, bgColor.y, bgColor.z, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
    glfwSwapBuffers(m_window);
}

void RehabInterface::Shutdown() {
    if (!m_initialized) return;
    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwDestroyWindow(m_window);
    glfwTerminate();
    m_initialized = false;
    m_window = nullptr;
}