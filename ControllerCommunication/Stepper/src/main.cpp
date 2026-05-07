#include <Arduino.h>
#include <SerialP6.h>
#include <P6Controller.h>


// Start/initializere serial lib /definere :)
SerialP6 SP6;
P6Controller Con;

// Stepmotor Variables:
int SPR = 200; // Steps per rev
const int pinStep = 19;
const int pinDir = 18;
const int pinSleep = 20;
const int pinM0 = 10;
const int pinM1 = 23;
const int pinM2 = 22;
const int pinFault =11;
const int pinRST = 21;
bool NewInfo = false;
int steps = 0;
int i = 0;
bool NewInfoStep;
//unsigned long t_now, t_prev; 
// put function declarations here:
int motorSpeed = 200; //RPM
int stepSetting = 32; //can be 1,2,4,8,16,32;
//RTOS
TaskHandle_t ComTaskHandle, MotorTaskHandle = NULL;
SemaphoreHandle_t infoMutex = NULL;

void comTask(void *pvParameters)
{
  while(1){
    //Serial.println("CT");
  steps = SP6.Ser_GetDegree(&NewInfo, infoMutex);
 // Serial.print("STEPS: ");
 // Serial.println(steps);
     
  if(xSemaphoreTake(infoMutex,portMAX_DELAY)== pdTRUE)
    {
      NewInfoStep = NewInfo; // har læst info, derfor ikke nyt
      xSemaphoreGive(infoMutex);
    }
    if(NewInfoStep == true)
    {
     Con.SetNewStep(steps);
    }
  //steps = SP6.Ser_GetDegree(&NewInfo, infoMutex);
  vTaskDelay(pdMS_TO_TICKS(10));
}
}
void MotorTask(void *pvParameters)
{
  while(1){
  
  
  }
}



void setup() {
  Serial.begin(115200);
  Serial.println("YEAH WE GOOD");
  // put your setup code here, to run once:
  infoMutex = xSemaphoreCreateMutex();
  SP6.Ser_Init(115200,50,2000);
  Serial.println("SERIAL INITIATED!!!");
  Con.InitStepMotor(SPR, pinDir, pinSleep, pinStep, pinRST, pinM0, pinM1, pinM2, pinFault);
  Con.ChangeMotorSpeed(motorSpeed);
  Con.ChangeStepperSetting(stepSetting);
  xTaskCreatePinnedToCore(comTask, "ComTask",2048,NULL,2,&ComTaskHandle,0);
  xTaskCreatePinnedToCore(MotorTask,"MotorTaskHandle", 2048, NULL,1,&MotorTaskHandle,0);


// com task has prio 2 and motor 1, so com takes prio  
  
}
void loop(){}
// void loop() {
//   // put your main code here, to run repeatedly:

//   // Få ny degree mpling fra serial:
//   int StepsToTurn = SP6.Ser_GetDegree(&NewInfo, infoMutex); 
//   // Move de givne steps!!!
//   Con.Step(StepsToTurn, &NewInfo); 
//   // Returnerer først her når stepsne er taget 

// }
