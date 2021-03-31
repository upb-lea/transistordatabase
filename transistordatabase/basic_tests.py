import numpy as np
from databaseClasses import Transistor

transistor_args = {"name": "Test-Transistor", "type": 'MOSFET', "v_max": 200, "i_max": 200, 'i_cont': 200}
metadata_args = {"author": "Manuel Klaedtke", "manufacturer": "Fuji", "housing_area": 200, "cooling_area": 200,
                 "housing_type": "TO-220"}
channel1 = {"t_j": 1.0,
            "graph_v_i": np.array([[1, 2],
                                  [3, 4]])}
channel2 = {"t_j": 2.0,
            "graph_v_i": np.array([[1, 2],
                                  [3, 4]])}

switchenergy1 = {'dataset_type': 'single', 't_j': 1, 'v_supply': 1, 'v_g': 1, 'e_x': 1, 'r_g': 1, 'i_x': 1}
switchenergy2 = {'dataset_type': 'graph_r_e', 't_j': 1, 'v_supply': 1, 'v_g': 1, 'graph_r_e': np.array([[1, 2], [3, 4]]),
                 'i_x': 1}
switchenergies = [switchenergy1, switchenergy2]
channels = [channel1, channel2]
foster_args = dict()
switch_args = {'channel': channels}
diode_args = {'channel': channel1, 'e_rr': switchenergies}

testTransistor = Transistor(transistor_args, metadata_args, foster_args, switch_args, diode_args)
# testTransistor2 = Transistor()
# testTransistor3 = Transistor(transistor_args,metadata_args)
