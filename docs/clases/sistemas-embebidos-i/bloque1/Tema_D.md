# Entradas digitales

## Qué es una entrada digital

Una **entrada digital** es un GPIO configurado para **leer** un nivel lógico: **alto (1)** o **bajo (0)**. A diferencia de una salida, **no impone** voltaje; solo observa el que llega desde un botón, sensor digital o lógica externa.

### Estados posibles

* **Alto (1):** voltaje considerado como “1”.
* **Bajo (0):** voltaje considerado como “0”.
* **Flotante (Z):** sin referencia; puede leer valores aleatorios (evítalo).

### Niveles lógicos y umbrales

En la práctica, el comparador interno decide 1/0 por **umbrales**:

* **1** típico: ≥ \~2.0–2.4 VDD
* **0** típico: ≤ \~0.5–0.8 VDD
  Entre ambos hay **zona incierta** → evita operar ahí.

![Niveles lógicos](../../../images/logicleve.png)

---

## Pull-ups / Pull-downs (evitar “flotante”)

Los **pulls** son resistencias hacia **VDD** (pull-up) o **GND** (pull-down) que fijan un estado por defecto cuando la línea puede quedar flotante.
En el Pi pico2 puedes usar **pulls internos** o **externos**.

**Pulls internos (≈ 50–80 kΩ, típ. \~50 kΩ)**

* **Útiles:** prototipos rápidos, botones cercanos (cables cortos), señales lentas/limpias.
* **Limitaciones:** son **débiles**; con cables largos o capacitancia elevada los flancos suben lento y entra ruido. No aptos para buses como **I²C/1-Wire**.

**Pulls externos (1 kΩ–100 kΩ)**

* **Útiles:** buses abiertos (I²C), cables largos/ambientes ruidosos, control preciso de **RC** (debounce), o para ajustar **consumo/tiempos de subida**.
* **Trade-off:** R baja → más corriente y flancos rápidos; R alta → menos corriente y flancos lentos/sensibles a ruido.

**Guía rápida de elección**

* **Botón local:** interno o 10 kΩ externo.
* **Cable largo/ruidoso:** 4.7–10 kΩ externo (+ Schmitt).
* **I²C (open-drain):** 4.7–10 kΩ y ajustar según capacitancia/frecuencia.

---

## Problemas típicos y mitigación

### Rebote (“bounce”)

Un botón mecánico genera múltiples conmutaciones en 1–20 ms al presionar/soltar.
**Mitiga** con **debounce** en **hardware (RC + Schmitt)**, en **software**, o ambos.

### Ruido (EMI, cables, Z)

Las entradas flotantes o cables largos capturan interferencia.
**Mitiga** con:

* Pull-ups/downs adecuados.
* **RC** + **Schmitt trigger**.
* Resistencia **serie 100–330 Ω** para limitar picos.
* **TVS** si el entorno es hostil (industrial/automotriz).

![Schmitt Trigger](../../../images/schmitt.png)

---

## Dimensionamiento práctico

**Consumo al presionar** (activo-bajo con pull-up): $I \approx \dfrac{V}{R}$

* 3.3 V / 10 kΩ ≈ **0.33 mA**
* 3.3 V / 4.7 kΩ ≈ **0.7 mA**

**RC para debounce (hardware):** $\tau = R \cdot C$

* Punto de partida: **2–10 ms** (p. ej., 10 kΩ + 220 nF → 2.2 ms).

**Buses abiertos (I²C):**

* Comienza con **4.7–10 kΩ** y ajusta según **capacitancia** y **frecuencia**.

> **Nota RP2350 – corrientes de E/S:** las cifras de **corriente por pin (2/4/8/12 mA)** y **límite total \~50 mA** aplican a **salidas**. En **entradas**, la corriente la dominan las resistencias de pull y fugas del pad.

---

## Implementación

### Bajo nivel (PADS/SIO)

```c
#include "hardware/regs/padsbank0.h"
#include "hardware/structs/padsbank0.h"
#include "hardware/structs/sio.h"
#include "pico/stdlib.h"

#define PIN 10

int main() {
    // Habilitar entrada, pull-up y Schmitt en el pad
    hw_set_bits(&padsbank0_hw->io[PIN],
        PADS_BANK0_GPIO0_IE_BITS |     // Input enable
        PADS_BANK0_GPIO0_PUE_BITS |    // Pull-up
        PADS_BANK0_GPIO0_SCHMITT_BITS  // Schmitt trigger
    );
    hw_clear_bits(&padsbank0_hw->io[PIN], PADS_BANK0_GPIO0_PDE_BITS); // sin pull-down

    // Asegurar que el GPIO no esté en salida (SIO)
    sio_hw->gpio_oe_clr = 1u << PIN;

    while (true) {
        bool v = (sio_hw->gpio_in >> PIN) & 1u; // leer pin
        // ... usar v ...
        sleep_ms(1); // ~1 kHz de muestreo (evita busy-wait)
    }
}
```

### Alto nivel (Pico SDK)

```c
#include "pico/stdlib.h"
#include "hardware/gpio.h"

#define BTN  10
#define LED  25

int main() {
    stdio_init_all();

    gpio_init(LED); gpio_set_dir(LED, true);
    gpio_init(BTN); gpio_set_dir(BTN, false); // false = input
    gpio_pull_up(BTN); // activo-bajo: presionado = 0

    while (true) {
        bool pressed = (gpio_get(BTN) == 0);
        gpio_put(LED, pressed);
        sleep_ms(1);  // CPU friendly
    }
}
```

---

## Debounce (hardware y software)

### Hardware (RC + Schmitt)

![Debounce Circuit](../../../images/debounce-sch.webp)

* Filtra rebotes con una constante de tiempo **2–10 ms**.
* Habilita **Schmitt** para histéresis.

### Software (tres patrones)

1. **Retardo fijo (bloqueante)**
   Tras detectar cambio, espera **10–20 ms** y vuelve a leer. Simple, pero bloquea (usa `sleep_ms`).

2. **Integrador / ventana deslizante (no bloqueante)**
   Muestrea a intervalos regulares; acepta el cambio cuando acumulas **N lecturas coherentes**. Útil con varios botones.

3. **Máquina de estados**
   Estados: `estable_0 → posible_1 → estable_1 → posible_0 → ...`
   Solo confirmas transición si se mantiene el nuevo valor por un tiempo/lecturas.
