"""
Test: Ambos ejes X (GP16) e Y (GP17) juntos.
Prueba movimiento simultaneo y busqueda dual con refinamiento.
"""

from machine import Pin, PWM, ADC
import time

# Config
SERVO_CW  = 1300
SERVO_CCW = 1700
SERVO_STOP = 1500
MAX_TRAVEL_MS = 5000
SCAN_STEPS = 20
SETTLE_MS = 300
ADC_SAMPLES = 10

srv_x = PWM(Pin(16)); srv_x.freq(50)
srv_y = PWM(Pin(17)); srv_y.freq(50)
adc = ADC(Pin(26))


def servo_us(srv, us):
    srv.duty_u16(us * 65535 // 20000)


def servo_mv(srv, d, ms):
    servo_us(srv, SERVO_CW if d == 1 else SERVO_CCW)
    time.sleep_ms(ms)
    servo_us(srv, SERVO_STOP)


def servo_stop_all():
    servo_us(srv_x, SERVO_STOP)
    servo_us(srv_y, SERVO_STOP)


def read_v():
    t = 0
    for _ in range(ADC_SAMPLES):
        t += adc.read_u16()
        time.sleep_ms(5)
    return t // ADC_SAMPLES


def search_axis(srv, name):
    """Barrido completo de un eje, retorna al maximo."""
    step_ms = MAX_TRAVEL_MS // SCAN_STEPS

    print("[%s] extremo" % name)
    servo_mv(srv, -1, MAX_TRAVEL_MS)
    time.sleep_ms(SETTLE_MS)

    print("[%s] barrido" % name)
    best_s = 0
    best_v = 0
    for i in range(SCAN_STEPS):
        servo_mv(srv, 1, step_ms)
        time.sleep_ms(SETTLE_MS)
        v = read_v()
        print("  %d/%d v=%d" % (i + 1, SCAN_STEPS, v))
        if v > best_v:
            best_v = v
            best_s = i

    print("[%s] mejor: paso %d v=%d" % (name, best_s + 1, best_v))

    diff = best_s - (SCAN_STEPS - 1)
    if diff != 0:
        d = 1 if diff > 0 else -1
        servo_mv(srv, d, abs(diff) * step_ms)

    print("[%s] ok" % name)
    return best_v


def test_movimiento_simultaneo():
    """Mueve ambos ejes en secuencia para verificar que no interfieren."""
    print("=== TEST XY - Movimiento independiente ===")

    print("X CW 2s...")
    servo_mv(srv_x, 1, 2000)
    time.sleep_ms(300)

    print("Y CW 2s...")
    servo_mv(srv_y, 1, 2000)
    time.sleep_ms(300)

    print("X CCW 2s...")
    servo_mv(srv_x, -1, 2000)
    time.sleep_ms(300)

    print("Y CCW 2s...")
    servo_mv(srv_y, -1, 2000)
    time.sleep_ms(300)

    servo_stop_all()
    print("Movimiento OK\n")


def test_busqueda_dual():
    """Busqueda completa en ambos ejes con refinamiento (como en main.py)."""
    print("=== TEST XY - Busqueda dual ===")

    print("--- Pasada 1: Y ---")
    search_axis(srv_y, "Y")

    print("--- Pasada 1: X ---")
    search_axis(srv_x, "X")

    print("--- Pasada 2 (refinar): Y ---")
    search_axis(srv_y, "Y")

    print("--- Pasada 2 (refinar): X ---")
    v = search_axis(srv_x, "X")

    print("Busqueda dual OK. Voltaje final: %d\n" % v)


print(">> Test ejes X+Y")
print("   Voltaje inicial: %d" % read_v())
test_movimiento_simultaneo()
test_busqueda_dual()
servo_stop_all()
print(">> Fin test ejes X+Y")
