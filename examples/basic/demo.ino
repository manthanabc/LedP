#include <LedSender.h>

LedSender led(13, 10); // Pin 13, 10 baud

void setup() {
  led.print_n("Hello", 3);
}

void loop() {
}
