#ifndef GPIO_HPP
#define GPIO_HPP

#include <atomic>
#include <memory>
#include <thread>

class GPIO
{
public:
  void Init();

  // High level functions using GPIO interface
  void Pulse( const unsigned n, const unsigned wait ) const;
  void LightsOn() const;
  void LightsOff() const;
  void SpareOn() const;
  void SpareOff() const;

  // High level function using PWM interface
  void SetPWM( const unsigned channel,
               const double   duty_cycle,
               const double   frequency );
  // Only storing the duty cycle for external reference.
  float GetPWM( unsigned channel );

  // High level functions for I2C ADC det interface
  void  SetADCRange( const int );
  void  SetADCRate( const int );
  float ReadADC( const unsigned channel ) const;
  float ReadNTCTemp( const unsigned channel ) const;
  float ReadRTDTemp( const unsigned channel ) const;
  void  SetReferenceVoltage( const unsigned channel, const float val );

  // On the raspberry PI, these pins correspond to the BCM pin from
  // wiringPi's `gpio readall` command. Falling back to
  static constexpr unsigned trigger_pin = 21;// PHYS PIN 40
  static constexpr unsigned light_pin   = 26; // PHYS PIN 37
  static constexpr unsigned spare_pin   = 20; // PHYS PIN 38

  static constexpr unsigned READ  = 0;
  static constexpr unsigned WRITE = 1;
  static constexpr unsigned LOW   = 0;
  static constexpr unsigned HI    = 1;

  // CONSTANT EXPRESSION for file pointers
  static constexpr int UNOPENED    = -2;
  static constexpr int OPEN_FAILED = -1;
  static constexpr int IO_FAILED   = -1;
  static constexpr int NORMAL_PTR  = 0;

  static const uint8_t ADS_RANGE_6V;
  static const uint8_t ADS_RANGE_4V;
  static const uint8_t ADS_RANGE_2V;
  static const uint8_t ADS_RANGE_1V;
  static const uint8_t ADS_RANGE_p5V;
  static const uint8_t ADS_RANGE_p25V;

  static const uint8_t ADS_RATE_8SPS;
  static const uint8_t ADS_RATE_16SPS;
  static const uint8_t ADS_RATE_32SPS;
  static const uint8_t ADS_RATE_64SPS;
  static const uint8_t ADS_RATE_128SPS;
  static const uint8_t ADS_RATE_250SPS;
  static const uint8_t ADS_RATE_475SPS;
  static const uint8_t ADS_RATE_860SPS;

  bool StatusGPIO() const;
  bool StatusADC() const;
  bool StatusPWM() const;

private:
  static int  InitGPIOPin( const int pin, const unsigned direction );
  static void CloseGPIO( const int pin );
  static int  GPIORead( const int fd );
  static void GPIOWrite( const int fd, const unsigned val );

  void InitPWM();
  void ClosePWM();

  static constexpr int ads_default_address = 0x48;
  static int InitI2C();
  void       PushADCSetting();
  int16_t    ADCReadRaw();
  void       FlushLoop( std::atomic<bool>& );
  void       InitI2CFlush();
  void       CloseI2CFlush();

  // File pointers triggers direct GPIO
  int gpio_trigger;
  int gpio_light;
  int gpio_spare;

  // File pointer to ADC
  int gpio_adc;

  // File pointer to PWM stuff
  int pwm_enable[2];
  int pwm_duty[2];
  int pwm_period[2];

  // Storing present duty cycle settings .
  float pwm_duty_value[2];

  uint8_t adc_range;
  uint8_t adc_rate;
  uint8_t adc_channel;

  float reference_voltage[4];

  // I2C interface continuous streaming.
  std::atomic<bool> i2c_flush;
  std::thread i2c_flush_thread;
  float i2c_flush_array[4];

/// singleton stuff

private:
  static std::unique_ptr<GPIO> _instance;
  GPIO();
  GPIO( const GPIO& )  = delete;
  GPIO( const GPIO&& ) = delete;
public:
  ~GPIO();
  static GPIO& instance();
  static int make_instance();

};

#endif
