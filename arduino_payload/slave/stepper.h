#include <Eventfun.h>



class Stepper {
private:
  int stepPin;
  int dirPin;

  long int stepTime = 600;  // Tiempo por paso en microsegundos
  long stepsPerRev = 4096;   // Pasos para una vuelta completa

  // Configuracion de velocidades
  long minStepTime = 600;
  long maxStepTime = 2000;

  int stepTimer = 0;

  // Variables de control de paso
  bool onHighStep = false;

  /// Repetidor de steps
  bool targetStepsClockwise = true;
  long int targetSteps = -1;
  long int actualSteps = 0;

  int id = 0;


public:
  typedef EventDelegate<Stepper, int> finishedEvent;
  EventSource<Stepper, int> onFinished;

  typedef EventDelegate<Stepper, int> stepedEvent;
  EventSource<Stepper, int> onStep;

  bool attached = false;

  void setId(int _id) {
    id = _id;
  }

  void attach(int _stepPin, int _dirPin) {
    stepPin = _stepPin;
    dirPin = _dirPin;

    pinMode(stepPin, OUTPUT);
    pinMode(dirPin, OUTPUT);
  }

  // Configurar tiempos del motor
  void config(int _stepsPerRev, int _minStepTime, int _maxStepTime) {
    stepsPerRev = _stepsPerRev;
    minStepTime = _minStepTime;
    maxStepTime = _maxStepTime;

     // Configurado por defecto a velocidad maxima
    setVelocity(100);
  }

  // Realizar un numero de pasos objetivo
  void doSteps(int stepsNum, bool dirClockwise = true) {
    if (targetSteps < 0) { targetSteps = 0; }
    //actualSteps = 0;
    targetSteps += stepsNum;

    // Aplicar direccion
    int _dir = LOW;
    if (dirClockwise) { _dir = HIGH; }
    digitalWrite(dirPin, _dir);
  }

  // A que velocidad correra el motor dentro del rango de tiempo por paso
  // va de 0 a 100
  void setVelocity(float velocity) {
    long range = (maxStepTime - minStepTime);
    stepTime = maxStepTime - (range * (velocity/100.0));
  }

  void interrupt() {
    finished();

    Serial.println("INTERRUPT");
  }

  // Llamada cuando el stepper ha llegado a su numero de pasos objetivo
  void finished() {
    // Apagar salidas para evitar falsos
    digitalWrite(stepPin, 0);
    digitalWrite(dirPin, 0);

    targetSteps = -1;
    actualSteps = 0;

    onFinished(this, id);
  }

  // deltaTime medido en microsegundos
  void update(int deltaTime) {
    if (targetSteps < 0) { return; }

    // Si alcanzamos el objetivo de pasos, informar de ello y terminar
    if (actualSteps >= targetSteps) {
      finished();
      return;
    }

    // Avanzar los pasos
    stepTimer += deltaTime;
    if (stepTimer >= stepTime) {
      stepTimer = 0;

      // Si el ultimo tiempo fue alto, apagar
      if (onHighStep) {
        onHighStep = false;
        digitalWrite(stepPin, 0);
        return;
      }

      actualSteps++;
      onStep(this, id);

      onHighStep = true;
      digitalWrite(stepPin, 1);
    }
  }
};





class Stepper4 {
private:
  int in1;
  int in2;
  int in3;
  int in4;

  const int numSteps = 8;
  const int stepsLookup[8] = { B1000, B1100, B0100, B0110, B0010, B0011, B0001, B1001 };

  const int stepTime = 1200;     // Tiempo por paso en microsegundos
  const int stepsPerRev = 4096;  // Pasos para una vuelta completa

  long int stepCounter = 0;
  int stepTimer = 0;

  /// Repetidor de steps
  bool targetStepsClockwise = true;
  long int targetSteps = -1;
  long int actualSteps = 0;

  int id = 0;


  void setOutput(int step) {
    step = step % numSteps;
    digitalWrite(in1, bitRead(stepsLookup[step], 0));
    digitalWrite(in2, bitRead(stepsLookup[step], 1));
    digitalWrite(in3, bitRead(stepsLookup[step], 2));
    digitalWrite(in4, bitRead(stepsLookup[step], 3));
  }

  void clockwise() {
    stepCounter--;
    if (stepCounter < 0) stepCounter = numSteps - 1;
    setOutput(stepCounter);
  }

  void counterclockwise() {
    stepCounter++;
    stepCounter = stepCounter % numSteps;
    setOutput(stepCounter);
  }



public:
  typedef EventDelegate<Stepper4, int> finishedEvent;
  EventSource<Stepper4, int> onFinished;
  bool attached = false;

  void setId(int _id) {
    id = _id;
  }

  void attach(int _in1, int _in2, int _in3, int _in4) {
    in1 = _in1;
    in2 = _in2;
    in3 = _in3;
    in4 = _in4;

    pinMode(in1, OUTPUT);
    pinMode(in2, OUTPUT);
    pinMode(in3, OUTPUT);
    pinMode(in4, OUTPUT);
  }

  // Realizar un simple paso
  void step(bool dirClockwise = true) {
    if (dirClockwise) clockwise();
    else counterclockwise();
  }

  // Realizar un numero de pasos objetivo
  void doSteps(int stepsNum, bool dirClockwise = true) {
    if (targetSteps < 0) { targetSteps = 0; }
    //actualSteps = 0;
    targetSteps += stepsNum;
    targetStepsClockwise = dirClockwise;
  }

  // Llamada cuando el stepper ha llegado a su numero de pasos objetivo
  void finished() {
    // Apagar bobinas para evitar sobrecalentamiento
    digitalWrite(in1, 0);
    digitalWrite(in2, 0);
    digitalWrite(in3, 0);
    digitalWrite(in4, 0);

    targetSteps = -1;
    actualSteps = 0;

    onFinished(this, id);
  }

  // deltaTime medido en microsegundos
  void update(int deltaTime) {
    if (targetSteps < 0) { return; }

    // Si alcanzamos el objetivo de pasos, no hacer nada
    if (actualSteps >= targetSteps) {
      finished();
      return;
    }

    // Realizar los pasos objetivo
    stepTimer += deltaTime;
    if (stepTimer >= stepTime) {
      actualSteps++;
      stepTimer = 0;
      step(targetStepsClockwise);
    }
  }
};
