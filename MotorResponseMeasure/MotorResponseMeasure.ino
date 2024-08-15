#include <stdint.h>
#include <timer.h>

#define MAX_ENTRIES 6000U

const unsigned MOTOR_CONTROL_PIN_1 = 0U;
const unsigned MOTOR_CONTROL_PIN_2 = 2U;
const unsigned MOTOR_PWM_PIN = 5U;
const unsigned ENCODER_OUT_PIN = 14U;
const unsigned DUTY_CYCLE_50_PERCENT_VALUE = 512U;
const unsigned DUTY_CYCLE_100_PERCENT_VALUE = 1024U;
const unsigned ENCODER_HOLES_COUNT = 20U;

const unsigned MEASUREMENT_VOLTAGE_LOW  = 0U;
const unsigned MEASUREMENT_VOLTAGE_HIGH = 6U;

const unsigned SAMPLE_PERIOD_MILLISECONDS             = 1U;
const unsigned MOTOR_STATE_CHANGE_PERIOD_MILLISECONDS = 1000U;

volatile static unsigned total_encoder_holes_count = 0U;
volatile static bool is_ready_to_print = false;
volatile static bool is_ready_to_change_motor_state = false;

uint8_t voltages[MAX_ENTRIES] = {0};
unsigned motor_speeds[MAX_ENTRIES] = {0U};

Timer print_timer_obj;
Timer motor_state_timer_obj;

ICACHE_RAM_ATTR void count_encoder_holes_callback() {
    total_encoder_holes_count++;
}

void set_ready_to_print_callback() {
    is_ready_to_print = true;
}

void set_ready_to_change_motor_state_callback() {
    is_ready_to_change_motor_state = true;
}

void setup() {
    pinMode(MOTOR_PWM_PIN, OUTPUT);
    pinMode(MOTOR_CONTROL_PIN_1, OUTPUT);
    pinMode(MOTOR_CONTROL_PIN_2, OUTPUT);
    pinMode(ENCODER_OUT_PIN, INPUT_PULLUP);

    digitalWrite(MOTOR_CONTROL_PIN_1, LOW);
    digitalWrite(MOTOR_CONTROL_PIN_2, LOW);

    // Set duty cycle to 50%
    analogWrite(MOTOR_PWM_PIN, DUTY_CYCLE_50_PERCENT_VALUE);

    Serial.begin(115200U);

    int ret = digitalPinToInterrupt(ENCODER_OUT_PIN);

    if(ret == -1) {
        Serial.println("Interrupts not supported on pin: ENCODER_OUT_PIN");
    }
    else {
        attachInterrupt(
            ret,
            count_encoder_holes_callback,
            FALLING);
    }

    print_timer_obj.setInterval(SAMPLE_PERIOD_MILLISECONDS);
    print_timer_obj.setCallback(set_ready_to_print_callback);
    print_timer_obj.start();

    motor_state_timer_obj.setInterval(MOTOR_STATE_CHANGE_PERIOD_MILLISECONDS);
    motor_state_timer_obj.setCallback(set_ready_to_change_motor_state_callback);
    motor_state_timer_obj.start();
}

void loop() {
    static const unsigned MOTOR_MOVE_STATE   = 0U;
    static const unsigned MOTOR_STOP_STATE   = 1U;
    static const unsigned MOTOR_STATES_COUNT = 2U;

    static unsigned motor_state = MOTOR_STOP_STATE;
    static int voltage_in_volts = MEASUREMENT_VOLTAGE_LOW;
    static unsigned entry_index = 0U;

    if(entry_index < MAX_ENTRIES) {
        if(is_ready_to_print) {
            motor_speeds[entry_index] = total_encoder_holes_count;
            voltages[entry_index++] = voltage_in_volts;
            is_ready_to_print = false;
        }

        if(is_ready_to_change_motor_state) {
            motor_state = (motor_state + 1U) % MOTOR_STATES_COUNT;

            switch(motor_state) {
            case MOTOR_MOVE_STATE:
                digitalWrite(MOTOR_CONTROL_PIN_2, LOW);
                digitalWrite(MOTOR_CONTROL_PIN_1, HIGH);
                voltage_in_volts = MEASUREMENT_VOLTAGE_HIGH;
                break;
            default:
                digitalWrite(MOTOR_CONTROL_PIN_1, LOW);
                digitalWrite(MOTOR_CONTROL_PIN_2, LOW);
                voltage_in_volts = MEASUREMENT_VOLTAGE_LOW;
                break;
            }

            is_ready_to_change_motor_state = false;
        }
    }
    else {
        unsigned i, t = 0U;
        for(i = 0U; i < MAX_ENTRIES; i++) {
            Serial.print(t);
            Serial.print(',');
            Serial.print((unsigned)voltages[i]);
            Serial.print(',');
            Serial.println(motor_speeds[i]);

            t += SAMPLE_PERIOD_MILLISECONDS;
        }

        while(true) {
            delay(100U);
        }
    }

    print_timer_obj.update();
    motor_state_timer_obj.update();
}
