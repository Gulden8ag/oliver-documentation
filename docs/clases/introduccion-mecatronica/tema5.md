# Introducción práctica al control y al PID

En mecatrónica **controlar** significa *hacer que algo se comporte como tú quieres*, aunque haya cambios y disturbios.

Ejemplos muy cotidianos:

- El **cruise control** de un coche que mantiene la velocidad.
- Un **climatizador** que mantiene la temperatura de un cuarto.
- Un **robot seguidor de línea** que se mantiene sobre la línea.

En todos los casos hay:

- Un **valor deseado** (referencia o *setpoint*).
- Un **sensor** que mide lo que está pasando.
- Un **controlador** (el “cerebro”, por ejemplo Arduino).
- Un **actuador** (motor, resistencia, ventilador, servo, etc.).

La idea básica es:

> Controlador = una receta para decidir cuánto actuar en función del error.
> 
> 
> Error = (lo que quiero) – (lo que tengo).
> 

---

## El controlador PID: P, I y D

El controlador PID es una de las recetas más usadas en la industria.

Las siglas vienen de:

- **P** → Proporcional
- **I** → Integral
- **D** → Derivativa

La fórmula es:

\[
u(t) = K_p \cdot e(t) \;+\; K_i \int e(t)\, dt \;+\; K_d \cdot \frac{de(t)}{dt}
\]

- \( u(t) \): salida del controlador (lo que manda al actuador, ej. PWM).
- \( e(t) \): error = referencia – salida medida.
- \( K_p, K_i, K_d \): ganancias que ajustamos.

---

## Componente P – Proporcional

**¿Qué hace?**

Responde proporcionalmente al error.

- Si el error es grande → acción grande.
- Si el error es pequeño → acción pequeña.
- Si el error es cero → acción cero.

**Uso:**

- **Subir \(K_p\)** → el sistema reacciona más **rápido** y **agresivo**.
- Pero si exageras \(K_p\) → puede haber **oscilaciones** o **inestabilidad**.

Ejemplo:

Quieres que un motor gire a 1000 rpm. Si estás en 500 rpm (error = 500), el controlador manda un PWM grande. Si estás en 950 rpm (error = 50), manda un PWM más pequeño.

**Ventajas del P:**

- Fácil de entender.
- Respuesta rápida.

**Desventajas del P:**

- Muchas veces deja un **error permanente** (nunca llega exactamente a la referencia, sólo se acerca).

---

## Componente I – Integral

**¿Qué hace?**

Suma el error a lo largo del tiempo.

- Si durante mucho tiempo estás por debajo de la referencia, la parte I **acumula** ese error.
- Esa “acumulación” aumenta la salida y **empuja** al sistema hasta que el error promedio tiende a cero.

**Uso:**

- **Agrega memoria**: recuerda errores pasados.
- **Elimina error en estado estacionario**: si con P solo no llegas a la referencia, I te ayuda a llegar.
- Si \(K_i\) es muy grande:
    - El sistema puede volverse **lento** en corregir.
    - Puede provocar **sobreimpulso (overshoot)**: se pasa mucho de la referencia.
    - El integrador se puede “saturar” (crecer demasiado), esto se llama **windup**.

---

## Componente D – Derivativa

**¿Qué hace?**

Mira **qué tan rápido cambia el error**.

- Si el error está creciendo muy rápido → la parte D actúa como **freno**.
- Si ya te estás acercando a la referencia, la D ayuda a no pasarte.

**Uso:**

- La parte D es como un **reflejo**: ve hacia dónde vas y trata de anticipar.
- Ayuda a **reducir el overshoot** y a **suavizar** la respuesta.

**Desventajas del D:**
- Es **muy sensible al ruido** del sensor (pequeñas variaciones se amplifican).

---

## Resumen rápido: cómo se sienten P, I y D

| Componente | Aporta… | Si lo pongo muy alto… |
| --- | --- | --- |
| **P** | Rapidez, reacción directa al error | Oscilaciones, posible inestabilidad |
| **I** | Elimina error permanente | Muy lento, mucho overshoot, integrador saturado |
| **D** | Suaviza, “frena” el movimiento | Muy sensible al ruido, respuesta nerviosa |

---


<iframe
  src="../../../clases/introduccion-mecatronica/pid_sim.html"
  width="100%"
  height="650"
  style="border:none;"
>
</iframe>

## ¿Cómo se usa un PID en Arduino?

La idea general en un Arduino es:

1. **Leer el sensor**
    - Ej: `analogRead()` para un potenciómetro o sensor de temperatura.
    - Ej: medir velocidad de un motor con un encoder.
2. **Calcular el error**
    
    ```c
    error = setpoint - medida;
    
    ```
    
