classdef TransistorClass
% * Initial author: Manuel Klaedtke      
% * Date of creation: 02.12.2020     
% * Last modified by: Manuel Klädtke       
% * Date of modification: 02.12.2020      
% * Version: 1.0      
% * Compatibility: Matlab       
% * Other files required: Full package folder +transistorDatabase      
% * Link to classdef: https://git.uni-paderborn.de/lea-git/lea-git-public/matlab-functions/transistor_database/-/blob/master/+transistorDatabase/@TransistorClass/TransistorClass.m       
% Syntax:  
%%%%% This creates an object with the default (mostly empty) property
%%%%% values. The properties have to be assigned (manually; for now)
%%%%% afterwards. Different constructors may be added in the future.
% import transistorDatabase.*;        
% myTransistor = TransistorClass;
%%%%%
%
% Description:   
% Main class of the transistor database. Contains properties of the 
% transistor that are not specifically grouped with other objects in its 
% Switch/Diode/Meta-properties.
% This classdef file does not (yet) include methods. Methods don't need to 
% be added in this file specifically but can be located in other .m-files
% inside the @TransistorClass class-folder.
%        
% Input parameters:      
% None. Might change with different constructor options.        
%         
% Output parameters:     
% An object of this class.       
%         
% Example:         
% See the file: Database/exampleTemplate.m       
%       
% Known Bugs:      
% Does not currently work with Octave because package namespaces and also 
% property class and size validation are not supported there.
%      
% Changelog:      
% VERSION / DATE / NAME: Comment  
% 1.0 / 02.12.2020 / Klaedtke: Added header information and property
% descriptions
%

    properties
        % Transistor Name:
        Name(1,1) string

        % Transistor type: IGBT or MOSFET
        Type(1,1) string {mustBeMember(Type,{'IGBT','MOSFET'})} = 'IGBT'
        % Type needs a default value if one chooses to restrict it to the
        % values 'IGBT' & 'MOSFET'. This could be problematic.
        
        % Classes in the package namespace need to specified with the 
        % following syntax:
        % PackageName.ClassName
        
        % Sub-Objects: These are explained in their respective classdefs
        Switch(1,1) transistorDatabase.SwitchClass 
        Diode(1,1) transistorDatabase.DiodeClass
        Meta(1,1) transistorDatabase.MetadataClass
        % Thermal data: See diagram for equivalent thermal circuit
        R_th_cs(1,1) double
        R_th_switch_cs(1,1) double
        R_th_diode_cs(1,1) double
        % Absolute maximum ratings:
        V_max(1,1) double
        I_max(1,1) double
    end
end

