import sys

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
        line_strs[i] = "%d,%d,%d\n" % (
            motor_time_second[i],
            motor_input_voltage_signal[i],
            motor_response_angular_speed[i])

    f.writelines(line_strs)
    f.close()

def clean_response_data(raw_response_data):
    response_data_size = len(raw_response_data)

    cleaned_response_data = [0.0 for i in range(response_data_size)]
    cleaned_response_data[0] = raw_response_data[0]
    data_corresction_rate = 0

    for i in range(1, response_data_size):
        data_change_rate = abs(raw_response_data[i] - raw_response_data[i - 1])
        if data_change_rate > 1:
            data_corresction_rate += data_change_rate

        cleaned_response_data[i] = raw_response_data[i] - data_corresction_rate

    return cleaned_response_data

def main(argv):
    try:
        motor_results = read_motor_results_from_csv("../MotorResponseMeasure/MotorResponseMeasurements.csv")
        motor_time_millisecond = motor_results[0]
        motor_input_voltage_signal = motor_results[1]
        motor_response_angular_displacement = motor_results[2]

        data_size = len(motor_response_angular_displacement)

        cleaned_motor_response_angular_displacement = clean_response_data(
            motor_response_angular_displacement)

        save_data(
            "MotorResponseMeasurementsCleaned.csv",
            motor_time_millisecond,
            motor_input_voltage_signal,
            cleaned_motor_response_angular_displacement)

    except FileNotFoundError:
        print("Error! CSV file does not exists. Exiting...")

    return 0

if __name__ == "__main__":
    ret = main(sys.argv)
    print("Program returned: %d" % (ret))
