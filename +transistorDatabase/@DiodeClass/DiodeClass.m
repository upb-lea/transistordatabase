classdef DiodeClass
    %DIODECLASS Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        Meta(1,1) transistorDatabase.MetadataClass
        Thermal(1,1) transistorDatabase.FosterThermalModelClass
        Channel(1,:) transistorDatabase.ChannelDataClass
        E_rr(1,:) transistorDatabase.SwitchEnergyDataClass
    end
    
    methods

    end
end

