import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# ---------- Parámetros de simulación ----------
T_total = 10.0       # tiempo total [s]
dt = 0.001           # paso de integración [s]
t = np.arange(0, T_total, dt)

# Dinámica de la pelota en cada eje:
# x'' = k_plate * u - b * x'
m = 1.0        # "masa" (no aparece explícitamente si la absorbemos en k_plate)
b = 0.1        # fricción (más chico => más oscilación)
k_plate = 5.0  # qué tanto acelera la pelota por grado de inclinación

# ---------- PID 2D sobre el error (Ex, Ey) ----------
def simulate_pid_2d(Kp, Ki, Kd, Ex0, Ey0):
    n = len(t)

    # Estados: posición (error) y velocidad en X e Y
    x = np.zeros(n)
    y = np.zeros(n)
    vx = np.zeros(n)
    vy = np.zeros(n)

    # Señales de control (inclinación) en X e Y
    ux = np.zeros(n)
    uy = np.zeros(n)

    # condiciones iniciales de error (posición de la pelota)
    x[0] = Ex0
    y[0] = Ey0
    # velocidad inicial = 0 -> si K=0 no se debe mover

    # términos del PID
    int_x = 0.0
    int_y = 0.0
    prev_err_x = x[0]
    prev_err_y = y[0]

    for i in range(1, n):
        # Setpoint = 0, error es simplemente la posición
        err_x = x[i-1]
        err_y = y[i-1]

        # Integrales
        int_x += err_x * dt
        int_y += err_y * dt

        # Derivadas (aproximadas)
        der_x = (err_x - prev_err_x) / dt
        der_y = (err_y - prev_err_y) / dt

        # PID en cada eje.
        # OJO: signo menos para empujar el error hacia 0, no al revés.
        u_pid_x = -(Kp * err_x + Ki * int_x + Kd * der_x)
        u_pid_y = -(Kp * err_y + Ki * int_y + Kd * der_y)

        ux[i] = u_pid_x
        uy[i] = u_pid_y

        # Dinámica: x'' = k_plate * u - b * x'
        acc_x = k_plate * ux[i] - b * vx[i-1]
        acc_y = k_plate * uy[i] - b * vy[i-1]

        # Integración: aceleración -> velocidad -> posición
        vx[i] = vx[i-1] + dt * acc_x
        vy[i] = vy[i-1] + dt * acc_y

        x[i] = x[i-1] + dt * vx[i]
        y[i] = y[i-1] + dt * vy[i]

        prev_err_x = err_x
        prev_err_y = err_y

    return x, y, ux, uy

# ---------- Valores iniciales ----------
Ex0 = 300.0   # error inicial en X (px)
Ey0 = 200.0   # error inicial en Y (px)
Kp0 = 0.5
Ki0 = 0.0
Kd0 = 0.0

x0, y0, ux0, uy0 = simulate_pid_2d(Kp0, Ki0, Kd0, Ex0, Ey0)

# ---------- Gráfica ----------
plt.style.use("default")
fig, ax = plt.subplots(figsize=(8, 5))
plt.subplots_adjust(left=0.1, bottom=0.38)  # espacio para 5 sliders

(line_ex,) = ax.plot(t, x0, label="Error X (px)")
(line_ey,) = ax.plot(t, y0, label="Error Y (px)")

# línea en 0 para referencia
ax.axhline(0, color="k", linestyle=":", linewidth=1)

ax.set_xlabel("Tiempo [s]")
ax.set_ylabel("Error [px]")
ax.set_title("PID 2D sobre error de posición (pelota en plataforma)")
ax.grid(True)
ax.legend(loc="best")

# ---------- Sliders ----------
axcolor = "lightgoldenrodyellow"

ax_Ex = plt.axes([0.1, 0.30, 0.8, 0.03], facecolor=axcolor)
ax_Ey = plt.axes([0.1, 0.25, 0.8, 0.03], facecolor=axcolor)
ax_Kp = plt.axes([0.1, 0.20, 0.8, 0.03], facecolor=axcolor)
ax_Ki = plt.axes([0.1, 0.15, 0.8, 0.03], facecolor=axcolor)
ax_Kd = plt.axes([0.1, 0.10, 0.8, 0.03], facecolor=axcolor)

sEx = Slider(ax_Ex, "Ex inicial", -640.0, 640.0, valinit=Ex0)
sEy = Slider(ax_Ey, "Ey inicial", -480.0, 480.0, valinit=Ey0)
sKp = Slider(ax_Kp, "Kp", 0.0, 5.0, valinit=Kp0)
sKi = Slider(ax_Ki, "Ki", 0.0, 2.0, valinit=Ki0)
sKd = Slider(ax_Kd, "Kd", 0.0, 2.0, valinit=Kd0)

# ---------- Función de actualización ----------
def update(val):
    Ex_init = sEx.val
    Ey_init = sEy.val
    Kp = sKp.val
    Ki = sKi.val
    Kd = sKd.val

    ex, ey, ux, uy = simulate_pid_2d(Kp, Ki, Kd, Ex_init, Ey_init)

    line_ex.set_ydata(ex)
    line_ey.set_ydata(ey)

    ax.relim()
    ax.autoscale_view()

    fig.canvas.draw_idle()

# Conectar sliders a la función update
sEx.on_changed(update)
sEy.on_changed(update)
sKp.on_changed(update)
sKi.on_changed(update)
sKd.on_changed(update)

plt.show()
