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

bool checkJsonFormat(const std::string msg, json ref_json) {
    int correspond = 0;

        if (!isJsonParseable(msg))
                return false;

        msg_json = json::parse(msg);
        std::set<std::string> keys_msg(msg_json.begin(), msg_json.end());
        std::set<std::string> keys_json(ref_json.begin(), ref_json.end());

        if (keys_msg == keys_json) {
            for (int i = 0; i < keys_json.size(); i++) {
                if (std::is_same<msg_json[i], ref_json[i]>::value) correspond++;
            }
        }

        // return keys_msg == keys_json
        return correspond == keys_json.size();
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
