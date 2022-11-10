"""

format.py

Python helper function for helping with logging string formatting. This includes
ASCII color code injection. And well as additional formatting to be performed
for logging. As all outputs should be logged through python logging, we
introduce more logging levels to better track all information.

"""
import logging
import logging.handlers
import re
import os
import copy
import traceback
import time
import collections
import textwrap
import json
import argparse
import numpy as np

## Custom logging levels. This should match what is defined the src/logging.cc
logging.CRITICAL = 50
logging.ERROR = 40
logging.WARNING = 30
logging.TRACEBACK = 25  # For trace_back message formatting
logging.INFO = 20  # Generic information on the execution of commands
logging.HW_DEBUG = 15  # For interactive hardware debugging dumps.
logging.INT_INFO = 14  # For interactive message displays (like action prompts)
logging.DEBUG = 10  # For generic debugging message <- Default screen logging level.
logging.CMD_HIST = 5  # The history of the command line interface
logging.MONITOR = 4 # For continuous monitoring stream
logging.NOTSET = 0  # <- Default memory log level

# Getting all string and integer representation of logging levels available.
# Look up from integer value is typically more needed, as the inverse can be
# done with getattr
__all_logging_levels__ = {
    val: k
    for k, val in logging.__dict__.items()
    if k.upper() == k and type(val) == int
}


def make_color_text(message: str, colorcode: int) -> str:
  """Adding ASCII color headers around message string"""
  return f"\033[1;{colorcode:d}m{message}\033[0m"


def RED(message: str) -> str:
  return make_color_text(message, 31)


def GREEN(message: str) -> str:
  return make_color_text(message, 32)


def YELLOW(message: str) -> str:
  return make_color_text(message, 33)


def CYAN(message: str) -> str:
  return make_color_text(message, 36)


def oneline_string(text):
  """
  Simplifying multiline text in python to a single line text in python, which
  also removes the additional whitespaces at the beginning of lines
  """
  return ' '.join(text.split())


def wrapped_string(text, width=120):
  """Reducing the message to a block of text"""
  # Reducing everything to a single whitespace-separated string
  text = oneline_string(text)
  # Wrapping the text to not exceed column width
  lines = textwrap.wrap(text, width=width, break_long_words=False)
  # Adding back the explicit line break characters
  lines = [x.replace('<br>', '\n') for x in lines]
  # Joining everything back into a single string
  return '\n'.join(lines)


def record_timestamp(record):
  """Standard time format for logging record"""
  return time.strftime('%Y-%m-%d@%H:%M:%S', time.localtime(record.created))


def remove_newline(s):
  """
  Removing new-line characters with HTML-style <br> to ensure line-based
  operations can work further down the line
  """
  return s.replace('\n', '<br>')


class FIFOHandler(logging.Handler):
  """
  Class for handling a first-in-first-out in-memory logging cache.

  As we don't expect to flush the log unless explicitly requested by the user,
  here we provide a class that stores the logging records in a
  first-in-first-out list, so that logging information can be retrieve for
  later use. The user should specify a maximum capacity.
  """
  _registered_extras_ = ['table']

  def __init__(self, capacity, level=logging.NOTSET):
    """Creating the FIFOCache provided in cachetools package"""
    super().__init__(level=level)
    self.record_list = collections.deque([], maxlen=capacity)

  def emit(self, record):
    self.record_list.append(record)

  def record_to_dict(self, record):
    """
    Transforming the a logging entry to a dictionary to be used for further
    processing.
    """
    ret_dict = {
        'time': record_timestamp(record),
        'name': record.name,
        'level': __all_logging_levels__[record.levelno],
        'msg': remove_newline(record.msg),
        'args': record.args,
    }
    for extra_keys in self._registered_extras_:
      if hasattr(record, extra_keys):
        ret_dict[extra_keys] = getattr(record, extra_keys)
    return ret_dict

  def dump_lines(self, file_obj, exclude: list[int]):
    """
    Dumping the the record entries to a file in line-based format.
    """
    def line_format(record):
      """
      Making a record into a single line entry. Using triple colons to separate
      between columns
      """
      rec_dict = self.record_to_dict(record)
      # Base information line
      line = '{time}:::{name}:::{level}:::{msg}'.format(**rec_dict)
      if rec_dict['args']:  # For non empty arguments
        line += f':::{remove_newline(str(rec_dict["args"]))}'
      extra_dict = {
          k: v
          for k, v in rec_dict.items()
          if k in self._registered_extras_
      }
      if extra_dict:
        line += f':::{remove_newline(str(extra_dict))}'
      return line

    # Looping over the record instance.
    _ = [
        file_obj.write(line_format(record) + '\n')
        for record in self.record_list
        if __all_logging_levels__[record.levelno] not in exclude
    ]

  def dump_json(self, file_obj, exclude: list[int]):
    """
    Dumping the record entries to a json file.
    """
    json_dict = {
        'dumptime':
        time.strftime('%Y-%m-%d@%H:%M:%S', time.localtime(time.time())),
        'excluded':
        exclude,
        'entries': [
            self.record_to_dict(record)
            for record in self.record_list
            if __all_logging_levels__[record.levelno] not in exclude
        ]
    }
    json.dump(json_dict, file_obj, indent=2)


