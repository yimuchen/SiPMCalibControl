"""
@file TBController.py
"""
import zmq, yaml, time, copy, uproot, os
import awkward as ak
from .rocv2 import from_raw

from typing import Mapping, List, Optional, Tuple


def _deep_merge_(dest: Mapping, update: Mapping, path=Optional[List[str]]):
    """
    Updating a deeply nested dictionary-like object "dest" in-place using an
    update dictionary. Adapted from this [response][response] on StackOverflow,
    except at because YAML configurations are not strictly dictionaries, we
    change the method of detecting nested structure to anything having the
    `__getitem__` method.

    [response]:
    https://stackoverflow.com/questions/7204805/how-to-merge-dictionaries-of-dictionaries/7205107#7205107
    """
    if path is None:  # Leaving default argument as empty mutable is dangerous!
        path = []
    for key in update:
        if key in dest:
            dest_is_nested = hasattr(dest[key], "__getitem__")
            up_is_nested = hasattr(update[key], "__getitem__")
            if dest_is_nested and up_is_nested:
                # If both are nested recursively update nested structure
                _deep_merge_(dest[key], update[key], path + [str(key)])
            elif not dest_is_nested and not up_is_nested:
                # If neither are nested update value directory
                dest[key] = update[key]
            else:
                # Otherwise there is a structure mismatch
                raise ValueError(
                    "Mismatch structure at %s".format(".".join(path + [str(key)]))
                )
        else:
            dest[key] = update[key]
    return dest


def _make_deep_(*args):
    """
    @brief Short hand function for making a deeply nested dictionary entry

    @details As YAML configurations are typically represented as nested
    dictionary entries, to set a single parameter configuration will be very
    verbose to declare in vanilla python, like  `{'a': {'b':{'c':{'d':v}}}}`,
    which is difficult to read and format using typical tools. This method takes
    arbitrary number of arguments, with all entries except for the last to be
    used as a key to a dictionary. So the example given above would be declared
    using this function as `make_deep('a','b','c','d', v)`
    """
    if len(args) == 1:
        return args[0]
    else:
        return {args[0]: TBController.make_deep(*args[1:])}


def update_yaml_node(yaml_node, mapping_dict, **kwargs):
    """
    @brief Simplified interface for updating a YAML node

    @details Short hand method for updating a YAML node using keyword arguments.
    The input expects the YAML key as the key for the mapping_dict key, while
    the value of the mapping_dict should be a length 2 tuple, with the first
    entry being the corresponding kwargs string-key, while the second entry is
    the default value to use should the keyword argument not be explicitly set.
    """
    for key, value in mapping_dict.items():
        yaml_node[key] = kwargs.get(value[0], value[1])


class ZMQController:
    """
    @brief Common ZQM client class with YAML configurations
    """

    def __init__(self, ip: str, port: int, yaml_config=str):
        """Storing to allow for reconnection"""
        self.ip = ip
        self.port = port
        self.socket = None

        self.load_config(yaml_config)
        self.reconnect()

    def load_config(self, yaml_config):
        with open(yaml_config) as fin:
            self.yaml_config = yaml.safe_load(fin)

    def reconnect(self):
        if self.socket is not None:
            self.socket.close()

        self.socket = zmq.Context().socket(zmq.REQ)
        self.socket.connect("tcp://" + str(self.ip) + ":" + str(self.port))
        print("Socket connected!!")

    def send_request(self, message: str) -> str:
        """
        Simple ZMQ request/respond pattern used in the subsequent classes.
        """
        self.socket.send_string(message)
        return self.socket.recv()

    def check_request(self, message: str, check_str: str) -> bool:
        """
        Checking the response string return by request contains check_str.
        """
        # Using the str.find method (return -1 if substring was not found)
        return self.send_request(message).decode().lower().find(check_str.lower()) >= 0

    def configure(self, yaml_config: Optional[dict] = None) -> str:
        """
        Sending current yaml config string to socket connection. The return
        function will be the results of sending the configuration.

        Notice that if no YAML fragment is specified, then the entire
        configuration stored in the class instance is sent (this is potentially
        slow!). If a YAML configuration fragment is specified, then the
        configuration updated in the main configuration instances as well.
        """
        if not self.socket_check("configure", "ready"):
            raise RuntimeError("Socket is not ready for configuration!")

        if yaml_config is None:
            yaml_config = self.yaml_config
        else:
            _deep_merge_(self.yaml_config, yaml_config)
        return self.send_request(yaml.dump(yaml_config))


