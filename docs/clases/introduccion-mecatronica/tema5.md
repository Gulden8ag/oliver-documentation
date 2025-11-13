# Control PID 101

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

<!-- PID 1D demo: segundo orden con Kp, Ki, Kd -->
<div id="pid1d-controls" style="margin-bottom: 1rem;">
  <p><strong>Setpoint fijo: 1.0</strong></p>
  <div>
    <label>Kp: <span id="label1d-Kp">5.0</span></label><br>
    <input id="slider1d-Kp" type="range" min="0" max="50" step="0.5" value="5">
  </div>
  <div>
    <label>Ki: <span id="label1d-Ki">0.0</span></label><br>
    <input id="slider1d-Ki" type="range" min="0" max="10" step="0.1" value="0">
  </div>
  <div>
    <label>Kd: <span id="label1d-Kd">0.0</span></label><br>
    <input id="slider1d-Kd" type="range" min="0" max="5" step="0.1" value="0">
  </div>
</div>

<div id="pid1d-plot" style="width: 100%; height: 400px;"></div>

<!-- Plotly desde CDN -->
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

<script>
  // ----- Parámetros de simulación (versión JS del código en Python) -----
  const T1D_total = 20.0;       // tiempo total [s]
  const dt1D = 0.01;            // paso de simulación [s] (más grande que 0.001 para navegador)
  const n1D = Math.floor(T1D_total / dt1D);
  const t1D = Array.from({ length: n1D }, (_, i) => i * dt1D);

  // Parámetros de la planta de 2º orden: m y'' + b y' + k y = u
  const m1D = 1.0;
  const b1D = 0.4;
  const k1D = 1.0;
  const SETPOINT_1D = 1.0;

  function simulatePID1D(Kp, Ki, Kd) {
    const y = new Array(n1D).fill(0);  // salida
    const v = new Array(n1D).fill(0);  // velocidad
    const u = new Array(n1D).fill(0);  // señal de control

    let integral = 0.0;
    let prev_error = 0.0;

    for (let i = 1; i < n1D; i++) {
      const error = SETPOINT_1D - y[i - 1];

      integral += error * dt1D;
      const derivative = (error - prev_error) / dt1D;

      u[i] = Kp * error + Ki * integral + Kd * derivative;

      // dinámica: y'' = (-b y' - k y + u) / m
      const acc = (-b1D * v[i - 1] - k1D * y[i - 1] + u[i]) / m1D;

      v[i] = v[i - 1] + dt1D * acc;
      y[i] = y[i - 1] + dt1D * v[i];

      prev_error = error;
    }

    return { y, u };
  }

  // ----- Sliders y labels -----
  const s1dKp = document.getElementById('slider1d-Kp');
  const s1dKi = document.getElementById('slider1d-Ki');
  const s1dKd = document.getElementById('slider1d-Kd');

  const lbl1dKp = document.getElementById('label1d-Kp');
  const lbl1dKi = document.getElementById('label1d-Ki');
  const lbl1dKd = document.getElementById('label1d-Kd');

  function get1DParams() {
    return {
      Kp: parseFloat(s1dKp.value),
      Ki: parseFloat(s1dKi.value),
      Kd: parseFloat(s1dKd.value),
    };
  }

  function update1DLabels() {
    const { Kp, Ki, Kd } = get1DParams();
    lbl1dKp.textContent = Kp.toFixed(2);
    lbl1dKi.textContent = Ki.toFixed(2);
    lbl1dKd.textContent = Kd.toFixed(2);
  }

  // ----- Inicializar gráfica -----
  function init1DPlot() {
    update1DLabels();
    const { Kp, Ki, Kd } = get1DParams();
    const sim = simulatePID1D(Kp, Ki, Kd);

    const traceY = {
      x: t1D,
      y: sim.y,
      mode: 'lines',
      name: 'Process output y(t)',
    };

    const traceSP = {
      x: t1D,
      y: t1D.map(() => SETPOINT_1D),
      mode: 'lines',
      name: 'Setpoint',
      line: { dash: 'dot' }
    };

    const layout = {
      title: 'PID Control (Second-order Plant)',
      xaxis: { title: 'Time [s]' },
      yaxis: { title: 'Value' },
      legend: { orientation: 'h' },
    };

    Plotly.newPlot('pid1d-plot', [traceY, traceSP], layout, { responsive: true });
  }

  function update1DPlot() {
    update1DLabels();
    const { Kp, Ki, Kd } = get1DParams();
    const sim = simulatePID1D(Kp, Ki, Kd);

    Plotly.react('pid1d-plot', [
      {
        x: t1D,
        y: sim.y,
        mode: 'lines',
        name: 'Process output y(t)',
      },
      {
        x: t1D,
        y: t1D.map(() => SETPOINT_1D),
        mode: 'lines',
        name: 'Setpoint',
        line: { dash: 'dot' }
      }
    ], {
      title: 'PID Control (Second-order Plant)',
      xaxis: { title: 'Time [s]' },
      yaxis: { title: 'Value' },
      legend: { orientation: 'h' },
    });
  }

  // ----- Eventos -----
  document.addEventListener('DOMContentLoaded', function () {
    init1DPlot();

    s1dKp.addEventListener('input', update1DPlot);
    s1dKi.addEventListener('input', update1DPlot);
    s1dKd.addEventListener('input', update1DPlot);
  });
