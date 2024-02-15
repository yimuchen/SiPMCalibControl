"""
@file cmdbase.py

@defgroup cli_design CLI Framework

The command line interface is designe daround the python
[`cmd.Cmd`][python-cmd] class: the `ctlcmd.cmdbase.controlterm` class inherits
from the python base class, and expects a list of `ctlcmd.cmdbase.controlcmd`
classes during construction, this allows for a simplified construction of
commands of arbitrary execution complexity while having a reusable framework
for common routines such as command argument parsing with
[`argparse`][python-argparse].

## Framework overview

In vanilla python, the [`cmd`][python-cmd] class implements command as a series
of `do_<cmd>` function, with corresponding, `help_<cmd>` and `complete_<cmd>`
function to manage help message generation and tag-autocomplete with GNU
readline. The [`controlterm`][controlterm] constructs these methods according
to the given list of [`controlcmd`][controlcmd] derived classes, with the
`control.do_<cmd>` method being mapped to the `<cmd>.do` method, and so on. The
`controlterm` class is also responsible for handling the various hardware
interface objects used for system control.

The [`controlcmd`][controlcmd] class further breaks down the `do` method into
common routines: first, the raw `line` string input is process via the
`argparse.ArgumentParser` instance with additional processing performed by the
overloaded `controlcmd.parse` methods. The argument argument is then passed
over to the `run` method for actually running. As many commands for the system
control will have similar/identical argument parsing processes, additional
subclasses have been provided for the argument construction and argument
parsing. To such processing will *always* be performed in the sequence of the
class derivative sequence (order listed in the `__mro__` method)

## Documentation guidelines

For user-level command classes (classes that actually get passed into the
construction of the master `controlterm` object), as the `__doc__` string of
the command classes is used for both the command line help message and the
generation of the user manual, developers should keep just a `@brief`
documentation in the user-level command class's `__doc__` string, more detail
documentation of how the command works should be kept in the dedicated
documentation files, which can also give examples as to how the various command
should be used. This is only true for the class level `__doc__` strings,
however. All *method* `__doc__` string should be kept self contained within the
class. In the same line of though, the help string for the command arguments
should be kept short, and a URL should added to a argument group should the
arguments require a more detailed documentation for advanced features.

For non user-level command classes, we keep in the usual convention that
documentation should be kept close to the implementation, to help with
bookkeeping during development, so use the typical doxygen tag directly in the
class and method  `__doc__` strings.

[python-cmd]: https://docs.python.org/3/library/cmd.html

[python-argparse]:https://docs.python.org/3/library/argparse.html

[controlterm]: @ref ctlcmd.cmdbase.controlterm

[controlcmd]: @ref ctlcmd.cmdbase.controlcmd
"""
from cmod.conditions import Conditions
import cmod.gcoder as gcoder
import cmod.board as board
import cmod.gpio as gpio
import cmod.visual as visual
import cmod.fmt as fmt
import cmod.TBController as tbc
import numpy as np
import cmd
import sys
import os
import argparse
import glob
import re
import datetime
import time
import traceback
import shlex
import select
import enum
import logging
import tqdm
import signal
import uproot
import awkward as ak

# Potentially missing package -- PICO
try:
    import cmod.pico as pico
except (ImportError, ModuleNotFoundError) as err:
    pico = None

# Potentially missing package -- DRS4
try:
    import cmod.drs as drs
except (ImportError, ModuleNotFoundError) as err:
    drs = None


