#ifndef LED_P_H
#define LED_P_H

#include <Arduino.h>

class LedSender {
private:
    uint8_t pin;
    unsigned int baudDelay;

    void sendBit(bool b);
    uint16_t hammingEncode(uint8_t data);
    void ledPrint(const char* arr);

public:
    LedSender(uint8_t ledPin, unsigned int baudRate = 10);
    void print(const char* str);
    void print_n(const char* str, int n);
};

#endif