</script>





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
    - P: Proporcional al error
    ```cpp
    P = Kp * error;
    ``` 
    - I: Error acumulado en el tiempo
        ```cpp 
        derivada = (error - error_anterior) / dt;
        float D = Kd * derivada;
        ```
    - D: razón de cambio del error
    ```cpp
    derivada = (error - error_anterior) / dt;
    float D = Kd * derivada;
    ```
4. **Combinar todo** para obtener la salida `u`.
    - `u = P + Ki * I + D;`
5. **Mandar la salida al actuador**
    - Ej: `analogWrite(pinPWM, salida);`
    - Ej: controlar un servo, motor, etc.
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
double error = 0;
double error_anterior = 0;
double integral = 0;
double derivada = 0;

int salidaPWM = 0;

// Tiempo
unsigned long tiempo_anterior = 0, tiempo_actual = 0;
double dt = 0;
const int pinSensor = A0;
const int pinPWM = 9;

void setup() {
  pinMode(pinPWM, OUTPUT);
  medida = analogRead(PIN_INPUT);
  Serial.begin(9600);
}

void loop() {
  // 1) Leer sensor 
  medida = analogRead(pinSensor);

  // 2) Calcular dt (en segundos)
  tiempo_actual = millis();
  dt = double(tiempo_actual - tiempo_anterior); // ms -> s
  if (dt <= 0) dt = 0.001; // evitar dividir entre 0

  // 3) Calcular error
  error = setpoint - medida;

  // 4) Calcular términos PID
  // P
  float P = Kp * error;
  // I (integración numérica sencilla)
  integral = integral + error * dt;
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

  // Pequeño delay para no saturar el puerto serie(Quitarlo para mejor reaccion)
  delay(10);
}

