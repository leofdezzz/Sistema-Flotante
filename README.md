<p align="center">
  <img src="docs/banner.png" alt="Floating Farm Banner" width="600">
</p>

<h1 align="center">Floating Farm</h1>

<p align="center">
  <strong>Aerogenerador flotante con búsqueda automática de viento</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/plataforma-Raspberry%20Pi%20Pico-C51A4A?style=flat-square&logo=raspberrypi&logoColor=white" alt="Pico">
  <img src="https://img.shields.io/badge/lenguaje-MicroPython-2b5b84?style=flat-square&logo=python&logoColor=white" alt="MicroPython">
  <img src="https://img.shields.io/badge/motores-28BYJ--48-orange?style=flat-square" alt="Stepper">
  <img src="https://img.shields.io/badge/licencia-MIT-green?style=flat-square" alt="MIT">
</p>

---

## Sobre el proyecto

Maqueta educativa que simula un aerogenerador flotante dentro de un tanque de agua. Ocho ventiladores generan viento desde distintas direcciones, y el sistema **busca automáticamente** la posición donde el aire pasa a través de un hueco en una pared, maximizando la generación de voltaje.

```
                    ┌─── Ventilador Arriba (GP10)
                    │
                    ▼
              ┌───────────┐
 Vent. Izq.  │           │  Vent. Der.
  (GP8) ───► │  ~~~🌊~~~ │ ◄─── (GP9)
              │  ⚡ Aero  │
              │  ~~~🌊~~~ │
              └───────────┘
                    ▲
                    │
                    └─── Ventilador Abajo (GP11)

         (+ 4 ventiladores en diagonales)
```

---

## Hardware

### Componentes

| Componente | Modelo | Cantidad | Función |
|:---:|:---:|:---:|:---|
| 🔧 MCU | Raspberry Pi Pico | 1 | Controlador principal |
| ⚙️ Motores | 28BYJ-48 + ULN2003 | 2 | Posicionamiento ejes X e Y |
| 💨 Ventiladores | — | 8 | Simulan viento desde 8 direcciones |
| 📡 Relés | Módulo 8 canales | 1 | Control ON/OFF de ventiladores |
| ⚡ Sensor | ADC interno | 1 | Lectura de voltaje del aerogenerador |
| 🔘 Botones | Pulsadores | 8 | Selección de dirección de viento |

### Esquema de conexiones

```
 ┌──────────────────────────────────────────────────────┐
 │                  RASPBERRY PI PICO                    │
 │                                                       │
 │  GP0  ○──── Botón Izquierda      ────○ GND           │
 │  GP1  ○──── Botón Derecha        ────○ GND           │
 │  GP2  ○──── Botón Arriba         ────○ GND           │
 │  GP3  ○──── Botón Abajo          ────○ GND           │
 │  GP4  ○──── Botón Diag. ↖        ────○ GND           │
 │  GP5  ○──── Botón Diag. ↙        ────○ GND           │
 │  GP6  ○──── Botón Diag. ↗        ────○ GND           │
 │  GP7  ○──── Botón Diag. ↘        ────○ GND           │
 │                                                       │
 │  GP8  ○───► Relé 1 → Vent. Izquierda                 │
 │  GP9  ○───► Relé 2 → Vent. Derecha                   │
 │  GP10 ○───► Relé 3 → Vent. Arriba                    │
 │  GP11 ○───► Relé 4 → Vent. Abajo                     │
 │  GP12 ○───► Relé 5 → Vent. Diag. ↖                   │
 │  GP13 ○───► Relé 6 → Vent. Diag. ↙                   │
 │  GP14 ○───► Relé 7 → Vent. Diag. ↗                   │
 │  GP15 ○───► Relé 8 → Vent. Diag. ↘                   │
 │                                                       │
 │  GP16 ○───► ULN2003 (X) IN1  ┐                       │
 │  GP17 ○───► ULN2003 (X) IN2  ├── Stepper X (28BYJ)   │
 │  GP18 ○───► ULN2003 (X) IN3  │                       │
 │  GP19 ○───► ULN2003 (X) IN4  ┘                       │
 │                                                       │
 │  GP20 ○───► ULN2003 (Y) IN1  ┐                       │
 │  GP21 ○───► ULN2003 (Y) IN2  ├── Stepper Y (28BYJ)   │
 │  GP22 ○───► ULN2003 (Y) IN3  │                       │
 │  GP23 ○───► ULN2003 (Y) IN4  ┘                       │
 │                                                       │
 │  GP26 ○◄─── Voltaje aerogenerador (ADC)               │
 │                                                       │
 └──────────────────────────────────────────────────────┘
```

---

