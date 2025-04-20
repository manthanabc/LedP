#include "LedP.h"

LedSender::LedSender(uint8_t ledPin, unsigned int baudRate) {
    pin = ledPin;
    pinMode(pin, OUTPUT);
    baudDelay = 1000 / baudRate; // in ms
}

void LedSender::sendBit(bool b) {
    digitalWrite(pin, b);
    delay(baudDelay);
}

uint16_t LedSender::hammingEncode(uint8_t data) {
    uint8_t bits[12] = {0};

    bits[2] = (data >> 7) & 1;
    bits[4] = (data >> 6) & 1;
    bits[5] = (data >> 5) & 1;
    bits[6] = (data >> 4) & 1;
    bits[8] = (data >> 3) & 1;
    bits[9] = (data >> 2) & 1;
    bits[10] = (data >> 1) & 1;
    bits[11] = data & 1;

    bits[0] = bits[2] ^ bits[4] ^ bits[6] ^ bits[8] ^ bits[10];
    bits[1] = bits[2] ^ bits[5] ^ bits[6] ^ bits[9] ^ bits[10];
    bits[3] = bits[4] ^ bits[5] ^ bits[6] ^ bits[11];
    bits[7] = bits[8] ^ bits[9] ^ bits[10] ^ bits[11];

    uint16_t encoded = 0;
    for (int i = 0; i < 12; i++) {
        encoded |= (bits[i] << (11 - i));
    }

    return encoded;
}

void LedSender::ledPrint(const char* arr) {
    int l = strlen(arr);

    // Start pattern (preamble)
    for (int i = 0; i < 8; i++) {
        sendBit(i % 2);
    }

    for (int i = 0; i < l; i++) {
        uint8_t c = arr[i];
        uint16_t codeword = hammingEncode(c);

        for (int j = 11; j >= 0; j--) {
            sendBit((codeword >> j) & 1);
        }
    }

    // End pattern (postamble)
    for (int i = 0; i < 8; i++) {
        sendBit(i % 2);
    }
}

void LedSender::print(const char* str) {
    ledPrint(str);
}

void LedSender::print_n(const char* str, int n) {
    for (int i = 0; i < n; i++) {
        ledPrint(str);
        delay(300); // delay between repeats
    }
}
