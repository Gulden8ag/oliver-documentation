import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# ---------- Simulation parameters ----------
T_total = 10.0      # total simulation time [s]
dt = 0.01           # time step [s]
t = np.arange(0, T_total, dt)

tau = 1.0           # time constant of the first-order plant

# ---------- PID + plant simulation ----------
def simulate_pid(Kp, Ki, Kd, setpoint, noise_level):
    n = len(t)
    y = np.zeros(n)          # real process output
    y_meas = np.zeros(n)     # measured (noisy) output
    u = np.zeros(n)          # control signal

    integral = 0.0
    prev_error = 0.0

    for i in range(1, n):
        # Sensor measurement (add noise to the true output)
        noise = noise_level * np.random.randn()
        y_meas[i-1] = y[i-1] + noise

        error = setpoint - y_meas[i-1]

        integral += error * dt
        derivative = (error - prev_error) / dt

        u[i] = Kp * error + Ki * integral + Kd * derivative

        # First-order plant: dy/dt = (-y + u) / tau
        y[i] = y[i-1] + dt * ((-y[i-1] + u[i]) / tau)

        prev_error = error

    # last measured point
    y_meas[-1] = y[-1] + noise_level * np.random.randn()

    return y, y_meas, u

# ---------- Initial parameters ----------
Kp0 = 2.0
Ki0 = 0.5
Kd0 = 0.0
setpoint0 = 1.0
noise0 = 0.0

y0, y_meas0, u0 = simulate_pid(Kp0, Ki0, Kd0, setpoint0, noise0)

# ---------- Plot setup ----------
plt.style.use("default")
fig, ax = plt.subplots(figsize=(8, 5))
plt.subplots_adjust(left=0.1, bottom=0.35)  # leave space for sliders

# Process output
(line_y,) = ax.plot(t, y0, label="Process output (y)")
# Measured output (sensor)
(line_y_meas,) = ax.plot(t, y_meas0, linestyle="--", alpha=0.7,
                         label="Measured output (sensor)")
# Setpoint (horizontal line)
(line_sp,) = ax.plot(t, setpoint0 * np.ones_like(t), ":", label="Setpoint")

ax.set_xlabel("Time [s]")
ax.set_ylabel("Value")
ax.set_title("PID Control with Sliders (First-order Plant)")
ax.grid(True)
ax.legend(loc="best")

# ---------- Sliders ----------
axcolor = 'lightgoldenrodyellow'

ax_Kp = plt.axes([0.1, 0.25, 0.8, 0.03], facecolor=axcolor)
ax_Ki = plt.axes([0.1, 0.20, 0.8, 0.03], facecolor=axcolor)
ax_Kd = plt.axes([0.1, 0.15, 0.8, 0.03], facecolor=axcolor)
ax_sp = plt.axes([0.1, 0.10, 0.8, 0.03], facecolor=axcolor)
ax_noise = plt.axes([0.1, 0.05, 0.8, 0.03], facecolor=axcolor)

sKp = Slider(ax_Kp, "Kp", 0.0, 10.0, valinit=Kp0)
sKi = Slider(ax_Ki, "Ki", 0.0, 5.0, valinit=Ki0)
sKd = Slider(ax_Kd, "Kd", 0.0, 2.0, valinit=Kd0)
sSP = Slider(ax_sp, "Setpoint", -2.0, 2.0, valinit=setpoint0)
sNoise = Slider(ax_noise, "Sensor noise", 0.0, 0.5, valinit=noise0)

# ---------- Update function ----------
def update(val):
    Kp = sKp.val
    Ki = sKi.val
    Kd = sKd.val
    sp = sSP.val
    noise = sNoise.val

    y, y_meas, u = simulate_pid(Kp, Ki, Kd, sp, noise)

    line_y.set_ydata(y)
    line_y_meas.set_ydata(y_meas)
    line_sp.set_ydata(sp * np.ones_like(t))

    ax.relim()
    ax.autoscale_view()

    fig.canvas.draw_idle()

# Call update when any slider is changed
sKp.on_changed(update)
sKi.on_changed(update)
sKd.on_changed(update)
sSP.on_changed(update)
sNoise.on_changed(update)

plt.show()
