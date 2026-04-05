# Floating Farm

Proyecto de MicroPython para **Raspberry Pi Pico** que controla un **aerogenerador flotante** dentro de un tanque de agua. Ocho ventiladores simulan viento desde distintas direcciones, y el sistema busca automáticamente la posición óptima donde el aire pasa a través de un hueco en una pared, maximizando la generación de voltaje.

## Hardware

| Componente | Descripción |
|---|---|
| **MCU** | Raspberry Pi Pico (MicroPython) |
| **Motores** | 2x 28BYJ-48 con driver ULN2003 (ejes X e Y) |
| **Ventiladores** | 8 unidades controladas por relés (activo alto) |
| **Sensor** | ADC en GP26 — lectura de voltaje del aerogenerador |
| **Botones** | 8 botones con pull-up interno (activo bajo) |

### Asignación de pines

```
Botones:       GP0-GP7     (entrada, pull-up)
Relés:         GP8-GP15    (salida, activo alto)
Stepper X:     GP16-GP19   (ULN2003: IN1-IN4)
Stepper Y:     GP20-GP23   (ULN2003: IN1-IN4)
ADC:           GP26        (lectura de voltaje)
```

## Cómo funciona

### Flujo principal

1. El sistema arranca con todo apagado y espera que se pulse un botón.
2. Al pulsar un botón (ej. "arriba"), se enciende el ventilador correspondiente.
3. Tras 2 segundos de estabilización del flujo de aire, inicia la **búsqueda automática**.
4. El aerogenerador queda posicionado en el punto de máximo voltaje.
5. Pulsar el mismo botón detiene todo. Pulsar otro cambia de dirección.

### Algoritmo de búsqueda

Para **direcciones cardinales** (izquierda, derecha, arriba, abajo) se barre un solo eje:

1. El stepper va a la posición 0 (origen).
2. Avanza paso a paso (200 pasos por defecto) hacia el otro extremo.
3. En cada paso espera 200ms de estabilización y lee el voltaje (promedio de 10 muestras ADC).
4. Identifica el paso con mayor voltaje y se posiciona exactamente ahí.

Para **diagonales** se hace un barrido iterativo en ambos ejes:

1. Barre eje Y completo → posiciona en el óptimo de Y.
2. Barre eje X completo → posiciona en el óptimo de X.
3. Repite ambos barridos como pasada de refinamiento.

Al finalizar, las bobinas se apagan para evitar calentamiento.

### Mapeo de direcciones

| Botón | Ventilador | Eje de búsqueda |
|---|---|---|
| Izquierda (GP0) | GP8 | Y |
| Derecha (GP1) | GP9 | Y |
| Arriba (GP2) | GP10 | X |
| Abajo (GP3) | GP11 | X |
| Diag. izq-arriba (GP4) | GP12 | X + Y |
| Diag. izq-abajo (GP5) | GP13 | X + Y |
| Diag. der-arriba (GP6) | GP14 | X + Y |
| Diag. der-abajo (GP7) | GP15 | X + Y |

## Archivos

| Archivo | Propósito |
|---|---|
| `main.py` | Programa principal |
| `calibrate_stepper.py` | Herramienta para calibrar el step delay óptimo del 28BYJ-48 |
| `test_ventiladores.py` | Test de relés: individual, pares opuestos, todos, secuencia circular |

## Despliegue

```bash
mpremote connect auto cp main.py :main.py
mpremote connect auto reset
```

## Calibración

Antes de usar la maqueta, ejecuta `calibrate_stepper.py` para encontrar el delay mínimo sin perder pasos:

```bash
mpremote connect auto run calibrate_stepper.py
```

La opción 3 (búsqueda automática) prueba delays de mayor a menor haciendo ida y vuelta. El menor delay donde el motor vuelve al punto de origen es tu valor óptimo para `_STEP_DELAY` en `main.py`.

### Parámetros calibrables en `main.py`

| Constante | Default | Descripción |
|---|---|---|
| `_SCAN_STEPS` | 200 | Pasos de muestreo por barrido |
| `_STEP_DELAY` | 2 ms | Tiempo entre pasos del motor |
| `_SETTLE_MS` | 200 ms | Espera antes de leer voltaje |
| `_ADC_SAMPLES` | 10 | Lecturas promediadas por muestra |
