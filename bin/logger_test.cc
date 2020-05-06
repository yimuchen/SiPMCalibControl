#include "logger.hpp"
#include <stdio.h>

int main()
{
  printmsg( "this is a test" );
  printmsg( "Hello world" );

  FILE* file = fopen( "test.txt", "w" );
  setloggingdescriptor( file->_fileno );
  printmsg( "this is a test" );
  printmsg( "Hello world" );

  setloggingdescriptor( stdout->_fileno );
  printmsg( "this is test2" );
  printmsg( "Hello world!!" );

  setloggingdescriptor( file->_fileno );
  printmsg( "this is a test3" );
  printmsg( "Hello world!!!!" );
}
