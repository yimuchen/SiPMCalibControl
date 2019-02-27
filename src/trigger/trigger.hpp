// Direct GPIO control from
// https://elinux.org/RPi_GPIO_Code_Samples#Direct_register_access


class Trigger
{
private:
  volatile unsigned* gpio;

public:
  Trigger();
  ~Trigger();

  void Pulse( const unsigned );
  void Init();

private:
  // GPIO setup macros. Always use INP_GPIO(x) before using OUT_GPIO(x)
  // or SET_GPIO_ALT(x,y)
  inline void
  input_gpio( const int g )
  { *( gpio+( ( g )/10 ) ) &= ~( 7<<( ( ( g )%10 )*3 ) ); }

  inline void
  out_gpio( const int g )
  { *( gpio+( ( g )/10 ) ) |= ( 1<<( ( ( g )%10 )*3 ) ); }

  inline int
  set_gpio_alt( const int g, const int a )
  { return *( gpio+( ( ( g )/10 ) ) ) |= ( ( ( a ) <= 3 ? ( a )+4 : ( a ) == 4 ? 3 : 2 )<<( ( ( g )%10 )*3 ) ); }

  inline void
  gpio_set( const int g ){ *( gpio+7 ) = 1 << g;}
  // sets   bits which are 1 ignores bits which are 0
  inline void
  gpio_clear( const int g ){ *( gpio+10 ) = 1 << g; }
  // clears bits which are 1 ignores bits which are 0

  inline int
  get_gpio( const int g ){ return *( gpio+13 )&( 1<<g ); }
  // 0 if LOW, (1<<g) if HIGH

  inline int
  gpio_pull(){ return *( gpio+37 ); }// Pull up/pull down

  inline int
  gpio_pullclock0(){ return *( gpio+38 );}// Pull up/pull down clock
};
