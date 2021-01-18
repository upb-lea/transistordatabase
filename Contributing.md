# Contributing to the code
Every function/script shoud have a uniform header. This header will be displayed, if a user runs 'help command'. Additionally to this, every function/script should contain a README.md file, which gives a short introduction to the code.      

## Maintainers
If you have any questions, don't hesitate to contact one of our maintainers.
  * rehlaender@lea.uni-paderborn.de
  * foerster@lea.uni-paderborn.de

## Header to copy
% * Initial author:       
% * Date of creation:      
% * Last modified by:        
% * Date of modification:       
% * Version:       
% * Compatibility:        
% * Other files required:       
% * Link to function:        
% Syntax:         
%         
%       
% Description:      
%        
%        
% Input parameters:      
%         
%         
% Output parameters:     
%        
%         
% Example:         
%        
%       
% Known Bugs:      
%      
%      
% Changelog:      
% VERSION / DATE / NAME: Comment     
%

## Header Example
Header should look like this.     
% * Initial author: Nikolas Foerster    
% * Date of creation: 24/02/2020    
% * Last modified by: Philipp Rehlaender    
% * Date of modification: 24/02/2020    
% * Version: 1.1    
% * Compatibility: Matlab/Octave    
% * Other files required: none       
% * Link to function: https://git.uni-paderborn.de/lea-git/lea-git-public/matlab-functions/matlab-general-functions/tree/master/01_simple_functions/Parallel_Resistor      
%       
% Syntax:    
% R_Parallel = Parallel_Resistor(R1,R2)    
%    
% Description:    
% Calculates the overall resistance of two parallel resistors based on the     
% equation R_parallel = 1 / (1/R1 + 1/R2)     
%     
% Input parameters:     
% R1: Resistor No. 1     
% R2: Resistor No. 2     
%     
% Output parameters:     
% R_Parallel     
%     
% Example:     
% R_Parallel = Parallel_Resistor(1000,1000)     
% >> R_Parallel = 5000;      
%       
%     
% Known Bugs:      
%      
%     
% Changelog:      
% VERSION / DATE      
% 1.0.0 / 1.7.2020 / Förster: Initial function
% 1.0.1 / 29.7.2020 / Förster: rename function Resistor_Parallel -> Parallel_Resistor

## Drawings for readme files
We recomment to use the program [Inkscape](https://inkscape.org/). It is open source software and runs on Linux, Mac and Windows.     
If you want to draw electirc circuits, we recommend this library on [github](https://github.com/upb-lea/Inkscape_electric_Symbols).