3. **Calcular cada término (P, I, D)**
    - P: `P = Kp * error;`
    - I: sumando error a lo largo del tiempo.
    - D: viendo cómo cambió el error respecto al ciclo anterior.
4. **Combinar todo** para obtener la salida `u`.
5. **Mandar la salida al actuador**
    - Ej: `analogWrite(pinPWM, salida);`
6. **Repetir** el ciclo en `loop()`.

## Ejemplo de código PID sencillo en Arduino

Queremos controlar, por ejemplo, la **velocidad** de un motor con PWM. Supongamos que tenemos:

- Un sensor que mide algo entre 0 y 1023 (`analogRead`).
- Un pin PWM para el motor, por ejemplo el 9.

```cpp
// Ganancias PID (se ajustan a prueba y error)
float Kp = 1.0;
float Ki = 0.5;
float Kd = 0.1;

// Variables del PID
float setpoint = 500;   // valor deseado (ej. 500 de 0-1023)
float medida = 0;       // lectura del sensor
float error = 0;
float error_anterior = 0;
float integral = 0;
float derivada = 0;

int salidaPWM = 0;

// Tiempo
unsigned long tiempo_anterior = 0;

const int pinSensor = A0;
const int pinPWM = 9;

void setup() {
  pinMode(pinPWM, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  // 1) Calcular dt (en segundos)
  unsigned long tiempo_actual = millis();
  float dt = (tiempo_actual - tiempo_anterior) / 1000.0; // ms -> s
  if (dt <= 0) dt = 0.001; // evitar dividir entre 0

  // 2) Leer sensor
  medida = analogRead(pinSensor);

  // 3) Calcular error
  error = setpoint - medida;

  // 4) Calcular términos PID
  // P
  float P = Kp * error;

  // I (integración numérica sencilla)
  integral = integral + error * dt;
  // Anti-windup básico
  if (integral > 1000) integral = 1000;
  if (integral < -1000) integral = -1000;
  float I = Ki * integral;

  // D (derivada)
  derivada = (error - error_anterior) / dt;
  float D = Kd * derivada;

  // 5) Salida total
  float u = P + I + D;

  // 6) Limitar salida a rango de PWM (0-255)
  if (u > 255) {
    u = 255;
  } else if (u < 0) {
    u = 0;
  }

  salidaPWM = (int)u;
  analogWrite(pinPWM, salidaPWM);

  // 7) Guardar para el siguiente ciclo
  error_anterior = error;
  tiempo_anterior = tiempo_actual;

  // 8) (Opcional) Imprimir para ver qué pasa
  Serial.print("Medida: ");
  Serial.print(medida);
  Serial.print("  Error: ");
  Serial.print(error);
  Serial.print("  PWM: ");
  Serial.println(salidaPWM);

  // Pequeño delay para no saturar el puerto serie
  delay(10);
}

```

## PID en tiempo discreto (cómo piensa realmente Arduino)

Aunque escribimos el PID con integrales y derivadas continuas, en Arduino todo es **por pasos** (muestreo):

- El `loop()` se ejecuta muchas veces por segundo.
- Cada vuelta:
    - Lees el sensor.
    - Calculas el error.
    - Actualizas P, I y D.
    - Mandas un nuevo PWM.

Versión mental del PID discreto:

- **Integral** → “integral = integral + error * dt;”
- **Derivada** → “derivada = (error - error_anterior) / dt;”

Mientras el tiempo entre iteraciones sea más o menos constante, el PID se comporta bien.

## Consejos prácticos para usar PID con Arduino

1. **Empieza simple (solo P)**
    - Comienza con KpK_pKp pequeño.
    - Ve subiendo hasta que el sistema responda rápido, pero sin volverse loco.
2. **Agrega I sólo si hace falta**
    - Si con P solo se queda “corto” (hay error fijo), agrega un KiK_iKi pequeño.
    - Revisa que no aparezcan oscilaciones lentas.
3. **Usa D con cuidado**
    - Úsalo si hay mucho overshoot o “rebote”.
    - Si tu sensor tiene mucho ruido, quizá sea mejor un PI que un PID.
4. **Filtrado de señal**
    - A veces vale la pena **promediar** varias lecturas del sensor:
    
    ```cpp
    int leerSensorFiltrado() {
      long suma = 0;
      const int N = 10;
      for (int i = 0; i < N; i++) {
        suma += analogRead(pinSensor);
        delay(2);
      }
      return (int)(suma / N);
    }
    ```
    
5. **Escala bien tus unidades**
- Si tu sensor da 0–1023, pero quieres trabajar en grados, rpm, etc., escala primero, por ejemplo:

```cpp
float volt = medida * (5.0 / 1023.0);
// o convertir rpm, °C, cm, etc.
```