class controlsignalhandle(object):
    """
    Simple class for handling signal termination signals emitted by user input
    (typically CTL+C). In this case, store that the termination signal has been
    requested, and do nothing else, the program should handle how to gracefully
    terminate the current running progress. Solution is taken from:
    https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully
    """

    """
  Storing the original in-built functions defined by python used to handle the
  interrupt and terminate signals.
  """
    ORIGINAL_SIGINT = signal.getsignal(signal.SIGINT)
    ORIGINAL_SIGTERM = signal.getsignal(signal.SIGTERM)

    def __init__(self):
        """
        Here we only provide a boolean flag to track whether an signal has been
        received during the run.
        """
        self.terminate = False
        self.release()
        ## SIG_INT is Ctl+C

    def receive_term(self, signum, frame):
        """When receiving a signal, do nothing other than changing the flag."""
        self.terminate = True

    def reset(self):
        """
        Setting the signal flag to a clean start, and set the function to handle the signal
        to the internal method.
        """
        self.terminate = False
        try:
            signal.signal(signal.SIGINT, self.receive_term)
            signal.signal(signal.SIGTERM, self.receive_term)
        except:
            pass

    def release(self):
        """
        Setting the signal flag to a clean start, also release the signal handling
        function to that used by the python.
        """
        self.terminate = False
        try:
            ## Disabling signal handling by releasing the found function
            signal.signal(signal.SIGINT, SigHandle.ORIGINAL_SIGINT)
            signal.signal(signal.SIGTERM, SigHandle.ORIGINAL_SIGTERM)
        except:
            pass


class controlterm(cmd.Cmd):
    """
    @ingroup cli_design

    @brief Overloading the terminal class.

    @details The master command-line session management class. Which holds:

    - All instances of the interface classes.
    - All instances of the controlcmd classes that will be used to map functions

    During construction, additional methods for this class are automatically
    spawned from the input class methods. As this class is also spawned as the
    control class for GUI interface, there are a couple of book keeping classes to
    keep track of the status of the last executed command.
    """

    doc_block = fmt.wrapped_string(
        """
  For the sake of declutering the interface, documentations of the commands in
  the interface will be kept brief. Go to the official operator manual if you
  are unsure which command/options you should used for you data collection
  needs, check out this link for the online manual
  https://umdcms.github.io/SiPMCalibControl/group__cli.html<br><br>
  """,
        width=100,
    )

    intro = (
        fmt.wrapped_string(
            """<br><br>
  SiPM Calibration Gantry Control System<br>
  - Type help or ? to list commands.<br>
  - Type help <cmd> for the individual help messages of each commands<br><br>
  """
        )
        + doc_block
    )

    doc_header = doc_block + fmt.wrapped_string(
        """<br>Below is a list of commands available to the be used. For the
      detailed arguments available for each command, type "help <cmd>". <br><br>""",
        width=100,
    )  # Trailing empty lines required

    ruler = ""

    prompt = "SiPMCalib> "
    last_status = None
    logname = "SiPMCalibCMD"

    def __init__(self, cmdlist, **base_kwargs):
        """
        @brief Constructing the command line instance from a list of classes that is
        requested.

        @details First the various hardware interface instances are created under for
        this class. Then all provided command classes will have a corresponding
        `do_<cmd>`, `help_<cmd>`, and `complete_<cmd>` methods spawned. As the
        autocomplete method uses the `readline` package, we also augment the readline
        behavior so that we can invoke autocompletion on hyphen-started arguments.
        """
        cmd.Cmd.__init__(self, **base_kwargs)

        # Instances for hardware control
        self.gcoder = gcoder.GCoder.instance()
        self.board = board.Board(self)
        self.conditions = Conditions(self)
        self.visual = visual.Visual()
        self.gpio = gpio.GPIO.instance()
        self.pico = pico.PicoUnit.instance() if pico is not None else None
        self.drs = drs.DRS.instance() if drs is not None else None
        self.tbc = tbc.TBController()

        # Session control
        self.sighandle = controlsignalhandle()

        # Creating logging instances for command line parsing
        self.cmdlog = logging.getLogger(self.logname)
        self.cmdlog.setLevel(logging.NOTSET)

        for com in cmdlist:
            comname = com.__name__.lower()
            dofunc = "do_" + comname
            helpfunc = "help_" + comname
            compfunc = "complete_" + comname
            self.__setattr__(comname, com(self))
            self.__setattr__(dofunc, self.__getattribute__(comname).do)
            self.__setattr__(helpfunc, self.__getattribute__(comname).callhelp)
            self.__setattr__(compfunc, self.__getattribute__(comname).complete)
            self.__getattribute__(comname).cmd = self

        # Modifying readline default behavior:
        import readline

        readline.set_completer_delims(" \t\n`~!@#$%^&*()=+[{]}\\|;:'\",<>?")
        readline.set_history_length(1000)

        self.init_log_format()

    def precmd(self, line):
        """
        @brief routines to run just before executing a command.

        @details Storing the command that is passed to the instance to the logger.
        This will be used to detect in future instances whether the the command line
        session is currently running the command using the in-memory log records, as
        well as help diagnose which function command generated which error message
        in log dumps.
        """
        self.cmdlog.log(logging.CMD_HIST, line, "start")
        return line  # Required for cmd execution.

    def postcmd(self, stop, line):
        """
        @brief routines to run just after executing the command

        @details We log the same command again, this time with the stop flag as well
        as the execution status return code, so that execution status can also be
        determined by looking at log dumps.

        If the command also generates a TERMINATE_SESSION signal, the function
        returns `True` to the base class to terminate the command line loop.
        """
        self.cmdlog.log(logging.CMD_HIST, line, "stop", stop)
        if stop == controlcmd.TERMINATE_SESSION:
            return True

    def get_names(self):
        """
        @brief Overriding the the original get_names command to allow for the dynamic
        introduced commands to be listed in the master help method.
        """
        return dir(self)

    def init_log_format(self):
        """
        @brief Additional settings for the logger instances

        @details Here we set up 2 handlers by default:

        - A stream handler for out-putting logging instances into a informative
          format for be used interactively. The formatting used for different log
          levels can be found in CmdStreamFormatter class.
        - An in-memory handler, which stores up to 65536 logging entries for the
          command line session. This is mainly used for history look up and
          debugging dump log. Here we will attempt to log everything.

        """
        self.out_handle = logging.StreamHandler()
        self.out_handle.setLevel(logging.DEBUG)
        self.out_handle.setFormatter(fmt.CmdStreamFormatter())
        self.mem_handle = fmt.FIFOHandler(65536, level=logging.NOTSET)

        self.cmdlog.addHandler(self.out_handle)
        self.cmdlog.addHandler(self.mem_handle)

    def devlog(self, devname):
        return logging.getLogger(self.logname + "." + devname)


