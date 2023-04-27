#include "logger.hpp"
#include "Python.h"

#include <cstdio>
#include <map>
#include <stdarg.h>
#include <stdexcept>

#ifndef PYTHON_H
#define PYTHON_H
#endif


// Static objects used for logging.
static PyObject* logging_lib = PyImport_ImportModuleNoBlock( "logging" );

/**
 * @brief Wrapping the python.logging modules call into a C function.
 *
 * Function modified from here: https://kalebporter.medium.com/logging-extending-python-with-c-or-c-fa746466b602
 *
 * @param name The name of the logger
 * @param level The info level
 * @param message The message string
 */
static void
logger_wrapped( const std::string& device,
                int                level,
                const std::string& message )
{
  PyObject* logging_name = Py_BuildValue( "s",
                                          ( "SiPMCalibCMD."+device ).c_str()  );
  PyObject* logging_args = Py_BuildValue( "(is)", level, message.c_str() );
  PyObject* logging_obj  = PyObject_CallMethod( logging_lib,
                                                "getLogger",
                                                "O",
                                                logging_name );
  PyObject_CallMethod( logging_obj, "log", "O", logging_args );
  Py_DECREF( logging_name );
  Py_DECREF( logging_args );
}


/**
 * @brief Printing a message on screen with a standard header. This is
 * implemented as a parallel to the update method.
 */
void
printdebug( const std::string& dev, const std::string& msg )
{
  logger_wrapped( dev, 6, msg );
}


/**
 * @brief
 *
 */
void
printinfo( const std::string& dev, const std::string& msg )
{
  logger_wrapped( dev, 20, msg );
}


/**
 * @brief Printing a message on screen with a standard header. This is
 * implemented as a parallel to the update method.
 */
void
printmsg( const std::string& dev, const std::string& msg )
{
  logger_wrapped( dev, 20, msg );
}


/**
 * @brief Printing a message on screen with the standard yellow `[WARNING]`
 * string at the start of the line.
 */
void
printwarn( const std::string& dev, const std::string& msg )
{
  logger_wrapped( dev, 30, msg );
}


std::runtime_error
device_exception( const std::string& dev, const std::string& msg )
{
  return std::runtime_error( msg );
}
