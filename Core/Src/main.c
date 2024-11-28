/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2024 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "crc.h"
#include "dma.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
// Arm and Wrist Pin Definitions
#define DEBUG_EN 0

#define PIN_DIR_WRIST GPIO_PIN_4 // GPIOB
#define  PIN_EN_WRIST GPIO_PIN_5 // GPIOB
#define  PIN_DIR_HAND GPIO_PIN_7 // GPIOB

// Packets' Codes
#define CHIMP_INIT_SOP 0xFF
#define CHIMP_COMM_SOP 0xAA
#define CHIMP_HB_SOP   0xBB
#define CHIMP_EOP 	   0xEE
#define CHIMP_ESCAPE   0x7E

// Packet sizes, to be kept updated
#define   CHIMP_RX_PCKT_SIZE 27
#define   CHIMP_TX_PCKT_SIZE 50
#define CHIMP_RESP_PCKT_SIZE 8
#define   CHIMP_HB_PCKT_SIZE 7
// Init Packet Indexes
#define        CHIMP_INIT_SOP_IDX 0
#define    CHIMP_INIT_ADDRESS_IDX 1
#define    CHIMP_INIT_VERSION_IDX 2
#define CHIMP_INIT_SUBVERSION_IDX 3
#define  CHIMP_INIT_HB_PERIOD_IDX 4
#define       CHIMP_INIT_CRC8_IDX 5
#define        CHIMP_INIT_EOP_IDX 6

// Response Packet Indexes
#define        CHIMP_RESP_SOP_IDX 0
#define    CHIMP_RESP_ADDRESS_IDX 1
#define    CHIMP_RESP_VERSION_IDX 2
#define CHIMP_RESP_SUBVERSION_IDX 3
#define   CHIMP_RESP_RESPONSE_IDX 4
#define       CHIMP_RESP_CRC8_IDX 5
#define        CHIMP_RESP_EOP_IDX 6

// Heart Beat Packet Indexes
#define     CHIMP_HB_SOP_IDX 0
#define CHIMP_HB_ADDRESS_IDX 1
#define  CHIMP_HB_STATUS_IDX 2
#define CHIMP_HB_PAYLOAD_IDX 3
#define    CHIMP_HB_CRC8_IDX 4
#define     CHIMP_HB_EOP_IDX 5

// Response Packet - Response field codes
#define                 CHIMP_RESP_OK 0x00
#define CHIMP_RESP_OLD_VERSION_MASTER 0x01
#define  CHIMP_RESP_OLD_VERSION_SLAVE 0x02
#define        CHIMP_RESP_CRC_FAILURE 0x03

// HB Packet - Status field codes
#define CHIMP_HB_READY  0b00000000
#define CHIMP_HB_NREADY 0b00000001
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
typedef enum {
	CHIMP_OK,
	CHIMP_BUSY
} CHIMP_StatusTypeDef;

typedef struct {
	CHIMP_StatusTypeDef  				         Status;
	uint16_t                              Motor_Arg[11];
	uint8_t									       Tick;
	uint8_t         		   				  HB_Period;
	uint8_t           		   			   	    Version;
	uint8_t         						 SubVersion;
	uint8_t             				      FillIndex;
	uint8_t                                       Esc_f;
	uint8_t 			                    UART_Buffer;
	uint8_t                                  Arm_Torque;
	uint8_t                TxPacket[CHIMP_TX_PCKT_SIZE];
	uint8_t                RxPacket[CHIMP_RX_PCKT_SIZE];
	uint8_t             Resp_Pckt[CHIMP_RESP_PCKT_SIZE];
	uint8_t                 HB_Pckt[CHIMP_HB_PCKT_SIZE];
} CHIMP_TypeDef;

