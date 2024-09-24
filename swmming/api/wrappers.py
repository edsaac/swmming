import ctypes
import platform
import datetime

_lib = None
_platform = platform.system()
path_to_libswmm5 = "/usr/local/lib/libswmm5.so"

if _platform == "Linux":
    # .:TODO: Automatically check other locations
    _lib = ctypes.CDLL(path_to_libswmm5)

elif _platform == "Windows":
    _lib = ctypes.WinDLL(R".\swmm5.dll")

else:
    raise BaseException("Platform " + _platform + " unsupported")


def get_version() -> str:
    """Retrieves version number of current SWMM engine which
    uses a format of xyzzz where x = major version number,
    y = minor version number, and zzz = build number.

    Returns
    -------
    str
        SWMM engine version number

    C Signature
    -----------
    int    DLLEXPORT swmm_getVersion(void);

    Notes
    -----
    Each new release should be updated in `consts.h`

    """
    return str(_lib.swmm_getVersion())


def run_swmm(
    input_file: str,
    report_file: str,
    output_file: str = "",
):
    """Runs a SWMM simulation.

    Parameters
    ----------
    input_file : str
        Name of input file
    report_file : str
        Name of report file
    output_file : str = ""
        Name of binary output file, by default ""

    Returns
    -------
    int
        Error code

    C Signature
    -----------
    int swmm_run(const char *f1, const char *f2, const char *f3);
    """

    return _lib.swmm_run(
        ctypes.c_char_p(input_file.encode()),
        ctypes.c_char_p(report_file.encode()),
        ctypes.c_char_p(output_file.encode()),
    )


def open_swmm(
    input_file: str,
    report_file: str,
    output_file: str = "",
):
    """Opens a SWMM project.

    Parameters
    ----------
    input_file : str
        Name of input file
    report_file : str
        Name of report file
    output_file : str = ""
        Name of binary output file, by default ""

    Returns
    -------
    int
        Error code

    C Signature
    -----------
    int DLLEXPORT swmm_open(const char *f1, const char *f2, const char *f3);
    """

    return _lib.swmm_open(
        ctypes.c_char_p(input_file.encode()),
        ctypes.c_char_p(report_file.encode()),
        ctypes.c_char_p(output_file.encode()),
    )


def start_swmm(save_flag: bool):
    """Starts a SWMM simulation.

    Parameters
    ----------
    save_flag : bool
        True if simulation results saved to binary file

    Returns
    -------
    int
        Error code

    C Signature
    -----------
    int    DLLEXPORT swmm_start(int saveFlag);

    """
    return _lib.swmm_start(ctypes.c_int(save_flag))


def step_swmm():
    """
    Advances the simulation by one routing time step.

    Returns
    -------
    int
        Updated value of elapsedTime, or error code

    C Signature
    -----------
    int    DLLEXPORT swmm_step(double *elapsedTime);
    """

    elapsed_time = ctypes.c_double()
    _lib.swmm_step(ctypes.byref(elapsed_time))
    return elapsed_time.value


def stride_swmm(strideStep: int):
    """
    Advances the simulation by a fixed number of seconds.

    Parameters
    ----------
    strideStep : int
        Number of seconds to advance the simulation

    Returns
    -------
    int
        Updated value of elapsedTime, or error code

    C Signature
    -----------
    int    DLLEXPORT swmm_stride(int strideStep, double *elapsedTime);
    """

    elapsed_time = ctypes.c_double()
    _lib.swmm_stride(ctypes.c_int(strideStep), ctypes.byref(elapsed_time))
    return elapsed_time.value


def end_swmm():
    """
    Ends a SWMM simulation.

    Returns
    -------
    int
        Error code

    C Signature
    -----------
    int    DLLEXPORT swmm_end(void);
    """

    _lib.swmm_end()


def get_mass_balance_errors():
    """Reports a simulation's mass balance errors.

    Returns
    -------
    tuple(float, float, float)
        - runoff mass balance error (percent)
        - flow routing mass balance error (percent)
        - quality routing mass balance error (percent)

    C Signature
    -----------
    int    DLLEXPORT swmm_getMassBalErr(float *runoffErr, float *flowErr, float *qualErr);
    """
    runoff = ctypes.c_float()
    flow = ctypes.c_float()
    qual = ctypes.c_float()

    _lib.swmm_getMassBalErr(
        ctypes.byref(runoff),
        ctypes.byref(flow),
        ctypes.byref(qual),
    )

    return runoff.value, flow.value, qual.value


def report_swmm():
    """Writes simulation results to the report file.

    Returns
    -------
    int
        Error code

    C Signature
    -----------
    int    DLLEXPORT swmm_report(void);
    """
    return _lib.swmm_report()


def close_swmm():
    """Closes a SWMM project.

    Returns
    -------
    int
        Error code

    C Signature
    -----------
    int    DLLEXPORT swmm_close(void);
    """
    _lib.swmm_close()


def get_number_of_warnings():
    """Retrieves number of warning messages issued during an analysis.

    Returns
    -------
    int
        Number of warning messages issued

    C Signature
    -----------
    int    DLLEXPORT swmm_getWarnings(void);
    """
    return _lib.swmm_getWarnings()


