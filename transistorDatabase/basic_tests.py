import numpy as np
from databaseClasses import Transistor

transistor_args = {"name": "Test-Transistor"}
channel1 = {"t_j": 1.0,
            "v_i_data": np.array([[1, 2],
                                  [3, 4]])}
channel2 = {"t_j": 2.0,
            "v_i_data": np.array([[1, 2],
                                  [3, 4]])}
channels = [channel1, channel2]
metadata_args = dict()
foster_args = dict()
switch_args = {'channel': channels}
diode_args = {'channel': channel1}

testTransistor = Transistor(transistor_args, metadata_args, foster_args, switch_args, diode_args)
# testTransistor2 = Transistor()
# testTransistor3 = Transistor(transistor_args,metadata_args)
