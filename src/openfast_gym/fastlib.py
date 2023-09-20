from os import path
import os
from typing import List, Tuple
import numpy as np
import math
import time
import logging
import win32api
import win32con

from ctypes import (
    CDLL,
    POINTER,
    create_string_buffer,
    byref,
    c_int,
    c_double,
    c_float,
    c_char,
    c_bool,
    RTLD_GLOBAL
)

IntfStrLen = 1025    # FAST_Library global
NumFixedOutputs = 11
NumFixedInputs = 51  # FAST_Library global
MAXInitINPUTS = 53  # From FAST_SFunc.c


class FastLib(CDLL):
    def __init__(self, libraryPath, inputFileName, max_time):
        print(libraryPath)
        dll_handle = win32api.LoadLibraryEx(libraryPath, 0, win32con.LOAD_WITH_ALTERED_SEARCH_PATH)
        super().__init__(libraryPath,handle=dll_handle)

        self.inputFileName = create_string_buffer(
            os.path.abspath(inputFileName).encode('utf-8'))
        self.myTmax = c_double(max_time)

        self.initialize_routines()
        self.fast_init()

        ###################### LIBRARY FUNCTIONS ############################
    def initialize_routines(self) -> None:
        self.FAST_AllocateTurbines.argtypes = [
            POINTER(c_int),
            POINTER(c_int),
            POINTER(c_char)
        ]
        self.FAST_AllocateTurbines.restype = c_int

        self.FAST_Sizes.argtype = [
            POINTER(c_int),         # iTurb IN
            POINTER(c_char),        # InputFileName_c IN
            POINTER(c_int),         # AbortErrLev_c OUT
            POINTER(c_int),         # NumOuts_c OUT
            POINTER(c_double),      # dt_c OUT
            POINTER(c_double),      # dt_out_c OUT
            POINTER(c_double),      # tmax_c OUT
            POINTER(c_int),         # ErrStat_c OUT
            POINTER(c_char),        # ErrMsg_c OUT
            POINTER(c_char),        # ChannelNames_c OUT
            POINTER(c_double),      # TMax OPTIONAL IN
            POINTER(c_double)       # InitInpAry OPTIONAL IN
        ]
        self.FAST_Sizes.restype = c_int

        self.FAST_Start.argtype = [
            POINTER(c_int),         # iTurb IN
            POINTER(c_int),         # NumInputs_c IN
            POINTER(c_int),         # NumOutputs_c IN
            POINTER(c_double),      # InputAry IN
            POINTER(c_double),      # OutputAry OUT
            POINTER(c_int),         # ErrStat_c OUT
            POINTER(c_char)         # ErrMsg_c OUT
        ]
        self.FAST_Start.restype = c_int

        self.FAST_Update.argtype = [
            POINTER(c_int),         # iTurb IN
            POINTER(c_int),         # NumInputs_c IN
            POINTER(c_int),         # NumOutputs_c IN
            POINTER(c_double),      # InputAry IN
            POINTER(c_double),      # OutputAry OUT
            POINTER(c_bool),        # EndSimulationEarly OUT
            POINTER(c_int),         # ErrStat_c OUT
            POINTER(c_char)         # ErrMsg_c OUT
        ]
        self.FAST_Update.restype = c_int

        self.FAST_DeallocateTurbines.argtypes = [
            POINTER(c_int),         # ErrStat_c OUT
            POINTER(c_char),        # ErrMsg_c OUT
        ]
        self.FAST_DeallocateTurbines.restype = c_int

        self.FAST_End.argtypes = [
            POINTER(c_int),         # iTurb IN
            POINTER(c_bool),        # StopTheProgram IN
        ]
        self.FAST_End.restype = c_int

        self.FAST_HubPosition.argtypes = [
            POINTER(c_int),         # iTurb IN
            POINTER(c_float),       # AbsPosition_c(3) OUT
            POINTER(c_float),       # RotationalVel_c(3) OUT
            POINTER(c_double),      # Orientation_c(9) OUT
            POINTER(c_int),         # ErrStat_c OUT
            POINTER(c_char)         # ErrMsg_c OUT
        ]
        self.FAST_HubPosition.restype = c_int

    def fast_init(self) -> None:
        # Create buffers for class data
        self.n_turbines = c_int(1)
        self.i_turb = c_int(0)
        self.dt = c_double(0.0)
        self.dt_out = c_double(0.0)
        self.t_max = c_double(0.0)  # Got from fst file
        self.abort_error_level = c_int(4)  # Initialize to 4 (ErrID_Fatal)
        self.end_early = c_bool(False)
        self.num_outs = c_int(NumFixedOutputs)
        self.output_channel_names = []
        self.output_values = (c_double * self.num_outs.value)(0.0, )
        self.ended = False
        self.num_inputs = c_int(NumFixedInputs)
        self.inp_array = (c_double * self.num_inputs.value)(0.0, )
        self.num_maxInitInputs = c_int(MAXInitINPUTS)
        self.InitInputArray = (c_double * self.num_maxInitInputs.value)(0.0, )


        _error_status = c_int(0)
        _error_message = create_string_buffer(IntfStrLen)

        self.FAST_AllocateTurbines(
            byref(self.n_turbines),
            byref(_error_status),
            _error_message
        )
        if self.fatal_error(_error_status):
            raise RuntimeError(f"Error {_error_status.value}: {_error_message.value}")

        # Create channel names argument
        channel_names = create_string_buffer(20 * 4000)        
        self.FAST_Sizes(
            byref(self.i_turb),
            self.inputFileName,
            byref(self.abort_error_level),
            byref(self.num_outs),
            byref(self.dt),
            byref(self.dt_out),
            byref(self.t_max),
            byref(_error_status),
            _error_message,
            channel_names,
            byref(self.myTmax),  # Optional arguments must pass C-Null pointer; with ctypes, use None.
            byref(self.InitInputArray)    # Optional arguments must pass C-Null pointer; with ctypes, use None.
        )

        if self.fatal_error(_error_status):
            raise RuntimeError(f"Error {_error_status.value}: {_error_message.value}")

        # Extract channel name strings from argument
        if len(channel_names.value.split()) == 0:
            self.output_channel_names = []
        else:
            self.output_channel_names = [n.decode('UTF-8') for n in channel_names.value.split()] 

        # Delete error message and channel name character buffers
        del _error_message
        del channel_names

    def fast_start(self):
        _error_status = c_int(0)
        _error_message = create_string_buffer(IntfStrLen)

        self.FAST_Start(
            byref(self.i_turb),
            byref(self.num_inputs),
            byref(self.num_outs),
            byref(self.inp_array),
            byref(self.output_values),
            byref(_error_status),
            _error_message
        )
        if self.fatal_error(_error_status):
            self.fast_deinit()
            raise RuntimeError(f"Error {_error_status.value}: {_error_message.value}")
    
    def fast_update(self):
        _error_status = c_int(0)
        _error_message = create_string_buffer(IntfStrLen)

        self.FAST_Update(
            byref(self.i_turb),
            byref(self.num_inputs),
            byref(self.num_outs),
            byref(self.inp_array),
            byref(self.output_values),
            byref(self.end_early),
            byref(_error_status),
            _error_message
        )

        return _error_status, _error_message
        
        #Dont worry babe, I will handle this error in fast_gym.py
        #if self.fatal_error(_error_status):
            #self.fast_deinit()
            #raise RuntimeError(f"Error {_error_status.value}: {_error_message.value}")

    def fatal_error(self, error_status) -> bool:
        return error_status.value >= self.abort_error_level.value
    
    @property
    def total_time_steps(self) -> int:
        # Note that Fortran indexing starts at 1 and includes the upper bound
        return math.ceil( self.t_max.value / self.dt.value) + 1  

    @property
    def total_output_steps(self) -> int:
        # From FAST_Subs ValidateInputData: DT_out == DT or DT_out is a multiple of DT
        return math.ceil(self.t_max.value / self.dt_out.value) + 1
   
    def fast_deinit(self) -> None:
        _error_status = c_int(0)
        _error_message = create_string_buffer(IntfStrLen)

        if not self.ended:
            self.ended = True

            # Deallocate all the internal variables and allocatable arrays
            # Despite the name, this does not actually end the program
            self.FAST_End(
                byref(self.i_turb),
                byref(c_bool(False))
            )

            # Deallocate the Turbine array
            self.FAST_DeallocateTurbines(
                byref(_error_status),
                _error_message
            )
            if self.fatal_error(_error_status):
                raise RuntimeError(f"Error {_error_status.value}: {_error_message.value}")

    def close(self):
        _error_status = c_int(0)
        _error_message = create_string_buffer(IntfStrLen)

        if not self.ended:
            self.ended = True
            # Deallocate all the internal variables and allocatable arrays
            # Despite the name, this does not actually end the program
            self.FAST_End(
                byref(self.i_turb),
                byref(c_bool(False))
            )

            # Deallocate the Turbine array
            self.FAST_DeallocateTurbines(
                byref(_error_status),
                _error_message
            )
            if self.fatal_error(_error_status):
                raise RuntimeError(f"Error {_error_status.value}: {_error_message.value}")
        
