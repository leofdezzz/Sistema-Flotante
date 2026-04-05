"""
Floating Farm - Aerogenerador flotante con busqueda automatica de viento
Plataforma: Raspberry Pi Pico (MicroPython)

Pines:
  Botones  GP0-7   (PULL_UP, activo bajo)
  Reles    GP8-15  (activo alto)
  Stepper X: GP16-19 (ULN2003: IN1-IN4)
  Stepper Y: GP20-23 (ULN2003: IN1-IN4)
  ADC      GP26
"""

from machine import Pin, ADC
from micropython import const
import gc
import time

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------
_SCAN_STEPS   = const(200)      # pasos de barrido por eje
_SETTLE_MS    = const(200)      # espera entre paso y lectura
_ADC_SAMPLES  = const(10)
_DEBOUNCE_MS  = const(200)
_STEP_DELAY   = const(2)        # ms entre pasos del motor (velocidad)

# Direcciones (indices)
_IZQ    = const(0)
_DER    = const(1)
_ARR    = const(2)
_ABJ    = const(3)
_DIA_IA = const(4)
_DIA_IB = const(5)
_DIA_DA = const(6)
_DIA_DB = const(7)
_N_DIR  = const(8)

# Ejes de busqueda por direccion: 0=X, 1=Y, 2=XY
_AXIS_X  = const(0)
_AXIS_Y  = const(1)
_AXIS_XY = const(2)

_DIR_AXES = (
    _AXIS_Y,   # izquierda  -> barre Y
    _AXIS_Y,   # derecha    -> barre Y
    _AXIS_X,   # arriba     -> barre X
    _AXIS_X,   # abajo      -> barre X
    _AXIS_XY,  # diag_izq_arr
    _AXIS_XY,  # diag_izq_abj
    _AXIS_XY,  # diag_der_arr
    _AXIS_XY,  # diag_der_abj
)

_DIR_NAMES = ("izq", "der", "arr", "abj", "dia_ia", "dia_ib", "dia_da", "dia_db")

# ---------------------------------------------------------------------------
# Secuencia half-step 28BYJ-48 (8 fases, mas suave y preciso)
# ---------------------------------------------------------------------------
_HALFSTEP = (
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
    (1, 0, 0, 1),
)

# ---------------------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------------------
_btns = tuple(Pin(i, Pin.IN, Pin.PULL_UP) for i in range(_N_DIR))
_fans = tuple(Pin(i + 8, Pin.OUT, value=0) for i in range(_N_DIR))

# Stepper X: GP16, GP17, GP18, GP19
_stx_pins = tuple(Pin(i, Pin.OUT, value=0) for i in range(16, 20))
# Stepper Y: GP20, GP21, GP22, GP23
_sty_pins = tuple(Pin(i, Pin.OUT, value=0) for i in range(20, 24))

_adc = ADC(Pin(26))

# Posicion actual de cada stepper (en pasos)
_pos = [0, 0]  # [x, y]
_phase = [0, 0]  # fase actual en la secuencia half-step


# ---------------------------------------------------------------------------
# Stepper
# ---------------------------------------------------------------------------

def _stepper_off(pins):
    """Apaga bobinas para no calentar el motor en reposo."""
    for p in pins:
        p.value(0)


def _step(pins, axis, direction):
    """Avanza un paso. direction: 1=adelante, -1=atras."""
    _phase[axis] = (_phase[axis] + direction) % 8
    seq = _HALFSTEP[_phase[axis]]
    for i in range(4):
        pins[i].value(seq[i])
    time.sleep_ms(_STEP_DELAY)


def _move(pins, axis, steps):
    """Mueve el stepper N pasos (positivo o negativo)."""
    d = 1 if steps > 0 else -1
    for _ in range(abs(steps)):
        _step(pins, axis, d)
    _pos[axis] += steps


def _go_to(pins, axis, target):
    """Mueve a una posicion absoluta."""
    diff = target - _pos[axis]
    if diff != 0:
        _move(pins, axis, diff)


def _steppers_off():
    _stepper_off(_stx_pins)
    _stepper_off(_sty_pins)


# ---------------------------------------------------------------------------
# ADC
# ---------------------------------------------------------------------------

def _read_v():
    t = 0
    for _ in range(_ADC_SAMPLES):
        t += _adc.read_u16()
        time.sleep_ms(5)
    return t // _ADC_SAMPLES


# ---------------------------------------------------------------------------
# Ventiladores
# ---------------------------------------------------------------------------

def _fans_off():
    for f in _fans:
        f.value(0)


def _fans_on(idx):
    _fans_off()
    _fans[idx].value(1)


# ---------------------------------------------------------------------------
# Busqueda
# ---------------------------------------------------------------------------

def _search_axis(pins, axis, name):
    """Busca el optimo en un eje: va a 0, barre, vuelve al mejor paso."""
    print("[%s] ir a origen" % name)
    _go_to(pins, axis, 0)
    time.sleep_ms(_SETTLE_MS)

    best_pos = 0
    best_v = 0

    print("[%s] barrido %d pasos" % (name, _SCAN_STEPS))
    for i in range(_SCAN_STEPS):
        _move(pins, axis, 1)
        time.sleep_ms(_SETTLE_MS)
        v = _read_v()
        if i % 20 == 0 or v > best_v:
            print("  %d/%d v=%d" % (i + 1, _SCAN_STEPS, v))
        if v > best_v:
            best_v = v
            best_pos = _pos[axis]

    print("[%s] mejor: pos %d v=%d" % (name, best_pos, best_v))
    _go_to(pins, axis, best_pos)

    print("[%s] ok" % name)
    return best_v


def _search_dual():
    """Busqueda en ambos ejes con refinamiento."""
    print("== doble eje ==")
    _search_axis(_sty_pins, 1, "Y")
    _search_axis(_stx_pins, 0, "X")
    # Refinamiento
    _search_axis(_sty_pins, 1, "Y")
    v = _search_axis(_stx_pins, 0, "X")
    print("== fin ==")
    return v


# ---------------------------------------------------------------------------
# Botones
# ---------------------------------------------------------------------------

def _check_btn():
    for i in range(_N_DIR):
        if _btns[i].value() == 0:
            time.sleep_ms(_DEBOUNCE_MS)
            if _btns[i].value() == 0:
                return i
    return -1


def _wait_release(i):
    while _btns[i].value() == 0:
        time.sleep_ms(50)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("FLOATING FARM (stepper 28BYJ-48)")
    print("Esperando dir...")

    _steppers_off()
    _fans_off()
    gc.collect()

    active = -1

    while True:
        p = _check_btn()
        if p < 0:
            time.sleep_ms(50)
            continue

        if p == active:
            print("\n[STOP] %s" % _DIR_NAMES[p])
            _fans_off()
            _steppers_off()
            active = -1
            _wait_release(p)
            print("Esperando dir...\n")
            continue

        active = p
        ax = _DIR_AXES[p]

        print("\n[ON] %s eje=%d" % (_DIR_NAMES[p], ax))
        _fans_on(p)

        print("Estabilizando...")
        time.sleep_ms(2000)

        if ax == _AXIS_Y:
            _search_axis(_sty_pins, 1, "Y")
        elif ax == _AXIS_X:
            _search_axis(_stx_pins, 0, "X")
        else:
            _search_dual()

        _steppers_off()
        gc.collect()
        print("\nv=%d. Pulsa mismo btn=stop, otro=cambiar.\n" % _read_v())
        _wait_release(p)


main()