class I2CController(ZMQController):
    """
    @ingroup hardware

    @brief Specialized ZMQController class for I2C slow controls
    """

    _passthrough_ = {}  # name: (ret_type, arg_names, )

    def _define_i2c_method_(method_name: str, arg_names: Tuple[str], return_type=str):
        """
        A typical pattern for either getting or setting I2C values is done by
        sending the a "set/read_<target> <val1> <val2>" request string to the
        I2C server, where values indicate the target channel/sub-channels or
        user input values. Here we provide a simple interface to generate the
        expression of interest.

        When defining a method, the arg_names tuple indicating the number of
        arguments that is expected should also be provided so that
        """

        def __inner_call__(self, *args):
            assert len(args) == len(arg_names), f"Expected arguments {arg_names}"
            return return_type(
                self.send_request(" ".join([method_name, *[str(x) for x in args]]))
            )

        setattr(I2CController, method_name, __inner_call__)

    def __init__(self, ip, port, yaml_config):
        # """Additional attribute: Masking by detector ID"""
        super().__init__(ip, port, yaml_config)
        # Not sure when this is needed. not adding for the time being.

        # Defining additional methods to be used
        I2CController._define_i2c_method_("read_sipm_voltage", (), float)
        I2CController._define_i2c_method_("read_sipm_current", (), float)
        I2CController._define_i2c_method_("read_led_voltage", (), float)
        I2CController._define_i2c_method_("read_led_current", (), float)
        I2CController._define_i2c_method_("set_led_dac", ("val"))
        I2CController._define_i2c_method_("set_gbtsca_dac", ("dac", "val"))
        I2CController._define_i2c_method_("read_gbtsca_dac", ("dac"), float)
        I2CController._define_i2c_method_("read_gbtsca_adc", ("channel"), int)
        I2CController._define_i2c_method_("read_gbtsca_gpio", (), str)
        I2CController._define_i2c_method_("set_gbtsca_gpio_direction", ("direction"))
        I2CController._define_i2c_method_("get_gbtsca_gpio_direction", (), str)
        I2CController._define_i2c_method_("set_gbtsca_gpio_vals", ("vals", "mask"))

        # self.maskedDetIds = []

    def reconnect(self):
        """
        Aside from the nominal routine, we also flush the current configuration
        into to the I2C server for completeness, as well as perform additional
        actions to set up the slow control IO directions.
        """
        super().reconnect()

        if not self.check_request("initialize", "ready"):
            raise RuntimeError(
                """
                I2C server did receive a ready signal! Make sure the I2C slow
                control server has been started without error on the
                tileboard"""
            )
        self.send_request(yaml.dump(self.yaml_config))

        ## GPIO Settings
        self.set_gbtsca_gpio_direction(0x0FFFFF9C)  # '0': input, '1': output

        # enable (1) MPPC_BIAS1 (GPIO20), disable (0) MPPC_BIAS2 (GPIO21)
        self.set_gbtsca_gpio_vals(0x01 << 20, 0x11 << 20)

        # global enable LED system: LED_ON_OFF ('1': LED system ON), GPIO7:
        self.set_gbtsca_gpio_vals(0x1 << 7, 0x1 << 7)

        # put LED_DISABLE1 and LED_DISABLE2 to '0' ('0': LED system ON), GPIOs 8-15
        self.set_gbtsca_gpio_vals(0x00000000, 0b11111111 << 8)

    def reset_tdc(self):
        """Resetting the TDC settings"""
        return yaml.safe_load(self.send_request("resettdc"))

    """
    More human readable formats for ADC value
    """

    def MPPC_Bias(self, channel=1) -> float:
        """Reading out the SiPM bias voltage in units of Volts"""
        adc_val = self.read_gbtsca_adc(9 if channel == 1 else 10)
        # Additional multiplier for resistor divider changes between different in
        # tileboard version TODO: update when TB version 2 or version 3 is received.
        ad_mult = (82.0 / 1.0) / (200.0 / 4.0)
        return float(adc_val) / 4095 * 204000 / 4000 * ad_mult


