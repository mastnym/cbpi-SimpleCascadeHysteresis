# cbpi-SimpleCascadeHysteresis
### This plugin is heavily inspired by Justin Angevaare's `cbpi-CascadeControl` plugin, thanks for the great work

##Why?
Justin's plugin is great. I have a Herms brewery with simple on/off heater
in HLT, so I immediately wanted to use `CascadeHystersis`.
I've setup the parameters and started testing. After several hours, lots of tests, writing to excel sheets and doing lots of charts
I  discovered that for this simple setup `CascadeHystersis` may be an overkill.

###Problem
Everytime (no matter which parameters I used) there was a huge overshoot in HLT.
The HLT temp (and of course a temp at the end of the coil in HLT) was much higher than target temperature in MashTun.
Although this lead to faster MashTun heating, the temperatures 
high above the Mash target at the end of coil is bad for wort. What is more, HLT is then too hot for next stage of brewing.

Ideally, what you want is to reach your Mash target temp in HLT as quickly as possible (maybe with some minor overshoot) to let
as much heat as possible to be transferred from HLT to coil/Mash, but not overshoot. 
The more you get closer to target temp, the slower the transfer will be, but that is the prize for precision.

The huge overshoot in `CascadeHysteresis` seems to be done by the fact, that hysteresis is controlled 
by PID algorithm. Whatever non-zero value is produced from this PID, it switches/keeps the heater ON.
Therefore, heater is switched on even when the PID value is very small - when the target is already reached and PID is minimizing it's value.
This is much worse, when you don't limit the integral error - this leads to much higher numbers and longer switched on heater - huge overshoot.

Therefore I decided to make it a bit simpler.

## How this works
This plugin is intended for HTL's with on/off heating element.
It monitors the HLT temp and uses hysteresis algorithm (with the ability to set offsets)
to regulate this temp with the Mash tun target temp. This way HLT does not overshoot too much (only by offset).
There is a possibility to add another sensor (after Herms coil/Rims tube) and monitor temp (with separate offset) there too.
There is also possibility to set a minimum heater on and off times to prevent excessive usage.
On/off element also does not adjust its power which is also bad for PID.

## Parameters


### License 
This plugin is open source, and has an MIT License. Please read the included license if you are not already familiar with it.

### Safety and Disclaimers
* This plugin is intended only for those knowledgeable and comfortable with control systems.
* Improper tuning could lead to unpredictable results with this plugin. The user must closely monitor their brewery at all times of operation. 
* This plugin should never be used in the absence of proper safety features, especially those related to element dry firing, stuck recirculation, properly rated hardware components, and GFCI protection.