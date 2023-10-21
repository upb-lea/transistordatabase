from transistordatabase.transistor import Transistor as tdb
from transistordatabase.database_manager import DatabaseManager
import numpy as np
import pandas as pd
import csv
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator
import scipy.interpolate as interp
from mpl_toolkits.mplot3d import Axes3D
import os
from pathlib import Path
import json
import time

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tdb_example_downloaded")
db = DatabaseManager()
db.set_operation_mode_json(path)
db.update_from_fileexchange(True)
original_list = [-40, 25, 175]
gradient_boosting_model = GradientBoostingRegressor()


def generate_data(new_list,list2, channel_values,n_value,identifier):
    '''parameters:
    n_value: datagenerated for the required value
    identifier: can be either 1 or 0
    list2: list of values (depending on new_list, if new_list is temperature values then it is gate_voltage values and vice versa)
    
    channel_values: dictionary containing channel current and voltage values with corresponding gate)
     if identifier is 1, key[1] is gate_v and key[0] is junction_temperature for identifier 0
    
    new list: is the list containing new generated values '''
    required_data = []
    input1 = []
    input2 = []
    output = []
    data = []
    for j in new_list:
    #print(j)
        for i  in list2:
            #print(i)    
            for key,value in channel_values.items():
                #print(key)
                    if key[identifier] == i:
                        #print(i,key)
                        input_voltages = value[0] 
                        current_values = value[1]
                        replicated_junction_temperature = np.repeat(i, len(input_voltages))
                        replicated_new_gate_voltage = np.repeat(j, len(input_voltages))
                        replicated_old_gate_voltage = np.repeat(key[1], len(input_voltages))
                        X = np.column_stack((input_voltages, replicated_old_gate_voltage, replicated_junction_temperature))
                        y = current_values
                        gradient_boosting_model.fit(X, y)
                        X_new = np.column_stack((input_voltages, replicated_new_gate_voltage,replicated_junction_temperature))
                        predicted_current_values_gb = gradient_boosting_model.predict(X_new)
                        channel_values = channel_values | {(i,j):[input_voltages,predicted_current_values_gb]}
                        if (j == n_value) :
                            #print(j,n_value,i)
                            #print(key)
                            for u,c in zip(input_voltages,predicted_current_values_gb):
                                data.append((u,i,c))
                            input1.extend(input_voltages)
                            input2.append(replicated_junction_temperature)
                            output.append(predicted_current_values_gb)
                            required_data.append([input_voltages,predicted_current_values_gb])
    return required_data
                
                    
def getplot_V(transistor, n_value):
    #fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    transistor_loaded = db.load_transistor(transistor)#"CREE_C3M0016120K")
    channel_loss = transistor_loaded.switch.channel
    temp = []
    lens = []
    gate_v = []
    input_voltages = [] 
    channel_values = {}
    for i in (channel_loss):
        if i.v_g not in gate_v:
            gate_v.append(i.v_g)
        if i.t_j not in temp:
            temp.append(i.t_j)
        lens.append(len(i.graph_v_i[0]))
        channel_values[(i.t_j,i.v_g)] = i.graph_v_i 
