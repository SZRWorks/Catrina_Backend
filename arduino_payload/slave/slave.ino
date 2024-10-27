#include <Servo.h>
#include "Stepper.h"
#include <Wire.h>
#include <ArduinoQueue.h>


#define I2C_ID 2      // ID 0 idenficia a un arduino maestro
#define MAX_SLAVES 2  // Reducir el numero de esclavos podria ayudar al rendimiento general

// Ejemplo payloads
// 1R:A0; - Leer puerto A0 del arduino esclavo 1
// 1R:05:0000; - Respuesta a la lectura del puerto 5 desde el esclavo 1
// 1W:02:0255; - Escribir puerto 2 con 255
// 1P:02:O; - Settear puerto 2 como salida (I:Input, S:Servo)
// 1S:03:0180; - Aplicar un angulo de 180' al servo 3
// 1M:0:02:03; - Aplicar stepPin 2 y dirPin 3 a un nuevo stepper motor con id: 0
// 1M:0:04096:T; - Hacer que el stepper 0 haga 4096 pasos en direccion del reloj. NOTA: valor maximo por payload : 32167 (Se pueden realizar varias llamadas para acumular)
// 1M:0:E; - Interrumpir los pasos del stepper 0 o El stepper 0 ha terminado su trabajo
// 1M:0:00400:0600:2000; - Configurar el stepper a 400 pasos por rev, con un tiempo de 600 microsegundos por rev, y un tiempo maximo de 2000 microsegundos por rev.
// 1M:0:100; - Aplicar velocidad maxima al stepper 0
// 2010; - El stepper 0 del arduino esclavo 2 ha realizado 10 pasos (La simplicidad del payload tiene como objetivo ahorrar ancho de banda) (el largo del numero de pasos puede variar) (Un id de arduino 0 indica al padre)
// Nota: El primer numero del payload indica el esclavo objetivo


String payload = "";
int payloadLength = 0;
bool payloadReady = false;

const int slaveRequestBytes = 11;
const int slaveBufferSize = 30;
ArduinoQueue<String> slavePayloadsBuffer(slaveBufferSize);

const float slavePayloadRequestRate = 16;  //Cantidad de veces por segundo que pediremos a los esclavos presentar payloads
const long slaveRequestPerTime = (1.0 / slavePayloadRequestRate) * 1000000UL;
long slaveRequestTime = 0;


Servo servos[14];
Stepper steppers[5];


void setup() {
  // Configuracion de maestro
  if (I2C_ID == 0) {
    Wire.begin();
    Wire.setClock(400000UL);
    Serial.begin(500000UL);
    return;
  }

  // Configuracion de esclavos
  Wire.begin(I2C_ID);
  Wire.setClock(400000UL);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);
  Serial.begin(500000UL);
}

unsigned long deltaStart = 0;
int _dt = 0;
void loop() {
  deltaStart = micros();
  update(_dt);
  _dt = micros() - deltaStart;
}


// Ciclo de actualizacion logico
void update(int deltaTime) {
  // Actualizar nuestros steppers
  for (int i = 0; i < 5; i++) { steppers[i].update(deltaTime); }

  // Obtener los payloads enviados por los esclavos
  getSlavePayload(deltaTime);

  // Si no hay un payload leer el siguiente
  if (!payloadReady) {
    getPayload();
    return;
  }

  // Ejecutar el payload una vez este listo
  executePayload();
}


void executePayload() {
  // Solo se puede ejecutar un payload completo
  if (!payloadReady) return;

  int payloadReceiver = payload[0] - '0';

  // Enviar datos a esclavos
  if (I2C_ID == 0 && payloadReceiver != I2C_ID) {
    Wire.beginTransmission(payloadReceiver);
    payload = payload + ";";
    Wire.write(payload.c_str());
    Wire.endTransmission();

    // Vaciar el payload una vez ha sido ejecutado
    payload = "";
    payloadReady = false;
    return;
  }

  payload.remove(0, 1);

  char action = payload[0];
  switch (action) {
    case 'P':
      {
        setPinMode(payload.substring(2, 4), payload[5]);
        break;
      }
    case 'R':
      {
        readValue(payload.substring(2, 4));
        break;
      }
    case 'W':
      {
        writeValue(payload.substring(2, 4), payload.substring(5, 9));
        break;
      }
    case 'S':
      {
        servoValue(payload.substring(2, 4), payload.substring(5, 9));
        break;
      }
    case 'M':
      {
        if (payload.length() == 9) {  // Adjuntar pines a stepper
          attachStepper(payload[2], payload.substring(4, 9));
        } else if (payload.length() == 11) {  //Valor de stepper
          stepperValue(payload[2], payload.substring(4, 9), payload[10]);
        } else if (payload.length() == 5) {  // Interrumpir stepper
          stepperInterrupt(payload[2]);
        } else if (payload.length() == 19) {  // Configurar parametros de stepper
          configStepper(payload[2], payload.substring(4, 9), payload.substring(10, 14), payload.substring(15, 19));
        } else if (payload.length() == 7) {  // Aplicar velocidad a stepper M:0:100;
          setStepperVelocity(payload[2], payload.substring(4, 7));
        }
        break;
      }
  }

  // Vaciar el payload una vez ha sido ejecutado
  payload = "";
  payloadReady = false;
}


void setPinMode(String pin, char val) {
  //  Convertir el character del pin a entero
  int intPin = pin.substring(0, 2).toInt();

  //  Convertir el character del valor a Output o Input
  int mode = INPUT;
  if (val == 'O') { mode = OUTPUT; }

  // Adjuntar servo al pin
  if (val == 'S') {
    pinMode(intPin, OUTPUT);
    servos[intPin].attach(intPin);
    return;
  }

  // Settear el pin mode
  pinMode(intPin, mode);
}