class DAQController(ZMQController):
    """
    @ingroup hardware

    @brief Specialization for the fast control and readout socket instances.

    @details Mainly for abstracting fast control settings to a human friendly
    function call.
    """

    def start(self):
        """Starting a config file control sequence"""
        while not self.check_request("start", "running"):
            time.sleep(0.1)

    def is_complete(self):
        """Checking whether then run sequence is complete"""
        return not self.check_request("run_done", "notdone")

    def stop(self):
        """Ensuring the the signal has been stopped"""
        return self.socket_send("stop")

    def enable_fast_commands(self, **kwargs):
        """Setting up the fast acquisition settings"""
        _defaults_ = {
            "periodic_l1a_A": ("A", 0),
            "periodic_l1a_B": ("B", 0),
            "periodic_l1a_C": ("C", 0),
            "periodic_l1a_D": ("D", 0),
            "random_l1a": ("random", 0),
            "external_l1a": ("external", 0),
            "block_sequencer": ("sequencer", 0),
            "periodic_ancillary": ("ancillary", 0),
        }
        update_yaml_node(self.yaml_config["daq"]["l1a_enables"], _defaults_, **kwargs)

    def l1a_generator_settings(self, name, **kwargs):
        """Setting up L1 acquisition generator"""
        _defaults_ = {
            "BX": ("BX", 0x10),
            "length": ("length", 43),
            "type": ("cmdtype", "L1A"),
            "prescale": ("prescale", 0),
            "followMode": ("followMode", "DISABLE"),
        }

        for gen in self.yaml_config["daq"]["l1a_generator_settings"]:
            if gen["name"] == name:
                update_yaml_node(gen, _defaults_, **kwargs)

    def l1a_settings(self, **kwargs):
        """Updating the L1 acquisition information"""
        _defaults_ = {
            "bx_spacing": ("bx_spacing", 43),
            "external_debounced": ("external_debounced", 0),
            "length": ("length", 43),
            "ext_delay": ("ext_delay", 0),
            "prescale": ("prescale", 0),
            "log_rand_bx_period": ("log_rand_bx_period", 0),
        }
        update_yaml_node(self.yaml_config["daq"]["l1a_settings"], _defaults, **kwargs)


def make_default_clients(
    tbt_ip: str,
    cli_ip: str = "localhost",
    daq_port: int = 6000,
    cli_port: int = 6001,
    i2c_port: int = 5555,
    config_file: str = "cfg/tbc_yaml/roc_config.yaml",
):
    """Default construction of the daq/cli/i2c zmq client triplet"""
    daq_client = DAQController(tbt_ip, daq_port, config_file)
    cli_client = DAQController(cli_ip, cli_port, config_file)
    i2c_client = I2CController(tbt_ip, i2c_port, config_file)

    cli_client.yaml_config["global"]["serverIP"] = self.daq_socket.ip
    return daq_client, cli_client, i2c_client


def run_daq(daq_client, cli_client, n_events):
    """
    @brief Acquiring n_events worth of data.

    @details Flushing the data puller configurations to the zmq-client instance.
    We split this into a separate function in case we need to run multiple data
    acquisition routines with different slow settings (frequently used for
    configuration scanning routines.)
    """
    # Number of events is set by the the daq_socket yaml configuration
    daq_client.yaml_config["daq"]["NEvents"] = str(n_events)
    # Additional settings for the client
    remote_dir = "/tmp/"
    remote_name = "data_acquire"

    cli_client.yaml_config["global"]["outputDirectory"] = remote_dir
    cli_client.yaml_config["global"]["run_type"] = remote_name

    cli_client.configure()
    daq_client.configure()

    cli_client.start()
    daq_client.start()
    while not daq_client.is_complete():
        time.sleep(0.01)
    daq_client.stop()
    cli_client.stop()

    time.sleep(0.1)  # Sleep 100ms for output to be complete
    return from_raw(f"{remote_dir}/{remote_name}0.raw")


# Unit test of Tileboard controller.
# Using a mock pedestal run as an example.
def test1():
    tbc = TBController()
    # Obtain these numbers from the server start up instance.
    tbc.init(
        "10.42.0.63",
        daq_port=6000,
        cli_port=6001,
        i2c_port=5555,
        config_file="cfg/tbc_yaml/roc_config_ConvGain4.yaml",
    )

    print(tbc.i2c_socket.MPPC_Bias())

    # Additional settings for the data acquisition fast controls
    tbc.daq_socket.enable_fast_commands(random=1)
    tbc.daq_socket.l1a_settings(bx_spacing=45)
    #
    arr = ak.concatenate([tbc.acquire(1000), tbc.acquire(1000)])

    print(arr[0:10].to_list())
    print(len(arr))


if __name__ == "__main__":
    test1()