def get_error_message():
    """
    Retrieves the code number and text of the error condition that
    caused SWMM to abort its analysis.

    Returns
    -------
    str
        Error message

    C Signature
    -----------
    int    DLLEXPORT swmm_getError(char *errMsg, int msgLen);
    """
    _message_lenght = 240
    error_message = ctypes.create_string_buffer(_message_lenght)

    _lib.swmm_getError(
        ctypes.byref(error_message),
        ctypes.c_int(_message_lenght),
    )

    return error_message.value.decode()


def get_count_of(objtype: int):
    """Retrieves the number of objects of a specific type.

    Parameters
    ----------
    objtype : int
        A type of SWMM object.
        .:TODO: Add support for Python swmming objects

    Returns
    -------
    int
        Number of objects

    C Signature
    -----------
    int    DLLEXPORT swmm_getCount(int objType);
    """

    return _lib.swmm_getCount(ctypes.c_int(objtype))


def get_name_of(objtype: int, index: int):
    """Retrieves the ID name of an object.

    Parameters
    ----------
    objtype : int
        A type of SWMM object
    index : int
        The object's index in the array of objects

    Returns
    -------
    str
        The object's ID name

    C Signature
    -----------
    int    DLLEXPORT swmm_getName(int objType, int index, char *name, int size);
    """
    _name_lenght = 240
    name = ctypes.create_string_buffer(_name_lenght)

    _lib.swmm_getName(
        ctypes.c_int(objtype),
        ctypes.c_int(index),
        ctypes.byref(name),
        ctypes.c_int(_name_lenght),
    )
    return name.value.decode()


def get_index_of(objtype: int, name: str):
    """Retrieves the index of a named object.

    Parameters
    ----------
    objtype : int
        A type of SWMM object
        .:TODO: Add support for Python swmming objects
    name : str
        The object's ID name

    Returns
    -------
    int
        The object's position in the array of like objects

    Notes
    -----
    - -1 if object type is invalid not found

    C Signature
    -----------
    int    DLLEXPORT swmm_getIndex(int objType, const char *name);
    """

    return _lib.swmm_getIndex(
        ctypes.c_int(objtype),
        ctypes.c_char_p(name.encode()),
    )


def get_value_of(property: int, index: int):
    """Retrieves the value of an object's property.

    Parameters
    ----------
    property : int
        An object's property code
    index : int
        The object's index in the array of like objects

    Returns
    -------
    float
        The property's current value

    C Signature
    -----------
    double DLLEXPORT swmm_getValue(int property, int index);
    """

    _lib.swmm_getValue.restype = ctypes.c_double
    return _lib.swmm_getValue(
        ctypes.c_int(property),
        ctypes.c_int(index),
    )


def get_saved_value_of(property: int, index: int, period: int):
    """Retrieves an object's computed value at a specific reporting time period.

    Parameters
    ----------
    property : int
        An object's property code
    index : int
        The object's index in the array of like objects
    period : int
        A reporting time period (starting from 1)

    Returns
    -------
    float
        The property's saved value

    C Signature
    -----------
    double DLLEXPORT swmm_getSavedValue(int property, int index, int period);
    """

    _lib.swmm_getSavedValue.restype = ctypes.c_double
    return _lib.swmm_getSavedValue(
        ctypes.c_int(property), ctypes.c_int(index), ctypes.c_int(period)
    )


def set_value_of(property, index, value):
    """Sets the value of an object's property.

    Parameters
    ----------
    property : int
        An object's property code
    index : int
        The object's index in the array of like objects
    value : float
        The property's new value

    C Signature
    -----------
    void   DLLEXPORT swmm_setValue(int property, int index, double value);
    """

    _lib.swmm_setValue(
        ctypes.c_int(property),
        ctypes.c_int(index),
        ctypes.c_double(value),
    )


def writeLine(line: str):
    """Writes a line of text to the report file.

    Parameters
    ----------
    line : str
        A character string

    C Signature
    -----------
    void   DLLEXPORT swmm_writeLine(const char *line);
    """

    _lib.swmm_writeLine(ctypes.c_char_p(line.encode()))


def decodeDate(date):
    """Decodes a SWMM DateTime value to a Python DateTime value."""
    """  Use Python's datetime.weekday()  method to get day of week """
    """  (where Monday = 0 and Sunday = 6) if needed. """

    year = ctypes.c_int()
    month = ctypes.c_int()
    day = ctypes.c_int()
    hour = ctypes.c_int()
    minute = ctypes.c_int()
    second = ctypes.c_int()
    dayofweek = ctypes.c_int()
    _lib.swmm_decodeDate(
        ctypes.c_double(date),
        ctypes.byref(year),
        ctypes.byref(month),
        ctypes.byref(day),
        ctypes.byref(hour),
        ctypes.byref(minute),
        ctypes.byref(second),
        ctypes.byref(dayofweek),
    )
    d = datetime.datetime(
        year.value, month.value, day.value, hour.value, minute.value, second.value
    )
    return d