```
<!-- PID 2D demo: pelota en plataforma -->
<div id="pid-controls" style="margin-bottom: 1rem;">
  <div>
    <label>Ex inicial: <span id="label-Ex">300</span></label><br>
    <input id="slider-Ex" type="range" min="-640" max="640" step="10" value="300">
  </div>
  <div>
    <label>Ey inicial: <span id="label-Ey">200</span></label><br>
    <input id="slider-Ey" type="range" min="-480" max="480" step="10" value="200">
  </div>
  <div>
    <label>Kp: <span id="label-Kp">0.5</span></label><br>
    <input id="slider-Kp" type="range" min="0" max="5" step="0.1" value="0.5">
  </div>
  <div>
    <label>Ki: <span id="label-Ki">0.0</span></label><br>
    <input id="slider-Ki" type="range" min="0" max="2" step="0.05" value="0">
  </div>
  <div>
    <label>Kd: <span id="label-Kd">0.0</span></label><br>
    <input id="slider-Kd" type="range" min="0" max="2" step="0.05" value="0">
  </div>
</div>

<div id="pid-plot" style="width: 100%; height: 400px;"></div>

<!-- Plotly desde CDN -->
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

<script>
  // ----- Parámetros de simulación -----
  const T_total = 10.0;
  const dt = 0.01;
  const n = Math.floor(T_total / dt);
  const t = Array.from({ length: n }, (_, i) => i * dt);

  // Dinámica pelota: x'' = k_plate * u - b * x'
  const b = 0.1;
  const k_plate = 5.0;

  function simulatePID2D(Kp, Ki, Kd, Ex0, Ey0) {
    const x = new Array(n).fill(0);
    const y = new Array(n).fill(0);
    const vx = new Array(n).fill(0);
    const vy = new Array(n).fill(0);

    // condiciones iniciales
    x[0] = Ex0;
    y[0] = Ey0;

    let int_x = 0.0;
    let int_y = 0.0;
    let prev_err_x = x[0];
    let prev_err_y = y[0];

    for (let i = 1; i < n; i++) {
      const err_x = x[i - 1];
      const err_y = y[i - 1];

      // integral
      int_x += err_x * dt;
      int_y += err_y * dt;

      // derivada
      const der_x = (err_x - prev_err_x) / dt;
      const der_y = (err_y - prev_err_y) / dt;

      // PID (con signo negativo para reducir el error)
      const u_pid_x = -(Kp * err_x + Ki * int_x + Kd * der_x);
      const u_pid_y = -(Kp * err_y + Ki * int_y + Kd * der_y);

      // dinámica
      const acc_x = k_plate * u_pid_x - b * vx[i - 1];
      const acc_y = k_plate * u_pid_y - b * vy[i - 1];

      vx[i] = vx[i - 1] + dt * acc_x;
      vy[i] = vy[i - 1] + dt * acc_y;

      x[i] = x[i - 1] + dt * vx[i];
      y[i] = y[i - 1] + dt * vy[i];

      prev_err_x = err_x;
      prev_err_y = err_y;
    }

    return { x, y };
  }

  // ----- Inicializar controles -----
  const sEx = document.getElementById('slider-Ex');
  const sEy = document.getElementById('slider-Ey');
  const sKp = document.getElementById('slider-Kp');
  const sKi = document.getElementById('slider-Ki');
  const sKd = document.getElementById('slider-Kd');

  const lblEx = document.getElementById('label-Ex');
  const lblEy = document.getElementById('label-Ey');
  const lblKp = document.getElementById('label-Kp');
  const lblKi = document.getElementById('label-Ki');
  const lblKd = document.getElementById('label-Kd');

  function getParams() {
    return {
      Ex: parseFloat(sEx.value),
      Ey: parseFloat(sEy.value),
      Kp: parseFloat(sKp.value),
      Ki: parseFloat(sKi.value),
      Kd: parseFloat(sKd.value),
    };
  }

  function updateLabels() {
    const { Ex, Ey, Kp, Ki, Kd } = getParams();
    lblEx.textContent = Ex.toFixed(0);
    lblEy.textContent = Ey.toFixed(0);
    lblKp.textContent = Kp.toFixed(2);
    lblKi.textContent = Ki.toFixed(2);
    lblKd.textContent = Kd.toFixed(2);
  }

  // ----- Inicializar gráfica -----
  function initPlot() {
    updateLabels();
    const { Ex, Ey, Kp, Ki, Kd } = getParams();
    const sim = simulatePID2D(Kp, Ki, Kd, Ex, Ey);

    const traceX = {
      x: t,
      y: sim.x,
      mode: 'lines',
      name: 'Error X (px)',
    };

    const traceY = {
      x: t,
      y: sim.y,
      mode: 'lines',
      name: 'Error Y (px)',
    };

    const layout = {
      title: 'PID 2D sobre error de posición (pelota en plataforma)',
      xaxis: { title: 'Tiempo [s]' },
      yaxis: { title: 'Error [px]' },
      legend: { orientation: 'h' },
    };

    Plotly.newPlot('pid-plot', [traceX, traceY], layout, { responsive: true });
  }

  function updatePlot() {
    updateLabels();
    const { Ex, Ey, Kp, Ki, Kd } = getParams();
    const sim = simulatePID2D(Kp, Ki, Kd, Ex, Ey);

    const update = {
      y: [sim.x, sim.y],
    };

    Plotly.react('pid-plot', [
      { x: t, y: sim.x, mode: 'lines', name: 'Error X (px)' },
      { x: t, y: sim.y, mode: 'lines', name: 'Error Y (px)' },
    ], {
      title: 'PID 2D sobre error de posición (pelota en plataforma)',
      xaxis: { title: 'Tiempo [s]' },
      yaxis: { title: 'Error [px]' },
      legend: { orientation: 'h' },
    });
  }

  // Inicializar al cargar
  document.addEventListener('DOMContentLoaded', function () {
    initPlot();

    sEx.addEventListener('input', updatePlot);
    sEy.addEventListener('input', updatePlot);
    sKp.addEventListener('input', updatePlot);
    sKi.addEventListener('input', updatePlot);
    sKd.addEventListener('input', updatePlot);
  });
</script>
