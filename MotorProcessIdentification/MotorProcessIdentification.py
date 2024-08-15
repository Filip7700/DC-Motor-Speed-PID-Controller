import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from scipy.optimize import minimize
from scipy.interpolate import interp1d
import warnings

# Number of how many times algorithm will perform optimisation.
# This should be enough to get satisfying process model accuracy,
# without overfitting model too much.
EPOCHS_COUNT = 3

# GLOBAL VARIABLES
t = []
u = []
yp = []
u0 = 0.0
y0 = 0.0
xp0 = 0.0

# specify number of steps
ns = 0
delta_t = 0.0

# create linear interpolation of the u data versus time
uf = []

def sopdt(x, t, uf, Kp, taus, zeta, thetap):
    # Kp = process gain
    # taus = second order time constant
    # zeta = damping factor
    # thetap = model time delay
    # ts^2 dy2/dt2 + 2 zeta taus dydt + y = Kp u(t-thetap)
    # time-shift u
    try:
        if (t - thetap) <= 0:
            um = uf(0.0)
        else:
            um = uf(t - thetap)
    except:
        # catch any error
        um = u0
    # two states (y and y')
    y = x[0] - y0
    dydt = x[1]
    dy2dt2 = (-2.0 * zeta * taus * dydt - y + Kp * (um - u0)) / taus ** 2

    return [dydt, dy2dt2]

# simulate model with x=[Km,taum,thetam]
def sim_model(x):
    # input arguments
    Kp = x[0]
    taus = x[1]
    zeta = x[2]
    thetap = x[3]

    # storage for model values
    xm = np.zeros((ns,2)) # model

    # initial condition
    xm[0] = xp0

    # loop through time steps
    for i in range(0, ns - 1):
        ts = [t[i], t[i + 1]]
        inputs = (uf, Kp, taus, zeta, thetap)

        # turn off warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # integrate SOPDT model
            x = odeint(sopdt, xm[i], ts, args=inputs)
        xm[i + 1] = x[-1]

    y = xm[:,0]

    return y

# define objective
def objective(x):
    # simulate model
    ym = sim_model(x)

    # calculate objective
    obj = 0.0
    for i in range(len(ym)):
        obj = obj + (ym[i] - yp[i]) ** 2

    return obj

def read_motor_results_from_csv(motor_results_csv_file_name):
    motor_results = []

    motor_results_csv_file = open(motor_results_csv_file_name, "rt")

    csv_lines = motor_results_csv_file.readlines()
    csv_lines_count = len(csv_lines)

    motor_results = [[0.0 for j in range(csv_lines_count)] for j in range(3)]

    for i in range(csv_lines_count):
        csv_line = csv_lines[i]
        motor_result_str = csv_line.split(",")
        motor_result_time_millisecond = float(motor_result_str[0])
        motor_result_voltage = float(motor_result_str[1])
        motor_result_angular_displacement = float(motor_result_str[2])

        motor_results[0][i] = motor_result_time_millisecond
        motor_results[1][i] = motor_result_voltage
        motor_results[2][i] = motor_result_angular_displacement

    motor_results_csv_file.close()

    return motor_results

def main(argv):
    global EPOCHS_COUNT

    global t
    global u
    global yp
    global u0
    global y0
    global yp
    global ns
    global delta_t
    global uf

    try:
        motor_process_data = read_motor_results_from_csv(
            "../MotorResponsePreprocess/MotorProcessData.csv")

        motor_time_second = motor_process_data[0]
        motor_input_voltage_signal = motor_process_data[1]
        motor_response_angular_speed_rads_per_second = motor_process_data[2]

        t = motor_time_second
        u = motor_input_voltage_signal
        yp = motor_response_angular_speed_rads_per_second
        y0 = yp[0]
        xp0 = yp[0]

        # specify number of steps
        ns = len(t)
        delta_t = t[1] - t[0]

        # create linear interpolation of the u data versus time
        uf = interp1d(t, u)

        motor_model_parameters = [0.0 for i in range(4)]

        # Give model initial parameters

        # K (process gain)
        motor_model_parameters[0] = 1.0

        # Ts (second oreder time constant /
        # natural period /
        # inverse of natural process frequency)
        motor_model_parameters[1] = 0.1

        # Zeta (damping factor)
        motor_model_parameters[2] = 1.0

        # thetap (process delay, not used, initialized to 0)
        motor_model_parameters[3] = 0.0

        # Optimized motor model parameters
        p = [0.0 for i in range(4)]

        for i in range(EPOCHS_COUNT):
            print("Epoch: %d" % (i + 1))

            # Show transfer function
            print('SSE Objective: ' + str(objective(motor_model_parameters)))

            # optimize Kp, taus, zeta, thetap
            solution = minimize(objective, motor_model_parameters)

            p = solution.x

            # show final objective
            # print('Final SSE Objective: ' + str(objective(p)))

            print('Kp: ' + str(p[0]))
            print('taup: ' + str(p[1]))
            print('zeta: ' + str(p[2]))
            print('thetap: ' + str(p[3]))

            # calculate model with updated parameters
            ym1 = sim_model(motor_model_parameters)
            ym2 = sim_model(p)

            # plot results
            plt.figure()
            plt.subplot(2, 1, 1)
            plt.plot(t, ym1,'b-', linewidth = 2, label = 'Initial Guess')
            plt.plot(t, ym2, 'r--', linewidth = 3, label = 'Optimized SOPDT (Epoch: %d)' % (i))
            plt.plot(t, yp, 'k--', linewidth = 2, label = 'Process Data')
            plt.ylabel('Output')
            plt.legend(loc = 'best')
            plt.subplot(2, 1, 2)
            plt.plot(t, u, 'bx-', linewidth = 2)
            plt.plot(t, uf(t), 'r--', linewidth = 3)
            plt.legend(['Measured', 'Interpolated'], loc = 'best')
            plt.ylabel('Input Data')

            # Update parameters
            for j in range(3):
                motor_model_parameters[j] = p[j]

            # Reset process delay, DC motor process model has no delays
            motor_model_parameters[3] = 0.0

        plt.show()

    except FileNotFoundError:
        print("Error! CSV file does not exists. Exiting...")

    return 0

if __name__ == "__main__":
    ret = main(sys.argv)

    print("Program returned: %d" % (ret))
