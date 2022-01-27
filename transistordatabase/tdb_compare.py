from .tdb_classes import *
from matplotlib import pyplot as plt
from typing import List


def compare(transistor_list: List, temperature: float, gatevoltage: float):

    fig1, axs = plt.subplots(3, 2, sharex='row', sharey='row')

    for transistor in transistor_list:
        transistor.update_wp(temperature, gatevoltage, transistor.i_cont)

        # plot forward characteristics
        axs[1, 0].plot(transistor.wp.switch_channel.graph_v_i[0], transistor.wp.switch_channel.graph_v_i[1],
                       label=transistor.name)
        axs[1, 1].plot(transistor.wp.diode_channel.graph_v_i[0], transistor.wp.diode_channel.graph_v_i[1],
                       label=transistor.name)

        # plot energy losses
        axs[0, 0].plot(transistor.wp.e_on.graph_i_e[0], transistor.wp.e_on.graph_i_e[1], label=transistor.name)
        axs[0, 1].plot(transistor.wp.e_off.graph_i_e[0], transistor.wp.e_off.graph_i_e[1], label=transistor.name)

        # plot energy in c_oss
        if transistor.graph_v_ecoss is not None:
            axs[2, 0].plot(transistor.graph_v_ecoss[0], transistor.graph_v_ecoss[1], label=transistor.name)

    axs[0, 0].set_title('Turn-on')
    axs[0, 0].legend()
    axs[0, 0].grid()
    axs[0, 0].set_xlabel('Current in A')
    axs[0, 0].set_ylabel('Eon in J')

    axs[0, 1].set_title('Turn-off')
    axs[0, 1].legend()
    axs[0, 1].grid()
    axs[0, 1].set_xlabel('Current in A')
    axs[0, 1].set_ylabel('Eoff in J')

    axs[1, 0].set_title('Switch forward characteristic')
    axs[1, 0].legend()
    axs[1, 0].grid()
    axs[1, 0].set_xlabel('Voltage in V')
    axs[1, 0].set_ylabel('Current in A')

    axs[1, 1].set_title('Diode forward characteristic')
    axs[1, 1].legend()
    axs[1, 1].grid()
    axs[1, 1].set_xlabel('Voltage in V')
    axs[1, 1].set_ylabel('Current in A')

    axs[2, 0].set_title('Energy in C_oss')
    axs[2, 0].legend()
    axs[2, 0].grid()
    axs[2, 0].set_xlabel('Voltage in V')
    axs[2, 0].set_ylabel('Energy in J')
    plt.tight_layout()
    plt.show()
