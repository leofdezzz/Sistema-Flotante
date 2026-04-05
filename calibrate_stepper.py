"""
Calibracion de step_delay para 28BYJ-48 + ULN2003
Ejecutar en el Pico via Thonny o mpremote.

Prueba distintos delays y cuenta cuantos pasos realmente completa
el motor midiendo con el ADC si hay desfase (o visualmente).
Tambien permite probar un rango automatico para encontrar el delay
minimo sin perder pasos.
"""

from machine import Pin
import time

# ---------------------------------------------------------------------------
# Config - ajustar segun tu cableado
# ---------------------------------------------------------------------------
# Pines del stepper a calibrar (cambiar a 20-23 para el eje Y)
PINS = (16, 17, 18, 19)

# Pasos por vuelta completa del 28BYJ-48 en half-step (~4076)
STEPS_PER_REV = 4076

# ---------------------------------------------------------------------------
# Half-step
# ---------------------------------------------------------------------------
HALFSTEP = (
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
    (1, 0, 0, 1),
)

pins = tuple(Pin(p, Pin.OUT, value=0) for p in PINS)
phase = 0


def step(delay_ms, direction=1):
    global phase
    phase = (phase + direction) % 8
    seq = HALFSTEP[phase]
    for i in range(4):
        pins[i].value(seq[i])
    time.sleep_ms(delay_ms)


def off():
    for p in pins:
        p.value(0)


# ---------------------------------------------------------------------------
# Test 1: Mover N pasos con un delay dado
# ---------------------------------------------------------------------------
def test_manual(delay_ms, steps=STEPS_PER_REV):
    """Mueve una cantidad de pasos con el delay indicado.
    Usa esto para verificar visualmente si completa el giro."""
    print(">> %d pasos a %d ms/paso" % (steps, delay_ms))
    t0 = time.ticks_ms()
    for _ in range(steps):
        step(delay_ms)
    elapsed = time.ticks_diff(time.ticks_ms(), t0)
    off()
    print("   Tiempo: %d ms (%.1f s)" % (elapsed, elapsed / 1000))
    print("   Velocidad: %.1f pasos/s" % (steps / (elapsed / 1000)))
    print()


# ---------------------------------------------------------------------------
# Test 2: Ida y vuelta - detectar pasos perdidos
# ---------------------------------------------------------------------------
def test_roundtrip(delay_ms, steps=STEPS_PER_REV):
    """Va N pasos adelante y N atras. Si el motor vuelve al mismo
    punto exacto, no pierde pasos a ese delay."""
    print(">> Ida y vuelta: %d pasos a %d ms" % (steps, delay_ms))
    print("   Marca la posicion inicial del eje.")
    input("   Pulsa ENTER para comenzar...")

    print("   Ida...")
    for _ in range(steps):
        step(delay_ms)
    time.sleep_ms(500)

    print("   Vuelta...")
    for _ in range(steps):
        step(delay_ms, direction=-1)
    off()

    print("   Si el eje volvio al punto exacto: OK, no pierde pasos.")
    print("   Si hay desfase: el delay es demasiado bajo.\n")


# ---------------------------------------------------------------------------
# Test 3: Busqueda automatica del delay minimo
# ---------------------------------------------------------------------------
def test_auto(min_delay=1, max_delay=5, steps=STEPS_PER_REV // 4):
    """Prueba cada delay de max a min. En cada prueba hace ida y vuelta
    de 1/4 de vuelta. Observa visualmente cual es el primero que falla."""
    print(">> Busqueda automatica: delay %d-%d ms, %d pasos" % (max_delay, min_delay, steps))
    print("   Observa cuando el motor empieza a vibrar o perder pasos.\n")

    for d in range(max_delay, min_delay - 1, -1):
        print("   delay = %d ms ... " % d, end="")

        # Ida
        for _ in range(steps):
            step(d)
        time.sleep_ms(300)

        # Vuelta
        for _ in range(steps):
            step(d, direction=-1)
        time.sleep_ms(500)
        off()

        print("hecho. Revisa posicion.")

    print("\n   El menor delay donde vuelve al origen = tu delay optimo.\n")


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------
def menu():
    print("=" * 40)
    print("Calibracion stepper 28BYJ-48")
    print("Pines: %s" % str(PINS))
    print("=" * 40)
    print()
    print("1. Girar 1 vuelta con delay especifico")
    print("2. Ida y vuelta (detectar pasos perdidos)")
    print("3. Busqueda automatica de delay minimo")
    print("4. Mover N pasos con delay especifico")
    print("0. Salir")
    print()

    while True:
        op = input("Opcion: ").strip()

        if op == "1":
            d = int(input("Delay (ms): "))
            test_manual(d)

        elif op == "2":
            d = int(input("Delay (ms): "))
            test_roundtrip(d)

        elif op == "3":
            mn = int(input("Delay minimo a probar (ms) [1]: ") or "1")
            mx = int(input("Delay maximo a probar (ms) [5]: ") or "5")
            test_auto(mn, mx)

        elif op == "4":
            d = int(input("Delay (ms): "))
            n = int(input("Pasos: "))
            test_manual(d, n)

        elif op == "0":
            off()
            print("Bye")
            break

        else:
            print("Opcion invalida")


menu()
