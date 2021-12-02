#ifndef SINGLETON_HPP
#define SINGLETON_HPP

#include <memory>

#define DECLARE_SINGLETON( MYCLASS )                      \
private:                                                  \
  static std::unique_ptr<MYCLASS> _instance;              \
  MYCLASS();                                              \
  MYCLASS( const MYCLASS& )   = delete;                   \
  MYCLASS( const MYCLASS && ) = delete;                   \
public:                                                   \
  ~MYCLASS();                                             \
  inline static MYCLASS& instance(){ return *_instance; } \
  static int make_instance();

#define IMPLEMENT_SINGLETON( MYCLASS )                   \
  std::unique_ptr<MYCLASS> MYCLASS::_instance = nullptr; \
  int                                                    \
  MYCLASS::make_instance()                               \
  {                                                      \
    if( _instance == nullptr ){                          \
      _instance.reset( new MYCLASS() );                  \
    }                                                    \
    return 0;                                            \
  }                                                      \
  static const int __make_instance_call = MYCLASS::make_instance();

#endif
