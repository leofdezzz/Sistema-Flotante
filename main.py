"""
Floating Farm - Aerogenerador flotante con busqueda automatica de viento
Plataforma: Raspberry Pi Pico (MicroPython)

Pines:
  Botones GP0-7 (PULL_UP, activo bajo)
  Reles  GP8-15 (activo alto)
  Servos GP16(X) GP17(Y) (PWM 50Hz)
  ADC    GP26
"""

from machine import Pin, PWM, ADC
from micropython import const
import gc
import time

# ---------------------------------------------------------------------------
# Configuracion (const -> compilado como literal, no ocupa RAM)
# ---------------------------------------------------------------------------
_MAX_TRAVEL = const(5000)       # ms recorrido completo
_SCAN_STEPS = const(20)
_SETTLE_MS  = const(300)
_ADC_SAMPLES = const(10)
_DEBOUNCE_MS = const(200)
_SERVO_CW   = const(1300)      # us - sentido horario
_SERVO_CCW  = const(1700)      # us - sentido antihorario
_SERVO_STOP = const(1500)      # us - parado

# Direcciones (indices)
_IZQ      = const(0)
_DER      = const(1)
_ARR      = const(2)
_ABJ      = const(3)
_DIA_IA   = const(4)
_DIA_IB   = const(5)
_DIA_DA   = const(6)
_DIA_DB   = const(7)
_N_DIR    = const(8)

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
# Hardware (tuplas indexadas por direccion, no dicts)
# ---------------------------------------------------------------------------
_btns = tuple(Pin(i, Pin.IN, Pin.PULL_UP) for i in range(_N_DIR))
_fans = tuple(Pin(i + 8, Pin.OUT, value=0) for i in range(_N_DIR))

_srv_x = PWM(Pin(16)); _srv_x.freq(50)
_srv_y = PWM(Pin(17)); _srv_y.freq(50)

_adc = ADC(Pin(26))


# ---------------------------------------------------------------------------
# Servo
# ---------------------------------------------------------------------------

def _servo_us(srv, us):
    srv.duty_u16(us * 65535 // 20000)


def _servo_mv(srv, d, ms):
    """Mueve servo: d=1 CW, d=-1 CCW. ms=duracion."""
    _servo_us(srv, _SERVO_CW if d == 1 else _SERVO_CCW)
    time.sleep_ms(ms)
    _servo_us(srv, _SERVO_STOP)


def _servo_stop():
    _servo_us(_srv_x, _SERVO_STOP)
    _servo_us(_srv_y, _SERVO_STOP)


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

def _scan_axis(srv, steps, step_ms):
    """Barre un eje rastreando el maximo in-place (sin crear lista)."""
    best_s = 0
    best_v = 0
    for i in range(steps):
        _servo_mv(srv, 1, step_ms)
        time.sleep_ms(_SETTLE_MS)
        v = _read_v()
        print("  %d/%d v=%d" % (i + 1, steps, v))
        if v > best_v:
            best_v = v
            best_s = i
    return best_s, best_v


def _search_axis(srv, name):
    """Busca optimo en un eje: extremo -> barrido -> retorno al maximo."""
    step_ms = _MAX_TRAVEL // _SCAN_STEPS

    print("[%s] extremo" % name)
    _servo_mv(srv, -1, _MAX_TRAVEL)
    time.sleep_ms(_SETTLE_MS)

    print("[%s] barrido" % name)
    best_s, best_v = _scan_axis(srv, _SCAN_STEPS, step_ms)
    print("[%s] mejor: paso %d v=%d" % (name, best_s + 1, best_v))

    # Retorno: estamos en paso SCAN_STEPS-1, ir a best_s
    diff = best_s - (_SCAN_STEPS - 1)
    if diff != 0:
        d = 1 if diff > 0 else -1
        _servo_mv(srv, d, abs(diff) * step_ms)

    print("[%s] ok" % name)
    return best_v


def _search_dual():
    """Busqueda en ambos ejes con refinamiento."""
    print("== doble eje ==")
    _search_axis(_srv_y, "Y")
    _search_axis(_srv_x, "X")
    # Refinamiento
    _search_axis(_srv_y, "Y")
    v = _search_axis(_srv_x, "X")
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
    print("FLOATING FARM")
    print("Esperando dir...")

    _servo_stop()
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
            _servo_stop()
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
            _search_axis(_srv_y, "Y")
        elif ax == _AXIS_X:
            _search_axis(_srv_x, "X")
        else:
            _search_dual()

        gc.collect()
        print("\nv=%d. Pulsa mismo btn=stop, otro=cambiar.\n" % _read_v())
        _wait_release(p)


main()
