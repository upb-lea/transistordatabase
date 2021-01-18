classdef SwitchEnergyDataClass
    %SWITCHENERGYDATACLASS Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        Type(1,1) string %Bsp: E_x over R_g, E_x over I_x, etc.
        T_j(1,1) double
        V_supply(1,1) double
        V_switch(1,1) double
        E_x(1,:) double
        R_g(1,:) double
        I_x(1,:) double
    end
    
end