# Calculate the number of intervals and the distance between them

    num_intervals = len(gate_v) - 1
    target_length = lens[0]
    distance = (gate_v[-1] - gate_v[0]) / (target_length - len(gate_v))
    required_data = []
    # Generate the new list
    new_list = []
    for i in range(len(gate_v)-1):
        interval_distance = (gate_v[i+1] - gate_v[i]) / (target_length // num_intervals)
        for j in range(1,target_length // num_intervals):
            value = round(gate_v[i] + j * interval_distance, 2)
            if value not in new_list and (value not in gate_v):
                #print(value)
                new_list.append(value)
    if n_value not in new_list:
        new_list.append(n_value)
    #print(temp)

    
   
   
    
 
# show plot
    plt.show()
    return data
        


#TODO 3-D plots and 2-D interpolation on it
#TODO 1 3-D containing v_i with gate_voltage for fixed junc_t and 1 3-D containing v_i with junc_tem for fixed gate_v
#TODO 2-D plot for fixed gate_v and fixed junc_t
#TODO naming variables and conventions to follow, and adding comments




def getplot_T(transistor, n_value):
    #fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

    transistor_loaded = db.load_transistor(transistor)#"CREE_C3M0016120K")
    channel_loss = transistor_loaded.switch.channel
    temp = []
    lens = []
    gate_v = []
    input_voltages = [] 
    channel_values = {}
    for i in (channel_loss):
        if i.v_g not in gate_v:
            gate_v.append(i.v_g)
        if i.t_j not in temp:
            temp.append(i.t_j)
        lens.append(len(i.graph_v_i[0]))
        channel_values[(i.t_j,i.v_g)] = i.graph_v_i 
# Calculate the number of intervals and the distance between them

    num_intervals = len(temp) - 1
    target_length = lens[0]
    distance = (temp[-1] - temp[0]) / (target_length - len(temp))
    required_data = []
    # Generate the new list
    new_list = []
    for i in range(len(temp)-1):
        interval_distance = (temp[i+1] - temp[i]) / (target_length // num_intervals)
        for j in range(1,target_length // num_intervals):
            value = round(temp[i] + j * interval_distance, 2)
            if value not in new_list and (value not in temp):
                #print(value)
                new_list.append(value)
    if n_value not in new_list:
        new_list.append(n_value)
    #print(temp)
    for j in new_list:
        #print(j)
        for i  in gate_v:
            #print(i)    
            for key,value in channel_values.items():
                #print(key)
                if key[1] == i:
                    #print(i,key)
                    input_voltages = value[0] 
                    current_values = value[1]
                    replicated_junction_temperature = np.repeat(i, len(input_voltages))
                    replicated_new_gate_voltage = np.repeat(j, len(input_voltages))
                    replicated_old_gate_voltage = np.repeat(key[1], len(input_voltages))
                    X = np.column_stack((input_voltages, replicated_old_gate_voltage, replicated_junction_temperature))
                    y = current_values
                    gradient_boosting_model.fit(X, y)
                    X_new = np.column_stack((input_voltages, replicated_new_gate_voltage,replicated_junction_temperature))
                    predicted_current_values_gb = gradient_boosting_model.predict(X_new)
                    channel_values = channel_values | {(i,j):[input_voltages,predicted_current_values_gb]}
                    if (j == n_value) :
                        #print(j,n_value,i)
                        #print(key)
                        for u,c in zip(input_voltages,predicted_current_values_gb):
                            
                            data.append((u,i,c))
                        input1.extend(input_voltages)
                        input2.append(replicated_junction_temperature)
                        output.append(predicted_current_values_gb)
                        required_data.append([input_voltages,predicted_current_values_gb])
    
   
   
   
    return data



getplot_V("CREE_C3M0016120K",10)

def get_interpolated_data(V_gate_required,T_junction_required, transistor):
    data = []
    data_T = getplot_T(transistor,V_gate_required)
    data_V = getplot_V(transistor,T_junction_required)
    data.extend(data_T)
    data.extend(data_V)
    
    
    X = [point[0] for point in data]
    Y = [point[1] for point in data]
    Z = [point[2] for point in data]

    
    plotx,ploty, = np.meshgrid(np.linspace(np.min(X),np.max(X),10),\
                       np.linspace(np.min(Y),np.max(Y),10))
    plotz = interp.griddata((X,Y),Z,(plotx,ploty),method='linear')
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    #ax.plot(X, Y, Z)
    ax.plot_surface(plotx,ploty,plotz,cstride=1,rstride=1,cmap='viridis',linewidth=0.5, zorder=100,edgecolor='royalblue')
    
    ax.set_xlabel('Input Voltage - V')
    ax.set_ylabel('Junction Temperature - C')
    ax.set_zlabel('Channel Current - I')
    ax.set_title('3D Graph')
    plt.show()
    










