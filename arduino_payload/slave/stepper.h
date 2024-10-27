#include <Eventfun.h>



class Stepper {
private:
  int stepPin;
  int dirPin;

  const float stepEventRate = 8;  //Cantidad de veces por segundo que notificaremos los pasos realizados por el motor
  const long stepEventPerTime = (1.0 / stepEventRate) * 1000000;
  long stepEventTime = 0;
  int elapsedSteps = 0;

  long int stepTime = 600;  // Tiempo por paso en microsegundos
  long stepsPerRev = 4096;  // Pasos para una vuelta completa

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

  typedef EventDelegate<Stepper, String> stepedEvent;
  EventSource<Stepper, String> onStep;

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

    targetStepsClockwise = dirClockwise;
  }

  // A que velocidad correra el motor dentro del rango de tiempo por paso
  // va de 0 a 100
  void setVelocity(float velocity) {
    long range = (maxStepTime - minStepTime);
    stepTime = maxStepTime - (range * (velocity / 100.0));
  }

  void interrupt() {
    finished();
  }

  // Llamada cuando el stepper ha llegado a su numero de pasos objetivo
  void finished() {
    sendElapsedSteps();

    // Apagar salidas para evitar falsos
    digitalWrite(stepPin, 0);
    digitalWrite(dirPin, 0);

    targetSteps = -1;
    actualSteps = 0;

    onFinished(this, id);
  }

  // deltaTime medido en microsegundos
  void update(int deltaTime) {
    // Avanzar los pasos
    executeSteps(deltaTime);

    stepEventTime += deltaTime;
    bool stepEventTimeReached = stepEventTime >= stepEventPerTime;
    if (!stepEventTimeReached) { return; }  // Evitar que la variable de tiempo crezca indefinidamente

    stepEventTime = 0;
    sendElapsedSteps();
  }

  void sendElapsedSteps() {
    if (elapsedSteps <= 0) { return; }

    int elapsed = elapsedSteps;
    if (!targetStepsClockwise) { elapsed = -elapsedSteps; }
    onStep(this, String(id) + String(elapsed));
    elapsedSteps = 0;
  }

  void executeSteps(int deltaTime) {
    if (targetSteps < 0) { return; }

    // Si alcanzamos el objetivo de pasos, informar de ello y terminar
    if (actualSteps >= targetSteps) {
      finished();
      return;
    }

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
      elapsedSteps++;
      onHighStep = true;
      digitalWrite(stepPin, 1);
    }
  }
};
