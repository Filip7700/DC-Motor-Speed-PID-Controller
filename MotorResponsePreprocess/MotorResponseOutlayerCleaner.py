# -*- coding: utf-8 -*-

import sys
import matplotlib.pyplot as plt

# Expected angular speed on 6 volts is around 39 rad/s (375 RMP) for yellow DC motor
# with gear ration 1:48.
# Here the maximal value is set to be 45 rad/s, and everything above this treshold is
# considered to be an outlyer.
MAX_VALID_ANGULAR_SPEED_RADS_PER_SEC = 45.0

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

def save_data(
    file_name,
    motor_time_second,
    motor_input_voltage_signal,
    motor_response_angular_speed):

    f = open(file_name, "wt")

    data_size = len(motor_time_second)

    line_strs = ["" for i in range(data_size)]

    for i in range(data_size):
        line_strs[i] = "%f,%f,%f\n" % (
            motor_time_second[i],
            motor_input_voltage_signal[i],
            motor_response_angular_speed[i])

    f.writelines(line_strs)
    f.close()

def remove_outlayers(motor_speed):
    motor_speed_samples_count = len(motor_speed)

    motor_speed_cleaned = [0.0 for i in range(motor_speed_samples_count)]

    for i in range(motor_speed_samples_count):
        if motor_speed[i] > MAX_VALID_ANGULAR_SPEED_RADS_PER_SEC:
            motor_speed_cleaned[i] = MAX_VALID_ANGULAR_SPEED_RADS_PER_SEC
        else:
            motor_speed_cleaned[i] = motor_speed[i]

    return motor_speed_cleaned

def main(argv):
    try:
        motor_results = read_motor_results_from_csv("MotorResponsePreprocessed.csv")

        motor_time_second = motor_results[0]
        motor_input_voltage_signal = motor_results[1]
        motor_response_angular_speed_rads_per_second = motor_results[2]

        motor_response_angular_speed_rads_per_second_cleaned = remove_outlayers(
            motor_response_angular_speed_rads_per_second)

        data_size = len(motor_time_second)

        # There are 3 DC motor process responses on 3 voltage step signals from LOW to
        # HIGH from preprocessed measurements data
        # (see file MotorResponsePreprocessed.csv).
        # The total measurement time takes 6 seconds, and we only want one responce.
        # Here, we only need one response sample, and the cleanest response is picked,
        # which is "graphically 2nd response" (from 3000 ms to 4000ms).
        # One respose on HIGH voltage signal takes 1000 ms, however we also want to
        # capture the transient state of the response.
        # So, 500 ms before voltage switches from LOW to HIGH and 500 ms after voltage
        # switches from HIGH to LOW have been also included.
        # This adds up to 2000 ms for measurement data of interest.
        # So the data starts at 2500 ms timestamp and ends at 4500 ms timestamp.
        # We also want to shift the time of beginning of measurements of interest by
        # 2500 ms, so it is start of measurement time.
        # Therefore, we take first 2000 ms of time stamps, but we take voltage and motor
        # angular speeds from 2500 ms to 4500 ms timestamps.
        save_data(
            "MotorProcessData.csv",
            motor_time_second[:2000],
            motor_input_voltage_signal[2500:4500],
            motor_response_angular_speed_rads_per_second_cleaned[2500:4500])

        plt.plot(
            motor_time_second[:2000], motor_input_voltage_signal[2500:4500], "r",
            motor_time_second[:2000], motor_response_angular_speed_rads_per_second_cleaned[2500:4500], "g")

        plt.xlabel("t [ms]")
        plt.ylabel("Motor input voltage signal [V]")
        plt.ylabel("Motor response angular speed [rad/s]")

        plt.show()

    except FileNotFoundError:
        print("Error! CSV file does not exists. Exiting...")

    return 0

if __name__ == "__main__":
    ret = main(sys.argv)

    print("Program returned: %d" % (ret))