class controlcmd(object):
    """
    @ingroup cli_design

    @brief Base interface for command classes.

    @details The control command is the base interface for defining a command in
    the terminal class, the instance do, callhelp and complete functions
    corresponds to the functions `do_<cmd>`, `help_<cmd>` and `complete_<cmd>`
    functions in the vanilla python cmd class. Here we will be using the argparse
    class by default to call for the help and complete functions. To see how the
    `do_<cmd>` method will be broken down, see the detailed documentation for the
    `do` method of this class.

    One big part of this class the the consistent construction of argument elements
    and the parsing of elements. This is how the creation and parsing of the
    arguments are performed:
    - Arguments will be added in the inverse order listed in the `__mro__` method
      via the `add_args` method that meta-command classes and command classes
      should overload.
    - Arguments will be also be parsed in the order inversely listed in the
      `__mro__` method via the `parse` argument. Because of this, the input args
      object in the `parse` argument in inherited classes should simply assume that
      the `parse` of parent classes' has already been assumed, and should not
      attempt to call the parent class's parse method.

    The `do_cmd` method of the parent cmd instance will be directed to the do
    method of this class, which handles the usual parsing/execution/clean-up flow,
    the method that should be overloaded by the subsequent children classes to
    define the execution routine is now `run`.
    """

    PARSE_ERROR = -1
    EXECUTE_ERROR = -2
    EXIT_SUCCESS = 0
    TERMINATE_SESSION = 1
    TERMINATE_CMD = 2

    _PROGRESS_BAR_CONSTRUCTOR_ = tqdm.tqdm

    @property
    def classname(self):
        return self.__class__.__name__.lower()

    @property
    def description_str(self):
        """
        Making the descriptions string to be display on help calls
        """
        desc_str = self.__class__.__doc__  # Getting the raw doc string.
        desc_str = desc_str.replace("@brief", "")  # Removing doc string

        ## Getting the file used to make the instance:
        file_path = sys.modules[self.__class__.__module__].__file__
        dir_name, file_name = file_path.split("/")[-2:]
        file_name = file_name.split(".")[0]
        __url_prefix = f"https://umdcms.github.io/SiPMCalibControl/"
        link_url = (
            f"{__url_prefix}/class{dir_name}_1_1{file_name}_1_1{self.classname}.html"
        )
        desc_str = desc_str.replace("<help link>", f"More information at {link_url}")
        return desc_str

    def __init__(self, cmdsession):
        """
        @brief Initializing the parser class and creating a reference to the control
        instances.

        @details The argument parser class is initialized with the class name as the
        program name and the class doc string as the description string. This greatly
        reduces the verbosity of writing custom commands. Each command will have
        accession to the cmd session, and by extension, every interface object the
        could potentially be used.
        """
        formatter = lambda prog: argparse.HelpFormatter(prog, width=120)

        self.parser = fmt.ArgumentParser(
            prog=self.classname,
            description=self.description_str,
            add_help=False,
            formatter_class=formatter,
            exit_on_error=False,
        )
        self.cmd = cmdsession  # Reference to the main control objects object.
        self.pbar = None

        # Getting reference to session objects for simpler shorthand
        for embedded_obj in [
            "cmdlog",
            "devlog",  # Logging objects
            "gcoder",
            "visual",
            "pico",
            "drs",
            "gpio",
            "tbc",  # Control objects ,
            "board",
            "sighandle",  # Session management
        ]:
            setattr(self, embedded_obj, getattr(cmdsession, embedded_obj))

        # Running the add arguments methods.
        self.__run_mro_method("add_args")

    def __run_mro_method(self, method, args=None):
        """
        @brief Running some method in inverted __mro__ order,

        @details Notice that the method needs to be explicitly defined for the class
        to be ran, as this avoids doubling running the same methods of child classes
        without new method definition.
        """
        for t in reversed(type(self).__mro__):
            if not hasattr(t, method):
                continue
            if method not in t.__dict__:
                continue  # Needs to be explicitly defined
            if args is None:
                getattr(t, method)(self)
            else:
                args = getattr(t, method)(self, args)
        return args

    def add_args(self):
        """
        @brief Adding arguments to the command.

        @details Method to be overridden for adding additional argument to the
        containing `parser` object. This can be added at any level of subsequently
        defined command classes.
        """
        pass

    def do(self, line):
        """
        @brief Method called by the parent controlterm class.

        @details Execution of the commands is now split up into following steps:

        - Parsing the command line using the standard argparse library, then
          additional parsing routines defined in sub classes. (See the parse_line
          method.)
        - Results of the parsing will passed the run method. This run method is to
          be overloaded be descendent classes.
        - Additional job clean defined by the post_run method will be called.
        - An additional return value will be evaluate execution status.

        For the standard processes, 2 "global" objects will also be initialized and
        handled here:

        - The resetting and closing of the progress bar to displaying loop-based
          execution process along with diagnostic information. The initialization of
          the progress bar instance is done through the `start_pbar` method, and
          should be used for commands that require loop-based operations.
        - A signal handler, so that the command that have a loop based executions
          can get terminated early via interruption signals. Notice that the
          `post_run` method will still be ran in case of interruption, so that
          partial data can still be obtained.
        """

        # Running the argument parsing routine
        try:
            args = self.parser.parse_args(shlex.split(line))
            args = self.__run_mro_method("parse", args)
        except (argparse.ArgumentError, fmt.ArgumentParseError) as err:
            # In-built argparser error
            self.printerr(
                'Argument format error: "'
                + str(err)
                + '"<br>'
                + self.parser.format_usage()
            )
            return controlcmd.PARSE_ERROR
        except fmt.ArgumentValueError as err:
            self.printerr(
                "Argument value error <br>"
                + str(err)
                + "<br>"
                + self.parser.format_usage()
            )
            return controlcmd.PARSE_ERROR
        except Exception as err:
            self.printerr(
                f"Unknown Exception type {type(err)}. Report tracestack to developers"
            )
            self.printtrace(err)
            return controlcmd.PARSE_ERROR

        # Running the main routine
        return_value = controlcmd.EXIT_SUCCESS

        self.sighandle.reset()
        try:
            x = self.run(args)
            if x == controlcmd.TERMINATE_SESSION:
                return_value = x
        except InterruptedError as err:
            self.printtrace(err)
            return_value = controlcmd.TERMINATE_CMD
        except Exception as err:
            self.printtrace(err)
            return_value = controlcmd.EXECUTE_ERROR
        self.sighandle.release()

        # Running the post run routines for clean up.
        try:
            self.__run_mro_method("post_run")
        except Exception as err:
            self.printtrace(err)
            return_value = controlcmd.EXECUTE_ERROR

        if self.pbar:
            self.pbar.close()

        return return_value

    def parse(self, args):
        """
        @brief Method that should be overwritten for additional argument parsing.

        @details Notice that the return of this method must be the augmented argument
        container instance.
        """
        return args

    def run(self, args):
        """
        @brief Method of execution to be overloaded.

        @details Functions that require command specific definitions, should be
        overwritten in the descendent classes
        """
        pass

    def post_run(self):
        """
        @brief Routines to run after the run argument is called.
        """
        pass

    def callhelp(self):
        """
        @brief Printing the help message through the logger instances via the
        ArgumentParser in built functions.
        """
        self.logger.log(fmt.logging.INT_INFO, self.parser.format_help())

    def complete(self, text, line, start_index, end_index):
        """
        @brief Auto completion of the functions.

        @details This function scans the options stored in the parse class and
        returns a string of things to return.

        - text is the word on this cursor is on (excluding tail)
        - line is the full input line string (including command)
        - start_index is the starting index of the word the cursor is at in the line
        - end_index is the position of the cursor in the line
        """
        cmdname = self.classname
        textargs = line[len(cmdname) : start_index].strip().split()
        prevtext = textargs[-1] if len(textargs) else ""
        options = [opt for x in self.parser._actions for opt in x.option_strings]

        def optwithtext():
            if text:
                return [x for x in options if x.startswith(text)]
            return options

        if prevtext in options:
            action = next(
                x for x in self.parser._actions if (prevtext in x.option_strings)
            )
            if type(action.type) == argparse.FileType:
                return controlcmd.globcomp(text)
            if action.nargs == 0:  ## For store_true options
                return optwithtext()
            return [
                "Input type: " + str(action.type),
                "Help: " + fmt.oneline_string(action.help),
            ]
        else:
            return optwithtext()

    @property
    def logger(self):
        """default logger to use is defined by the command name"""
        return self.devlog(self.classname)

    def printmsg(self, text):
        """Printing a newline message using the custom LOG variable."""
        self.logger.info(fmt.oneline_string(text))

    def printerr(self, text):
        """Printing a error message with a standard red "ERROR" header."""
        self.logger.error(fmt.oneline_string(text))

    def printwarn(self, text):
        """Printing a warning message with a standard yellow "WARNING" header."""
        self.logger.warning(fmt.oneline_string(text))

    def printdump(self, text, table):
        self.logger.log(
            fmt.logging.INT_INFO, fmt.oneline_string(text), extra={"table": table}
        )

    def printtrace(self, err):
        """
        @brief Better trackstack printing function.

        @details Using a custom log-level to trigger a unique formatter. Details of
        the formatting can be found in the fmt.CmdStreamFormatter class.
        """
        self.logger.log(logging.TRACEBACK, err)
        self.printerr(str(err))  # Printing the original error for clarity.

    def start_pbar(self, *args, **kwargs):
        """
        @brief Resetting and starting the progress bar for loop-based commands

        @details The inputs of these arguments will be pass directly to the tqdm
        progress bar constructor, so anything options that is compatible with tqdm
        can be used. By default, we set the left-hand description to the command
        name.
        """
        kwargs.setdefault("desc", fmt.GREEN(f"[{self.classname}]"))
        kwargs.setdefault("unit", "steps")
        if self.pbar is not None:
            self.pbar.close()
        self.pbar = self._PROGRESS_BAR_CONSTRUCTOR_(*args, **kwargs)
        self.pbar_data()  # Empty data for the first start
        return self.pbar

    def pbar_data(self, **kwargs):
        """
        @brief Adding information to the progress bar

        @details Adding information to be displayed on the right hand side of the
        tqdm progress bar. This is handled via a dictionary. The default information
        that will be displayed for all progress bars will include:

        - The current coordindate of the gantry system
        - The pulser board low voltage value.
        - Temperature of the pulser board and SiPM board.
        """
        self.pbar.set_postfix(
            {
                "Gantry": "({x:0.1f},{y:0.1f},{z:0.1f})".format(
                    x=self.gcoder.opx, y=self.gcoder.opy, z=self.gcoder.opz
                ),
                "LV": f"{self.gpio.adc_read(2)/1000:5.3f}V",
                "PT": f"{self.gpio.ntc_read(0):4.1f}C",
                "ST": f"{self.gpio.rtd_read(1):4.1f}C",
                **kwargs,
            }
        )

    def check_handle(self):
        """
        @brief Helper function for handling signals.

        Checking the status of the signal handle, raising an exception if a
        termination signal was ever set by the user.
        """
        if self.sighandle.terminate:
            if self.pbar:
                self.pbar.close()
            raise InterruptedError("TERMINATION SIGNAL")

    def move_gantry(self, x, y, z):
        """
        @brief Wrapper for gantry motion to be called by children method.

        @details Suppresses the exception raised for in case that the gantry isn't
        connected so that one can test with pre-defined models. Notice that the
        stepper motor disable will not be handled here, as it should only be disabled
        for readout. See the readoutcmd class to see how the readout handles the
        motor disabling routine.
        """
        try:
            # Try to move the gantry. Even if it fails there will be fail safes
            # in other classes
            self.gcoder.moveto(x, y, z)
            while self.gcoder.in_motion(x, y, z):
                self.check_handle()  # Allowing for interuption
                time.sleep(0.01)  ## Updating position in 0.01 second increments
        except Exception as e:
            # Setting internal coordinates to the designated position anyway.
            self.gcoder.opx = x
            self.gcoder.opy = y
            self.gcoder.opz = z
            self.gcoder.cx = x
            self.gcoder.cy = y
            self.gcoder.cz = z
            pass

    def prompt_input(self, message, allowed=None) -> str:
        """Thin wrapper for prompt input of the main controlterm method"""
        return self.cmd.prompt_input(self.classname, message, allowed)

    @staticmethod
    def globcomp(text):
        """Helper function for getting globbed files for autocompletion"""
        globlist = glob.glob(text + "*")
        globlist = [file + "/" if os.path.isdir(file) else file for file in globlist]
        return globlist