# Custom output formatter
class CmdStreamFormatter(logging.Formatter):
  """
  @brief Given a logging.Record object, format into a string that should be
  printed on string.

  @details The nominal format would be:

  [level][module] message

  Where the level would be omitted should for level that are lower than WARNING.
  For clarity, if the message is long, then when the line wraps, it should not
  pass wrap after the text-column of the [level][module] part.

  For the message, because it is typically cleaner to simply have a multiline
  with jagged newline in leading spaces in the code when writing a long string,
  by default we will pass the message string through a standard white string
  reduction functions. For these messages, break line characters would need to
  be explicitly defined via an html style "<br>" tag.

  """
  def __init__(self, linewidth=120):
    super().__init__(style='{')
    self.linewidth = linewidth

  def make_header(self, record):
    _level_header_ = {
        logging.ERROR: RED(f'[{"ERROR":7s}]'),
        logging.WARNING: YELLOW(f'[{"WARNING":7s}]'),
        logging.TRACEBACK: YELLOW(f'[{"TRACE":7s}]'),
    }
    #Making the first prefixes
    header = _level_header_.get(record.levelno, '')
    hlen = 7 + 2 if record.levelno in _level_header_.keys() else 0

    # removing the header level logger name
    recname = '.'.join(record.name.split('.')[1:])
    header += CYAN(f'[{recname}] ')
    hlen += len(recname) + 3
    return header, hlen

  def default_message_parse(self, record):
    """Reducing the message to a block of text"""
    return wrapped_string(record.msg, self.linewidth)

  def traceback_message_parse(self, record):
    """
    Formatting of the track stack string to something easier to read.
    """
    exc_msg = record.msg.splitlines()
    exc_msg = exc_msg[1:-1]  ## Remove traceback and error line.
    lines = []
    for idx in range(0, len(exc_msg), 2):
      file = re.findall(r'\"[A-Za-z0-9\/\.]+\"', exc_msg[idx])
      if len(file):  # For non-conventional error messages
        file = file[0].strip().replace('"', '')
        file = file.replace(os.getenv('PWD'), '.')
      else:
        continue

      lno = re.findall(r'line\s[0-9]+', exc_msg[idx])
      if len(lno):  # For non-conventional error messages
        lno = [int(s) for s in lno[0].split() if s.isdigit()][0]
      else:
        continue

      content = exc_msg[idx + 1].strip()
      lines.append(CYAN(f'{lno:4d}L|') + YELLOW(f'{file}| ') + content)
    return '\n'.join(lines)

  def interactive_message_parse(self, record):
    msg = record.msg  # To note make modifications!
    if hasattr(record, 'table'):
      if msg:
        msg += '\n' + self.format_table(record.table)
      else:
        msg = self.format_table(record.table)
    return msg

  def format_table(self, table):
    """
    Converting a nested list-of-list to a pleasant table string.
    """
    ncols = np.max([len(x) for x in table])
    padded_table = list([list(x) + [''] * (ncols - len(x)) for x in table])
    colwidth = np.char.str_len(padded_table)
    colwidth = np.max(colwidth, axis=0)
    lines = []
    for i in range(len(padded_table)):
      line = ''
      for j in range(ncols):
        if j == 0:
          line = GREEN(padded_table[i][j].rjust(colwidth[j] + 2))
        else:
          line += ' ' + padded_table[i][j].ljust(colwidth[j] + 1)
      lines.append(line)
    return '\n'.join(lines)

  def format(self, record):
    """
    Over riding the main format method defined in the formatter class.
    """

    _msg_parser_ = {
        logging.TRACEBACK: self.traceback_message_parse,
        logging.INT_INFO: self.interactive_message_parse
    }

    header, hlen = self.make_header(record)
    msg = _msg_parser_.get(record.levelno, self.default_message_parse)(record)
    # Adding additional spacers for multi-line outputs
    msg = msg.replace('\n', '\n' + ' ' * hlen)
    return header + msg


### Miscellaneous items
class ArgumentParser(argparse.ArgumentParser):
  """
  @brief Thin wrapper for overwriting the 'error' method behavior

  @details Changing the SystemExit error to a ValueError. As the SystemExit is a
  very hard error that needs to be explicitly caught (not caught by simply
  catching 'Exception'), and only contains the exit code not the original error
  message. We also add a prefix to help indicate that this is an error that was
  raise from the ArgumentParser's parsing methods.
  """
  __prefix__ = '[parser_error]'

  def error(self, message):
    raise ValueError(self.__prefix__ + message)