static CHIMP_TypeDef chimp;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_CRC_Init();
  MX_TIM6_Init();
  MX_TIM16_Init();
  MX_TIM1_Init();
  MX_TIM2_Init();
  MX_TIM15_Init();
  MX_USART2_UART_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */
  // CHIMP initialization
  chimp. HB_Period = 1;
  chimp.   Version = 1;
  chimp.SubVersion = 0;

  // Fill Response Packet
  chimp.Resp_Pckt       [CHIMP_RESP_SOP_IDX] =   CHIMP_INIT_SOP;
  chimp.Resp_Pckt   [CHIMP_RESP_ADDRESS_IDX] =             0x00;
  chimp.Resp_Pckt   [CHIMP_RESP_VERSION_IDX] =    chimp.Version;
  chimp.Resp_Pckt[CHIMP_RESP_SUBVERSION_IDX] = chimp.SubVersion;

  // Fill HB Packet
  chimp.HB_Pckt    [CHIMP_HB_SOP_IDX] =   CHIMP_HB_SOP;
  chimp.HB_Pckt[CHIMP_HB_ADDRESS_IDX] =           0x00;
  chimp.HB_Pckt [CHIMP_HB_STATUS_IDX] = CHIMP_HB_READY;

  #if (DEBUG_EN == 1)
  	  HAL_UART_Receive_DMA(&huart2, &chimp.UART_Buffer, 1);
  #else
  	  HAL_UART_Receive_DMA(&huart1, &chimp.UART_Buffer, 1);
  #endif

  HAL_TIM_Base_Start_IT(&htim6);

  HAL_TIM_Base_Start_IT(&htim1);
  HAL_TIM_Base_Start_IT(&htim2);
  HAL_TIM_Base_Start_IT(&htim15);
  HAL_TIM_Base_Start_IT(&htim16);

  HAL_TIM_OC_Start_IT(&htim1,TIM_CHANNEL_1);
  HAL_TIM_OC_Start_IT(&htim1,TIM_CHANNEL_2);
  HAL_TIM_OC_Start_IT(&htim1,TIM_CHANNEL_3);
  HAL_TIM_OC_Start_IT(&htim1,TIM_CHANNEL_4);

  HAL_TIM_OC_Start_IT(&htim2,TIM_CHANNEL_1);
  HAL_TIM_OC_Start_IT(&htim2,TIM_CHANNEL_2);
  HAL_TIM_OC_Start_IT(&htim2,TIM_CHANNEL_3);
  HAL_TIM_OC_Start_IT(&htim2,TIM_CHANNEL_4);

  HAL_TIM_OC_Start_IT(&htim15,TIM_CHANNEL_1);

  HAL_TIM_OC_Start_IT(&htim16,TIM_CHANNEL_1);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  if (HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_MSI;
  RCC_OscInitStruct.MSIState = RCC_MSI_ON;
  RCC_OscInitStruct.MSICalibrationValue = 0;
  RCC_OscInitStruct.MSIClockRange = RCC_MSIRANGE_6;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_MSI;
  RCC_OscInitStruct.PLL.PLLM = 1;
  RCC_OscInitStruct.PLL.PLLN = 40;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV7;
  RCC_OscInitStruct.PLL.PLLQ = RCC_PLLQ_DIV2;
  RCC_OscInitStruct.PLL.PLLR = RCC_PLLR_DIV2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_4) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
	uint8_t pcktFilled_f = 0;

	if ((chimp.UART_Buffer == CHIMP_EOP && !chimp.Esc_f) || chimp.FillIndex == (CHIMP_RX_PCKT_SIZE - 1)) {
		chimp.RxPacket[chimp.FillIndex] = chimp.UART_Buffer;
		pcktFilled_f = 1;
	}
	else if (chimp.UART_Buffer == CHIMP_ESCAPE && !chimp.Esc_f) {
		chimp.Esc_f = 1;
	}
	else {
		chimp.RxPacket[chimp.FillIndex] = chimp.UART_Buffer;
		chimp.FillIndex++;
		chimp.Esc_f = 0;
	}

	if (pcktFilled_f) {
		// Check if Address field contains current board address
		if (chimp.RxPacket[1] == 0x00 && chimp.FillIndex >= 6) {

			if (chimp.RxPacket[0] == CHIMP_INIT_SOP) {
				// Response field evaluation //

				// Perform CRC-8 check
				if (HAL_CRC_Calculate(&hcrc, (uint32_t *)chimp.RxPacket, CHIMP_INIT_CRC8_IDX) != chimp.RxPacket[CHIMP_INIT_CRC8_IDX])
					chimp.Resp_Pckt[CHIMP_RESP_RESPONSE_IDX] = CHIMP_RESP_CRC_FAILURE;
				// If there is no other failure, perform version check
				else {
					if (chimp.Version == chimp.RxPacket[CHIMP_INIT_VERSION_IDX]) {
						if (chimp.SubVersion == chimp.RxPacket[CHIMP_INIT_SUBVERSION_IDX]) {
							chimp.Resp_Pckt[CHIMP_RESP_RESPONSE_IDX] = CHIMP_RESP_OK;
						}
						else if (chimp.SubVersion < chimp.RxPacket[CHIMP_INIT_SUBVERSION_IDX]) {
							chimp.Resp_Pckt[CHIMP_RESP_RESPONSE_IDX] = CHIMP_RESP_OLD_VERSION_SLAVE;
						}
						else chimp.Resp_Pckt[CHIMP_RESP_RESPONSE_IDX] = CHIMP_RESP_OLD_VERSION_MASTER;
					}
					else if (chimp.Version < chimp.RxPacket[CHIMP_INIT_VERSION_IDX]) {
						chimp.Resp_Pckt[CHIMP_RESP_RESPONSE_IDX] = CHIMP_RESP_OLD_VERSION_SLAVE;
					}
					else chimp.Resp_Pckt[CHIMP_RESP_RESPONSE_IDX] = CHIMP_RESP_OLD_VERSION_MASTER;
				}

				// ------------------------- //

				// Response Packet CRC8 calculation
				uint8_t tmp = HAL_CRC_Calculate(&hcrc, (uint32_t *)chimp.Resp_Pckt, CHIMP_RESP_CRC8_IDX);
				uint8_t offset = 0;
				if (tmp == CHIMP_ESCAPE || tmp == CHIMP_INIT_SOP || tmp == CHIMP_COMM_SOP || tmp == CHIMP_HB_SOP || tmp == CHIMP_EOP) {
					chimp.Resp_Pckt[CHIMP_RESP_CRC8_IDX] = CHIMP_ESCAPE;
					offset = 1;
				}
				chimp.Resp_Pckt[CHIMP_RESP_CRC8_IDX + offset] = tmp;
				chimp.Resp_Pckt[CHIMP_RESP_EOP_IDX  + offset] = CHIMP_EOP;

				// Send Response Packet
				#if (DEBUG_EN == 1)
					while (HAL_UART_Transmit_DMA(&huart2, chimp.Resp_Pckt, (CHIMP_RESP_PCKT_SIZE - 1 + offset)) != HAL_OK) {}
				#else
					while (HAL_UART_Transmit_DMA(&huart1, chimp.Resp_Pckt, (CHIMP_RESP_PCKT_SIZE - 1 + offset)) != HAL_OK) {}
				#endif

				// No Errors, update HB period
				if (chimp.Resp_Pckt[CHIMP_RESP_RESPONSE_IDX] == CHIMP_RESP_OK) {
					// Setting HB period and starting generation of HB packets
					chimp.HB_Period = chimp.RxPacket[CHIMP_INIT_HB_PERIOD_IDX] + 1;
				}
			}
			else {
				// Perform CRC-8 check
				chimp.RxPacket[0] = CHIMP_COMM_SOP;
				if (HAL_CRC_Calculate(&hcrc, (uint32_t *)chimp.RxPacket, (chimp.FillIndex - 1)) == chimp.RxPacket[chimp.FillIndex - 1]) {
					memcpy(chimp.Motor_Arg, (chimp.RxPacket + 3), (chimp.FillIndex - 4));

					if (!chimp.RxPacket[2]) {
						htim1.Instance->CCR1 = chimp.Motor_Arg[0];
						htim1.Instance->CCR2 = chimp.Motor_Arg[1];
						htim1.Instance->CCR3 = chimp.Motor_Arg[2];
						htim1.Instance->CCR4 = chimp.Motor_Arg[3];

						htim2.Instance->CCR1 = chimp.Motor_Arg[4];
						htim2.Instance->CCR2 = chimp.Motor_Arg[5];
						htim2.Instance->CCR3 = chimp.Motor_Arg[6];
						htim2.Instance->CCR4 = chimp.Motor_Arg[7];
					} else {
						switch((uint16_t) chimp.RxPacket[3]) {
							case 0:
								HAL_GPIO_WritePin(GPIOB, PIN_DIR_WRIST, 1);
								HAL_GPIO_WritePin(GPIOB,  PIN_EN_WRIST, 0);
								htim15.Instance->CCR1 = 127;
								break;
							case 1:
								HAL_GPIO_WritePin(GPIOB, PIN_DIR_WRIST, 0);
								HAL_GPIO_WritePin(GPIOB,  PIN_EN_WRIST, 0);
								htim15.Instance->CCR1 = 127;
								break;
							case 2:
								if(chimp.Arm_Torque == 1)
									htim15.Instance->CCR1 = 0;
								else
									HAL_GPIO_WritePin(GPIOB, PIN_EN_WRIST, 1);
								break;
							case 3: //close claw
								HAL_GPIO_WritePin(GPIOB, PIN_DIR_HAND, 0);
								htim16.Instance->CCR1 = 127;
								break;
							case 4: //open claw
								HAL_GPIO_WritePin(GPIOB, PIN_DIR_HAND, 1);
								htim16.Instance->CCR1 = 127;
								break;
							case 5: //stop hand
								htim16.Instance->CCR1 = 0;
								break;
							case 6:
								chimp.Arm_Torque = 1;
								HAL_GPIO_WritePin(GPIOB, PIN_EN_WRIST, 0);
								htim15.Instance->CCR1 = 0;
								break;
							case 7:
								chimp.Arm_Torque = 1;
								HAL_GPIO_WritePin(GPIOB, PIN_EN_WRIST, 1);
								break;
							default:
								break;
						}
					}
				}
			}
		}

		// Resetting Communication Packet
		memset(chimp.RxPacket, 0, chimp.FillIndex + 1);

		chimp.Esc_f = 0;
		chimp.FillIndex = 0;
	}
}

