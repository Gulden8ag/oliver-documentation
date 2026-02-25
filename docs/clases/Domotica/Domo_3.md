# Guía práctica para un sistema hidropónico  

Esta guía está pensada para que armes un “cerebro” de control para hidroponía (NFT, DWC o goteo) usando **ESP32** en **Arduino IDE**, con énfasis en:  
- temporización **sin `delay()`** usando `millis()`  
- reloj de tiempo real **DS3231** para horarios  
- **watchdog** y **estados de falla**  
- buenas prácticas: máquina de estados, filtrado, calibración, seguridad eléctrica

Antes de empezar, revisemos algunos ejemplos de proyectos reales para inspirarnos:

- [Growzen](https://fabacademy.org/2025/labs/dilijan/students/zhirayr-ghukasyan/projects/final-project/)
- [Green Bricks](https://fabacademy.org/archives/2015/eu/students/monaco.lina/00_mainprojdiary.html)
- [Rotary Hydroponics](https://fabacademy.org/2023/labs/charlotte/students/ryan-kim/projects/final-project/)
- [Growbox](https://archive.fabacademy.org/2017/fablabbottrophrw/students/64/finalsummary.html)
- [Oxgrow](https://archive.fabacademy.org/2018/labs/fablabkochi/students/suhail-p/project.html)
- [Local Farm](https://fabacademy.org/archives/2014/students/garita.robert/19.ProjectDevelopment.html)
- [Dima ALBOT](https://archive.fabacademy.org/archives/2017/fablabkamplintfort/students/396/final.html)
- [Bamboco](https://fabacademy.org/archives/2015/eu/students/boavida.maria/final_project.html)

---

## 0) Arquitectura recomendada (visión general)

**Entradas típicas**
- Nivel de tanque (flotador, ultrasónico, presión)  
- Temperatura agua (DS18B20)  
- pH (módulo con salida analógica)  
- EC/TDS (módulo con salida analógica)  
- Temperatura y humedad ambiente (SHT31/DHT22)  
- Caudal (sensor de flujo)  
- Voltaje de batería/fuente

**Salidas típicas**
- Bomba recirculación (relevador/SSR/MOSFET)  
- Solenoide de llenado (relevador)  
- Bomba peristáltica pH+/pH- (PWM o relevador)  
- Aireador (relevador)  
- Ventiladores/iluminación (PWM/SSR)

**Regla de oro (seguridad):**
- Si manejas AC (110/220V), usa **relevadores con optoaislamiento**, fusibles, tierra física y gabinete.  
- Mantén **AC separada físicamente** de señales (I2C/ADC) y usa filtros/TVS si hay ruido.

---

## 1) Convenciones de pines en ESP32 (importante)

- Evita usar pines “problemáticos” en arranque (strapping pins): **GPIO0, GPIO2, GPIO12, GPIO15** (dependen de la placa).  
- ADC: en ESP32 hay ADC1 y ADC2; **ADC2 se comparte con WiFi**. Si piensas usar WiFi, prefiere **ADC1** (GPIO32–GPIO39).  
- I2C: puedes usar casi cualquier GPIO; por convención:
  - SDA = 21, SCL = 22 (muy común en DevKit)

---

## 2) Ejercicio 1 — Temporización robusta con `millis()` (sin `delay()`)

### Objetivo
Controlar una bomba con ciclos:  
- ON 10 s  
- OFF 50 s  
y al mismo tiempo leer un sensor cada 2 s, sin bloquear el programa.

### Idea clave
Cada tarea tiene su **propio temporizador** y se ejecuta si ya “tocó” (por diferencia de `millis()`).

```cpp
// EJERCICIO 1: Scheduler simple con millis() (ESP32 / Arduino IDE)

const int PIN_BOMBA = 26; // ejemplo (ajusta)
bool bombaEncendida = false;

unsigned long tBomba = 0;
unsigned long tSensor = 0;

const unsigned long BOMBA_ON_MS  = 10UL * 1000;
const unsigned long BOMBA_OFF_MS = 50UL * 1000;
const unsigned long SENSOR_MS    = 2UL  * 1000;

void setup() {
  pinMode(PIN_BOMBA, OUTPUT);
  digitalWrite(PIN_BOMBA, LOW);
  Serial.begin(115200);
}

void loop() {
  unsigned long ahora = millis();

  // 1) Tarea: ciclo de bomba
  if (bombaEncendida) {
    if (ahora - tBomba >= BOMBA_ON_MS) {
      bombaEncendida = false;
      tBomba = ahora;
      digitalWrite(PIN_BOMBA, LOW);
      Serial.println("BOMBA: OFF");
    }
  } else {
    if (ahora - tBomba >= BOMBA_OFF_MS) {
      bombaEncendida = true;
      tBomba = ahora;
      digitalWrite(PIN_BOMBA, HIGH);
      Serial.println("BOMBA: ON");
    }
  }

  // 2) Tarea: lectura de sensor (simulada)
  if (ahora - tSensor >= SENSOR_MS) {
    tSensor = ahora;
    int adc = analogRead(34); // ejemplo ADC1
    Serial.printf("ADC=%d\n", adc);
  }

  // Aquí podrían convivir más tareas (WiFi, UI, control pH, etc.)
}
```

### Retos
1. Cambia el patrón a: ON 5 min, OFF 25 min.  
2. Agrega una tercera tarea: imprimir el “uptime” cada 1 minuto.  
3. Implementa un **“modo noche”** (variable booleana) que duplique el OFF cuando sea `true`.

---

## 3) Ejercicio 2 — Máquina de estados para operación + fallas 

### Objetivo
Separar claramente:
- NORMAL: todo ok  
- LLENANDO: abre solenoide hasta nivel alto  
- ERROR: detiene actuadores y enciende alerta

### Señales de ejemplo
- `nivelBajo` (flotador bajo = 1)  
- `nivelAlto` (flotador alto = 1)  
- `timeout` llenado (si tarda demasiado)

```cpp
enum Estado {
  NORMAL,
  LLENANDO,
  ERROR
};

const int PIN_SOLENOIDE = 27;
const int PIN_ALERTA    = 25;

const int PIN_NIVEL_BAJO = 33;
const int PIN_NIVEL_ALTO = 32;

Estado estado = NORMAL;
unsigned long tEstado = 0;
const unsigned long TIMEOUT_LLENADO_MS = 3UL * 60UL * 1000; // 3 min

void setup() {
  pinMode(PIN_SOLENOIDE, OUTPUT);
  pinMode(PIN_ALERTA, OUTPUT);

  pinMode(PIN_NIVEL_BAJO, INPUT_PULLUP);
  pinMode(PIN_NIVEL_ALTO, INPUT_PULLUP);

  digitalWrite(PIN_SOLENOIDE, LOW);
  digitalWrite(PIN_ALERTA, LOW);

  Serial.begin(115200);
}

bool nivelBajo() { return digitalRead(PIN_NIVEL_BAJO) == LOW; }
bool nivelAlto() { return digitalRead(PIN_NIVEL_ALTO) == LOW; }

void entrar(Estado nuevo) {
  estado = nuevo;
  tEstado = millis();
  Serial.printf("-> Estado: %d\n", estado);
}

void loop() {
  unsigned long ahora = millis();

  switch (estado) {
    case NORMAL: {
      digitalWrite(PIN_ALERTA, LOW);
      digitalWrite(PIN_SOLENOIDE, LOW);

      if (nivelBajo() && !nivelAlto()) {
        entrar(LLENANDO);
      }
      break;
    }

    case LLENANDO: {
      digitalWrite(PIN_SOLENOIDE, HIGH);

      if (nivelAlto()) {
        digitalWrite(PIN_SOLENOIDE, LOW);
        entrar(NORMAL);
      } else if (ahora - tEstado > TIMEOUT_LLENADO_MS) {
        digitalWrite(PIN_SOLENOIDE, LOW);
        entrar(ERROR);
      }
      break;
    }

    case ERROR: {
      // fail-safe
      digitalWrite(PIN_SOLENOIDE, LOW);
      digitalWrite(PIN_ALERTA, HIGH);

      // “reset” manual: si ambos niveles están OK por 5s, vuelve a NORMAL
      if (!nivelBajo() && nivelAlto()) {
        if (ahora - tEstado > 5000) entrar(NORMAL);
      } else {
        tEstado = ahora; // reinicia ventana si condición no se cumple
      }
      break;
    }
  }
}
```

### Retos
1. Agrega un estado **MANTENIMIENTO** activado por un botón (con debounce).  
2. En ERROR, registra un código de falla (ej. 1=timeout llenado, 2=sensor inválido).  
3. Haz que la bomba de recirculación se apague siempre que el estado sea ERROR.

---

## 4) Ejercicio 3 — DS3231 (RTC) para horarios reales

### Objetivo
- Leer hora/fecha del DS3231  
- Controlar iluminación o bomba en una ventana horaria (ej. 06:00–22:00)  
- Evitar depender del “uptime”

### Librerías sugeridas
- `RTClib` (Adafruit) o `DS3231` (varias). Aquí usamos **RTClib**.

**Cableado típico:**
- VCC → 3.3V (muchos módulos aceptan 3.3–5V; verifica el tuyo)  
- GND → GND  
- SDA → GPIO21  
- SCL → GPIO22

```cpp
#include <Wire.h>
#include "RTClib.h"

RTC_DS3231 rtc;

const int PIN_LUZ = 26;

bool enVentana(DateTime now, int hIni, int mIni, int hFin, int mFin) {
  int mins = now.hour() * 60 + now.minute();
  int ini  = hIni * 60 + mIni;
  int fin  = hFin * 60 + mFin;
  // caso simple (misma fecha): ini <= mins < fin
  return (mins >= ini && mins < fin);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LUZ, OUTPUT);
  digitalWrite(PIN_LUZ, LOW);

  Wire.begin(21, 22);

  if (!rtc.begin()) {
    Serial.println("No se encontró DS3231. Revisa cableado.");
    while (true) delay(1000);
  }

  // Si el RTC perdió energía, ajusta a fecha/hora de compilación:
  if (rtc.lostPower()) {
    Serial.println("RTC sin energía previa. Ajustando a compile time...");
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }
}

void loop() {
  DateTime now = rtc.now();

  bool luzOn = enVentana(now, 6, 0, 22, 0); // 06:00 a 22:00
  digitalWrite(PIN_LUZ, luzOn ? HIGH : LOW);

  Serial.printf("%04d-%02d-%02d %02d:%02d:%02d | LUZ=%d\n",
                now.year(), now.month(), now.day(),
                now.hour(), now.minute(), now.second(),
                (int)luzOn);

  delay(1000); // aquí sí es aceptable si solo estás monitoreando
}
```

### Retos
1. Implementa ventana “que cruza medianoche” (ej. 20:00–06:00).  
2. Guarda 2 ventanas (día/noche) y alterna por día de la semana (Lun–Dom).  
3. Agrega un “override manual” por 15 min usando `millis()`.

---

## 5) Ejercicio 4 — Watchdog (WDT) para evitar cuelgues y reinicios controlados

### Objetivo
- Usar el **Task Watchdog** de ESP32 para reiniciar si el loop se “atora”  
- Registrar reinicios y causa (opcional)

**Nota:** En Arduino-ESP32 existen dos enfoques comunes:
1) `esp_task_wdt_*` (oficial ESP-IDF)  
2) `Ticker` + `ESP.restart()` (no es watchdog real)

Aquí usamos el **Task WDT** (más “real”).

```cpp
#include <esp_task_wdt.h>

// Timeout del WDT en segundos
const int WDT_TIMEOUT_S = 5;

void setup() {
  Serial.begin(115200);

  // Inicializa WDT para la tarea actual (loopTask)
  esp_task_wdt_init(WDT_TIMEOUT_S, true); // true = panic/restart
  esp_task_wdt_add(NULL); // añade la tarea actual
}

void loop() {
  // Alimenta el watchdog (feed) regularmente
  esp_task_wdt_reset();

  // Simula tareas normales
  delay(100);

  // PRUEBA: descomenta para forzar cuelgue (no alimenta WDT)
  // while(true) { delay(1000); }
}
```

### Buenas prácticas con WDT
- Alimenta el WDT **solo** si el sistema está “sano” (ej. sensores válidos, tareas corriendo).
- Si tienes tareas largas (WiFi reconexión, I/O), aliméntalo dentro de esos ciclos o mejor: hazlas no-bloqueantes.

### Retos
1. Alimenta el WDT únicamente si un “latido” (heartbeat) se actualizó en los últimos 2 s.  
2. Guarda en NVS/Preferences un contador de reinicios para diagnóstico.  
3. Implementa un “modo seguro” al detectar 3 reinicios en menos de 10 minutos.

---

## 6) Ejercicio 5 — Detección de fallas (sensor inválido, bomba sin caudal, etc.)

### Objetivo
Crear una capa de “salud” que active FAIL-SAFE si algo no tiene sentido.

Ejemplos de reglas:
- pH fuera de rango físico: < 0 o > 14 → inválido  
- Temperatura agua > 45°C → falla/sobrecalentamiento  
- Bomba ON pero caudal = 0 durante 15 s → posible cavitación/atasco  
- Nivel bajo + bomba ON → riesgo de quemar bomba

**Plantilla: validación + latido**
```cpp
struct Health {
  bool okSensores = true;
  bool okCaudal   = true;
  bool okNivel    = true;
  unsigned long lastHeartbeat = 0;
} health;

void heartbeat() {
  health.lastHeartbeat = millis();
}

bool sistemaSano() {
  unsigned long ahora = millis();
  bool okLatido = (ahora - health.lastHeartbeat) < 2000;
  return okLatido && health.okSensores && health.okCaudal && health.okNivel;
}
```

### Retos
1. Implementa un contador de fallas por tipo y “backoff” antes de reintentar.  
2. Define fallas **críticas** (parar todo) vs **degradadas** (seguir con funciones mínimas).  
3. En ERROR, registra la última lectura válida y la última inválida.

---

## 7) Ejercicio 6 — Lecturas analógicas (filtro + calibración)

En hidroponía, pH/EC suelen ser analógicos y ruidosos.

### Ideas prácticas
- Promedio móvil (moving average)  
- Mediana de N muestras (bueno contra picos)  
- Calibración: `y = a*x + b` (lineal) o tabla de puntos

**Ejemplo: filtro por mediana de 9 lecturas**
```cpp
int mediana9(int pin) {
  int v[9];
  for (int i=0;i<9;i++) {
    v[i] = analogRead(pin);
    delay(5);
  }
  // ordenamiento simple
  for (int i=0;i<9;i++) {
    for (int j=i+1;j<9;j++) {
      if (v[j] < v[i]) { int tmp=v[i]; v[i]=v[j]; v[j]=tmp; }
    }
  }
  return v[4]; // mediana
}
```

**Calibración lineal (ej. convertir ADC→voltaje→pH):**
```cpp
float adcToVolt(int adc) {
  // Para ADC de 12 bits: 0..4095
  // OJO: el ESP32 no es perfectamente lineal; para precisión alta usa calibración ADC.
  return (adc / 4095.0f) * 3.3f;
}

float aplicarCal(float x, float a, float b) {
  return a * x + b;
}
```

### Retos
1. Implementa promedio móvil de 20 muestras sin usar arrays gigantes (circular buffer).  
2. Crea un modo de calibración por Serial: ingresa (ADC, pH real) y calcula `a` y `b`.  
3. Detecta “sensor desconectado” (ADC casi 0 o saturado) por más de 10 s.

---

## 8) Control de dosificación (pH) con anti-overshoot

**Advertencia:** Dosificar pH es delicado. Haz pruebas con agua, en pequeño, y usa límites de seguridad.

Estrategia simple:
- Si pH > setpoint + histéresis → dosifica pH- en pulsos cortos  
- Espera mezcla (ej. 60–120 s) antes de medir y dosificar otra vez  
- Límite diario de dosificación (ml) para evitar desastre

**Pseudocódigo**
- Estado DOSIFICANDO  
- Timer de “pulso” (ej. 2 s ON)  
- Timer de “mezcla” (ej. 90 s)  
- Máximo pulsos por hora / día

### Retos
1. Implementa histéresis (ej. setpoint=6.0, banda=±0.1).  
2. Limita dosificación a 30 s acumulados por día.  
3. Si pH cambia en dirección contraria, marca falla “sensor invertido / error químico”.

---

## 9) Registro de datos (CSV) y telemetría

Opciones comunes:
- **Serial** (rápido para debug)  
- **SD** (CSV)  
- **WiFi + MQTT** (Home Assistant / Node-RED)  
- **HTTP** a un endpoint o Google Sheets (más frágil)

**Formato recomendado de log (una línea):**
`epoch, tempC, pH, EC, nivel, bomba, estado, errorCode`

### Retos
1. Construye una línea CSV cada 10 s con `millis()` y luego con DS3231.  
2. Si falla SD, entra a “degradado” pero sigue controlando.  
3. Agrega un contador de “paquetes perdidos” si no hay WiFi.

---

## 10) Checklist de confiabilidad (lo que suele fallar en hidroponía)

- Ruido eléctrico por bombas → lecturas ADC inestables  
  - Solución: filtros RC, tierra adecuada, desacoplos, cable apantallado, promedios/medianas  
- Bloqueos por `delay()`/loops largos → sin control real  
  - Solución: `millis()`, máquina de estados, WDT  
- Sensor desconectado o mojado → lecturas absurdas  
  - Solución: validación y “último valor bueno” con timeout  
- Bomba sin agua → quemada  
  - Solución: nivel mínimo + caudal + fail-safe  
- Interferencias I2C (RTC)  
  - Solución: pull-ups correctas (a veces ya están en el módulo), cables cortos, 100 kHz

---

## Apéndice A — Sugerencias de librerías (Arduino IDE)
- `RTClib` (DS3231)  
- `OneWire` + `DallasTemperature` (DS18B20)  
- `Preferences` (NVS en ESP32)  
- `WiFi`, `PubSubClient` (MQTT)

---

## Apéndice B — Preguntas guía para depuración
- ¿Qué pasa si el sensor da NaN o se desconecta?  
- ¿Qué estado queda activo si se va la luz y regresa?  
- ¿Se reinicia demasiado por WDT? ¿Qué lo bloquea?  
- ¿Cómo sabes que la bomba realmente está moviendo agua?  
- ¿Tienes límites para dosificación química?

---
