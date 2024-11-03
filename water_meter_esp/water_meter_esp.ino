#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
// Network SSID
#define WIFI_SSID "Reem-iPhone"
#define WIFI_PASS "reem1234"
#define UDP_PORT 49393

WiFiUDP UDP;

char packet[255];
char reply[20];


int sensorPin = D2;
volatile long pulse = 0;
volatile long was_liquid = 0;
unsigned long lastTime;

void setup() {

  pinMode(sensorPin, INPUT);
  Serial.begin(9600);
  attachInterrupt(digitalPinToInterrupt(sensorPin), increase, RISING);

  delay(10);
 
  // Begin WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
 
  // Connecting to WiFi...
  Serial.print("Connecting to ");
  Serial.print(WIFI_SSID);
  // Loop continuously while WiFi is not connected
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(100);
    Serial.print(".");
  }
  // Connected to WiFi
  Serial.println();
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());

  // Begin listening to UDP port
  UDP.begin(UDP_PORT);
  Serial.print("Listening on UDP port ");
  Serial.println(UDP_PORT);
}

void loop() {
  int packetSize = UDP.parsePacket();
  if (pulse > 0) {
    was_liquid = 1;
  }
  else {
    was_liquid = 0;
  }
  if (packetSize) {
    // Restart pulse
    pulse = 0;

    // Send return packet
    UDP.beginPacket(UDP.remoteIP(), UDP.remotePort());
    sprintf(reply, "%d v", was_liquid);
    UDP.write(reply);
    UDP.endPacket();
  }
  delay(500);
}

ICACHE_RAM_ATTR void increase() {
  pulse++;
}