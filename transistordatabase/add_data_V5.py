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
    if identifier == 1:
        complement = 0
    else:
        complement = 1
    #print(list2,new_list,n_value)
    #print(channel_values.keys())
    for j in new_list:
    #print(j)
        for i  in list2:
            #print(i)    
            for key,value in channel_values.items():
                    #print(key)
                    if key[identifier] == j:
                        print(i,j,key)
                        if i == key[complement]:
                            input_voltages = value[0] 
                            current_values = value[1]
                            replicated_X1 = np.repeat(j, len(input_voltages))
                            replicated_new_X2 = np.repeat(i, len(input_voltages))
                            replicated_old_X2 = np.repeat(key[complement], len(input_voltages))
                        else:
                            input_voltages = value[0] 
                            current_values = value[1]
                            replicated_X1 = np.repeat(j, len(input_voltages))
                            replicated_new_X2 = np.repeat(i, len(input_voltages))
                            replicated_old_X2 = np.repeat(key[complement], len(input_voltages))
                    elif j != key[identifier] :
                        input_voltages = value[0] 
                        current_values = value[1]
                        replicated_old_X2 = np.repeat(key[complement], len(input_voltages))
                        replicated_X1 = np.repeat(j, len(input_voltages))
                        replicated_new_X2 = np.repeat(i, len(input_voltages))
                    X = np.column_stack((input_voltages, replicated_old_X2, replicated_X1))
                    y = current_values
                    gradient_boosting_model.fit(X, y)
                    X_new = np.column_stack((input_voltages, replicated_new_X2,replicated_X1))
                    predicted_current_values_gb = gradient_boosting_model.predict(X_new)
                    channel_values = channel_values | {(i,j):[input_voltages,predicted_current_values_gb]}
                    if (j == n_value) :
                        print("Here",n_value)
                        for u,c in zip(input_voltages,predicted_current_values_gb):
                            data.append((u,i,c))
                        
                        input1.extend(input_voltages)
                        input2.append(replicated_X1)
                        output.append(predicted_current_values_gb)
                        #required_data.append([input_voltages,predicted_current_values_gb])
                        required_data.append((input_voltages,replicated_X1,predicted_current_values_gb))   
    return data, channel_values



def getplot(channel_loss, V_value,T_value,identifier):
    #fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

    
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
    new_junction_Temperatures = generate_values(temp,lens[0],T_value)
    new_gate_voltages = generate_values(gate_v,lens[0],V_value)
    #new_gate_voltages = new_gate_voltages.sort()
    #new_junction_Temperatures = new_junction_Temperatures.so
    print(new_gate_voltages)
    
    if identifier==1:
        required_data,channel_updated = generate_data(new_gate_voltages,new_junction_Temperatures,channel_values,V_value,1)
    elif identifier == 0:
        required_data,channel_updated = generate_data(new_junction_Temperatures,new_gate_voltages,channel_values,T_value,0)
    
    return required_data,channel_updated

def generate_values(lst, len1,n_value):
    print(lst,len1,n_value)
    num_intervals = len(lst) - 1
    target_length = len1
    distance = (lst[-1] - lst[0]) / (target_length - len(lst))
    required_data = []
    # Generate the new list
    new_list = []
    for i in range(len(lst)-1):
        interval_distance = (lst[i+1] - lst[i]) / (target_length // num_intervals)
        for j in range(1,target_length // num_intervals):
            value = round(lst[i] + j * interval_distance, 2)
            if value not in new_list and (value not in lst):
                #print(value)
                new_list.append(value)
    if n_value not in new_list:
        new_list.append(n_value)
    for i in lst:
        if i not in new_list:
            #print(i,new_list)
            new_list.append(i)
    #new_list = new_list.sort()
    #print(new_list)
    return new_list




def get_interpolated_data(V_gate_required,T_junction_required, transistor):
    data = []
    transistor_loaded = db.load_transistor(transistor)#"CREE_C3M0016120K")
    channel_loss = transistor_loaded.switch.channel



    data, channel_values_updated = getplot(channel_loss,V_gate_required,T_junction_required,0)
    print(data)
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
    #ax.scatter3D(X, Y, Z, color = "green")
    ax.set_xlabel('Input Voltage - V')
    ax.set_ylabel('Gate Voltage - C')
    ax.set_zlabel('Channel Current - I')
    ax.set_title('3D Graph')
    plt.show() 




get_interpolated_data(8,35,"CREE_C3M0016120K")