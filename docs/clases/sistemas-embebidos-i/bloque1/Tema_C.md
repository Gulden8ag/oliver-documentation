# Control de GPIO

Este tutorial guía desde la manipulación de registros hasta el uso de abstracciones modernas (SDKs, HALs) para controlar GPIO en microcontroladores.

---

## 1. ¿Qué es el control de registros?

Un registro es una pequeña memoria interna del microcontrolador, normalmente de 8, 16 o 32 bits. Cada bit de un registro controla o refleja el estado de alguna función del hardware: habilitar una salida, indicar una entrada, seleccionar un modo, etc.

Cuando se programa a nivel de registro, se leen y escriben directamente las direcciones de memoria donde residen esos registros, sin funciones de librerías de alto nivel.

Ejemplos de familias:

* ATmega328P (Arduino Uno):

  * `DDRB` → dirección de datos (input/output)
  * `PORTB` → valores de salida
  * `PINB` → lectura de entradas
* RP2040 (Pico 2):

  * `SIO->gpio_oe` → configuración de pines como salida
  * `SIO->gpio_out` → valores de salida
  * `SIO->gpio_in` → lectura de entradas

La idea transversal es la misma: leer y escribir bits en registros.

---

## 2. Operadores bit a bit (bitwise) en C

Para manipular registros se usan operadores bitwise:

