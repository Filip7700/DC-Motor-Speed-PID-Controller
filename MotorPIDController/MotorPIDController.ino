#include <stdint.h>
#include <timer.h>

const unsigned MOTOR_CONTROL_PIN_1 = 0U;
const unsigned MOTOR_CONTROL_PIN_2 = 2U;
const unsigned MOTOR_PWM_PIN = 5U;
const unsigned ENCODER_OUT_PIN = 14U;

const unsigned MIN_PWM_VALUE =   0U; // 0% duty cycle
const unsigned MAX_PWM_VALUE = 920U; // ~90% duty cycle;
const unsigned MAX_SUPPLY_VOLTAGE_VOLTS = 12U;

static unsigned GAPS_IN_ENCODER_COUNT = 20U;

//static const float PI = 3.141592653589F

static const float DESIRED_MOTOR_RPM = 375.0F;
static const float DESIRED_MOTOR_RADS_PER_SECOND = 39.269908F;

static const float SAMPLING_PERIOD_SECONDS = 0.01F;
static const unsigned SAMPLING_PERIOD_MILLISECONDS = 10U;

static const float PID_PROPORTIONAL_GAIN = 28.926230F;
static const float PID_INTEGRAL_GAIN = 2.891828F;
static const float PID_DERIVATIVE_GAIN = 0.079449F;

static unsigned total_encoder_gaps_count = 0U;

bool is_ready_to_update_control_voltage_pwm = false;

Timer timer_obj;

ICACHE_RAM_ATTR void count_encoder_gaps_callback() {
    total_encoder_gaps_count++;
}

void set_ready_to_update_control_voltage_pwm() {
    is_ready_to_update_control_voltage_pwm = true;
}

float convert_rpm_to_rads_per_second(const float rpm) {
    float rads_per_second = rpm / 60.0F * 2.0F * PI;

    return rads_per_second;
}

float convert_gaps_per_sample_to_rads_per_second(const unsigned gaps_per_sample) {
    float rads_per_second = (
        2.0F
        * PI
        * ((gaps_per_sample / SAMPLING_PERIOD_SECONDS)
        / GAPS_IN_ENCODER_COUNT));

    return rads_per_second;
}

float convert_gaps_per_sample_to_rpm(const unsigned gaps_per_sample) {
    float rpm = (
        60.0F
        * ((gaps_per_sample / SAMPLING_PERIOD_SECONDS)
        / GAPS_IN_ENCODER_COUNT));

    return rpm;
}

unsigned convert_voltage_to_pwm_value(float voltage) {
    unsigned pwm_value = (voltage / MAX_SUPPLY_VOLTAGE_VOLTS) * MAX_PWM_VALUE;
    return pwm_value;
}

void setup() {
    pinMode(MOTOR_PWM_PIN, OUTPUT);
    pinMode(MOTOR_CONTROL_PIN_1, OUTPUT);
    pinMode(MOTOR_CONTROL_PIN_2, OUTPUT);
    pinMode(ENCODER_OUT_PIN, INPUT_PULLUP);

    digitalWrite(MOTOR_CONTROL_PIN_1, LOW);
    digitalWrite(MOTOR_CONTROL_PIN_2, LOW);

    // Set duty cycle to 50%
    analogWrite(MOTOR_PWM_PIN, MIN_PWM_VALUE);

    Serial.begin(115200U);

    int ret = digitalPinToInterrupt(ENCODER_OUT_PIN);

    if(ret == -1) {
        Serial.println("Interrupts not supported on pin: ENCODER_OUT_PIN");
    }
    else {
        attachInterrupt(
            ret,
            count_encoder_gaps_callback,
            FALLING);

        timer_obj.setInterval(SAMPLING_PERIOD_MILLISECONDS);
        timer_obj.setCallback(set_ready_to_update_control_voltage_pwm);
        timer_obj.start();

        // Move motor forwards
        digitalWrite(MOTOR_CONTROL_PIN_1, HIGH);
        digitalWrite(MOTOR_CONTROL_PIN_2, LOW);
    }
}

void loop() {
    static unsigned previous_encoder_gaps_count = 0U;
    static float previous_error = 0.0F;
    static float cumulative_error_sum = 0.0F;

    if(is_ready_to_update_control_voltage_pwm) {
        unsigned gaps_per_sample = (
            total_encoder_gaps_count
            - previous_encoder_gaps_count);

        previous_encoder_gaps_count = total_encoder_gaps_count;

        float motor_speed_rads_per_second = convert_gaps_per_sample_to_rads_per_second(
            gaps_per_sample);

        Serial.println(motor_speed_rads_per_second);

        float error = DESIRED_MOTOR_RADS_PER_SECOND - motor_speed_rads_per_second;

        // PID controller in concrete action!!!

        // PID controller BEGIN

        float proportional_compensation = PID_PROPORTIONAL_GAIN * error;
        float integral_compensation = (
            cumulative_error_sum + 
            PID_INTEGRAL_GAIN * SAMPLING_PERIOD_SECONDS * error);
        float derivative_compensation = (
            PID_DERIVATIVE_GAIN
            / SAMPLING_PERIOD_SECONDS
            * (error - previous_error));

        float control_voltage = (
            proportional_compensation
            + integral_compensation
            + derivative_compensation);

        // Update previous error for derivator component of PID
        previous_error = error;

        // PID controller END

        unsigned control_pwm_value = convert_voltage_to_pwm_value(control_voltage);

        // Cap maximum PWM
        if(control_pwm_value > MAX_PWM_VALUE) {
            control_pwm_value = MAX_PWM_VALUE;
        }
        else {
            /* Update cumulative error sum for integrator component of PID.
            Note that integrator updates its cumulative sum only when control PWM is
            within its normal working range.
            In case of PWM control signal rises above its maximum rated PWM value
            (see MAX_PWM_VALUE constant), integrator keeps accumulating error, and thus
            requesting even more PWM value to compensate external forces that are
            beyond motor's capabilities.
            In that case, it is a good idea to avoid breaking motor by pausing
            integrator until external forces stop stressing the motor beyong its rated
            working range. */
            cumulative_error_sum = integral_compensation;
        }

        analogWrite(MOTOR_PWM_PIN, control_pwm_value);

        is_ready_to_update_control_voltage_pwm = false;
    }

    timer_obj.update();
}