class singlexycmd(controlcmd):
    """
    @ingroup cli_design

    @brief Commands that require the motion around a single x-y position.

    @details Commands derived from this class can have x-y coordinates specified
    via 2 methods:
    - Raw x,y values (via the `-x`, and `-y` values) If this is the case, no
      additional parsing is performed.
    - Specifying a detector ID that is specified in the loaded board layout
      (assuming it exists). In this case the board will look up the coordinates in
      the following sequence:
      - If the `VISUAL_OFFSET` flag is set to `False`, we first look if a
        luminosity alignment exists for the specified detector, and use that
        coordinate if it does, if not, then see if a visual alignment exists and
        add the visual/lumi horizontal offset. If neither exists, simply load the
        original uncalibrated coordinates specified in the original board layout.
      - If the `VISUAL_OFFSET` flag is set to `True`, then the look up sequence is
        swapped to first find the visual alignment coordinates, then some
        luminosity alignment coordinates, then the default coordinates (the
        addition of the visual/lumi offset value is also swapped.)

    For more details on how the parsing is handled, see that method documentation
    of the `ctlcmd.cmdbase.singlexycmd.parse` method.
    """

    VISUAL_OFFSET = False
    DEFAULT_XOFFSET = -35
    DEFAULT_YOFFSET = 0

    def __init__(self, cmd):
        controlcmd.__init__(self, cmd)
