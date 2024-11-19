#ifndef UTILS_H
#define UTILS_H

#include <iostream>
#include <iomanip>
#include <sstream>
#include <json.hpp>
#include "motorID.hpp"

std::string motorID_to_string(MotorID id);

std::string floatToStringWithDecimals(float value, int n);

bool isJsonParseable(const std::string& str);

#endif