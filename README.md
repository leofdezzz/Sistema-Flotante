# Sistema Flotante

Proyecto de MicroPython para Raspberry Pi Pico que controla un **aerogenerador flotante** dentro de un tanque de agua. Ocho ventiladores simulan viento desde distintas direcciones, y el sistema busca automáticamente la posición óptima donde el aire pasa a través de un hueco en una pared, maximizando la generación de voltaje.

## Hardware

| Componente | Descripción |
|---|---|
| **MCU** | Raspberry Pi Pico (MicroPython) |
| **Servos** | 2x MG996R 360° rotación continua (ejes X e Y) |
| **Ventiladores** | 8 unidades controladas por relés (activo alto) |
| **Sensor** | ADC en GP26 — lectura de voltaje del aerogenerador |
| **Botones** | 8 botones con pull-up interno (activo bajo) |

### Asignación de pines

```
Botones:     GP0-GP7   (entrada, pull-up)
Relés:       GP8-GP15  (salida, activo alto)
Servo X:     GP16      (PWM 50Hz)
Servo Y:     GP17      (PWM 50Hz)
ADC:         GP26      (lectura de voltaje)
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

1. El servo va al extremo inicial (CCW durante 5 segundos).
2. Avanza en 20 pasos discretos hacia el otro extremo (CW).
3. En cada paso espera 300ms de estabilización y lee el voltaje (promedio de 10 muestras ADC).
4. Identifica el paso con mayor voltaje y retrocede hasta esa posición.

Para **diagonales** se hace un barrido iterativo en ambos ejes:

1. Barre eje Y completo → posiciona en el óptimo de Y.
2. Barre eje X completo → posiciona en el óptimo de X.
3. Repite ambos barridos como pasada de refinamiento.

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

## Código — `main.py`

### Configuración

Todas las constantes usan `const()` de MicroPython para compilarse como literales y no consumir RAM:

- `_MAX_TRAVEL = 5000` — tiempo en ms para recorrer un eje completo.
- `_SCAN_STEPS = 20` — número de pasos de muestreo por barrido.
- `_SETTLE_MS = 300` — espera antes de leer voltaje para que el aire se estabilice.
- `_ADC_SAMPLES = 10` — lecturas promediadas por muestra.
- `_SERVO_CW / _SERVO_CCW / _SERVO_STOP` — anchos de pulso en µs para controlar los servos 360°.

### Estructura del código

```
Constantes y configuración
    ↓
Inicialización de hardware (tuplas indexadas, no diccionarios)
    ↓
Funciones de servo (_servo_us, _servo_mv, _servo_stop)
    ↓
Lectura ADC (_read_v)
    ↓
Control de ventiladores (_fans_off, _fans_on)
    ↓
Algoritmo de búsqueda (_scan_axis, _search_axis, _search_dual)
    ↓
Detección de botones (_check_btn, _wait_release)
    ↓
Bucle principal (main)
```

### Optimizaciones de memoria

- **`const()`** en todas las constantes numéricas.
- **Tuplas indexadas por entero** en lugar de diccionarios con strings como clave.
- **Seguimiento del máximo in-place** durante el barrido (sin almacenar lista de lecturas).
- **Aritmética entera** (`//`, `sleep_ms`) en lugar de floats.
- **`gc.collect()`** después de cada búsqueda para liberar memoria fragmentada.

## Archivos de test

| Archivo | Propósito |
|---|---|
| `test_eje_x.py` | Prueba aislada del servo X: movimiento y barrido con ADC |
| `test_eje_y.py` | Prueba aislada del servo Y: movimiento y barrido con ADC |
| `test_eje_xy.py` | Ambos ejes: movimiento independiente y búsqueda dual |
| `test_ventiladores.py` | Relés: individual, pares opuestos, todos, secuencia circular |

Para ejecutar un test, cópialo como `main.py` al Pico:

```bash
mpremote connect auto cp test_eje_x.py :main.py
mpremote connect auto reset
```

## Parámetros calibrables

Los valores de pulso del servo (`_SERVO_CW`, `_SERVO_CCW`, `_SERVO_STOP`) deben ajustarse según el servo físico concreto. El tiempo de recorrido (`_MAX_TRAVEL`) y los pasos de barrido (`_SCAN_STEPS`) dependen del tamaño del tanque y la precisión deseada.