| Operador     | Uso                    | Ejemplo            | Explicación                             |               |                                           |
| ------------ | ---------------------- | ------------------ | --------------------------------------- | ------------- | ----------------------------------------- |
| \`           | \` (OR)                | Poner un bit en 1  | \`reg                                   | = (1 << n);\` | fuerza el bit n a 1 sin afectar los demás |
| `&` (AND)    | Conservar ciertos bits | `reg &= mask;`     | mantiene en 1 solo donde `mask` tiene 1 |               |                                           |
| `~` (NOT)    | Invertir bits          | `~(1 << n)`        | máscara con todos 1 excepto el bit n    |               |                                           |
| `^` (XOR)    | Invertir un bit        | `reg ^= (1 << n);` | cambia el bit n de 0↔1                  |               |                                           |
| `<<` (shift) | Desplazar              | `(1 << 5)`         | genera un valor con el bit 5 en 1       |               |                                           |

Ejemplo breve:

```
reg = 00001000  (bit 3 = 1)
reg |= (1 << 2)  → 00001100
reg &= ~(1 << 3) → 00000100
reg ^= (1 << 2)  → 00000000
```

---

## 3. El bloque SIO (Single-Cycle I/O) en RP2040

SIO es la unidad del RP2040 para acceso rápido a GPIO. Proporciona registros de lectura/escritura directa con operaciones atómicas por bits.

### Registros principales de SIO

* `gpio_oe` → estado de dirección (1 = salida, 0 = entrada)
* `gpio_oe_set` → pone bits a 1 (salida)
* `gpio_oe_clr` → pone bits a 0 (entrada)
* `gpio_out` → estado actual de salidas
* `gpio_out_set` → pone pines en alto (1) de forma atómica multipin
* `gpio_out_clr` → pone pines en bajo (0) de forma atómica multipin
* `gpio_out_xor` → invierte pines de forma atómica multipin
* `gpio_in` → lectura de entradas

Cada bit corresponde a un GPIO (bit 2 controla GPIO2, etc.).

### Tabla de direcciones de referencia de SIO

La siguiente tabla resume direcciones base de registros SIO relacionados con GPIO (RP2040):

| Registro           | Dirección  |
| ------------------ | ---------- |
| gpio\_in           | 0xd0000004 |
| gpio\_hi\_in       | 0xd0000008 |
| gpio\_out          | 0xd0000010 |
| gpio\_set          | 0xd0000014 |
| gpio\_clr          | 0xd0000018 |
| gpio\_togl         | 0xd000001c |
| gpio\_oe           | 0xd0000020 |
| gpio\_oe\_set      | 0xd0000024 |
| gpio\_oe\_clr      | 0xd0000028 |
| gpio\_togl         | 0xd000002c |
| gpio\_hi\_out      | 0xd0000030 |
| gpio\_hi\_set      | 0xd0000034 |
| gpio\_hi\_clr      | 0xd0000038 |
| gpio\_hi\_togl     | 0xd000003c |
| gpio\_hi\_oe       | 0xd0000040 |
| gpio\_hi\_oe\_set  | 0xd0000044 |
| gpio\_hi\_oe\_clr  | 0xd0000048 |
| gpio\_hi\_oe\_togl | 0xd000004c |

---

## 4. De registros a SDKs y HALs

Trabajar con registros ofrece control máximo, pero puede ser verboso y menos portable. Las capas de abstracción ayudan a mantener el código legible y reutilizable:

1. Nivel de registros (SIO): máximo control, mínima portabilidad.

2. Pico SDK: funciones tipo `gpio_init()`, `gpio_set_dir()`, `gpio_put()` envuelven el acceso a registros. Existen también primitivas multipin atómicas (`gpio_set_mask`, `gpio_clr_mask`, `gpio_xor_mask`).

3. HAL/Arduino: API genérica (`pinMode`, `digitalWrite`) fácil de usar y portable entre placas, pero las escrituras suelen ser secuenciales por pin.

4. Capas aún más altas (MicroPython/CircuitPython): prototipado rápido a costa de latencia.

---

## 5. Simultaneidad entre pines: qué esperar

* **Escritura atómica multipin (SIO):** cuando se escribe una máscara a `gpio_out_set`, `gpio_out_clr` o `gpio_out_xor`, el hardware actualiza **todos los bits de la máscara** con una única operación; esto produce flancos prácticamente simultáneos en todos los pines de la máscara.
* **RMW vs atómico:** evitar `sio_hw->gpio_out |= mask;` porque puede implicar una secuencia leer–modificar–escribir. Prefiera los registros alias `*_set/*_clr/*_xor` que son atómicos.
* **Desfase residual esperado:** aunque la operación sea única, pueden existir diferencias de pocos ns por:

  * camino interno del banco de GPIO
  * configuración de `slew rate`/`drive strength`
  * carga y longitud del trazado a cada pin
  * sondas del instrumento (capacitancia y masa)
* **Conclusión práctica:** con SIO y máscara, los flancos son efectivamente simultáneos a escala de instrucción; el desfase que observará proviene mayormente de la física de salida y del método de medición.

Sugerencia avanzada: para sincronía aún más estricta (ej. marcos de reloj precisos), puede emplearse **PIO** con una única instrucción que empuje un bus de bits, o **DMA→SIO/PIO** para temporización repetible.

---

## 6. Ejemplos prácticos: parpadeo múltiple orientado a simultaneidad

Objetivo: demostrar simultaneidad con SIO (atómico multipin) y comparar con SDK y Arduino HAL. Pines usados: GPIO 2, 3 y 4.

### 6.1. SIO directo — simultáneo vs secuencial

```c
// Archivo: sio_multi_blink.c
#include "pico/stdlib.h"
#include "hardware/structs/sio.h"

#define P2 2
#define P3 3
#define P4 4

static inline void busy_cycles(uint32_t n) {
    while (n--) { __asm volatile ("nop"); }
}

int main() {
    stdio_init_all();

    // Configurar como salida (atómico)
    sio_hw->gpio_oe_set = (1u << P2) | (1u << P3) | (1u << P4);

    const uint32_t mask = (1u << P2) | (1u << P3) | (1u << P4);

    while (true) {
        // Simultáneo: una sola escritura atómica
        sio_hw->gpio_out_set = mask;   // flancos de subida simultáneos
        busy_cycles(1000);
        sio_hw->gpio_out_clr = mask;   // flancos de bajada simultáneos
        busy_cycles(1000);

        // Secuencial: medir separación entre flancos
        sio_hw->gpio_out_xor = (1u << P2);
        busy_cycles(100);
        sio_hw->gpio_out_xor = (1u << P3);
        busy_cycles(100);
        sio_hw->gpio_out_xor = (1u << P4);
        busy_cycles(800);
    }
}
```

Notas:

* Use los alias `*_set/*_clr/*_xor` para garantizar operación atómica multipin.
* Ajuste `busy_cycles` para que su osciloscopio distinga flancos.

### 6.2. Pico SDK — primitivas multipin

```c
// Archivo: sdk_multi_blink.c
#include "pico/stdlib.h"

#define P2 2
#define P3 3
#define P4 4

int main() {
    stdio_init_all();

    gpio_init(P2); gpio_set_dir(P2, GPIO_OUT);
    gpio_init(P3); gpio_set_dir(P3, GPIO_OUT);
    gpio_init(P4); gpio_set_dir(P4, GPIO_OUT);

    const uint32_t mask = (1u << P2) | (1u << P3) | (1u << P4);

    while (true) {
        // Simultáneo: funciones que mapean a alias atómicos de SIO
        gpio_set_mask(mask);   // HIGH simultáneo
        busy_wait_us_32(100);
        gpio_clr_mask(mask);   // LOW simultáneo
        busy_wait_us_32(100);

        // Secuencial (comparación)
        gpio_xor_mask(1u << P2); busy_wait_us_32(5);
        gpio_xor_mask(1u << P3); busy_wait_us_32(5);
        gpio_xor_mask(1u << P4); busy_wait_us_32(50);
    }
}
```

Notas:

* `gpio_set_mask/gpio_clr_mask/gpio_xor_mask` son multipin y atómicos.
* Si usa `gpio_put(pin, val)` repetido, la conmutación será secuencial.

### 6.3. Arduino HAL — escrituras secuenciales

```cpp
// Archivo: arduino_multi_blink.ino
// Seleccione la placa RP2040 adecuada en el core de Arduino

const uint8_t P2 = 2;
const uint8_t P3 = 3;
const uint8_t P4 = 4;

void setup() {
  pinMode(P2, OUTPUT);
  pinMode(P3, OUTPUT);
  pinMode(P4, OUTPUT);
}

void loop() {
  // Aproximación a "simultáneo": tres escrituras consecutivas
  // (no atómicas; espere pequeños desfases entre pines)
  digitalWrite(P2, HIGH);
  digitalWrite(P3, HIGH);
  digitalWrite(P4, HIGH);
  delayMicroseconds(100);
  digitalWrite(P2, LOW);
  digitalWrite(P3, LOW);
  digitalWrite(P4, LOW);
  delayMicroseconds(100);
}
```

Notas:

* El HAL de Arduino no provee una primitiva multipin atómica estándar; por tanto, medirá desfases entre escrituras.

---

## 7. Recomendaciones de medición con osciloscopio y lógica

1. Conecte sondas a P2, P3 y P4. Use la misma referencia de masa y cables cortos para minimizar inductancias.
2. Habilite persistencia o adquisición rápida para observar la superposición de flancos.
3. Mida:

   * Diferencia de tiempo entre flancos de subida de P2 vs P3 vs P4 en modo simultáneo (SIO/SDK): deberá ser cercana a 0 dentro de la resolución del instrumento; el residuo vendrá de física de salida y sondas.
   * Diferencias en modo secuencial: cuantifique la separación entre escrituras.
4. Pruebe distintas cargas (resistivas/capacitivas) y ajuste `drive strength`/`slew rate` en la configuración de los pads si fuese pertinente a su placa.
5. Para aún más sincronía, considere PIO con `OUT PINS, 3` alimentado por un `PULL` desde TX FIFO o un `DMA`.

---

## 8. Comparación rápida de estilos

| Acción                     | ATmega328P (AVR)      | RP2040 (SIO)                     | Pico SDK                         | Arduino HAL              | MicroPython                  |                   |
| -------------------------- | --------------------- | -------------------------------- | -------------------------------- | ------------------------ | ---------------------------- | ----------------- |
| Configurar pin como salida | \`DDRB                | = (1<\<PB0);\`                   | `sio_hw->gpio_oe_set = (1<<2);`  | `gpio_set_dir(2, true);` | `pinMode(2, OUTPUT);`        | `Pin(2, Pin.OUT)` |
| Encender LED               | \`PORTB               | = (1<\<PB0);\`                   | `sio_hw->gpio_out_set = (1<<2);` | `gpio_put(2, 1);`        | `digitalWrite(2, HIGH);`     | `led.value(1)`    |
| Apagar LED                 | `PORTB &= ~(1<<PB0);` | `sio_hw->gpio_out_clr = (1<<2);` | `gpio_put(2, 0);`                | `digitalWrite(2, LOW);`  | `led.value(0)`               |                   |
| Invertir LED               | `PORTB ^= (1<<PB0);`  | `sio_hw->gpio_out_xor = (1<<2);` | `gpio_xor_mask(1<<2);`           | *(no atómico multipin)*  | `led.value(not led.value())` |                   |

---
