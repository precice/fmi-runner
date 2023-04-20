#include <math.h>  // for fabs()
#include <float.h> // for DBL_MIN
#include "config.h"
#include "model.h"

#define V_MIN (0.1)
#define EVENT_EPSILON (1e-10)


void setStartValues(ModelInstance *comp) {
    M(read_data)	= 0;
    M(write_data)   = 0;
    M(increment)    = 1;

}

Status calculateValues(ModelInstance *comp) {
    
    UNUSED(comp);
    return OK;
    
}

Status getFloat64(ModelInstance* comp, ValueReference vr, double *value, size_t *index) {
    switch (vr) {
        case vr_time:
            value[(*index)++] = comp->time;
            return OK;
        case vr_read_data:
            value[(*index)++] = M(read_data);
            return OK;
        case vr_write_data:
            value[(*index)++] = M(write_data);
            return OK;
        case vr_increment:
            value[(*index)++] = M(increment);
            return OK;
        default:
            logError(comp, "Get Float64 is not allowed for value reference %u.", vr);
            return Error;
    }
}

Status setFloat64(ModelInstance* comp, ValueReference vr, const double *value, size_t *index) {
    switch (vr) {

        case vr_read_data:
            M(read_data) = value[(*index)++];
            return OK;
        case vr_write_data:
            M(read_data) = value[(*index)++];
            return OK;
        case vr_increment:
            M(read_data) = value[(*index)++];
            return OK;
        default:
            logError(comp, "Unexpected value reference: %u.", vr);
            return Error;
    }
}

Status getOutputDerivative(ModelInstance *comp, ValueReference valueReference, int order, double *value) {

    if (order != 1) {
        logError(comp, "The output derivative order %d for value reference %u is not available.", order, valueReference);
        return Error;
    }

    switch (valueReference) {

    default:
        logError(comp, "The output derivative for value reference %u is not available.", valueReference);
        return Error;
    }
    
    UNUSED(value);
}

void eventUpdate(ModelInstance *comp) {

    if (false) {
    
    } else {
        comp->valuesOfContinuousStatesChanged = false;
    }

    comp->nominalsOfContinuousStatesChanged = false;
    comp->terminateSimulation  = false;
    comp->nextEventTimeDefined = false;
}

void getContinuousStates(ModelInstance *comp, double x[], size_t nx) {
    UNUSED(comp);
    UNUSED(nx);
    UNUSED(x);
}

void setContinuousStates(ModelInstance *comp, const double x[], size_t nx) {
    UNUSED(comp);
    UNUSED(nx);
    UNUSED(x);
}

void getDerivatives(ModelInstance *comp, double dx[], size_t nx) {
    UNUSED(comp);
    UNUSED(nx);
    UNUSED(dx);
}

void getEventIndicators(ModelInstance *comp, double z[], size_t nz) {

    UNUSED(nz);
    UNUSED(comp);
    UNUSED(z);

}
