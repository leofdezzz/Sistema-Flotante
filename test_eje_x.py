"""
Test: Servo eje X (GP16) de forma aislada.
Mueve CW, CCW, para, y ejecuta un barrido completo con lectura ADC.
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
adc = ADC(Pin(26))


def servo_us(srv, us):
    srv.duty_u16(us * 65535 // 20000)


def servo_mv(srv, d, ms):
    servo_us(srv, SERVO_CW if d == 1 else SERVO_CCW)
    time.sleep_ms(ms)
    servo_us(srv, SERVO_STOP)


def read_v():
    t = 0
    for _ in range(ADC_SAMPLES):
        t += adc.read_u16()
        time.sleep_ms(5)
    return t // ADC_SAMPLES


def test_movimiento():
    """Prueba movimientos basicos: CW, pausa, CCW, pausa, stop."""
    print("=== TEST EJE X - Movimiento ===")

    print("CW 2s...")
    servo_mv(srv_x, 1, 2000)
    time.sleep_ms(500)

    print("CCW 2s...")
    servo_mv(srv_x, -1, 2000)
    time.sleep_ms(500)

    print("CW 1s...")
    servo_mv(srv_x, 1, 1000)
    time.sleep_ms(500)

    print("CCW 1s...")
    servo_mv(srv_x, -1, 1000)
    time.sleep_ms(500)

    servo_us(srv_x, SERVO_STOP)
    print("Movimiento OK\n")


def test_barrido():
    """Barrido completo del eje X con lectura de voltaje."""
    print("=== TEST EJE X - Barrido ===")
    step_ms = MAX_TRAVEL_MS // SCAN_STEPS

    print("Ir a extremo (CCW %dms)..." % MAX_TRAVEL_MS)
    servo_mv(srv_x, -1, MAX_TRAVEL_MS)
    time.sleep_ms(SETTLE_MS)

    print("Barriendo %d pasos..." % SCAN_STEPS)
    best_s = 0
    best_v = 0
    for i in range(SCAN_STEPS):
        servo_mv(srv_x, 1, step_ms)
        time.sleep_ms(SETTLE_MS)
        v = read_v()
        print("  paso %d/%d v=%d" % (i + 1, SCAN_STEPS, v))
        if v > best_v:
            best_v = v
            best_s = i

    print("Mejor: paso %d v=%d" % (best_s + 1, best_v))

    # Retorno al mejor paso
    diff = best_s - (SCAN_STEPS - 1)
    if diff != 0:
        d = 1 if diff > 0 else -1
        servo_mv(srv_x, d, abs(diff) * step_ms)

    print("Posicionado. Voltaje actual: %d" % read_v())
    servo_us(srv_x, SERVO_STOP)
    print("Barrido OK\n")


print(">> Test eje X")
print("   Voltaje inicial: %d" % read_v())
test_movimiento()
test_barrido()
print(">> Fin test eje X")
