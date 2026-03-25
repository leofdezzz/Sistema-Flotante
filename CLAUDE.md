# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Floating Farm is a MicroPython project for a Raspberry Pi Pico that controls a floating wind turbine in a water tank. Fans simulate wind from 8 directions, and the turbine automatically searches for the optimal position (where a hole in a wall lets air through) by maximizing voltage output.

## Hardware

- **MCU**: Raspberry Pi Pico (MicroPython) — may be ported to other microcontrollers later
- **Servos**: 2x MG996R 360° continuous rotation (X and Y axes) controlled via PWM at 50Hz
- **Fans**: 8 fans (one per direction) switched via relays (active high, ON/OFF only)
- **Sensor**: ADC on GP26 reads turbine voltage output
- **Buttons**: 8 buttons with internal pull-up (active low)

## Architecture

Single-file (`main.py`) MicroPython application. Key sections:

- **Pin configuration**: Buttons GP0-7, relays GP8-15, servos GP16-17, ADC GP26
- **Servo control**: Time-based positioning (no encoders) — `servo_move(servo, direction, duration)`
- **Search algorithm**: Sweeps each relevant axis end-to-end in discrete steps, reads voltage at each step, returns to the position with maximum reading. Diagonal directions do iterative refinement across both axes.
- **Main loop**: Polls buttons, activates corresponding fan(s), runs search, holds position

## Development

Deploy `main.py` to the Pico via Thonny, mpremote, or rshell:

```bash
mpremote connect auto cp main.py :main.py
mpremote connect auto reset
```

## Key Configuration Constants

All tunable parameters are at the top of `main.py`: travel time, scan resolution, servo pulse widths, debounce, ADC averaging. Servo pulse values (`SERVO_CW_US`, `SERVO_CCW_US`, `SERVO_STOP_US`) must be calibrated per physical servo.

## Language

The user works in Spanish. Use Spanish for all communication.