void writeValue(String pin, String val) {
  //  Convertir el character del pin a entero
  int intPin = pin.substring(0, 2).toInt();
  int value = val.toInt();

  analogWrite(intPin, value);
}


void readValue(String pin) {
  // Queremos leer un pin analogo
  if (pin[0] == 'A') {
    //  Convertir el character a entero
    int intPin = pin[1] - '0';

    // Leer y enviar el valor analogico
    int val = analogRead(intPin);
    sendPayload("R:" + pin + ":" + String(val));

    return;
  }

  /// Queremos leer un pin digital
  //  Convertir el character del pin a entero
  int intPin = pin.substring(0, 2).toInt();

  // Leer y enviar el valor analogico
  int val = digitalRead(intPin);
  sendPayload("R:" + pin + ":" + String(val));
}


void servoValue(String pin, String val) {
  //  Convertir el character del pin a entero
  int intPin = pin.substring(0, 2).toInt();
  int value = val.toInt();

  servos[intPin].write(value);
}


void attachStepper(char charId, String pines) {
  //  Convertir el character del id a entero
  int id = charId - '0';

  int stepPin = pines.substring(0, 2).toInt();
  int dirPin = pines.substring(3, 5).toInt();

  steppers[id].onFinished += stepperFinished;
  steppers[id].onStep += stepperStep;
  steppers[id].setId(id);
  steppers[id].attach(stepPin, dirPin);
}

void configStepper(char charId, String stepsPerRev, String minStepTime, String maxStepTime) {
  //  Convertir el character del pin a entero
  int id = charId - '0';
  int _stepsPerRev = stepsPerRev.toInt();
  int _minStepTime = minStepTime.toInt();
  int _maxStepTime = maxStepTime.toInt();

  steppers[id].config(_stepsPerRev, _minStepTime, _maxStepTime);
}

void setStepperVelocity(char charId, String velocity) {
  //  Convertir el character del pin a entero
  int id = charId - '0';
  int _velocity = velocity.toInt();

  steppers[id].setVelocity(_velocity);
}

void stepperValue(char charId, String val, char clockwiseChar) {
  //  Convertir el character del pin a entero
  int id = charId - '0';
  int value = val.toInt();
  bool clockwise = (clockwiseChar == 'T');

  steppers[id].doSteps(value, clockwise);
}

void stepperInterrupt(char charId) {
  //  Convertir el character del pin a entero
  int id = charId - '0';

  steppers[id].interrupt();
}

void stepperStep(Stepper* sender, String data) {
  //Enviar señal por puerto serial
  sendPayload(data);
}

// Lamada cuando un stepper ha terminado sus pasos objetivo
void stepperFinished(Stepper* sender, int id) {

  //Enviar señal por puerto serial
  sendPayload("M:" + String(id) + ":E");
}


void sendPayload(String _payload) {
  if (I2C_ID == 0) {
    _payload = String(I2C_ID) + _payload;
    Serial.println(_payload);
    return;
  }

  // Enviar datos del esclavo al maestro
  _payload = String(I2C_ID) + _payload + ";";
  Serial.println("Buffering -> " + _payload);
  slavePayloadsBuffer.enqueue(_payload);
}


void getPayload() {
  char readChar;
  if (I2C_ID == 0) {
    // Leer solo cuando haya datos en el buffer
    if (Serial.available() <= 0) return;

    // read the incoming byte:
    readChar = Serial.read();
  } else {
    // Leer solo cuando haya datos en el buffer
    if (Wire.available() <= 0) return;

    // read the incoming byte:
    readChar = Wire.read();
  }

  // Evitar ingresar espacios en blanco al payload
  if (readChar == ' ' || readChar == '\n' || readChar == '  ') {
    return;
  }

  // Tratar de eliminar payloads corruptas *FALTA IMPLEMENTAR*
  payloadLength++;

  // Punto y coma indica el fin de este payload
  if (readChar == ';') {
    payloadReady = true;
    if (I2C_ID != 0) { Serial.println(payload); }
    return;
  }

  // Guardar en el payload el byte leido
  payload += readChar;
}


// Utilizada solo para obtener informacion de los esclavos y ser reenviada por el serial del maestro
void getSlavePayload(int deltaTime) {
  if (I2C_ID != 0) { return; }

  if (slaveRequestTime <= slaveRequestPerTime) {
    slaveRequestTime += deltaTime;
    return;
  }
  slaveRequestTime = 0;

  for (int i = 1; i <= MAX_SLAVES; i++) {
    if (Wire.requestFrom(i, slaveRequestBytes) <= 0) { continue; }
    char _payload[slaveRequestBytes];
    Wire.readBytes(_payload, slaveRequestBytes);

    String finalPayload = "";
    bool badPayload = true;
    for (int ci = 0; ci < slaveRequestBytes; ci++) {
      char readChar = _payload[ci];

      // Evitar ingresar espacios en blanco al payload
      if (readChar == ' ' || readChar == '\n' || readChar == '  ') {
        continue;
      }

      if (readChar == ';') {
        badPayload = false;
        break;
      }

      finalPayload += readChar;
    }

    if (badPayload) { continue; }
    Serial.println(finalPayload);
  }
}

void receiveEvent(int howMany) {}
void requestEvent() {
  if (I2C_ID == 0) { return; }

  String data = "";
  if (!slavePayloadsBuffer.isEmpty()) {
    data = slavePayloadsBuffer.dequeue();
  }
  Wire.write(data.c_str());
}