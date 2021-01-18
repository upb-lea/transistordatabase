classdef SwitchClass
    %SWITCH Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        Meta(1,1) transistorDatabase.MetadataClass
        Thermal(1,1) transistorDatabase.FosterThermalModelClass
        Channel(1,:) transistorDatabase.ChannelDataClass
        E_on(1,:) transistorDatabase.SwitchEnergyDataClass
        E_off(1,:) transistorDatabase.SwitchEnergyDataClass
    end
    
    methods
%         function obj = SwitchClass
%             %SWITCH Construct an instance of this class
%             %   Detailed explanation goes here
%             obj.Property1 = string('test');
%         end
%         
%         function this = set.Property1(this, value)
%             if ~isa(value,'string')
%                 error('This should be a string')
%             end
%             this.Property1 = value;
%         end

    end
end

