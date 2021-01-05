# cbpi-SimpleCascadeHysteresis

### This plugin is heavily inspired by Justin Angevaare's `cbpi-CascadeControl` plugin, thanks for the great work

## Why?

Justin's plugin is great. I have a Herms brewery with simple on/off heater in HLT, so I immediately wanted to
use `CascadeHystersis`. I've set up the parameters and started testing. After several hours, lots of tests, writing to
Excel sheets and doing lots of charts I discovered that for this simple setup `CascadeHystersis` may be an overkill.

### Problem

Everytime (no matter which parameters I used) there was a huge overshoot in HLT. The HLT temp (and of course a temp at
the end of the coil in HLT) was much higher than target temperature in MashTun. Although this lead to faster MashTun
heating, the temperatures high above the Mash target at the end of coil is bad for wort. What is more, HLT is then too
hot for next stage of brewing.

Ideally, what you want is to reach your Mash target temp in HLT as quickly as possible (maybe with some minor overshoot)
to let as much heat as possible to be transferred from HLT to coil/Mash, but not overshoot. The more you get closer to
target temp, the slower the transfer will be, but that is the prize for precision.

The huge overshoot in `CascadeHysteresis` seems to be done by the fact, that hysteresis is controlled by PID algorithm.
Whatever non-zero value is produced from this PID, it switches/keeps the heater ON. Therefore, heater is switched on
even when the PID value is very small - when the target is already reached and PID is minimizing its value. This is much
worse, when you don't limit the integral error - this leads to much higher numbers and longer switched on heater - huge
overshoot.

Therefore, I decided to make it a bit simpler.

## How this works

This plugin is intended for HTL's with on/off heating element. It monitors the HLT temp and uses hysteresis algorithm (
with the ability to set offsets)
to regulate this temp with the Mash tun target temp. This way HLT does not overshoot too much (only by offset). There is
a possibility to add another sensor (after Herms coil/Rims tube) and monitor temp (with separate offset) there too.
There is also possibility to set a minimum heater on and off times to prevent excessive usage. On/off element also does
not adjust its power which is also bad for PID.

## Parameters and setup

Configure your MT (MashTun) to use `SimpleCascadeHysteresis` as `Logic`. Also setup the same
`Actor` as you have in your HLT. As a `Sensor` leave your default MT temp sensor. Now setup your target temp and press
auto in MT.

HLT sensor - choose your temp sensor in HLT

**Positive offset for hysteresis** - number which adds to target and if the HLT temp goes above it switches off

**Negative offset for hysteresis** - number which subtracts from a target and if the HLT temp goes below it switches off

**Hysteresis minimum time on** - prevents switching off for a minimum of this amount of seconds (0 to disable)

**Hysteresis minimum time off** - prevents switching on for a minimum of this amount of seconds (0 to disable)

**Sensor after the HERMS coil or RIMS tube** - choose the right one or leave blank

**Positive offset for coil/tube** - heating is switched off if the coil/tube temp reaches target + this value

### License

This plugin is open source, and has an MIT License. Please read the included license if you are not already familiar
with it.

### Safety and Disclaimers

* This plugin is intended only for those knowledgeable and comfortable with control systems.
* Improper tuning could lead to unpredictable results with this plugin. The user must closely monitor their brewery at
  all times of operation.
* This plugin should never be used in the absence of proper safety features, especially those related to element dry
  firing, stuck recirculation, properly rated hardware components, and GFCI protection.