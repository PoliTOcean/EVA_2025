#include "utils.hpp"

using json = nlohmann::json;

bool isJsonParseable(const std::string& str) {
    try {
        // Try to parse the string as JSON
        json::parse(str);
        return true;
    } catch (const json::parse_error& e) {
        // If a parse error is thrown, the string is not valid JSON
        return false;
    }
}

std::string motorID_to_string(MotorID id) {
    switch (id) {
        case MotorID::FSX:    return "FSX";
        case MotorID::FDX:    return "FDX";
        case MotorID::RSX:    return "RSX";
        case MotorID::RDX:    return "RDX";
        case MotorID::UPFSX:  return "UPFSX";
        case MotorID::UPFDX:  return "UPFDX";
        case MotorID::UPRSX:  return "UPRSX";
        case MotorID::UPRDX:  return "UPRDX";
        default:              return "DEFAULT";
    }
}

std::string floatToStringWithDecimals(float value, int n) {
    std::ostringstream out;
    out << std::fixed << std::setprecision(n) << value;
    return out.str();
}
