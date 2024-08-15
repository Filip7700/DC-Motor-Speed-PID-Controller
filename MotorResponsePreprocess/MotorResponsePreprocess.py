# -*- coding: utf-8 -*-

import sys
import math
import matplotlib.pyplot as plt

ENCODER_GAPS_COUNT = 20
# ENCODER_GRIDS_COUNT = 20
# ENCODER_GAPS_GRIDS_COUNT = 40

MEASUREMENT_VOLTAGE_LOW  = 0
MEASUREMENT_VOLTAGE_HIGH = 6

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

def calculate_linear_interpolation(t, input_data, response_data):
    global MEASUREMENT_VOLTAGE_LOW
    global MEASUREMENT_VOLTAGE_HIGH

    TOLERANCE = 0.0000001

    data_size = len(response_data)

    interpolated_data = [0.0 for i in range(data_size)]

    interpolation_start = 0
    interpolation_stop = 0
    interpolated_data[0] = response_data[0]
    for i in range(1, data_size):
        if((input_data[i] != MEASUREMENT_VOLTAGE_LOW
            and input_data[i - 1] != MEASUREMENT_VOLTAGE_HIGH)
            or (abs(response_data[i] - response_data[i - 1]) > TOLERANCE)
            or i == data_size - 1):

            slope = (
                (response_data[interpolation_stop]
                - response_data[interpolation_start])
                / (t[interpolation_stop]
                    - t[interpolation_start]))

            if i == data_size - 1:
                for j in range(interpolation_start, interpolation_stop + 1):
                    interpolated_data[j] = response_data[j] + slope * (j - interpolation_start)
            else:
                for j in range(interpolation_start, interpolation_stop):
                    interpolated_data[j] = response_data[j] + slope * (j - interpolation_start)

            interpolation_start = i
            interpolation_stop = i

        interpolation_stop += 1

    return interpolated_data

def derivate(x, t):
    x_count = len(x)

    dx_per_dt = [0.0 for i in range(x_count)]

    for i in range(1, x_count):
        dx = x[i] - x[i - 1]
        dt = t[i] - t[i - 1]

        dx_per_dt[i] = dx / dt

    return dx_per_dt

def save_data(
    file_name,
    motor_time_second,
    motor_input_voltage_signal,
    motor_response_angular_speed):

    f = open(file_name, "wt")

    data_size = len(motor_time_second)

    line_strs = ["" for i in range(data_size)]

    for i in range(data_size):
        line_strs[i] = "%f,%d,%f\n" % (
            motor_time_second[i],
            motor_input_voltage_signal[i],
            motor_response_angular_speed[i])

    f.writelines(line_strs)
    f.close()

def main(argv):
    global ENCODER_GAPS_COUNT

    try:
        motor_results = read_motor_results_from_csv("MotorResponseMeasurementsCleaned.csv")
        motor_time_millisecond = motor_results[0]
        motor_input_voltage_signal = motor_results[1]
        motor_response_angular_displacement = motor_results[2]

        data_size = len(motor_response_angular_displacement)

        motor_time_second = [motor_time_millisecond[i] / 1000.0 for i in range(data_size)]

        motor_response_angular_displacement_interpolated = calculate_linear_interpolation(
            motor_time_millisecond,
            motor_input_voltage_signal,
            motor_response_angular_displacement)

        # Angular speed in counted encoder gaps per second
        motor_response_angular_speed = derivate(
            motor_response_angular_displacement_interpolated,
            motor_time_second)

        motor_response_angular_speed_interpolated = calculate_linear_interpolation(
            motor_time_millisecond,
            motor_input_voltage_signal,
            motor_response_angular_speed)

        motor_speed_rads_per_second = [
            2.0 * math.pi * motor_response_angular_speed_interpolated[i] / ENCODER_GAPS_COUNT
            for i in range(data_size)]

        motor_speed_rpm = [
            60.0 * motor_response_angular_speed_interpolated[i] / ENCODER_GAPS_COUNT
            for i in range(data_size)]

        save_data(
            "MotorResponsePreprocessed.csv",
            motor_time_second,
            motor_input_voltage_signal,
            motor_speed_rads_per_second)

        save_data(
            "MotorResponsePreprocessedRPM.csv",
            motor_time_second,
            motor_input_voltage_signal,
            motor_speed_rpm)

        plt.plot(
            motor_time_millisecond, motor_input_voltage_signal, "r",
            motor_time_millisecond, motor_speed_rads_per_second, "g")

        plt.xlabel("t [ms]")
        plt.ylabel("Motor input voltage signal [V]")
        plt.ylabel("Motor response angular speed [rad/s]")

        plt.figure()
        plt.plot(
            motor_time_millisecond, motor_input_voltage_signal, "r",
            motor_time_millisecond, motor_speed_rpm, "g")

        plt.xlabel("t [ms]")
        plt.ylabel("Motor input voltage signal [V]")
        plt.ylabel("Motor response angular speed [RPM]")

        plt.show()

    except FileNotFoundError:
        print("Error! CSV file does not exists. Exiting...")

    return 0

if __name__ == "__main__":
    ret = main(sys.argv)

    print("Program returned: %d" % (ret))
