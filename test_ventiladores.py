"""
Test: Sistema de ventiladores (reles GP8-GP15).
Enciende cada ventilador individualmente, luego combinaciones.
"""

from machine import Pin
import time

# Nombres para cada ventilador
_NAMES = ("izq", "der", "arr", "abj", "dia_ia", "dia_ib", "dia_da", "dia_db")

# Reles (GP8-GP15, activo alto)
_fans = tuple(Pin(i + 8, Pin.OUT, value=0) for i in range(8))


def fans_off():
    for f in _fans:
        f.value(0)


def test_individual():
    """Enciende cada ventilador 2s uno por uno."""
    print("=== TEST VENTILADORES - Individual ===")
    for i in range(8):
        print("  ON: %s (GP%d)" % (_NAMES[i], i + 8))
        _fans[i].value(1)
        time.sleep_ms(2000)
        _fans[i].value(0)
        time.sleep_ms(500)
    print("Individual OK\n")


def test_pares_opuestos():
    """Enciende pares opuestos para verificar que no hay conflicto."""
    print("=== TEST VENTILADORES - Pares opuestos ===")
    pares = (
        (0, 1, "izq + der"),
        (2, 3, "arr + abj"),
        (4, 7, "dia_ia + dia_db"),
        (5, 6, "dia_ib + dia_da"),
    )
    for a, b, desc in pares:
        print("  ON: %s" % desc)
        _fans[a].value(1)
        _fans[b].value(1)
        time.sleep_ms(2000)
        fans_off()
        time.sleep_ms(500)
    print("Pares OK\n")


def test_todos():
    """Enciende todos los ventiladores a la vez 3s."""
    print("=== TEST VENTILADORES - Todos ===")
    print("  Encendiendo todos...")
    for f in _fans:
        f.value(1)
    time.sleep_ms(3000)
    fans_off()
    print("Todos OK\n")


def test_secuencia_rapida():
    """Enciende y apaga cada ventilador rapidamente (0.5s) en secuencia circular."""
    print("=== TEST VENTILADORES - Secuencia rapida ===")
    for vuelta in range(2):
        print("  Vuelta %d" % (vuelta + 1))
        for i in range(8):
            fans_off()
            _fans[i].value(1)
            time.sleep_ms(500)
    fans_off()
    print("Secuencia OK\n")


print(">> Test ventiladores")
test_individual()
test_pares_opuestos()
test_todos()
test_secuencia_rapida()
fans_off()
print(">> Fin test ventiladores")
