#include "logger.hpp"
#include "Python.h"

#include <cstdio>
#include <map>
#include <stdexcept>

#ifndef PYTHON_H
#define PYTHON_H
#endif


// Static flags to be mapped to python logging package
static const int DEBUG    = 10;
static const int INFO     = 20;
static const int WARNING  = 30;
static const int ERROR    = 40;
static const int CRITICAL = 50;

// Static objects used for logging.
static PyObject* logging_lib  = PyImport_ImportModuleNoBlock( "logging" );
static PyObject* logging_name = Py_BuildValue( "s", "devlog" );
static PyObject* logging_obj  = PyObject_CallMethod( logging_lib,
                                                     "getLogger",
                                                     "O",
                                                     logging_name );

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
logger_wrapped( int level, const char* message )
{
  // Log Accordingly
  const char* logging_level = level == DEBUG ?
                              "debug" :
                              level == INFO ?
                              "info" :
                              level == WARNING ?
                              "warning" :
                              level == ERROR ?
                              "error" :
                              level == CRITICAL ?
                              "critical" :
                              "";
  PyObject* logging_str    = Py_BuildValue( "s", message ); // Build the Logger Object
  PyObject_CallMethod( logging_obj, logging_level, "O", logging_str );
  Py_DECREF( logging_str );
}


static std::string
device_format( const std::string& device, const std::string & message )
{
  return "[["+device+"]] "+message;
}


/**
 * @brief Printing a message on screen with a standard header. This is
 * implemented as a parallel to the update method.
 */
void
printdebug( const std::string& dev, const std::string& msg )
{
  logger_wrapped( DEBUG, device_format( dev, msg ).c_str() );
}


/**
 * @brief Printing a message on screen with a standard header. This is
 * implemented as a parallel to the update method.
 */
void
printmsg( const std::string& dev, const std::string& msg )
{
  logger_wrapped( INFO, device_format( dev, msg ).c_str() );
}


/**
 * @brief Printing a message on screen with the standard yellow `[WARNING]`
 * string at the start of the line.
 */
void
printwarn( const std::string& dev, const std::string& msg )
{
  logger_wrapped( WARNING, device_format( dev, msg ).c_str() );
}


std::runtime_error
device_exception( const std::string& dev, const std::string& msg )
{
  return std::runtime_error( device_format( dev, msg ) );
}