void HAL_TIM_PWM_PulseFinishedCallback(TIM_HandleTypeDef* htim){
	if(htim->Instance == TIM1 ) {
		if(htim->Channel == HAL_TIM_ACTIVE_CHANNEL_2) {
			HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, 0);  // A8 | D9
		}
		if(htim->Channel == HAL_TIM_ACTIVE_CHANNEL_3) {
			HAL_GPIO_WritePin(GPIOB, GPIO_PIN_1, 0);  // B1 | D6
		}
		if(htim->Channel == HAL_TIM_ACTIVE_CHANNEL_4) {
			HAL_GPIO_WritePin(GPIOA, GPIO_PIN_11, 0); // A11 | D10
		}
		if(htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1) {
			HAL_GPIO_WritePin(GPIOA, GPIO_PIN_3, 0);  // A3 | A2
		}
	}
	else if(htim->Instance == TIM2) {
		if(htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1) {
			HAL_GPIO_WritePin(GPIOA, GPIO_PIN_6, 0); // A6 | A5
		}
		if(htim->Channel == HAL_TIM_ACTIVE_CHANNEL_3) {
			HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, 0); // A4 | A3
		}
		if(htim->Channel == HAL_TIM_ACTIVE_CHANNEL_4) {
			HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, 0); // B0 | D3
		}
		if(htim->Channel == HAL_TIM_ACTIVE_CHANNEL_2) {
			HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, 0); // A0 | A0
		}
	}
	else if(htim->Instance == TIM15) {
		if(htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1) {
			HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1, 0);
		}
	}
	else if(htim->Instance == TIM16) {
		if(htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1) {
			HAL_GPIO_WritePin(GPIOA, GPIO_PIN_7, 0);
		}
	}
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef* htim){
	if (htim->Instance == TIM6) {
		chimp.Tick++;

		if (chimp.Tick == chimp.HB_Period) {
			chimp.HB_Pckt[CHIMP_HB_PAYLOAD_IDX] = 0x00;

			// HB Packet CRC8 calculation
			uint8_t tmp = HAL_CRC_Calculate(&hcrc, (uint32_t *)chimp.HB_Pckt, CHIMP_HB_CRC8_IDX);
			uint8_t offset = 0;
			if (tmp == CHIMP_ESCAPE || tmp == CHIMP_INIT_SOP || tmp == CHIMP_COMM_SOP || tmp == CHIMP_HB_SOP || tmp == CHIMP_EOP) {
				chimp.HB_Pckt[CHIMP_HB_CRC8_IDX] = CHIMP_ESCAPE;
				offset = 1;
			}
			chimp.HB_Pckt[CHIMP_HB_CRC8_IDX + offset] = tmp;
			chimp.HB_Pckt[CHIMP_HB_EOP_IDX  + offset] = CHIMP_EOP;

			// Send Init Response Packet
			#if (DEBUG_EN == 1)
				while (HAL_UART_Transmit_DMA(&huart2, chimp.HB_Pckt, (CHIMP_HB_PCKT_SIZE - 1 + offset)) != HAL_OK) {}
			#else
				while (HAL_UART_Transmit_DMA(&huart1, chimp.HB_Pckt, (CHIMP_HB_PCKT_SIZE - 1 + offset)) != HAL_OK) {}
			#endif

			chimp.Tick = 0;
		}
	}
	else if (htim->Instance == TIM1) {            // Communication Packet Args order
		HAL_GPIO_WritePin(GPIOA,  GPIO_PIN_8, 1); // 1
		HAL_GPIO_WritePin(GPIOB,  GPIO_PIN_1, 1); // 2
		HAL_GPIO_WritePin(GPIOA, GPIO_PIN_11, 1); // 3
		HAL_GPIO_WritePin(GPIOA,  GPIO_PIN_3, 1); // 4
    }
	else if (htim->Instance == TIM2) {
		HAL_GPIO_WritePin(GPIOA, GPIO_PIN_6, 1); // 5
		HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, 1); // 6
		HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, 1); // 7
		HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, 1); // 8
	}
	else if (htim->Instance == TIM15) {
		HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1, 1);
	}
	else if (htim->Instance == TIM16) {
		HAL_GPIO_WritePin(GPIOA, GPIO_PIN_7, 1);
	}
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
