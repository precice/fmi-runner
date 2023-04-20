#ifndef config_h
#define config_h

// define class name and unique id
#define MODEL_IDENTIFIER Dummy
#define INSTANTIATION_TOKEN "{1AE5E10D-9521-4DE3-80B9-D0EAAA7D5AF1}"

#define CO_SIMULATION
#define MODEL_EXCHANGE

// define model size
#define NX 2
#define NZ 1

#define SET_FLOAT64
#define GET_OUTPUT_DERIVATIVE
#define EVENT_UPDATE

#define FIXED_SOLVER_STEP 1e-3
#define DEFAULT_STOP_TIME 3

typedef enum {
    vr_time, vr_read_data, vr_write_data, vr_increment
} ValueReference;

typedef struct {

    double read_data;
    double write_data;
    double increment;

} ModelData;

#endif /* config_h */