## Cómo funciona

### Flujo de operación

```
  ┌─────────────┐     ┌──────────────┐     ┌────────────────┐
  │  Esperando   │────►│ Botón pulsado │────►│ Enciende vent. │
  │   botón...   │     │  (dirección)  │     │  + espera 2s   │
  └─────────────┘     └──────────────┘     └───────┬────────┘
         ▲                                          │
         │                                          ▼
  ┌──────┴──────┐                          ┌────────────────┐
  │ Mismo botón │◄─────────────────────────│   Búsqueda     │
  │   = STOP    │                          │  automática    │
  └─────────────┘                          └───────┬────────┘
                                                    │
                                                    ▼
                                           ┌────────────────┐
                                           │  Posicionado   │
                                           │  en el óptimo  │
                                           └────────────────┘
```

### Algoritmo de búsqueda (eje simple)

```
Posición:  0 ─────────────────────────────────► 200
Voltaje:   ░░░░░▒▒▒▓▓████████▓▓▒▒░░░░░░░░░░░░

  1. Ir a posición 0 (origen)
  2. Avanzar paso a paso leyendo voltaje
  3. Detectar máximo ──────────────► ⚡ pos=42
  4. Volver exactamente a pos=42
```

Para **diagonales**, se hace doble barrido con refinamiento:

```
  Barrido Y ──► Barrido X ──► Refinar Y ──► Refinar X
      │              │              │              │
      ▼              ▼              ▼              ▼
   óptimo Y      óptimo X     ajuste Y      ajuste X
                                               (final)
```

### Mapa de direcciones

```
          ↖ GP4        ↑ GP2        ↗ GP6
            ╲          │          ╱
              ╲        │        ╱
    ← GP0 ─────┤  TANQUE  ├───── GP1 →
              ╱        │        ╲
            ╱          │          ╲
          ↙ GP5        ↓ GP3        ↘ GP7
```

| Dirección | Botón | Ventilador | Eje de búsqueda |
|:---:|:---:|:---:|:---:|
| ← Izquierda | GP0 | GP8 | Y |
| → Derecha | GP1 | GP9 | Y |
| ↑ Arriba | GP2 | GP10 | X |
| ↓ Abajo | GP3 | GP11 | X |
| ↖ Diag. | GP4 | GP12 | X + Y |
| ↙ Diag. | GP5 | GP13 | X + Y |
| ↗ Diag. | GP6 | GP14 | X + Y |
| ↘ Diag. | GP7 | GP15 | X + Y |

---

## Estructura del proyecto

```
Floating-Farm/
├── main.py                  # Programa principal
├── calibrate_stepper.py     # Calibración de step delay
├── test_ventiladores.py     # Test de relés y ventiladores
├── test_eje_x.py            # Test aislado eje X
├── test_eje_y.py            # Test aislado eje Y
├── test_eje_xy.py           # Test ambos ejes
└── docs/
    └── banner.png           # (opcional) imagen del proyecto
```

---

## Inicio rápido

### 1. Calibrar motores

Antes de usar la maqueta, encuentra el step delay óptimo:

```bash
mpremote connect auto run calibrate_stepper.py
```

> Usa la **opción 3** (búsqueda automática). El menor delay donde el motor vuelve al punto de origen sin perder pasos es tu valor óptimo.

### 2. Configurar y desplegar

Ajusta `_STEP_DELAY` en `main.py` con el valor obtenido, luego:

```bash
mpremote connect auto cp main.py :main.py
mpremote connect auto reset
```

### 3. Usar

1. Pulsa un botón → se enciende el ventilador y busca automáticamente.
2. Mismo botón → para todo.
3. Otro botón → cambia dirección.

---

## Parámetros configurables

| Constante | Default | Descripción |
|:---|:---:|:---|
| `_SCAN_STEPS` | `200` | Pasos de muestreo por barrido |
| `_STEP_DELAY` | `2 ms` | Tiempo entre pasos del motor |
| `_SETTLE_MS` | `200 ms` | Espera antes de leer voltaje |
| `_ADC_SAMPLES` | `10` | Lecturas promediadas por muestra |
| `_DEBOUNCE_MS` | `200 ms` | Anti-rebote de botones |

---

## Tecnología

```
MicroPython ──► Raspberry Pi Pico
                    │
                    ├── 28BYJ-48 + ULN2003  (posicionamiento por pasos)
                    ├── Half-step (8 fases)  (~4076 pasos/rev)
                    ├── ADC 16-bit           (lectura de voltaje)
                    └── GPIO + Relés         (control de ventiladores)
```

---

<p align="center">
  Hecho con ⚡ para aprender sobre energía eólica
</p>
