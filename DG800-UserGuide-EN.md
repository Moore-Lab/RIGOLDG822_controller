



## RIGOL
## User’s Guide
















DG800 Series
Function/Arbitrary Waveform
## Generator















## Jul. 2018
## RIGOL (SUZHOU) TECHNOLOGIES INC.



## RIGOL
DG800 User's Guide I
Guaranty and Declaration

## Copyright
© 2018 RIGOL (SUZHOU) TECHNOLOGIES INC. All Rights Reserved.

## Trademark Information
RIGOL is a registered trademark of RIGOL (SUZHOU) TECHNOLOGIES INC.

## Publication Number
## UGB11100-1110

## Software Version
## 00.00.01
Software upgrade might change or add product features. Please acquire the latest
version of the manual from RIGOL website or contact RIGOL to upgrade the
software.

## Notices
 RIGOL products are covered by P.R.C. and foreign patents, issued and pending.
 RIGOL reserves the right to modify or change parts of or all the specifications
and pricing policies at the company’s sole decision.
 Information in this publication replaces all previously released materials.
 Information in this publication is subject to change without notice.
 RIGOL shall not be liable for either incidental or consequential losses in
connection with the furnishing, use, or performance of this manual, as well as
any information contained.
 Any part of this document is forbidden to be copied, photocopied, or rearranged
without prior written approval of RIGOL.

## Product Certification
RIGOL guarantees that this product conforms to the national and industrial
standards in China as well as the ISO9001:2015 standard and the ISO14001:2015
standard. Other international standard conformance certifications are in progress.

## Contact Us
If you have any problem or requirement when using our products or this manual,
please contact RIGOL.
E-mail: service@rigol.com
Website: www.rigol.com


## RIGOL
II                               DG800 User's Guide
## Safety Requirement

## General Safety Summary

Please review the following safety precautions carefully before putting the
instrument into operation so as to avoid any personal injury or damage to the
instrument and any product connected to it. To prevent potential hazards, please
follow the instructions specified in this manual to use the instrument properly.

Use the BNC output connector properly.
The BNC output connector on the front panel only allows to output the signal but not
to input the signal.

## Use Proper Power Cord.
Only the exclusive power cord designed for the instrument and authorized for use
within the local country could be used.

Ground the Instrument.
The instrument is grounded through the Protective Earth lead of the power cord. To
avoid electric shock, connect the earth terminal of the power cord to the Protective
Earth terminal before connecting any input or output terminals.

Connect the Probe Correctly.
If a probe is used, the probe ground lead must be connected to earth ground. Do not
connect the ground lead to high voltage. Improper way of connection could result in
dangerous voltages being present on the connectors, controls or other surfaces of
the oscilloscope and probes, which will cause potential hazards for operators.

## Observe All Terminal Ratings.
To avoid fire or shock hazard, observe all ratings and markers on the instrument and
check your manual for more information about ratings before connecting the
instrument.

## Use Proper Overvoltage Protection.
Ensure that no overvoltage (such as that caused by a bolt of lightning) can reach the
product. Otherwise, the operator might be exposed to the danger of an electric
shock.

## Do Not Operate Without Covers.
Do not operate the instrument with covers or panels removed.

Do Not Insert Objects Into the Air Outlet.
Do not insert objects into the air outlet, as doing so may cause damage to the
instrument.


## RIGOL
DG800 User's Guide III
## Use Proper Fuse.
Please use the specified fuses.

Avoid Circuit or Wire Exposure.
Do not touch exposed junctions and components when the unit is powered on.

## Do Not Operate With Suspected Failures.
If you suspect that any damage may occur to the instrument, have it inspected by
RIGOL authorized personnel before further operations. Any maintenance,
adjustment or replacement especially to circuits or accessories must be performed
by RIGOL authorized personnel.

## Provide Adequate Ventilation.
Inadequate ventilation may cause an increase of temperature in the instrument,
which would cause damage to the instrument. So please keep the instrument well
ventilated and inspect the air outlet and the fan regularly.

Do Not Operate in Wet Conditions.
To avoid short circuit inside the instrument or electric shock, never operate the
instrument in a humid environment.

Do Not Operate in an Explosive Atmosphere.
To avoid personal injuries or damage to the instrument, never operate the
instrument in an explosive atmosphere.

Keep Product Surfaces Clean and Dry.
To avoid dust or moisture from affecting the performance of the instrument, keep the
surfaces of the instrument clean and dry.

## Prevent Electrostatic Impact.
Operate the instrument in an electrostatic discharge protective environment to avoid
damage induced by static discharges. Always ground both the internal and external
conductors of cables to release static before making connections.

Use the Battery Properly.
Do not expose the battery (if available) to high temperature or fire. Keep it out of the
reach of children. Improper change of a battery (lithium battery) may cause an
explosion. Use the RIGOL specified battery only.

Handle with Caution.
Please handle with care during transportation to avoid damage to keys, knobs,
interfaces, and other parts on the panels.





## RIGOL
IV                               DG800 User's Guide
Safety Notices and Symbols

Safety Notices in this Manual:


## WARNING
Indicates a potentially hazardous situation or practice which, if not
avoided, will result in serious injury or death.


## CAUTION
Indicates a potentially hazardous situation or practice which, if not
avoided, could result in damage to the product or loss of important data.

Safety Terms on the Product:

DANGER It calls attention to an operation, if not correctly performed, could
result in injury or hazard immediately.
WARNING It calls attention to an operation, if not correctly performed, could
result in potential injury or hazard.
CAUTION It calls attention to an operation, if not correctly performed, could
result in damage to the product or other devices connected to the
product.

Safety Symbols on the Product:





## Hazardous
## Voltage
## Safety Warning Protective Earth
## Terminal
## Chassis Ground Test Ground








## RIGOL
DG800 User's Guide V
Care and Cleaning

## Care
Do not store or leave the instrument where it may be exposed to direct sunlight for
long periods of time.

## Cleaning
Clean the instrument regularly according to its operating conditions.
- Disconnect the instrument from all power sources.
- Clean the external surfaces of the instrument with a soft cloth dampened with
mild detergent or water. Avoid having any water or other objects into the chassis
via the heat dissipation hole. When cleaning the LCD, take care to avoid
scarifying it.



## CAUTION
To avoid damage to the instrument, do not expose it to caustic liquids.



## WARNING
To avoid short-circuit resulting from moisture or personal injuries, ensure
that the instrument is completely dry before connecting it to the power
supply.


## Environmental Considerations

The following symbol indicates that this product complies with the WEEE Directive
## 2002/96/EC.




Product End-of-Life Handling
The equipment may contain substances that could be harmful to the environment or
human health. To avoid the release of such substances into the environment and
avoid harm to human health, we recommend you to recycle this product
appropriately to ensure that most materials are reused or recycled properly. Please
contact your local authorities for disposal or recycling information.

You can log in to RIGOL official website (www.rigol.com) to download the latest
version of the RoHS-WEEE certification file.

## RIGOL
VI                               DG800 User's Guide
DG800 Series Function/Arbitrary
## Waveform Generator Overview

As a multi-functional signal generator, DG800 series function/arbitrary waveform
generator integrates many instruments into 1, such as function generator, arbitrary
waveform generator, noise generator, pulse generator, harmonic generator,
analog/digital modulator, and frequency counter. As a multi-functional and portable
instrument, it offers you a new choice in education, R&D, production, measurement,
and other industries with its user-friendly touch screen and high performance at an
unprecedented price point.

## Main Features:
 Unique SiFi II  (Signal Fidelity II) technology: generate the arbitrary waveforms
point by point; recover the signal without distortion; sample rate accurate and
adjustable; jitter of all the output waveforms (including Sine, Pulse, etc.) as low
as 200 ps
 2 Mpts memory depth (standard); 8 Mpts memory depth (optional) per channel
for arbitrary waveforms
 Optional dual-channel with the same performance, equivalent to two
independent signal sources
 High frequency stability: ±1 ppm; low phase noise: -105 dBc/Hz
 Built-in  up to 8 orders harmonics generator
 Built-in 7 digits/s, 240 MHz bandwidth full featured frequency counter
 Up to 160 built-in arbitrary waveforms, covering the common signals in
engineering application, medical electronics, auto electronics, math processing,
and other various fields
 Sample rate up to 125 MSa/s, vertical resolution 16 bits
 Arbitrary waveform sequence editing function available; arbitrary waveforms
also can be generated through the PC software
 Various analog and digital modulation functions: AM, FM, PM, ASK, FSK, PSK,
and PWM.
 Standard waveform combine function, capable of outputting specified
waveforms combined with the basic waveforms
 Standard channel tracking function, when enabled, all the parameters of both
channels are updated based on users' configurations
 USB HOST&DEVICE interface (standard); USB-GPIB function supported
 4.3'' TFT color touch screen
 RS232,  PRBS, and Dualtone outputs supported


## RIGOL
DG800 User's Guide VII
## Document Overview

Main Topics in this Manual
Chapter 1 Quick Start Introduces the appearance and dimensions of
DG800, its front/rear panel, and user interface.
## Chapter 2 Front Panel Operations
Introduces the main functions and operation
methods of DG800.
Chapter 3 Remote Control Introduces how to control DG800 remotely.
Chapter 4 Troubleshooting Lists the possible failures and solutions in using
## DG800.
Chapter 5 Appendix Provides the information about the options and
accessories list, as well as warranty information
of DG800.

Format Conventions in this Manual
## 1. Keys:
The keys on the front panel are usually denoted by the format of "Key Name
(Bold) + Text Box". For example, Utility denotes the Utility key.

## 2. Menu Labels:
The menu labels are usually denoted by the format of "Menu Word (Bold) +
Character Shading". For example, System Setting.

## 3. Connectors:
The connectors on the front or rear panel are usually denoted by the format of
"Connector Name (Bold) + Square Brackets (Bold)". For example, [Counter].

## 4. Operation Procedures:
"" represents the next step of operation. For example, Utility  System
Setting denotes that first press Utility on the front panel, and then tap the
System Setting menu label.

Content Conventions in this Manual
- DG800 series function/arbitrary waveform generator includes the following
models: This manual takes DG83  2 as an example to illustrate the operation
methods of the DG800 series.

Model No. of Channels Max. Output Frequency
DG812 2 10 MHz
DG822 2 25 MHz
DG832 2 35 MHz
DG811 1 10 MHz
DG821 1 25 MHz
DG831 1 35 MHz

## RIGOL
VIII                               DG800 User's Guide
- DG800 series function/arbitrary waveform generator is equipped with two
channels (CH1 and CH2). Unless otherwise specified, this manual takes CH1 as
an example to introduce the operation methods of the generator. The operation
methods of CH2 is the same as that of CH1.

Manuals of this Product
The manuals of this product mainly include the quick guide, user’s guide,
programming guide, data sheet, and etc. For the latest version of this manual,
download it from the official website of RIGOL (www.rigol.com).


Contents RIGOL
DG800 User's Guide IX
## Contents

Guaranty and Declaration ......................................................................... I
Safety Requirement ................................................................................ II
General Safety Summary ........................................................................... II
Safety Notices and Symbols ...................................................................... IV
Care and Cleaning .................................................................................... V
Environmental Considerations .................................................................... V
DG800 Series Function/Arbitrary Waveform Generator Overview ......... VI
Document Overview .............................................................................. VII
Chapter 1 Quick Start ......................................................................... 1-1
General Inspection ................................................................................ 1-2
Appearance and Dimensions ................................................................... 1-3
Front Panel Overview ............................................................................. 1-4
Rear Panel Overview .............................................................................. 1-8
To Prepare for Use ................................................................................ 1-11
To Connect to AC Power ................................................................. 1-11
Tu r n-on Checkout .......................................................................... 1-11
To Set the System Language ........................................................... 1-11
User Interface ...................................................................................... 1-12
To Use the Built-in Help System ............................................................. 1-15
Chapter 2 Front Panel Operations ...................................................... 2-1
To Output Basic Waveform ..................................................................... 2-2
To Select Output Channel ................................................................ 2-2
To Select Basic Waveform ................................................................ 2-3
To Set Frequency/Period .................................................................. 2-4
To Set Amplitude/High Level ............................................................ 2-5
To Set Offset/Low Level ................................................................... 2-7
To Set Start Phase .......................................................................... 2-8
To Set Duty Cycle (Square) .............................................................. 2-9
To Set Symmetry (Ramp) ................................................................ 2-10
To Set Pulse Width/Duty Cycle (Pulse) ............................................. 2-11

To Set Rising/Falling Edge (Pulse) .................................................... 2-12
To   Enable Channel Output .............................................................. 2-13
Align Phase ................................................................................... 2-14
Example: To Output Sine ................................................................ 2-15
To Output the Arbitrary Waveform .......................................................... 2-17
To Enable Arbitrary Waveforms........................................................ 2-17
To Select the Waveform .................................................................. 2-17
To Set Parameters .......................................................................... 2-22
To Output Harmonic ............................................................................. 2-23
Harmonic Overview ........................................................................ 2-23

RIGOL Contents
X                               DG800 User's Guide
To Set Fundamental Waveform Parameters ...................................... 2-24
To Select Harmonic Type ................................................................ 2-24
To   Set Harmonic Order ................................................................... 2-24
To Select Harmonic Amplitude ......................................................... 2-25
To Set Harmonic Phase .................................................................. 2-25
Example: To Output Harmonic ........................................................ 2-25
DC ...................................................................................................... 2-28
To Output Dual-tone Waveform ............................................................. 2-29
To Output Advanced Waveform ............................................................. 2-30
PRBS ............................................................................................ 2-30
RS232 .......................................................................................... 2-31
Sequence ...................................................................................... 2-32
Modulation .......................................................................................... 2-34
Amplitude Modulation (AM) ............................................................ 2-34
Frequency Modulation (FM) ............................................................ 2-38
Phase Modulation (PM) .................................................................. 2-41
Amplitude Shift Keying (ASK) .......................................................... 2-44
Frequency Shift Keying (FSK) .......................................................... 2-47
Phase Shift Keying (PSK) ................................................................ 2-50
Pulse Width Modulation (PWM) ....................................................... 2-53
Sweep................................................................................................. 2-56
To Enable the Sweep Function ........................................................ 2-56
Sweep Type .................................................................................. 2-56
Sweep Time .................................................................................. 2-58
Return Time .................................................................................. 2-58
Start Frequency and Stop Frequency ............................................... 2-59
Center Frequency and Frequency Span ............................................ 2-59
Sweep Trigger Source .................................................................... 2-60
Marker Freq .................................................................................. 2-61
Start Hold ..................................................................................... 2-62

Stop Hold ..................................................................................... 2-62
Burst .................................................................................................. 2-63
To Enable the Burst Function .......................................................... 2-63
B u r st  Typ e .................................................................................... 2-63
Burst Delay ................................................................................... 2-65
Burst Period .................................................................................. 2-66
Idle Level ...................................................................................... 2-66
Burst Trigger Source ...................................................................... 2-67
Gated Polarity ............................................................................... 2-68
Frequency Counter ............................................................................... 2-69
To Enable the Frequency Counter .................................................... 2-69
To Set the Frequency Counter ......................................................... 2-70
Store and Recall ................................................................................... 2-73
Storage System ............................................................................. 2-73
File Type ....................................................................................... 2-74
Categories .................................................................................... 2-74

Contents  RIGOL
DG800 User's Guide XI
File Operation ................................................................................ 2-75
Seamless Interconnection with Oscilloscope ..................................... 2-79
Channel Setting .................................................................................... 2-81
Output Setting ............................................................................... 2-81
Sync Setting .................................................................................. 2-83
Coupling Setting ............................................................................ 2-85
Waveform Combination .................................................................. 2-89
Common Settings ................................................................................. 2-90
System Setting .............................................................................. 2-90
Interface ....................................................................................... 2-92
System Info ................................................................................... 2-96
Option .......................................................................................... 2-96
Display Setting .............................................................................. 2-96
Print Setting .................................................................................. 2-97
System Utility Function ......................................................................... 2-98
To Restore Preset ........................................................................... 2-98
Channel Copy .............................................................................. 2-102
To Install the Option..................................................................... 2-103
To Lock the Keyboard ................................................................... 2-105
Chapter 3 Remote Control ..................................................................  3-1
Remote Control via USB ......................................................................... 3-2
Remote Control via LAN ......................................................................... 3-2
Remote Control via GPIB ........................................................................ 3-4
Chapter 4 Troubleshooting ................................................................. 4-1
Chapter 5 Appendix ............................................................................ 5-1
Appendix A: Accessories and Options ...................................................... 5-1
Appendix B: Warranty ............................................................................ 5-2
Index ....................................................................................................... 1





Chapter 1 Quick Guide                                                                                                                      RIGOL
DG800 User's Guide 1-1
## Chapter 1 Quick Start

This chapter briefly introduces the appearance and dimensions of DG800 series
function/arbitrary waveform generator, its front/rear panel, and user interface.

Contents in this chapter:
##  General Inspection
 Appearance and Dimensions
##  Front Panel Overview
##  Rear Panel Overview
 To Prepare for Use
##  User Interface
 To Use the Built-in Help System



RIGOL Chapter 1 Quick Guide
1-2                               DG800 User's Guide
## General Inspection

1． Inspect the packaging
If the packaging has been damaged, do not dispose the damaged packaging or
cushioning materials until the shipment has been checked for completeness and
has passed both electrical and mechanical tests.

The consigner or carrier shall be liable for the damage to the instrument
resulting from shipment. RIGOL would not be responsible for free
maintenance/rework or replacement of the instrument.

2． Inspect the instrument
In case of any mechanical damage, missing parts, or failure in passing the
electrical and mechanical tests, contact your RIGOL sales representative.

3． Check the accessories
Please check the accessories according to the packing lists. If the accessories
are damaged or incomplete, please contact your RIGOL sales representative.




























Chapter 1 Quick Guide RIGOL
DG800 User's Guide 1-3
Appearance and Dimensions



Front  View                                  Unit:  mm




Side  View                                  Unit:  mm











RIGOL Chapter 1 Quick Guide
1-4                               DG800 User's Guide
## Front Panel Overview







## Figure 1-1 Front Panel

## 1. Power Key
Turns on or off the generator.

## 2. Align Key
Performs the phase alignment operation. For details, refer to descriptions in
"Align Phase".

- CH1 Output Connector
BNC connector, with 50 Ω nominal output impedance.
When Output1 is enabled (the backlight turns on), this connector outputs
waveforms according to the current configuration of CH1.

## 4. Channel Control Area

It is used to control the output of CH1.
— Press this key to enable the output of CH1, the backlight
turns on. At this time, the [CH1] connector outputs the
waveforms according to the current configuration of CH1.
— Press this key again to disable the output of CH1, and the
backlight turns off.


It is used to control the output of CH2.
— Press this key to enable the output of CH2, the backlight
turns on. At this time, the [CH2] connector outputs the
waveforms according to the current configuration of CH2.
— Press this key again to disable the output of CH2, and the
backlight turns off.
1                                                                        2            3    4      5          6      7
13                          12    11          10                    9          8

Chapter 1 Quick Guide RIGOL
DG800 User's Guide 1-5
- CH2 Output Connector
BNC connector, with 50 Ω nominal output impedance.
When Output2 is enabled (the backlight turns on), this connector outputs
waveforms according to the current configuration of CH2.

## 6. Counter Measurement Signal Input Connector
BNC connector, with 1 MΩ input impedance. It is used to receive the signal
measured by the counter.




## 7. Frequency Counter
Enables or disables the frequency counter.
— Press this key to enable the frequency counter, and the backlight turns on
and blinks continuously.
— Press this key again to disable the frequency counter, and the backlight
turns off. At this time, the frequency counter is disabled.
Note: When the frequency counter is enabled, no waveforms will be output
from the CH2 connector. When the frequency counter is disabled, waveforms are
allowed to be output from the CH2 connector.

## 8. Arrow Key
— It is used to move the cursor to select the digit to be edited when you use
the knob to set the parameters (pressing down the knob can enter the
editing mode).
— In the user interface, it is used to move left or right the cursor.

## 9. Knob
— When you select a menu label in the interface, the knob can be used to
move the cursor down (clockwise) or up (counterclockwise).
— It can be used to increase (clockwise) or decrease (counterclockwise) the
value marked by the cursor when you use the knob to set the parameters
(pressing down the knob can enter the editing mode). Press down the knob
again to exit the editing mode.
— It can be used to select the desired waveform by moving the cursor with the
knob when you select the waveform (pressing the right arrow key will locate
the cursor to the right of the interface). Press down the knob to select the
desired waveform.
— When you store or read a file, it can be used to select a storage location or
select a file to be read. Press down the knob to unfold the currently selected
directory.
— It can be used to select the desired parameter by moving the cursor with
the knob when you set the common information (pressing the right arrow
key will locate the cursor to the right of the interface). Press down the knob
## CAUTION
To avoid damages to the instrument, the input signal voltage cannot
exceed ±2.5 V.

RIGOL Chapter 1 Quick Guide
1-6                               DG800 User's Guide
to select the desired parameter. Then, rotate the knob to modify the
parameter, and press it down again to confirm your modification.
— It is used to select the desired configuration type in the Preset interface.
Press down the knob to confirm your selection. At this time, a dialog box is
displayed. Use the knob to select the corresponding button, then press
down the knob to perform the corresponding operation (note that only
when the button turns green, can your operation on the knob be valid).

## 10. Menu Key
Enters the waveform mode selection interface.

## 11. Home Key
Enters the main interface of the instrument.

## 12. Function Keys

Restores the instrument to its preset state. At most 10 states can
be preset.


Locks or unlocks the front-panel keys and the touch screen. In
the unlocked state, press Lock to lock the front-panel keys and
the touch screen. At this time, except the Lock key, all other
keys on the front panel and the touch screen operation are
invalid. Press the Lock key again to unlock the keys and the
touch screen.


Used for manual trigger.
— The default trigger setting for the generator is Internal
trigger. In this mode, when you select the sweep or burst
mode, the generator outputs the waveforms continuously. At
this time, press the Trig key, and instrument automatically
switches to the manual trigger mode from auto trigger.
— Each time you press the Trig key, one sweep will be
triggered manually or one burst will be output.


It is used to set the utility function parameters and system
parameters.


Stores or recalls the instrument state or the user-defined
arbitrary waveform data. A non-vol   atile memory (Disk C) is built
in, and a USB storage device (Disk D) can be externally
connected.


Gets the help information of any front-panel keys and the help
information of the current interface.


Chapter 1 Quick Guide RIGOL
DG800 User's Guide 1-7
Note: When the instrument is in the remote mode, press this
key to return to the local mode.

## 13. LCD
4.3-inch TFT (480×272) color LCD display. The menu label and parameter
settings of the current function, system state, prompt messages, and other
information can be clearly displayed on the LCD. For details, refer to descriptions
in "User Interface".



RIGOL Chapter 1 Quick Guide
1-8                               DG800 User's Guide
## Rear Panel Overview




## Figure 1-2 Rear Panel

- [10MHz In/Out]
BNC female connector, with 50 Ω nominal impedance. Its function is determined
by the clock type used by the instrument.
1) When  internal  clock  source  is  selected,  this  connector  (as  10MHz  Out)
outputs the 10 MHz clock signal generated by the internal crystal oscillator
inside the generator.
2) When  external  clock  source  is  selected,  this  connector  (as  10MHz  In)
receives an external 10 MHz clock signal.
This connector is usually used to realize synchronization among multiple
instruments. For details about the signals mentioned above, please refer to
the descriptions in "Clock Source".

- [CH1/Sync/Ext Mod/Trig/FSK]
BNC female connector, with 50 Ω nominal impedance. Its function is determined
by the current working mode of CH1.
## 1) Sync
When the output of CH1 is enabled, this connector outputs the
corresponding sync signal that matches the current configuration of CH1.
For detailed information about the characteristics of the sync signals that
correspond to various output signals, refer to the descriptions in "Sync
## Setting".
## 2) Ext Mod
When AM, FM, PM, or PWM of CH1 is enabled and external modulation
source is selected, this connector receives an external modulation signal. Its
input impedance is 1000 Ω. For details, refer to descriptions in
"Modulation".

1                  2                  3              4              5                      6

Chapter 1 Quick Guide RIGOL
DG800 User's Guide 1-9
## 3) FSK
When ASK, FSK, or PSK of CH1 is enabled and external modulation source is
selected, this connector receives an external modulation signal whose
polarity can be set by users. Its input impedance is 1000 Ω. For details,
refer to descriptions in "Modulation".
## 4) Trig In
When Sweep or Burst of CH1 is enabled and external trigger source is
selected, this connector receives an external trigger signal whose polarity
can be set by users.
## 5) Trig Out
When Burst of CH1 is enabled, and the internal/manual trigger source is
selected, this connector outputs a trigger signal with specified edge type.

- [CH2/Sync/Ext Mod/Trig/FSK]
BNC female connector, with 50 Ω nominal impedance. Its function is determined
by the current working mode of CH2.
## 1) Sync
When the output of CH2 is enabled, this connector outputs the
corresponding sync signal that matches the current configuration of CH2.
For detailed information about the characteristics of the sync signals that
correspond to various output signals, refer to the descriptions in "Sync
## Setting".
## 2) Ext Mod
When AM, FM, PM or PWM of CH2 is enabled and external modulation
source is selected, this connector receives an external modulation signal. Its
input impedance is 1000 Ω. For details, refer to descriptions in
"Modulation".
## 3) FSK
When ASK, FSK, or PSK of CH2 is enabled and external modulation source is
selected, this connector receives an external modulation signal whose
polarity can be set by users. Its input impedance is 1000 Ω. For details,
refer to descriptions in "Modulation".
## 4) Trig In
When Sweep or Burst of CH2 is enabled and external trigger source is
selected, this connector receives an external trigger signal whose polarity
can be set by users.
## 5) Trig Out
When Burst of CH2 is enabled, and the internal/manual trigger source is
selected, this connector outputs a trigger signal with specified edge type.

## 4. USB HOST
Supports FAT32 format Flash type USB storage device, RIGOL TMC digital
oscilloscope (DS), and the USB-GPIB interface converter.
 USB storage device: reads the waveform files or state files saved in the USB
storage device; or stores the current instrument states or edited waveform
data into the USB storage device. Besides, the contents displayed on the

RIGOL Chapter 1 Quick Guide
1-10                               DG800 User's Guide
screen can also be saved to the USB storage device in the format of an
image (*.Bmp).
 TMC DS: seamlessly interconnects with the RIGOL DS that meets the TMC
standard. Reads and stores the waveform data collected by the DS and
rebuilds waveforms without distortion.
 USB-GPIB interface converter (optional accessory): extends the GPIB
interface for RIGOL instruments that integrates the USB HOST interface
but not the GPIB interface.

## 5. USB DEVICE
It is used to connect the generator to a computer which can control the
generator remotely by using PC software or by programming.

- AC Power Cord Connector
The rated AC power source supported by the signal generator is (100-127 V,
45  -440 Hz) or (100-240 V, 45-65 Hz), and its maximum input power shall not
exceed 30 W. The specification of the fuse is 250 Vac, T4.0 A.

Chapter 1 Quick Guide RIGOL
DG800 User's Guide 1-11
To Prepare for Use

To Connect to AC Power

Please use the power cord provided in the accessories to connect the signal
generator to the AC power source, as shown in the figure below. The rated AC power
source supported by the signal generator is (100-127 V, 45  -440Hz) or (100-240 V,
45  -65Hz), and its maximum input power shall not exceed 30 W. When the signal
generator is connected to the AC power source via the power cord, the instrument
automatically adjusts itself to within the proper voltage range, and you do not need
to select the voltage range manually.




## CAUTION
To avoid electric shock, ensure that the instrument is correctly
grounded.


## Turn-on Checkout

After connecting the instrument to the power source properly, press
on the front
panel to start the signal generator. During the start-up, the instrument will undergo
the initialization and self-check process. Then, it will enter a default interface. If you
still fail to power on the instrument normally, refer to the methods in
"Troubleshooting" to resolve the problem.


To Set the System Language

DG800 arbitrary waveform generator supports multiple languages. You can press
Utility  System Setting, and then select a desired language from the
"Language" drop-down list.

RIGOL Chapter 1 Quick Guide
1-12                               DG800 User's Guide
## User Interface

The DG800 user interface is shown in the following figure.






## Figure 1-1 User Interface

## 1. Channel Output Configuration Status Bar
Displays the current output configuration of the channel.














Note: Two channels can be enabled simultaneously, but you cannot select both
channels at the same time.



## Output Impedance Type:
High impedance: displays HighZ.
Load: displays impedance (the
default is 50 Ω and the range is
from 1 Ω to 10 kΩ).
## Channel Output State:
ON: illuminated in yellow.
OFF: grayed out.
## Selected Waveform:
Sine/Square/Ramp/Pulse/Noise/Prbs/Dualtone/Harm
/Rs232/DC/Arb/Sequence
Modulation Type: AM/FM/PM/ASK/FSK/PSK/PWM
Sweep Type: Linear/Log/Step
Burst Type: Ncycle/Infinite/Gated
1                                                      2                              3
## 6                  5                              4
## 7


## 8


## 9


## 10

Chapter 1 Quick Guide RIGOL
DG800 User's Guide 1-13
## 2. Interface Switchover
When left point is grayed out and the right point is illuminated, sliding right on
the touch screen can switch to the waveform selection interface. When the left
point is illuminated and the right point is grayed out, sliding left on the touch
screen can switch to the current interface of waveform parameter setting.

## 3. Information Setting
: opens the Store interface.
: opens the Utility interface.
: performs the channel copy function.
: performs the screen print operation.

## 4. Status Bar
:  indicates that the front-panel keys and the screen are locked.
:  indicates that the beeper is disabled.
: indicates that the instrument is in programming-controlled mode.
: indicates that the instrument has been successfully connected to the local
area network by using the network cable.
: indicates that a USB storage device is found.

## 5. Waveform
Displays the currently selected waveform of each channel.

## 6. Interface Label
Displays the label of the current interface.

## 7. Frequency
Displays the frequency of the current waveform of each channel. Tap the Freq
parameter input field to modify the parameter with the pop-up numeric keypad.
You can also use the arrow keys and the knob to modify the parameter.

## 8. Amplitude
Displays the amplitude of the current waveform of each channel. Tap the Ampl
parameter input field to modify the parameter with the pop-up numeric keypad.
You can also use the arrow keys and the knob to modify the parameter.

## 9. Offset
Displays the DC offset of the current waveform of each channel. Tap the Offset
parameter input field to modify the parameter with the pop-up numeric keypad.
You can also use the arrow keys and the knob to modify the parameter.



RIGOL Chapter 1 Quick Guide
1-14                               DG800 User's Guide
## 10. Phase
Displays the phase of the current waveform of each channel. Tap the Phase
parameter input field to modify the parameter with the pop-up numeric keypad.
You can also use the arrow keys and the knob to modify the parameter.

Chapter 1 Quick Guide RIGOL
DG800 User's Guide 1-15
To Use the Built-in Help System

DG800 series provides the help information for each front-panel function menu and
the current display interface. You can view the help information if you have any
questions during the operation process.

- Obtain the help information of the front panel keys
To get the help information about any front-panel key or menu softkey,
press the Help/Local key first, and then press the desired key for the help
information. Then, the corresponding help information is displayed.

- Obtain the common help topics
Press Help/Local on the front panel, and then the following interface is
displayed below. Ta p   "Help" to enter the help interface. At this time, you can
tap on the touch screen to move up and down the help items or rotate the knob
to scroll up and down the list to select the desired help item. Then, the help
information for the item is displayed in the interface.



- Obtain the descriptions of the data in the interface
Press Help/Local on the front panel to enter the interface, as shown above.
Ta p   "Center" to view the descriptions for the data in the center of the current
interface. Tap "Top" to view the descriptions for the data in the top part of the
current interface. Tap "Bottom" to view the descriptions for the data in the
bottom part of the current interface. Tap "Guide" to enter the guide interface.

- Page up/down operation
When the help information is displayed in multiple pages, you can tap to move
up and down the touch screen to view the help information.

- Close the current help information
When the help information is displayed in the interface, press Help/Local on
the front panel to close the help information currently displayed on the screen.



Chapter 2 Front Panel Operations  RIGOL
DG800 User's Guide 2-1
## Chapter 2 Front Panel Operations

Introduces the main functions and operation methods of DG800.

Contents in this chapter:
##  To Output Basic Waveform
 To Output the Arbitrary Waveform
##  To Output Harmonic
##  DC
##  To Output Dual-tone Waveform
##  To Output Advanced Waveform
##  Modulation
##  Sweep
##  Burst
##  Frequency Counter
 Store and Recall
##  Channel Setting
##  Common Settings
##  System Utility Function



RIGOL Chapter 2 Front Panel Operations
2-2                               DG800 User's Guide
## To Output Basic Waveform

DG800 series can output basic waveforms (including Sine, Square, Ramp, Pulse, and
Noise) from one channel or from both two channels at the same time. At start-up,
the dual channels are configured to output a sine waveform with 1 kHz frequency
and 5 Vpp amplitude by default. Users can configure the instrument to output
various basic waveforms.

## To Select Output Channel

At start-up, the instrument displays the CH1 parameter interface by default. You can
press Output1 or Output2 (also, you can tap the channel output configuration
status bar or ) to switch between CH1 and CH2 as the
currently selected channel.

After the desired channel is selected, you can configure the waveform and
parameters of the selected channel.

## Key Points:

CH1 and CH2 cannot be both selected at the same time. You can first select CH1,
after configuring the waveform and parameters of CH1, then select CH2 for
configuration.



Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-3
## To Select Basic Waveform

DG800 can output 5 basic waveforms, including Sine, Square, Ramp, Pulse and Noise.
Press Menu on the front panel, then tap the touch screen to select the desired
waveform. After selecting the desired waveform, you are automatically directed to
the waveform parameter setting interface. To go back to the waveform selection
interface, tap to slide right or press the Menu key on the front panel. At start-up,
Sine is selected by default.

Ta b l e   2-1 Basic Waveforms
## Basic Waveforms
## Sine Square Ramp Pulse Noise

## Function Name
## Sine Square Ramp Pulse Noise
Freq/Period
## √ √ √ √

Ampl/HighL
## √ √ √ √ √
Offset/LowL
## √ √ √ √ √
## Start Phase
## √ √ √ √

## Align Phase
## √ √ √ √

## Duty

## √

## √

## Symmetry

## √

Width/Duty

## √

RisEdge

## √

FallEdge

## √



RIGOL Chapter 2 Front Panel Operations
2-4                               DG800 User's Guide
To Set Frequency/Period

Frequency is one of the most important parameters of basic waveforms. For different
ins trument models and waveforms, the setting ranges of frequency are different. The
default frequency is 1 kHz.

Sine Square Ramp Pulse Noise (-3 dB)
## DG812/DG811
1 μHz to
10 MHz
1 μHz to
5 MHz
1 μHz to
200 kHz
1 μHz to
5 MHz
100 MHz
## Bandwidth
## DG822/DG821
1 μHz to
25 MHz
1 μHz to
10 MHz
1 μHz to
500 kHz
1 μHz to
10 MHz
100 MHz
## Bandwidth
## DG832/DG831
1 μHz to
35 MHz
1 μHz to
10 MHz
1 μHz to
1 MHz
1 μHz to
10 MHz
100 MHz
## Bandwidth

The frequency displayed on the screen is the default value or the frequency
pr  eviously set. When the instrument function is changed, if this frequency is valid
under the new function, the instrument will still use this frequency; otherwise, the
instrument would display a prompt message and set the frequency to the frequency
upper limit of the new function automatically.

Ta p   t h e   Freq parameter input field to input the desired frequency value with the
numeric keypad, then select the unit. Ta p   "Ok".
 The frequency units available are MHz, kHz, Hz, mHz, and μHz.
 Tap the label again to switch to Period setting.
 The period units available are s, ms, μs, and ns.

You can also use the arrow keys and the knob to set the parameter value: press
down the knob to enter the editing mode, use the arrow keys to move the cursor to
select the digit to be edited, and then rotate the knob to modify the value. Besides,
you can use the knob to switch between different parameters.



Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-5
To Set Amplitude/High Level

The amplitude setting range is limited by the "Impedance" and "Freq/Period" settings.
By default, it is 5 Vpp.

The amplitude displayed on the screen is the default value or the amplitude
previously set. When the instrument configuration (e.g. frequency) is changed, if this
amplitude is valid, the instrument will still use this amplitude; otherwise, the
instrument would display a prompt message and set the amplitude to the amplitude
upper limit of the new configuration automatically. You can also use "High Level" or
"Low Level" to set the amplitude.

Ta p   t h e   Ampl parameter input field to input the desired frequency value with the
numeric keypad, then select the unit. Tap "Ok".
 The amplitude units available are Vpp, mVpp, Vrms, mVrms, and dBm (invalid in
HighZ).
 Tap the label again to switch to High Level setting.
 The high level units available are V and mV.

You can also use the arrow keys and the knob to set the parameter value: press
down the knob to enter the editing mode, use the arrow keys to move the cursor to
select the digit to be edited, and then rotate the knob to modify the value. Besides,
you can use the knob to switch between different parameters.

## Key Points:

1． How to convert the amplitude in Vpp to the corresponding value in
## Vrms?

## Method:
Vpp is the unit for signal peak-peak value and Vrms is the unit for
root-mean-
square value. The default unit is Vpp. When you set the amplitude,
input a decimal point in the numeric keypad, and then select a unit. Tap "Ok"
to switch to the unit of the current amplitude.

## Remarks:
For different waveforms, the relation between Vpp and Vrms is different. The
relation of the two units is as shown in the figure below (take sine waveform
as an example).
Vpp=2Vamp
Vrms=0.707Vamp
## Vamp


RIGOL Chapter 2 Front Panel Operations
2-6                               DG800 User's Guide
According to the figure above, the conversion relation between Vpp and Vrms
fulfills the following equation:
Vrms22Vpp=


For example, if the current amplitude is 5 Vpp, input a decimal point in the
numeric keypad, and then select a unit Vrms. Tap "Ok". Then, it can be
conv
erted to a value with Vrms as the unit. For sine waveform, the converted
value is 1.768 Vrms.

2． How to set the amplitude of the waveform in dBm?

## Method:
1) Press Output1 or Output2 (also, you can tap the channel output
configuration status bar or ) to select the desired
channel.
2) Tap the channel output configuration status bar
(CH1) or
(CH2). In the channel setting interface, tap the OutputSet
menu label and select "Off". Then use the numeric keypad to set a proper
load value.
3) Select the desired waveform, tap the Ampl menu label, and then input
the desired value by using the numeric keypad. Then select the unit
"dBm" from the pop-up menu.

## Remarks:
dBm is the unit for signal power absolute value，
and the conversion relation
between dBm and Vrms fulfills the following equation:
## 2
## 1
10 lg()
## 0.001
## Vrms
dBm
## RW
## =×

Wherein, R represents the channel output impedance value and it must be a
specific value, so the u
nit dBm is not available when the output impedance is
"HighZ".

For example, if the current output impedance is 50 Ω and the amplitude is
1.768 Vrms (i.g. 5 Vpp), input a decimal point in the numeric keypad and then
select "dBm". Tap "Ok" to convert the amplitude value to the corresponding
value in dBm. The converted value is 17.9601 dBm.






Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-7
To Set Offset/Low Level

The DC offset setting range is limited by the "Impedance" and "Amplitude/High
Level" settings. The default value is 0 V
dc
## .

The DC offset voltage displayed on the screen is the default value or the offset
previously set. When the instrument configuration (e.g. impedance) is changed, if
this offset is valid, the instrument will still use this offset; otherwise, the instrument
would display a prompt message and set the offset to the offset upper limit of the
new configuration automatically.

Ta p   t h e   Offset parameter input field to input the desired offset value with the
numeric keypad, then select the unit. Tap "Ok".
 The DC offset voltage units available are V
dc
and mV
dc
## .
 Tap the label again to switch to Low Level setting.
 The low level should be at least 1 mV smaller than the high level (output
impedance: 50 Ω).
 The low level units available are V and mV.

You can also use the arrow keys and the knob to set the parameter value: press
down the knob to enter the editing mode, use the arrow keys to move the cursor to
select the digit to be edited, and then rotate the knob to modify the value. Besides,
you can use the knob to switch between different parameters.



RIGOL Chapter 2 Front Panel Operations
2-8                               DG800 User's Guide
## To Set Start Phase

The setting range of start phase is from 0° to 360°. The default is 0°.

The start phase displayed on the screen is the default value or the phase previously
set. When the instrument function is changed, the new function will still use this
phase.

Ta p   t h e   Phase parameter input field to input the desired phase value with the
numeric keypad, then select the unit "°". Tap "Ok".

You can also use the arrow keys and the knob to set the parameter value: press
down the knob to enter the editing mode, use the arrow keys to move the cursor to
select the digit to be edited, and then rotate the knob to modify the value. Besides,
you can use the knob to switch between different parameters.



Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-9
To Set Duty Cycle (Square)

Duty cycle is defined as the percentage that the high level takes up in the whole
period (as shown in the figure below). This parameter is only available when Square
or Pulse is selected.

## T
t
Duty Cycle=t/T*100%


The available range of the duty cycle is from 0.01% to 99.99% (limited by the
current frequency setting). The default is 50%.

Ta p   t h e   Duty parameter input field to input the desired duty cycle value with the
numeric keypad, then select the unit "%". Tap "Ok".

You can also use the arrow keys and the knob to set the parameter value: press
down the knob to enter the editing mode, use the arrow keys to move the cursor to
select the digit to be edited, and then rotate the knob to modify the value. Besides,
you can use the knob to switch between different parameters.



RIGOL Chapter 2 Front Panel Operations
2-10                               DG800 User's Guide
To Set Symmetry (Ramp)

Symmetry  is defined as the percentage that the rising period of the ramp takes up in
the whole period (as shown in the figure below). This parameter is only available
when Ramp is selected.

## T
t
Symmetry=t/T*100%


The setting range of symmetry is from 0% to 100%. The default is 50%.

Ta p   t h e   Symm parameter input field to input the desired symmetry value with the
numeric keypad, then select the unit "%". Tap "Ok".

You can also use the arrow keys and the knob to set the parameter value: press
down the knob to enter the editing mode, use the arrow keys to move the cursor to
select the digit to be edited, and then rotate the knob to modify the value. Besides,
you can use the knob to switch between different parameters.


Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-11
To Set Pulse Width/Duty Cycle (Pulse)

Pulse width is defined as the time from the 50% threshold of a pulse's rising edge to
the 50% threshold of the next falling edge (as shown in the figure below).

















The settable range of the pulse width is from 16 ns to 999.999982118 ks (limited by
"minimum pulse width" and "pulse period"). The default is 500 μs.
##  Pulse Width ≥ Minimum Pulse Width
##  Pulse Width < Pulse Period - 2 × Minimum Pulse Width

Pulse duty cycle is defined as the percentage that the pulse width takes up in the
whole pulse period.

Pulse duty cycle and pulse width are correlative. Modifying either of them (pulse duty
cycle or pulse width) will automatically affect the other. The settable range of the
pulse duty cycle is from 0.001% to 99.999% (limited by "minimum pulse width" and
"pulse period"). The default is 50%.
##  Pulse Duty Cycle ≥ 100 × Minimum Pulse Width ÷ Pulse Period
##  Pulse Duty Cycle < 100 × (1 - 2 × Minimum Pulse Width ÷ Pulse Period)

Ta p   t h e   Width parameter input field to input the desired pulse width value with the
numeric keypad, then select the unit. Tap "Ok".
 The pulse width units available are s, ms, μs, and ns.
 Tap this menu label again to switch to duty cycle setting.

You can also use the arrow keys and the knob to set the parameter value: press
down the knob to enter the editing mode, use the arrow keys to move the cursor to
select the digit to be edited, and then rotate the knob to modify the value. Besides,
you can use the knob to switch between different parameters.
## Pulse
## 10%
tRise
tFall
## 90%
## 50%
## Pulse Period

RIGOL Chapter 2 Front Panel Operations
2-12                               DG800 User's Guide
To Set Rising/Falling Edge (Pulse)

The rising edge time is defined as the duration of the pulse amplitude rising from
10% to 90% threshold, while falling edge time is defined as the duration of the pulse
amplitude moving down from 90% to 10% threshold (as shown in the figure below).

The setting range of rising/falling edge time is limited by the currently specified pulse
width limit (as shown in the formula below). DG800 will automatically adjust the
edge time to match the specified pulse width if the value currently set exceeds the
limit value.

Rising/Falling Edge Time ≤ 0.625 × Pulse Width


















Ta p   the RisEdge or FallEdge parameter input field. Use the numeric keypad to
input the desired value and then select the desired unit from the pop-up menu.
 The pulse width units available are sec, msec, μsec, and nsec.
 The rising and falling edge time are independent of each other, and users can
set them separately.

You can also use the arrow keys and the knob to set the parameter value: press
down the knob to enter the editing mode, use the arrow keys to move the cursor to
select the digit to be edited, and then rotate the knob to modify the value. Besides,
you can use the knob to switch between different parameters.


## Pulse
## 10%
tRise
tFall
## 90%
## 50%
## Pulse Period

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-13
## To Enable Channel Output

After configuring the parameters of the waveform selected, enable the channel to
output the waveforms.

Before enabling channel output, you can also tap
or   and
then tap the corresponding menu label in the channel setting interface to set the
parameters related with the channel output. For details, refer to descriptions in
"Channel Setting".

Press Output1 or Output2 on the front panel, and then the backlight turns on. You
can also tap the channel output configuration status bar   or
enable the channel output in the channel setting interface. When the channel status
bar is highlighted, (i.g.
), the configured waveforms are output from the
corresponding output connector on the front panel.






























RIGOL Chapter 2 Front Panel Operations
2-14                               DG800 User's Guide
## Align Phase

DG800 series dual-channel function/arbitrary waveform generator enables you to
align the phases of the two channels. Press Align on the front panel, then the
instrument will re-configure the two channels and enable the generator to output
with specified frequency and start phase.

For two signals whose frequencies are the same or in multiple relationship, this
operation can align their phases. For example, assume a sine waveform (1 kHz, 5
Vpp, 0°) is output from CH1, while another one (1 kHz, 5 Vpp, 180°) from CH2. Use
the oscilloscope to acquire the waveforms of the two channels and stably display the
waveforms. It can be found that the phase deviation between the two waveforms is
no longer 180°. At this point, press Align on the generator and the waveforms
shown on the oscilloscope will have a phase deviation of 180° without manual
adjustment of the start phase of the generator.


## Figure 2-1 Before Aligning Phase


## Figure 2-2 After Aligning Phase


## CH1
## CH2
## CH1
## CH2

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-15
## Example: To Output Sine

This section mainly introduces how to output Sine waveforms (frequency 20 kHz,
amplitude 2.5 Vpp, offset 500 mV
dc, start phase 90°) from the [CH1] connector.

- Select the output channel: Press Output1 on the front panel or tap the
channel output configuration status bar to select CH1.

- Select Sine waveforms: Press Menu on the front panel, and then the
waveform selection interface is displayed. Tap Continuous and then select the
"Sine" icon to go to the sine waveform parameter setting interface
automatically.

- Set frequency: Ta p  t h e  Freq parameter input field to input 20 with the pop-up
numeric keypad, and then select the unit "kHz". Tap "Ok".

- Set amplitude: Ta p   t h e   Ampl parameter input field to input 2.5 with the
pop-up numeric keypad, and then select "Vpp" as the unit. Tap "Ok".

- Set offset voltage: Ta p  t h e  Offset parameter input field to input 500 with the
pop-up   numeric keypad, and then select "mVdc" as the unit. Tap "Ok".

- Set start phase: Ta p   t h e   Phase parameter input field to input 90 with the
pop-up numeric keypad, and then select "°" as the unit. Tap "Ok".

- Enable channel output: Press Output1 and the backlight turns on. Also, you
can tap the channel output configuration status bar   to enable the
channel output. Then, the channel status is highlighted (i.g.
), and
the Sine signal is output from the [CH1] connector based on the current
configurations.

- Observe the output waveform: Connect the [CH1] connector of DG800 to
the oscilloscope by using the BNC cable. The waveform is as shown in the figure
below.


RIGOL Chapter 2 Front Panel Operations
2-16                               DG800 User's Guide

## Figure 2-3 Sine Waveform

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-17
To Output the Arbitrary Waveform

DG800 can output built-in waveforms from a single channel or from two channels at
the same time. The 160 kinds of built-in arbitrary waveforms are stored in the
internal non-volatile memory.

## To Enable Arbitrary Waveforms

Press Menu  Continuous  "Arb" to enable arbitrary waveform function and
open the arbitrary waveform selection interface, as shown in the figure below.


## Figure 2-4 Arbitrary Waveform Selection Interface


To Select the Waveform

DG800 allows users to select 160 built-in waveforms and arbitrary waveforms stored
in the internal or external memory of the instrument.

## Key Points:

After selecting the desired waveform, press the corresponding channel output
control key (Output1 or Output2), and the specified waveform will be output
from the channel. For details, refer to descriptions in "To Enable Channel
## Output
".   Note that when the frequency of the arbitrary waveforms is greater than
1 MHz, some waveforms will be distorted.






RIGOL Chapter 2 Front Panel Operations
2-18                               DG800 User's Guide
## Built-in Waveform

DG800 has 160 built-in arbitrary waveforms, as shown in Ta b l e   2-2
. In the arbitrary
waveform selection interface, tap the Engineering, Medical, AutoElec, or Maths
menu label to select the corresponding type. Tap or rotate the knob (pressing the
right arrow key will locate the cursor to the right of the interface) to select the
desired waveform (the selected waveform is highlighted). The waveforms under the
Common menu label are most frequently selected ones by users. At most, 8
waveforms can be stored.

Ta b l e   2-2 160 Built-in Arbitrary Waveforms
## Type Waveform Remarks

## Engineering

Sinc Sinc function
Lorentz Lorentz function
Log Logarithm function and the base is 10
GausPul Gauss pulse
NegRamp Negative ramp
NPulse Negative pulse
PPulse Positive pulse
SineTra Sine-Tra waveform
SineVer Sine-Ver waveform
StairDn Stair-down waveform
StairUD Stair-up and stair-down waveform
StairUp Stair-up waveform
Trapezia Trapezia waveform
AmpALT Gain oscillation curve
AttALT Attenuation oscillation curve
RouHalf RoundHalf Wave
RousPM RoundsPM Waveform
BlaWave
Time-velocity curve of explosive
vibration
DampOsc
Time-displacement curve of damped
oscillation
SwigOsc
Kinetic energy- time curve of swing
oscillation
Dischar Discharge curve of Ni-MH battery
## Pahcur
Current waveform of DC brushless
motor
Combin Combination function
SCR SCR firing profile
Bworth Butterworth filter
Chshev1 Chebyshev1 filter

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-19
Chshev2 Chebyshev2 filter
TV TV signal
Voice Voice signal
Surge Surge signal
Radar Radar signal
DualTone Dual-tone signal
Ripple Power ripple
Quake Analog quake waveform
Gamma Gamma signal
StepResp Step-response signal
BandLim Bandwidth-limited signal
CPulse C-Pulse signal
CWPulse CW pulse signal
GateVibr Gate self-oscillation signal
LFMPulse Linear FM pulse signal
MCNoise Mechanical construction noise
AM Sectioned sine AM signal
FM Sectioned sine FM signal
PFM Sectioned pulse FM signal
PM Sectioned sine PM signal
PWM Sectioned PWM signal

## Medical

Cardiac Cardiac signal
EOG Electro-oculogram
EEG Electroencephalogram
EMG Electromyogram
## Pulgram Pulsilogram
ResSpd Speed curve of the respiration
ECG1 Electrocardiogram 1
ECG2 Electrocardiogram 2
ECG3 Electrocardiogram 3
ECG4 Electrocardiogram 4
ECG5 Electrocardiogram 5
ECG6 Electrocardiogram 6
ECG7 Electrocardiogram 7
ECG8 Electrocardiogram 8
ECG9 Electrocardiogram 9
ECG10 Electrocardiogram 10
ECG11 Electrocardiogram 11
ECG12 Electrocardiogram 12
ECG13 Electrocardiogram 13
ECG14 Electrocardiogram 14
ECG15 Electrocardiogram 15

RIGOL Chapter 2 Front Panel Operations
2-20                               DG800 User's Guide
LFPulse
Waveform of the low frequency pulse
electrotherapy
Te n s 1
Waveform 1 of the nerve stimulation
electrotherapy
Te n s 2
Waveform 2 of the nerve stimulation
electrotherapy
Te n s 3
Waveform 3 of the nerve stimulation
electrotherapy

AutoElec

## Ignition
Ignition waveform of the automotive
motor
SP Automotive starting profile with ringing
## VR
Automotive supply voltage profile for
resetting
## TP1
Automotive transients arising from
disconnection
## TP2A
Automotive transients arising from
inductance in wiring
## TP2B
Automotive transients arising from the
ignition switching off
## TP3A
Automotive transients arising from
switching
## TP3B
Automotive transients arising from
switching
## TP4
Automotive working profile during
start-up
## TP5A
Automotive transients arising from
cut-off of battery power
## TP5B
Automotive transients arising from
cut-off of battery power

## Maths

Airy Airy function
Besseli Bessel functions of the first kind
Bessely Bessel functions of the second kind
Cubic Cubic function
Dirichlet Dirichlet function
Erf Error function
Erfc Complementary error function
ErfcInv Inverted complementary error function
ErfInv Inverted error function
ExpFall Exponential fall function
ExpRise Exponential rise function
HavSin HaverSine function

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-21
Laguerre 4-times Laguerre polynomial
Legend 5-times Legend polynomial
## Versiera Versiera
ARB_X2 Square function
## Gauss
Gaussian distribution or normal
distribution
Weibull Weibull distribution
LogNorm Logarithmic normal distribution
Laplace Laplace distribution
Maxwell Maxwell distribution
Rayleigh Rayleigh distribution
Cauchy Cauchy distribution
CosH Hyperbolic cosine
CosInt Integral cosine
## Cot Cotangent
CotHCon Concave hyperbolic cotangent
CotHPro Protuberant hyperbolic cotangent
CscCon Concave cosecant
CscPro Protuberant cosecant
CscHCon Concave hyperbolic cosecant
CscHPro Protuberant hyperbolic cosecant
RecipCon Concave reciprocal
RecipPro Protuberant reciprocal
SecCon Concave secant
SecPro Protuberant secant
SecH Hyperbolic secant
SinH Hyperbolic sine
SinInt Integral sine
Sqrt Square root
Ta n Tangent
Ta n H Hyperbolic tangent
AbsSine Absolute value of sine
AbsSinH Absolute value of half sine
ACos Arc cosine
ACosH Arc hyperbolic cosine
ACotCon Concave arc cotangent
ACotPro Protuberant arc cotangent
ACotHCon Concave arc hyperbolic cotangent
ACotHPro Protuberant arc hyperbolic cotangent
ACscCon Concave arc cosecant
ACscPro Protuberant arc cosecant
ACscHCon Concave arc hyperbolic cosecant
ACscHPro Protuberant arc hyperbolic cosecant
ASecCon Concave arc secant

RIGOL Chapter 2 Front Panel Operations
2-22                               DG800 User's Guide
ASecPro Protuberant arc secant
ASecH Arc hyperbolic secant
ASin Arc Sinc
ASinH Arc hyperbolic sine
ATa n Arc tangent
ATa n H Arc hyperbolic tangent
Bartlett Bartlett window
BarWin Modified Bartlett-Hann window
Blkman Blackman window
BlkmanH Blackman-Harris window
BohWin Bohman  window
Boxcar Rectangular window
ChebWin Chebyshev window
FlatWin Flat Top weighted window
Ham Hamming window
Hanning Hanning window
Kaiser Kaiser window
NutWin
Nuttall-defined minimum 4-term
Blackman-Harris window
ParWin Parzen window
Ta y W i n Taylor window
Triang Triangle window (Fejer window)
TukWin Tukey (tapered cosine) window


## To Set Parameters

After selecting the desired waveform, you are automatically directed to the waveform
parameter setting interface.

- Freq/Period: sets the output frequency/period of the arbitrary waveform.

- Ampl/HighL: sets the output amplitude/high level of the arbitrary waveform.

- Offset/LowL: sets the output offset/low level of the arbitrary waveform.

- Phase: sets the output start phase of the arbitrary waveform.

Please refer to "To Output Basic Waveform"   to configure the parameters and
output for the channel.





Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-23
## To Output Harmonic

DG800 can be used as a harmonic generator to output harmonic with specified order,
amplitude and phase. It is usually used in the test of harmonic detector device or
harmonic filter device. This section introduces how to configure the generator to
output harmonic.

## Harmonic Overview

According to Fourier transform, time domain waveform is the superposition of a
series of sine waveforms, as shown in the equation below:

## ......)2sin()2sin()2sin()(
## 333222111
## ++++++=
φπφπφπ
tfAtfAtfAtf


Generally, component with
## 1
f
frequency is called fundamental waveform,
## 1
f
is the
fundamental waveform frequency,
## 1
## A
is the fundamental waveform amplitude, and
## 1
φ
is the fundamental waveform phase. The frequencies of the other components
(called harmonics) are all integral multiple of the fundamental waveform frequency.
Components whose frequencies are odd multiples of the fundamental waveform
frequency are called odd harmonics, and components whose frequencies are even
multiples of the fundamental waveform frequency are called even harmonics.

At most, 8th harmonic can be output by DG800. After selecting CH1 or CH2, press
Menu  Continuous  "Harm" to enter the harmonic setting menu. You can set
fundamental waveform parameters, select the type of output harmonic, specify the
highest order of harmonic, and set the amplitude and phase of each order of
harmonic.

After completing the harmonic parameters setting, press Output1, and the
backlight turns on. The instrument outputs the specified harmonic from the
corresponding output terminal. For details, refer to descriptions in "
## To Enable
## Channel Output".












RIGOL Chapter 2 Front Panel Operations
2-24                               DG800 User's Guide
## To Set Fundamental Waveform Parameters

DG800 allows users to set various fundamental waveform parameters such as
frequency, period, amplitude, DC offset voltage, high level, low level, and start phase.
It also supports align phase operation. To set the above fundamental waveform
parameters, refer to descriptions in "To Output Basic Waveform".


## To Select Harmonic Type

DG800 can output even harmonic, odd harmonic, both harmonics, and user-defined
order of harmonic. After entering the harmonic setting interface, tap the Type
parameter selection field to select the desired harmonic type.

- Even: outputs fundamental waveform and even harmonics.

- Odd: outputs fundamental waveform and odd harmonics.

- Both: outputs fundamental waveform and all the harmonics in order.

- User: outputs the user-defined orders of harmonics. The highest order is 8.

8 bits binary data are used to represent the output status of the 8 orders of
harmonics respectively. Wherein, 1 represents enabling the output of the
corresponding harmonic, and 0 represents disabling the output of the
corresponding harmonic. You only need to tap the User parameter input field,
and then modify the value of each data bit by using the numeric keypad (note
that the leftmost bit representing fundamental waveform is always X and cannot
be modified). For example, if you set the 8 bits data to X001 0001, it indicates
that the fundamental waveform, 4th and 8th orders of harmonics are output.

Note: The actually output harmonics is determined by the currently specified
harmonic order and harmonic type.


## To Set Harmonic Order

The highest order of harmonic output from DG800 cannot be greater than the
specified value.

After entering the harmonic setting interface, tap the Count parameter selection
field to input a value with numeric keypad.
 The range is limited by the maximum output frequency of the instrument and
current fundamental waveform frequency.
 Range: 2 to maximum output frequency ÷ fundamental waveform

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-25
frequency, an integer.
 The maximum is 8.

You can also use the arrow keys and the knob to set the parameter value: press
down the knob to enter the editing mode, use the arrow keys to move the cursor to
select the digit to be edited, and then rotate the knob to modify the value. Besides,
you can use the knob to switch between different parameters.


## To Select Harmonic Amplitude

After entering the harmonic setting interface, tap the Harm Ampl parameter input
field to set the amplitude of each order of harmonic.

1) No.: selects the sequence number of the harmonic to be set.

2) Harm Ampl: sets the amplitude of the specified order of harmonic. Use the
numeric keypad to input the amplitude value, and then select the desired unit.
Ta p   "Ok". The amplitude units available are Vpp, mVpp, Vrms, mVrms, and dBm
(invalid in HighZ).


## To Set Harmonic Phase

After entering the harmonic setting interface, tap the Harm Phase parameter input
field to  set the phase of each order of harmonic.

- No.: selects the sequence number of the harmonic to be set.

- Harm Phase: sets the phase of the specified order of harmonic. Use the
numeric keypad to input the phase value, and then select the desired unit "°".
Ta p "Ok".


## Example: To Output Harmonic

This section introduces how to output 2th order of harmonic (harmonic amplitude: 2
Vpp, harmonic phase: 30°) and 4th orders of harmonic (harmonic amplitude: 1 Vpp,
harmonic phase: 50°) from the [CH1] connector.

- Select the output channel: Press Output1 on the front panel or tap the
channel output configuration status bar   to select CH1. At this time,
the channel is indicated in red in the status bar.


RIGOL Chapter 2 Front Panel Operations
2-26                               DG800 User's Guide
- Set fundamental waveform parameters: In this example, various
parameters of the fundamental waveform take the default values. You can also
refer to descriptions in "To Output Basic Waveform"   to set various
fundamental waveform parameters such as frequency/period, amplitude/high
lev  el, offset/low level, and start phase.

- Enable harmonic function: Press Menu on the front panel, and then the
waveform selection interface is displayed. Tap Continuous and then select the
"Harm" icon to go to the harmonic parameter setting interface automatically.

- Set harmonic count: In the harmonic parameter setting interface, tap the
Count parameter input field to input a value 5 with pop-up numeric keypad. Tap
"Ok".

- Select the harmonic type: In the harmonic parameter setting interface, tap
the Type parameter selection field to select the desired even harmonic.

- Set harmonic amplitude: In the harmonic parameter setting menu, set the
amplitude of 2th and 4th orders of harmonic.
1) Ta p   t h e   No. parameter input field to input 2 with the pop-up numeric
keypad, and then tap "Ok".
2) Ta p   t h e   Harm Ampl parameter input field to input 2 with the pop-up
numeric keypad, select the unit "Vpp". Then tap "Ok".
3) Refer to Step 1 and Step 2 to set the amplitude of the 4th order harmonic to
## 1 Vpp.

- Set harmonic phase: In the harmonic parameter setting menu, set the phases
of 2th and 4th orders of harmonic in sequence.
1) Ta p   t h e   No. parameter input field to input 2 with the pop-up numeric
keypad, and then tap "Ok".
2) Ta p   t h e   Harm Phase parameter input field to input 30 with the pop-up
numeric keypad, select the unit "°". Then tap "Ok".
3) Refer to Step 1 and Step 2 to set the phase of the 4th order harmonic to
## 50°.

- Enable channel output: Press Output1, and the backlight turns on. Also,
you can tap the channel output configuration status bar   to enable
the channel output. Then, the channel status is highlighted (i.g.
## ),
and the fundamental waveform, 2th and 4th order of harmonics are output from
the [CH1] connector based on the current configurations.

- Observe the output waveform: Connect the [CH1] connector of DG800 to
the oscilloscope by using the BNC cable. The waveform is as shown in the figure
below.


Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-27

## Figure 2-5 Harmonic



RIGOL Chapter 2 Front Panel Operations
2-28                               DG800 User's Guide
## DC

DG800 can output DC signal with amplitude range from -10 V to 10 V (HighZ) or from
-5 V to 5 V (when the load is 50 Ω). The figure below shows a sketch of the DC signal.
Press Menu  Continuous  "DC" to select the DC signal.

Figure 2-6 Sketch of DC signal

Ta p   t h e   Offset parameter input field to input the desired offset value with the
numeric keypad, then select the unit. Tap "Ok".

You can also use the arrow keys and the knob to set the parameter value: press
down the knob to enter the editing mode, use the arrow keys to move the cursor to
select the digit to be edited, and then rotate the knob to modify the value.





Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-29
## To Output Dual-tone Waveform

Press Menu  Continuous  "Dualtone" to enter the dual-tone signal parameter
setting interface.

- Freq1/CentFreq: sets the output frequency/period of Signal 1 in the dual-tone
signal.

- Freq2/OffsFreq: sets the output frequency/period of Signal 2 in the dual-tone
signal.

- Ampl/HighL: sets the output amplitude/high level of the dual-tone signal.

- Offset/LowL: sets the output offset/low level of the dual-tone signal.


Please refer to "To Output Basic Waveform"   to configure the parameters and
output for the channel.


RIGOL Chapter 2 Front Panel Operations
2-30                               DG800 User's Guide

## 6      7      8        9
## To Output Advanced Waveform

DG800 provides three advanced waveforms: PRBS, RS232, and Sequence.

Note: When one channel is set to one of the advanced waveforms, the other
channel will automatically switch to the set advanced waveform from other
waveform.

## PRBS

A PRBS is generated by a linear-feedback shift register (LFSR), as shown below.






An LFSR is specified by the number of stages it contains (L) and which stages (taps)
feed the exclusive-or (XOR) gates in its feedback network. The PRBS output is taken
from the last stage. After selecting proper taps, an L-stage LFSR produces a
repetitive PRBS of length 2
## L
-1. The clock frequency of LFSR determines the "bit rate"
of PRBS.

Press Menu  Advanced  "PRBS" to open the PRBS parameter setting interface.

- Bit Rate: sets the output bit rate of the PRBS waveform.

- Ampl/HighL: sets the output amplitude/high level of the PRBS waveform.

- Offset/LowL: sets the output offset/low level of the PRBS waveform.

- Data: selects the data type of the PRBS waveform to PRBS7, PRBS9, PRBS11,
resulting in sequences of 127, 511, and 2047 bits in length. By default, it is
## PRBS7.

Please refer to "To Output Basic Waveform"   to configure the parameters and
output for the channel.









## 1      2        3      4      5
## XOR
## PRBS

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-31
## RS232

In RS232 serial protocol, a character is transmitted as a frame of data. The frame
consists of 1 start bit, 5-8 data bits, 0-1 check bit, and 1-2 stop bits. Its format
diagram is as shown in the figure below. RS232 uses "Negative Logic", i.g. high level
is logic "0" and low level is logic "1".



Press Menu  Advanced  "RS232" to open the RS232 waveform parameter
setting interface.

- Baud Rate: sets the output baud rate of RS232 waveform.

- Ampl/HighL: sets the output amplitude/high level of RS232 waveform.

- Offset/LowL: sets the output offset/low level of RS232 waveform.

- Data Bits: sets the data bits of RS232 waveform to 5, 6, 7, or 8.

- Stop Bits: sets the stop bits of RS232 waveform to "1", "1.5", or "2".

- Parity Bit: sets the check bit of RS232 waveform to "Odd", "Even", or "None".

- Data: sets the data of RS232 waveform. The available value is from 0 to 255.

Please refer to "To Output Basic Waveform"   to configure the parameters and
output for the channel.















RIGOL Chapter 2 Front Panel Operations
2-32                               DG800 User's Guide
## Sequence

You can self-define the sequence, and the edited waveforms can be stored in the
internal or external memory of the instrument in "*.SEQ" format.

Press Menu  Advanced  "Sequence" to open the Sequence parameter setting
interface. Tap the icon   at the upper-right corner of the interface to enter the
Sequence editing interface, as shown in the figure below.

## Figure 2-7 Sequence Editing Interface

No.: indicates the serial number represented by "n". The available range of "n" is
from 1 to 8.
Wave: selects the waveform that corresponds to the current No.
Period: sets the number of cycles of the currently selected waveform in "n".
Ta p   "Ok" to confirm the current editing and go back to the Sequence parameter
setting interface. You can preview the currently set waveforms in the right section of
the interface and set the waveform parameters at the left section of the interface.
Ta p   "Store"   to save the currently edited Sequence waveform to the internal
non-volatile memory (Disk C) or the external memory (Disk D, when a USB storage
device is inserted).

- Filter: selects the filter type of Sequence.
 Smooth: The frequency response is relatively wide and flat. The edge time
is fast but the sharp transitions will have overshoot and ringing.
 Step: The sharp transitions are relatively ideal, with a narrower frequency
bandwidth and the edge time is relatively slow.
 Interpolation: An abrupt change may occur among the output
points-to-points. The edge time can be adjustable.

- Samp. Rate: sets the output sample rate of Sequence.

- Ampl/HighL: sets the output amplitude/high level of Sequence.

- Offset/LowL: sets the output offset/low level of Sequence.

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-33
- Phase: sets the output start phase of Sequence.

- Edge Time: sets the edge time of Sequence.

Please refer to "To Output Basic Waveform"   to configure the parameters and
output for the channel.

RIGOL Chapter 2 Front Panel Operations
2-34                               DG800 User's Guide
## Modulation

DG800 can output modulated waveforms from a single channel or from dual
channels at the same time. Modulation is the process of modifying certain
parameters (e.g. amplitude, frequency, or phase) of the carrier waveform signal
according to the changes of the modulating signal. The carrier waveform can be Sine,
Square, Ramp, Arbitrary waveform, or Pulse (only in PWM). The modulating
waveform can be from internal or external modulation source. The modulation types
supported by DG800 include AM, FM, PM, ASK, FSK, PSK, and PWM.

Amplitude Modulation (AM)

For amplitude modulation (AM), the amplitude of the carrier waveform varies with
the instantaneous voltage of the modulating waveform.

To Select AM Modulation

Press Menu  Modulation  "AM" to enable the AM function. When Modulation
is enabled, Sweep or Burst will be automatically disabled (if enabled currently). Tap
the icon
at the upper-right corner of the interface (when Sine is selected as the
carrier waveform) to view and set the parameters of the current carrier waveform.
Tap the icon
at the upper-right corner of the interface again to go back to the
current modulation parameter interface.


To Select the Carrier Waveform

AM carrier waveform could be Sine, Square, Ramp, or Arbitrary waveform. The
default is Sine.
 Press Menu  Continuous to select the desired carrier waveform.
 Pulse, Noise, Harmonic, Dual-tone, and DC could not be used as carrier
waveform.


## To Set Carrier Waveform Parameters

The different settings of various parameters (e.g. frequency, amplitude, offset, and
start phase) of the carrier waveform will affect the output AM modulated waveform.
For different carrier waveform shapes, the ranges of the various parameters are
different (the ranges are related to the instrument model that you are using and the
currently selected carrier waveform). For all carrier waveform shapes, the default
values are 1 kHz frequency, 5 Vpp amplitude, 0 Vdc offset, and 0° start phase.


Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-35
 When the carrier waveform currently selected is Sine, Square, or Ramp, please
refer to descriptions in "To Output Basic Waveform" to set the parameters of
the carrier waveform currently selected.
 When the carrier waveform currently selected is arbitrary waveform, please
refer to descriptions in "To Output the Arbitrary Waveform" to set the
parameters of the carrier waveform currently selected.


## To Select Modulation Source

DG800 can receive modulating waveform from the internal or external modulation
source. Tap the Source parameter selection field to select an "Internal" or "External"
modulation source.

## 1. Internal Source
When the internal modulation source is selected, tap the Mod.Wave parameter
selection field to select Sine, Square, Triangle, UpRamp, DnRamp, Noise, or Arb
as modulating waveform. By default, Sine is selected.
 Square: 50% duty cycle.
 Triangle: 50% symmetry.
 UpRamp: 100% s y mm e t r y.
 DnRamp: 0% symmet r y.
 Arb: the arbitrary waveform selected for the current channel.
Note: Noise can be used as the modulating waveform but cannot be used as
carrier waveform.

## 2. External Source
When the external modulation source is selected, Mod.Wave and Mod.Freq
will be grayed out and disabled. The generator receives the external modulating
signal from the rear-panel [CH1/Sync/Ext Mod/Trig/FSK] connector. At this
time, amplitude of the modulated waveform is controlled by the ±5 V signal level
of the connector. For example, if the modulation depth is set to 100%, the output
amplitude will be the maximum when the modulating signal is +5 V and the
minimum when the modulating signal is -5   V.












RIGOL Chapter 2 Front Panel Operations
2-36                               DG800 User's Guide
## Key Points:

How to realize the intermodulation between dual channels? The
following example takes the output signal of CH2 as the modulating
waveform.
- Connect the CH2 output terminal to the rear-panel [CH1/Sync/Ext
Mod/Trig/FSK] connector by using the dual BNC cable.
- Select CH1, then press Menu  Modulation to select the desired
modulation type and set the corresponding parameters. After that, select the
external modulation source.
- Select CH2 and set the desired modulating waveform and the corresponding
parameters.
- Press Output1 to enable the output of CH1.


## To Set Modulating Waveform Frequency

When the internal modulation source is selected, tap the Mod.Freq parameter input
field, use the numeric keypad to input the modulating waveform frequency.
 You can also use the arrow keys and the knob to input a desired frequency
value.
 The modulating waveform frequency ranges from 2 mHz to 1 MHz, and the
default value is 100 Hz.
Note: When the external modulation source is selected, this menu will be grayed out
and disabled.


To Set the Modulation Depth

Modulation depth indicates the amplitude variation. It is expressed in percentage.
The AM modulation depth ranges from 0% to 120%. Tap the Mod.Depth parameter
input field to set the AM modulation depth.
 At 0% depth, the output amplitude is half of the carrier waveform amplitude.
 At 100% depth, the output amplitude is equal to carrier waveform amplitude.
 At >100% depth, the output amplitude of the instrument will not exceed 10 Vpp
(into a 50 Ω load).

When the external modulation source is selected, the output amplitude of the
instrument is controlled by the ±5 V signal level of the rear-panel [CH1/Sync/Ext
Mod/Trig/FSK] connector. For example, if the modulation depth is set to 100%,
the output amplitude will be the maximum when the modulating signal is +5 V and
the minimum when the modulating signal is -5   V.



Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-37
## Carrier Waveform Suppression

DG800 supports two types of amplitude modulation: normal amplitude modulation
and double sideband suppressed carrier (DSSC) amplitude modulation. In the normal
amplitude modulation, the modulated waveform contains carrier waveform
components. Because carrier waveform components carry no information, the
modulation is less efficient. In order to improve the modulation efficiency, the carrier
waveform components are suppressed on the basis of the normal amplitude
modulation. At this time, the modulated waveforms all carry information. This
method is called double sideband suppressed carrier modulation. By default, DG800
selects the normal amplitude modulation. Tap the DSSC parameter selection field to
select "On" to enable the double sideband suppressed carrier modulation.



RIGOL Chapter 2 Front Panel Operations
2-38                               DG800 User's Guide
Frequency Modulation (FM)

For frequency modulation (FM), the frequency of the carrier waveform varies with
the instantaneous voltage of the modulating waveform.

To Select FM Modulation

Press Menu  Modulation  "FM" to enable the FM function. When Modulation
is enabled, Sweep or Burst will be automatically disabled (if enabled currently). Tap
the icon
at the upper-right corner of the interface (when Sine is selected as the
carrier waveform) to view and set the parameters of the current carrier waveform.
Tap the icon
at the upper-right corner of the interface again to go back to the
current modulation parameter interface.


To Select the Carrier Waveform

FM carrier waveform could be Sine, Square, Ramp, or Arbitrary waveform. The
default is Sine.
 Press Menu  Continuous to select the desired carrier waveform.
 Pulse, Noise, Harmonic, Dual-tone, and DC could not be used as carrier
waveform.


## To Set Carrier Waveform Parameters

The different settings of various parameters (e.g. frequency, amplitude, offset, and
start phase) of the carrier waveform will affect the output FM modulated waveform.
For different carrier waveform shapes, the ranges of the various parameters are
different (the ranges are related to the instrument model that you are using and the
currently selected carrier waveform). For all carrier waveform shapes, the default
values are 1 kHz frequency, 5 Vpp amplitude, 0 Vdc offset, and 0° start phase.

 When the carrier waveform currently selected is Sine, Square, or Ramp, please
refer to descriptions in "To Output Basic Waveform" to set the parameters of
the carrier waveform currently selected.
 When the carrier waveform currently selected is arbitrary waveform, please
refer to descriptions in "To Output the Arbitrary Waveform" to set the
parameters of the carrier waveform currently selected.






Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-39
## To Select Modulation Source

DG800 can receive modulating waveform from the internal or external modulation
source. Tap the Source parameter selection field to select an "Internal" or "External"
modulation source.

## 1. Internal Source
When internal modulation source is selected, tap the Mod.Wave parameter
selection field to select Sine, Square, Triangle, UpRamp, DnRamp, Noise, or Arb
as modulating waveform. By default, Sine is selected.
 Square: 50% duty cycle.
 Triangle: 50% symmetry.
 UpRamp: 100% s y mm e t r y.
 DnRamp: 0% symmetry.
 Arb: the arbitrary waveform selected for the current channel.
Note: Noise can be used as the modulating waveform but cannot be used as
carrier waveform.

## 2. External Source
When the external modulation source is selected, Mod.Wave and Mod.Freq
will be grayed out and disabled. The generator receives the external modulating
signal from the rear-panel [CH1/Sync/Ext Mod/Trig/FSK] connector. At this
time, the frequency deviation of the modulated waveform is controlled by the ±5
V signal level of the connector. For example, if the frequency deviation is set to 1
kHz, +5 V signal level corresponds to a 1 kHz increase in frequency and -5 V
signal level corresponds to a 1 kHz decrease in frequency.


## To Set Modulating Waveform Frequency

When the internal modulation source is selected, tap the Mod.Freq parameter input
field and use the numeric keypad to set the modulating waveform frequency.
 You can also use the arrow keys and the knob to input a desired frequency
value.
 The modulating waveform frequency ranges from 2 mHz to 1 MHz, and the
default value is 100 Hz.
Note: When the external modulation source is selected, this menu will be grayed out
and disabled.


To Set the Frequency Deviation

Frequency deviation indicates the variation in the modulating waveform frequency
from the carrier frequency. Tap the Freq.Dev parameter input field to set the FM
frequency deviation.

RIGOL Chapter 2 Front Panel Operations
2-40                               DG800 User's Guide
 The frequency deviation must be smaller than or equal to the carrier frequency.
 The sum of frequency deviation and carrier frequency must be smaller than or
equal to the the upper limit of the current carrier frequency plus 1 kHz.

Note: If Sine is selected currently as the carrier waveform, the carrier amplitude will
be limited at 2 Vpp when the sum of the frequency deviation and the carrier
frequency is greater than the frequency upper limit of the current carrier.

When the external modulation source is selected, the frequency deviation is
controlled by the ±5 V signal level on the rear-panel [CH1/Sync/Ext
Mod/Trig/FSK] connector. Positive signal level corresponds to frequency increase,
and negative signal level corresponds to frequency decrease. Lower signal levels
produce less deviation. For example, if the frequency deviation is set to 1 kHz, +5 V
signal level corresponds to a 1 kHz increase in frequency and -5 V signal level
corresponds to a 1 kHz decrease in frequency.



Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-41
Phase Modulation (PM)

For phase modulation (PM), the phase of the carrier waveform varies with the
instantaneous voltage of the modulating waveform.

To Select PM Modulation

Press Menu  Modulation  "PM"  to enable the PM function. When Modulation
is enabled, Sweep or Burst will be automatically disabled (if enabled currently). Tap
the icon
at the upper-right corner of the interface (when Sine is selected as the
carrier waveform) to view and set the parameters of the current carrier waveform.
Tap the icon
at the upper-right corner of the interface again to go back to the
current modulation parameter interface.


To Select the Carrier Waveform

PM carrier waveform could be Sine, Square, Ramp, or Arbitrary waveform. The
default is Sine.
 Press Menu  Continuous to select the desired carrier waveform.
 Pulse, Noise, Harmonic, Dual-tone, and DC could not be used as carrier
waveform.


## To Set Carrier Waveform Parameters

The different settings of various parameters (e.g. frequency, amplitude, and offset)
of the carrier waveform will affect the output PM modulated waveform. For different
carrier waveform shapes, the ranges of the various parameters are different (the
ranges are related to the instrument model that you are using and the currently
selected carrier waveform). For all carrier waveform shapes, the default values are 1
kHz frequency, 5 Vpp amplitude, and 0 Vdc offset.

 When the carrier waveform currently selected is Sine, Square, or Ramp, please
refer to descriptions in "To Output Basic Waveform" to set the parameters of
the carrier waveform currently selected.
 When the carrier waveform currently selected is arbitrary waveform, please
refer to descriptions in "To Output the Arbitrary Waveform" to set the
parameters of the carrier waveform currently selected.

Note: After the PM function is enabled, the start phase of the carrier waveform
cannot be set.



RIGOL Chapter 2 Front Panel Operations
2-42                               DG800 User's Guide
## To Select Modulation Source

DG800 can receive modulating waveform from the internal or external modulation
source. Tap the Source parameter selection field to select an "Internal" or "External"
modulation source.

## 1. Internal Source
When internal modulation source is selected, tap the Mod.Wave parameter
selection field to select Sine, Square, Triangle, UpRamp, DnRamp, Noise, or Arb
as modulating waveform. By default, Sine is selected.
 Square: 50% duty cycle.
 Triangle: 50% symmetry.
 UpRamp: 100% s y mm e t r y.
 DnRamp: 0% symmetry.
 Ar  b: the arbitrary waveform selected for the current channel.
Note: Noise can be used as the modulating waveform but cannot be used as
carrier waveform.

## 2. External Source
When the external modulation source is selected, Mod.Wave and Mod.Freq
will be grayed out and disabled. The generator receives the external modulating
signal from the rear-panel [CH1/Sync/Ext Mod/Trig/FSK] connector. At this
time, the phase deviation of the modulated waveform is controlled by the ±5 V
signal level of the connector. For example, if the phase deviation is set to 180°,
+5 V signal level corresponds to a 180º phase variation. The lower external
signal levels produce less deviation.


## To Set Modulating Waveform Frequency

When the internal modulation source is selected, tap the Mod.Freq parameter input
field and use the numeric keypad to set the modulating waveform frequency.
 You can also use the arrow keys and the knob to input a desired frequency
value.
 The modulating waveform frequency ranges from 2 mHz to 1 MHz, and the
default value is 100 Hz.
Note: When the external modulation source is selected, this menu will be grayed out
and disabled.








Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-43
## To Set Phase Deviation

Phase deviation indicates the deviation of the modulating waveform phase from the
carrier waveform phase. Tap the Phas.Dev parameter input field and use the
numeric keypad to set the PM phase deviation.
 You can also use the arrow keys and the knob to input a   desired phase value.
 The setting range of the phase deviation is from 0° to 360°, and the default is
## 90°.

When the external modulation source is selected, the phase deviation is controlled by
the ±5 V signal level on the rear-panel [CH1/Sync/Ext Mod/Trig/FSK] connector.
For example, if the phase deviation is set to 180°, +5 V signal level corresponds to a
180º phase variation. The lower external signal levels produce less deviation.


RIGOL Chapter 2 Front Panel Operations
2-44                               DG800 User's Guide
Amplitude Shift Keying (ASK)

When using ASK (Amplitude Shift Keying), you can configure the generator to "shift"
its output amplitude between two preset amplitude values ("carrier amplitude" and
"modulating amplitude").

To Select ASK Modulation

Press Menu  Modulation  "ASK" to enable the ASK function. When
Modulation is enabled, Sweep or Burst will be automatically disabled (if enabled
currently). Tap the icon
at the upper-right corner of the interface (when Sine is
selected as the carrier waveform) to view and set the parameters of the current
carrier waveform. Tap the icon
at the upper-right corner of the interface again
to go back to the current modulation parameter interface.


To Select the Carrier Waveform

ASK carrier waveform could be Sine, Square, Ramp, or Arbitrary waveform. The
default is Sine.
 Press Menu  Continuous to select the desired carrier waveform.
 Pulse, Noise, Harmonic, Dual-tone, and DC could not be used as carrier
waveform.


## To Set Carrier Waveform Parameters

The different settings of various parameters (e.g. frequency, amplitude, offset, and
start phase) of the carrier waveform will affect the output ASK modulated waveform.
For different carrier waveform shapes, the ranges of the various parameters are
different (the ranges are related to the instrument model that you are using and the
currently selected carrier waveform). For all carrier waveform shapes, the default
val   ues are 1 kHz frequency, 5 Vpp amplitude, 0 Vdc offset, and 0° start phase.

 When the carrier waveform currently selected is Sine, Square, or Ramp, please
refer to descriptions in "To Output Basic Waveform" to set the parameters of
the carrier waveform currently selected.
 When the carrier waveform currently selected is arbitrary waveform, please
refer to descriptions in "To Output the Arbitrary Waveform" to set the
parameters of the carrier waveform currently selected.





Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-45
## To Select Modulation Source

Ta p   t h e   Source parameter selection field to select an "Internal" or "External"
modulation source.

## 1. Internal Source
When the internal source is selected, the modulating waveform is set as a Square
with 50% duty cycle. At this time, the rate at which the output amplitude "shifts"
between "carrier amplitude" and "modulating amplitude" is determined by the
modulation rate.

## 2. External Source
When the external source is selected, the generator receives the external
modulating signal from the rear-panel [CH1/Sync/Ext Mod/Trig/FSK]
connector.

Note: The [CH1/Sync/Ext Mod/Trig/FSK] connector controlling ASK
modulation externally is different from controlling AM/FM/PM modulations
externally. While controlling the ASK modulation, you can set the polarity.


## To Set Modulating Rate

When the internal source is selected, tap the Mod.Rate parameter input field and
use the numeric keypad to set the rate at which the output amplitude shifts between
"carrier amplitude" and "modulating amplitude".
 You can also use the arrow keys and the knob to input a desired frequency
value.
 The frequency range is from 2 mHz to 1 MHz, and the default is 100 Hz.
Note: When the external modulation source is selected, this menu will be grayed out
and disabled.


To Set the Modulation Amplitude

Ta p   t h e   Mod.Ampl parameter input field and use the numeric keypad to set the
modulation amplitude.
 You can also use the arrow keys and the knob to input a   desired amplitude
value.
 The range of amplitude (HighZ) is from 0 to 10 Vpp, and the default is 2 Vpp.





RIGOL Chapter 2 Front Panel Operations
2-46                               DG800 User's Guide
To Set the Modulation Polarity

Ta p   t h e   Polarity parameter selection field to select "Positive" or "Negative" polarity
of the modulating waveform to control the output amplitude.

In the internal modulation, set the polarity to "Positive", and the generator will
output an amplitude whichever is smaller between the carrier amplitude and
modulating amplitude when the modulating waveform is a logic low level. It will
output an amplitude whichever is greater between the carrier amplitude and
modulating amplitude when the modulating waveform is a logic high level. The
situation is the opposite when the polarity is set to "Negative".

In the external modulation, set the polarity to "Positive", and the generator will
output an amplitude whichever is smaller between the carrier amplitude and
modulating amplitude when the external input signal is a logic low level. It will output
an amplitude whichever is greater between the carrier amplitude and the modulating
amplitude when the external input signal is a logic high level. The situation is the
opposite when the polarity is set to "Negative".

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-47
Frequency Shift Keying (FSK)

When using FSK (Frequency Shift Keying), you can configure the generator to "shift"
its output frequency between two preset frequency values ("carrier amplitude" and
"hop frequency").

To Select FSK Modulation

Press Menu  Modulation  "FSK" to enable the FSK function. When
Modulation is enabled, Sweep or Burst will be automatically disabled (if enabled
currently). Tap the icon
at the upper-right corner of the interface (when Sine is
selected as the carrier waveform) to view and set the parameters of the current
carrier waveform. Tap the icon
at the upper-right corner of the interface again
to go back to the current modulation parameter interface.


To Select the Carrier Waveform

FSK carrier waveform could be Sine, Square, Ramp, or Arbitrary waveform. The
default is Sine.
 Press Menu  Continuous to select the desired carrier waveform.
 Pulse, Noise, Harmonic, Dual-tone, and DC could not be used as carrier
waveform.


## To Set Carrier Waveform Parameters

The different settings of various parameters (e.g. frequency, amplitude, offset, and
start phase) of the carrier waveform will affect the output FSK modulated waveform.
For different carrier waveform shapes, the ranges of the various parameters are
different (the ranges are related to the instrument model that you are using and the
currently selected carrier waveform). For all carrier waveform shapes, the default
values are 1 kHz frequency, 5 Vpp amplitude, 0 V
dC
offset, and 0° start phase.

 When the carrier waveform currently selected is Sine, Square, or Ramp, please
refer to descriptions in "To Output Basic Waveform" to set the parameters of
the carrier waveform currently selected.
 When the carrier waveform currently selected is arbitrary waveform, please
refer to descriptions in "To Output the Arbitrary Waveform" to set the
parameters of the carrier waveform currently selected.





RIGOL Chapter 2 Front Panel Operations
2-48                               DG800 User's Guide
## To Select Modulation Source

Ta p   t h e   Source parameter selection field to select an "Internal" or "External"
modulation source.

## 1. Internal Source
When the internal source is selected, the modulating waveform is set as a Square
with 50% duty cycle. At this time, the rate at which the output frequency "shifts"
between "carrier frequency" and "hop frequency" is determined by the
modulation rate.

## 2. External Source
When the external source is selected, the generator receives the external
modulating signal from the rear-panel [CH1/Sync/Ext Mod/Trig/FSK]
connector.

Note: The [CH1/Sync/Ext Mod/Trig/FSK] connector controlling ASK
modulation externally is different from controlling AM/FM/PM modulations
externally. While controlling the FSK modulation, you can set the polarity.


## To Set Modulating Rate

When the internal source is selected, tap the Mod.Rate parameter input field and
use the numeric keypad to set the rate at which the output frequency shifts between
"carrier frequency" and "hop frequency".
 You can also use the arrow keys and the knob to input a desired frequency
value.
 The frequency range is from 2 mHz to 1 MHz, and the default is 100 Hz.
Note: When the external modulation source is selected, this menu will be grayed out
and disabled.


## To Set Hop Frequency

Hop frequency indicates the
frequency of the modulating waveform. The range of the hop frequency is
determined by the currently selected carrier waveform. Tap the Hop Freq parameter
input field and use the numeric keypad to input a desired frequency value. You can
also use the arrow keys and the knob to input a desired frequency value.

 Sine: 1 μHz to 35   MHz
 Square: 1 μHz to 10 MHz
 Ramp: 1 μHz to 1 MHz
 Arb: 1 μHz to 10 MHz

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-49
To Set the Modulation Polarity

Ta p   t h e   Polarity parameter selection field to select "Positive" or "Negative" polarity
of the modulating waveform to control the output frequency.

In the internal modulation, set the polarity to "Positive", and the generator will
output the carrier frequency when the modulating waveform amplitude is a logic low
level. It will output the hop frequency when the modulating waveform amplitude is a
logic high level. The situation is the opposite when the polarity is set to "Negative".

In the external modulation, set the polarity to "Positive", and the generator will
output the carrier frequency when the external input signal is a logic low level. It will
output the hop frequency when the external input signal is a logic high level. The
situation is the opposite when the polarity is set to "Negative".


RIGOL Chapter 2 Front Panel Operations
2-50                               DG800 User's Guide
Phase Shift Keying (PSK)

When using PSK (Phase Shift Keying), you can configure the generator to "shift" its
output phase between two preset phase values ("carrier phase" and "modulating
phase").

To Select PSK Modulation

Press Menu  Modulation  "PSK" to enable the PSK function. When
Modulation is enabled, Sweep or Burst will be automatically disabled (if enabled
currently). Tap the icon
at the upper-right corner of the interface (when Sine is
selected as the carrier waveform) to view and set the parameters of the current
carrier waveform. Tap the icon
at the upper-right corner of the interface again
to go back to the current modulation parameter interface.


To Select the Carrier Waveform

PSK carrier waveform could be Sine, Square, Ramp, or Arbitrary waveform. The
default is Sine.
 Press Menu  Continuous to select the desired carrier waveform.
 Pulse, Noise, Harmonic, Dual-tone, and DC could not be used as carrier
waveform.


## To Set Carrier Waveform Parameters

The different settings of various parameters (e.g. frequency, amplitude, offset, and
start phase) of the carrier waveform will affect the output PSK modulated waveform.
For different carrier waveform shapes, the ranges of the various parameters are
different (the ranges are related to the instrument model that you are using and the
currently selected carrier waveform). For all carrier waveform shapes, the default
values are 1 kHz frequency, 5 Vpp amplitude, 0 V
dC
offset, and 0° start phase.

 When the carrier waveform currently selected is Sine, Square, or Ramp, please
refer to descriptions in "To Output Basic Waveform" to set the parameters of
the carrier waveform currently selected.
 When the carrier waveform currently selected is arbitrary waveform, please
refer to descriptions in "To Output the Arbitrary Waveform" to set the
parameters of the carrier waveform currently selected.





Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-51
## To Select Modulation Source

Ta p   t h e   Source parameter selection field to select an "Internal" or "External"
modulation source.

## 1. Internal Source
When the internal source is selected, the modulating waveform is set as a Square
with 50% duty cycle. At this time, the rate at which the output phase "shifts"
between "carrier phase" and "modulating phase" is determined by the
modulation rate.

## 2. External Source
When the external source is selected, the generator receives the external
modulating signal from the rear-panel [CH1/Sync/Ext Mod/Trig/FSK]
connector.

Note: The [CH1/Sync/Ext Mod/Trig/FSK] connector controlling PSK
modulation externally is different from controlling AM/FM/PM modulations
externally. While controlling the PSK modulation, you can set the polarity.


## To Set Modulating Rate

When the internal source is selected, tap the Mod.Rate parameter input field and
use the numeric keypad to set the rate at which the output phase shifts between
"carrier phase" and "modulating phase".
 You can also use the arrow keys and the knob to input a desired frequency
value.
 The frequency range is from 2 mHz to 1 MHz, and the default is 100 Hz.
Note: When the external modulation source is selected, this menu will be grayed out
and disabled.


## To Set Modulating Phase

Modulating phase indicates the phase of the modulating waveform. Tap the Phase
parameter input field and use the numeric keypad to set the modulation phase.
 You can also use the arrow keys and the knob to input a desired phase value.
 The phase range is from 0° to 360°, and the default is 180°.







RIGOL Chapter 2 Front Panel Operations
2-52                               DG800 User's Guide
## To Set Modulation Polarity

Ta p   t h e   Polarity parameter selection field to select "Positive" or "Negative" polarity
of the modulating waveform to control the output phase.
In the internal modulation, set the polarity to "Positive", and the generator will
output the carrier phase when the modulating waveform amplitude is a logic low
level. It will output the modulating phase when the modulating waveform amplitude
is a logic high level. The situation is the opposite when the polarity is set to
"Negative".

In the external modulation, set the polarity to "Positive", and the generator will
output the carrier phase when the external input signal is a logic low level. It will
output the modulation phase when the external input signal is a logic high level. The
situation is the opposite when the polarity is set to "Negative".

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-53
Pulse Width Modulation (PWM)

For PWM (Pulse Width Modulation), the pulse width of the carrier waveform varies
with the instantaneous voltage of the modulating waveform.

To Select PWM Modulation

PWM can only be used to modulate pulse. To select PWM modulation, first select
Pulse, then press Menu  Modulation  "PWM" to enable PWM function. Tap
the icon   at the upper-right corner of the interface to view and set the
parameters of the current carrier waveform. Tap the icon
at the upper-right
corner of the interface again to go back to the current modulation parameter
interface.
 If the "Pulse" waveform is not selected, PWM modulation is unavailable.
 When Modulation is enabled but the modulation type is not PWM, pressing
"Pulse" will select PWM automatically.
 When Modulation is enabled, Sweep or Burst will be automatically disabled
(if   enabled currently).


To Select the Carrier Waveform

As mentioned before, the carrier waveform of PWM can only be Pulse. To select Pulse
waveform, press Menu  Continuous  "Pulse".


## To Set Carrier Waveform Parameters

The different settings of various parameters (e.g. frequency, amplitude, offset, pulse
width, and duty cycle) of the Pulse waveform will affect the output PWM modulated
waveform. For all the pulses, the ranges of the various parameters are different. The
default values are 1 kHz frequency, 5 Vpp amplitude, 0 Vdc offset, 500 μs pulse width,
and 50% duty cycle.

Please refer to descriptions in "To Output Basic Waveform" to set the parameters
of the carrier waveform.









RIGOL Chapter 2 Front Panel Operations
2-54                               DG800 User's Guide
## To Select Modulation Source

Ta p   t h e   Source parameter selection field to select an "Internal" or "External"
modulation source.

## 1. Internal Source
When internal modulation source is selected, tap the Mod.Wave parameter
selection field to select Sine, Square, Triangle, UpRamp, DnRamp, Noise, or Arb
as modulating waveform. By default, Sine is selected.
 Square: 50% duty cycle.
 Triangle: 50% symmetry.
 UpRamp: 100% s y mm e t r y.
 DnRamp: 0% symmetry.
 Arb: the arbitrary waveform selected for the current channel.
Note: Noise can be used as the modulating waveform but cannot be used as
carrier waveform.

## 2. External Source
When the external modulation source is selected, Mod.Wave and Mod.Freq
will be grayed out and disabled. The generator receives the external modulating
signal from the rear-panel [CH1/Sync/Ext Mod/Trig/FSK] connector. At this
time, the width deviation or the duty cycle deviation of the modulated waveform
is controlled by the ±5 V signal level on the connector. For example, if the width
deviation is set to 10 s, the +5 V signal level corresponds to a 10 s width
variation.


## To Set Modulating Waveform Frequency

When the internal modulation source is selected, tap the Mod.Freq parameter input
field and use the numeric keypad to set the modulating waveform frequency.
 You can also use the arrow keys and the knob to input a desired frequency
value.
 The modulating waveform frequency ranges from 2 mHz to 1 MHz, and the
default value is 100 Hz.
Note: When the external modulation source is selected, this menu will be grayed out
and disabled.









Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-55
To Set Width/Duty Deviation

If "Width" is currently selected in the pulse of the specified channel, "Width Dev" is
displayed in the interface when the PWM modulation function is enabled; if the
"Duty" is currently selected in the pulse of the specified channel, "Duty Dev" is
displayed in the interface when the PWM modulation function is enabled.
Ta p   t h e   Width Dev (or Duty Dev) parameter input field and use the numeric
keypad to input a desired value. You can also use the arrow keys and the knob to
input a desired value.
 Width deviation represents the variation of the modulated waveform pulse width
relative to the original pulse width (the available units are ns, μs, ms, s, and ks).
Width deviation cannot exceed the current pulse width.
The width deviation is limited by the minimum pulse width and current edge
time setting.
 Duty deviation represents the variation of the modulated waveform pulse duty
cycle relative to the original duty cycle (expressed in %).
Duty deviation cannot exceed the current duty cycle of the pulse.
The duty deviation is limited by the minimum duty cycle and current edge time
setting.

When the external modulation source is selected, the width deviation is controlled by
the ±5 V signal level on the rear-panel [CH1/Sync/Ext Mod/Trig/FSK] connector.
For example, if the width deviation is set to 10 s, the +5 V signal level corresponds to
a 10 s width variation.

RIGOL Chapter 2 Front Panel Operations
2-56                               DG800 User's Guide
## Sweep

DG800 can output sweep waveforms from a single channel or from dual channels at
the same time. In sweep mode, the generator outputs a signal variably from the start
frequency to stop frequency within the specified sweep time. DG800 supports linear,
log, and step sweep modes; allows users to set start hold, stop hold, and return time;
supports internal, external, or manual trigger source; and capable of generating
sweep output for Sine, Square, Ramp, and Arbitrary waveform.

To Enable the Sweep Function

Press Menu  Sweep to select "Linear", "Log", or "Step" to enable the sweep
function. The Modulation or Burst function will be disabled automatically (if
enabled currently). At this time, the generator will generate the sweep waveform
from the corresponding channel (if enabled currently) according to the current
configuration. You can also reset the sweep parameters. For details, refer to the
following section.


## Sweep Type

DG800 provides Linear, Log, and Step sweep types.

## Linear Sweep

In the linear sweep type, the output frequency of the instrument varies linearly in the
way of "several Hertz per second". The variation is controlled by "Start Frequency",
"Stop Frequency" and "Sweep Time".

Press Menu  Sweep  "Linear" to enable the linear sweep. A straight line is
displayed on the waveform on the screen, indicating that the output frequency varies
linearly.

## Figure 2-8 Linear Sweep

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-57
## Log Sweep

In Log Sweep type, the output frequency of the instrument varies in a logarithmic
fashion, that is, the output frequency changes in the way of "octave per second" or
"decade per second". The variation is controlled by "Start Frequency", "Stop
Frequency", and "Sweep Time".

When Log Sweep is enabled, you can set the following parameter: start
frequency
start
## F
, stop frequency
stop
## F
, and sweep time
sweep
## T
. The function prototype
of Log Sweep is:
## T
current
## FP=

current
## F
is the instantaneous frequency of the current output. The parameter
## P
and
## T
can be expressed with the above parameter.
sweepstartstop
## TFF
## P
## /)/lg(
## 10=

)lg(/)lg(PFtT
start
## +=

## Wherein,
t
is the time from the start of the sweep, and its range is from 0 to
sweep
## T
## .


Press Menu  Sweep  "Log" to enable the log sweep. An exponential function
curve is displayed on the screen, indicating that the output frequency changes in a
logarithmic mode.

## Figure 2-9 Log Sweep


## Step Sweep

In Step Sweep type, the output frequency of the instrument "steps" from "Start
Frequency" to "Stop Frequency" with a stepwise increase. The duration of the output
signal on each frequency point is determined by "Sweep Time" and "Steps".

Press Menu  Sweep  "Step" to enable the step sweep. A step waveform is
displayed on the screen, indicating that the output frequency varies with a stepwise

RIGOL Chapter 2 Front Panel Operations
2-58                               DG800 User's Guide
increase. At this point, tap to slide the screen or use the knob to page up or down.
Ta p   t h e   Step parameter input field and use the numeric keypad to set the step. You
can also use the arrow keys and the knob to set the step. By default, it is 2, and its
settable range is from 2 to 1024.
Note: In the "Linear" and "Log" sweep modes, the Step menu label is grayed out
and disabled.


## Figure 2-10 Step Sweep


## Sweep Time

When the sweep function is enabled, tap the Sweep Time parameter input field   and
use the numeric keypad to modify the sweep time. You can also use the arrow keys
and the knob to modify the sweep time. By default, it is 1 s, and its settable range is
from 1 ms to 500 s. The generator will restart to sweep and output from the specified
"Start Frequency" after the sweep time is modified.


## Return Time

Return time indicates the time that the output signal restores from "End Freq" to
"Start Freq" after the signal generator sweeps from "Start Freq" to "End Freq" and
the "StopHold" time expires.

When the sweep function is enabled, tap the Return Time parameter input field
and use the numeric keypad to modify the return time. You can also use the arrow
keys and the knob to modify the return time. By default, it is 0 s, and its settable
range is from 0 s to 500 s.

The generator will restart to sweep and output from the specified "Start Frequency"
once the return time is modified.



Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-59
Start Frequency and Stop Frequency

Start frequency and stop frequency are the upper and lower limits of the frequency
for frequency sweep. The generator always sweeps from the start frequency to the
stop frequency, and then returns back to the start frequency.
 Start Frequency < Stop Frequency: the generator sweeps from low frequency to
high frequency.
 Start Frequency > Stop Frequency: the generator sweeps from high frequency
to low frequency.
 Start Frequency = Stop Frequency: the generator outputs with a fixed
f r eq u e nc y.

After the sweep function is enabled, tap the Start/Center menu label to enable the
display of "Start". Notice that the "Stop" in Stop/Span menu label will also be
highlighted at the same time. Input the desired frequency value by using the numeric
keypad, the arrow keys, or the knob. By default, the start frequency is 100 Hz, and
the stop frequency is 1 kHz. Different sweep waveforms correspond to different start
frequency and stop frequency ranges.

After modifying the "Start Freq" or "Stop Freq", the signal generator will restart to
output from the specified "Start Freq".


Center Frequency and Frequency Span

You can also set the frequency boundaries of frequency sweep through center
frequency and frequency span.
 Center Frequency = (|Start Frequency + Stop Frequency|)/2
##  Frequency Span = Stop Frequency – Start Frequency

After the sweep function is enabled, tap the Start/Center menu label to enable the
display of "Center". At this time, the "Span" in Stop/Span menu label will also be
highlighted at the same time. Input the desired frequency value by using the numeric
keypad, the arrow keys, or the knob. By default, the center frequency is 550 Hz, and
the frequency span is 900 Hz. Different sweep waveforms correspond to different
center frequency and frequency span ranges. Besides, the center frequency and
frequency span are mutually affected.

Define the minimum frequency of the currently selected waveform
min
## F
, the
maximum frequency as
max
## F
and
## 2/)(
max
min
## F
## FF
m
## +=
## .
 The available range of the center frequency is from
min
## F
to
max
## F
## . The
parameters of different waveforms are as follows:
Sine: 1 μHz to 35   MHz
Square: 1 μHz to 10 MHz

RIGOL Chapter 2 Front Panel Operations
2-60                               DG800 User's Guide
Ramp: 1 μHz to 1 MHz
Arb: 1 μHz to 10 MHz
 The range of the frequency span is affected by the center frequency.
Center frequency <
m
## F
: the range of the frequency span is ±2× (center
frequency –
min
## F
## );
Center frequency ≥
m
## F
: the range of the frequency span is ±2× (
max
## F
## -
center frequency).

Take sine as an example.
min
## F
is 1 μHz,
max
## F
is  35   MHz, and
m
## F
is  17.5 MHz.
If the center frequency is 550 Hz, the frequency span range is ±2×(550 Hz–1 μHz) =
±1.099999998 kHz; if the center frequency is 20 MHz, the frequency span range is
±2×(35   MHz – 20 MHz) = ±30 MHz.

The generator will restart to sweep from the specified "start frequency" after the
"center frequency" or "frequency span" is modified.

## Tip:

In large-scale sweep, the amplitude characteristic of the output signal might
change.


## Sweep Trigger Source

The trigger sources of the sweep can be Internal, External, or Manual. When the
signal generator receives a trigger signal, a sweep output is generated, and then the
signal generator waits for another trigger signal. After the sweep function is enabled,
tap the Source to select "Internal", "External", or "Manual". The default is
"Internal".

## 1. Internal Trigger
The generator outputs continuous sweep waveforms when the internal trigger is
selected. The trigger period is determined by the specified sweep time, return
time, start hold, and stop hold time.

## 2. External Trigger
In the External trigger, the signal generator receives the trigger signal input from
the rear-panel [CH1/Sync/Ext Mod/Trig/FSK] connector. Once it receives a
TTL pulse with a specified polarity, a sweep is initiated. To specify the polarity of
the TTL pulse, tap the Trig In to select "RisEdge" or "FallEdge". By default, it is
"RisEdge".



Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-61
## 3. Manual Trigger
In the Manual trigger, when you press Trig on the front panel for one time, one
sweep is immediately launched for the corresponding channel.

## Key Points:

When "External" trigger is selected, tap the Trig In to select "RisEdge" or
"FallEdge". The rear-panel [CH1/Sync/Ext Mod/Trig/FSK] connector is used
as the input terminal of the external trigger signal. When "RisEdge" is selected, the
instrument triggers one sweep at the rising edge of the input signal. When
"FallEdge" is selected, the instrument triggers one sweep at the falling edge of the
input signal.


## Marker Freq

The sync signal output from the rear-panel [CH1/Sync/Ext Mod/Trig/FSK]
connector that corresponds to the channel on the front panel always changes from
low level to high level at the start of each sweep. When the "Marker" function is
disabled, the sync signal will change to low level at the center frequency point. When
the "Marker" function is enabled, the sync signal changes to low level at the specified
marker frequency point.

After the sweep function is enabled, tap the Marker menu label to select "On". Then
tap the Marker Freq menu label, and use the numeric keypad to modify the marker
frequency. You can also use the arrow keys and the knob to modify the marker
frequency. The default value is 550 Hz, and the available range is limited by "Start
Frequency" and "Stop Frequency".

The generator will restart to sweep and output from the specified "Start Frequency"
after the mark frequency is modified.

## Key Points:

For step sweep (the sweep points determined by the start frequency, stop
frequency, and step respectively are f
## 1
, f
## 2
, ......, f
n
, f
n+1
......), if the marker frequency
setting is one of the sweep points values, the sync signal is TTL high level at the
start of the sweep and will change to low level at the marker frequency point. If the
set marker frequency is not equal to the value at the sweep point, the sync signal
will change to low level at the sweep point which is closest to this marker
f r eq u e nc y.





RIGOL Chapter 2 Front Panel Operations
2-62                               DG800 User's Guide
## Start Hold

Start hold is the duration that the output signal outputs with the "Start Frequency"
after the sweep starts. After the start hold time expires, the generator will continue
outputting with varied frequencies according to the current sweep type.

When the sweep function is enabled, tap the StartHold menu label and use the
numeric keypad to modify the start hold time. You can also use the arrow keys and
the knob to modify the start hold time. By default, it is 0 s, and its settable range is
from 0 s to 500 s.

The generator will restart to sweep and output from the specified "Start Frequency"
once the Start Hold time is changed.


## Stop Hold

Stop Hold is the duration that the output signal continues outputting with the "Stop
Frequency" after the generator has swept from the "Start Frequency" to the "Stop
## Frequency".

When the sweep function is enabled, tap the StopHold menu label and use the
numeric keypad to modify the stop hold time. You can also use the arrow keys and
the knob to modify the stop hold time. By default, it is 0 s, and its settable range is
from 0 s to 500 s.

The generator will restart to sweep and output from the specified "Start Frequency"
after the Stop Hold time is modified.






Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-63
## Burst

DG800 can output the waveforms with a specified number of cycles (Burst) from a
single channel or from dual channels at the same time. DG800 supports control of
burst output by internal, manual or external trigger source; supports three kinds of
burst types, including N cycle, Infinite, and Gated. The generator can generate burst
by using Sine, Square, Ramp, Pulse, Noise (only for gated burst), arbitrary waveform,
PRBS, RS232, or Sequence.

To Enable the Burst Function

Press Menu  Burst to select "NCycle", "Infinite", or "Gated" to enable the
pulse function. The Modulation or Sweep function will be disabled automatically (if
enabled currently). At this time, the generator will output burst waveform from the
corresponding channel (if currently turned on) according to the current configuration.
You can also reset the burst function menu. Please refer to the following section for
details.


## Burst Type

DG800 can output three types of bursts, including N cycle, Infinite and Gated.

Ta b l e   2-3 Relations among Burst type, Trigger Source, and Carrier Waveforms
## Type Trigger Source Carrier Waveform
N Cycle Internal/External/Manual Sine, Square, Ramp, Pulse, Arbitrary
Waveform, PRBS, RS232, Sequence
Infinite External/Manual Sine, Square, Ramp, Pulse, Arbitrary
Waveform, PRBS, RS232, Sequence
## Gated External Sine, Square, Ramp, Pulse, Noise, Arbitrary
Waveform, PRBS, RS232, Sequence


## N Cycle

In N Cycle mode, the generator will output waveforms with a specified number of
cycles after receiving the trigger signal.

Press Menu  Burst  "NCycle" to enable the N Cycle burst. Tap the Cycles
menu label, then use the numeric keypad to input the number of cycles. You can also
use the arrow keys and the knob to modify the number of cycles. The default is 1,
and the range is from 1 to 1,000,000 (external or manual trigger) or from 1 to
500,000 (internal trigger).

RIGOL Chapter 2 Front Panel Operations
2-64                               DG800 User's Guide

## Figure 2-11 N Cycle Burst

For N cycle burst, "Internal", "External", or "Manual" trigger source could be selected.
Besides, you can also set the parameters of "Period" (internal trigger), "Delay",
"Trig In" (external trigger) and "Trig Out" (internal and manual trigger).


## Infinite Burst

In Infinite mode, the cycle number of the waveform is set as an infinite value. The
generator outputs a continuous waveform after receiving a trigger signal.

Press Menu  Burst  "Infinite" to enable the Infinite burst. The instrument will
set the trigger source to "Manual" automatically. A diagram of an infinite cycle burst
will appear on the screen.

## Figure 2-12 Infinite Burst

For the Infinite burst, "External" or "Manual" trigger source could be selected.
Besides, users can set the parameters of "Delay", "Trig In" (external trigger), and
"Trig Out" (manual trigger).




Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-65
## Gated Burst

In Gated Burst Mode, the generator controls the waveform output according to the
external signal level input from the rear-panel [CH1/Sync/Ext Mod/Trig/FSK]
connector.

Press Menu  Burst  "Gated" to enable the gated burst. Then tap the Polarity
menu label to select "Positive" or "Negative". Only when the gated signal is Positive
or Negative, can the waveforms be output.

## Figure 2-13 Gated Burst

When the gated signal is "True", the generator outputs a continuous waveform.
When the gated signal is "False", the generator first completes the output of the
current period and then stops. For Noise waveform, the output will stop immediately
once the gated signal becomes "False".

Gated Burst could only be triggered by "External" trigger source.


## Burst Delay

Burst delay is only available for N cycle and Infinite burst mode. It is defined as the
duration from the time when the generator receives the trigger signal to the time
when it starts to output the N Cycle (or Infinite) burst.

Press Menu  Burst to select "NCycle" or "Infinite", and then tap the Delay menu
label and use the numeric keypad to input the desired delay time. You can also use
the arrow keys and the knob to input a desired delay time. The range of the delay
time is: 0 s ≤delay time ≤ 100 s. The default is 0 s.






RIGOL Chapter 2 Front Panel Operations
2-66                               DG800 User's Guide
## Burst Period

Burst period is only available for N cycle burst in the internal trigger. It is defined as
the time from the start of a burst to the time when the next burst starts.
 Burst Period ≥ 1 μs + waveform period × number of bursts. Wherein, the
waveform period indicates the period of burst function (e.g. Sine and Square).
 If the burst period currently set is too small, the generator will increase this
period automatically to allow the output of the specified number of cycles.

Press Menu  Burst  "NCycle" to enable the N Cycle burst. Tap the Source
menu label to select "Internal", and then tap the Period menu label to input the
desired period by using the numeric keypad. You can also use the arrow keys and the
knob to input a desired period. By default, it is 10 ms, and its available range is from
1 μs to 500 s.


## Idle Level

In burst mode, the generator outputs the carrier waveform with a specified number
of cycles and then outputs a level, as shown in the figure below. The level is defined
as idle level.


Figure 2-14 Definition of Idle Level

When Burst is enabled, tap Idle Level to select your desired menu to set the idle
level.

## 1. 1st Point
Sets the level at the first point of the carrier waveform as the idle level.

- To p
Sets the level at the top point of the carrier waveform as the idle level.

## 3. Center
Sets the level at the center point of the carrier waveform as the idle level.

## 4. Bottom
Sets the level at the bottom point of the carrier waveform as the idle level.

## 5. User
Sets the level at the specified point of the carrier waveform as the idle level.
## Idle Level

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-67
Ta p   t h e   User menu label, and input the desired value by using the numeric
keypad. You can also use the arrow keys and the knob to input a desired value.
Its range is from 0 to 65535.


## Burst Trigger Source

Burst trigger source can be internal, external, or manual. The generator will generate
a burst output when a trigger signal is received, and then it waits for the next trigger
signal. After the burst function is enabled, tap the Source to select "Internal",
"External", or "Manual". The default is "Internal".

## 1. Internal Trigger
When internal trigger is selected, the generator can only output N cycle burst,
and the output burst frequency is determined by the "Burst Period".

Ta p   t h e   Trig Out menu label to select "RisEdge" or "FallEdge".
The rear-panel [CH1/Sync/Ext Mod/Trig/FSK] connector will output the
trigger signal with a specified edge. If you select "Off", the trigger output is
disabled.

## 2. External Trigger
When external trigger is selected, the generator can only output N cycle burst,
Infinite burst, or Gated burst. The signal generator receives the trigger signal
input from the rear-panel [CH1/Sync/Ext Mod/Trig/FSK] connector. Once it
receives a TTL pulse with a specified polarity, a burst output is initiated. To
specify the polarity of the TTL pulse, tap Trig In to select "RisEdge" or
"FallEdge". By default, it is "RisEdge".

## 3. Manual Trigger
When manual trigger is selected, the generator can output N cycle burst or
Infinite burst. When you press Trig on the front panel for one time, one burst
output is immediately launched for the corresponding channel (if enabled
currently).
Ta p   t h e   Trig Out menu label to select "RisEdge" or "FallEdge".
The rear-panel [CH1/Sync/Ext Mod/Trig/FSK] connector will output the
trigger signal with a specified edge. If you select "Off", the trigger output is
disabled.








RIGOL Chapter 2 Front Panel Operations
2-68                               DG800 User's Guide
## Gated Polarity

Gated polarity is only available in gated burst mode.
The instrument outputs the burst when the gated signal on the rear-panel
[CH1/Sync/Ext Mod/Trig/FSK] connector is "High Level" or "Low Level".

Press Menu  Burst  "Gated" to enable the gated burst. Tap the Polarity to
select "Positive" or "Negative", and the default is "Positive".




Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-69
## Frequency Counter

DG800 provides a frequency counter which can measure various parameters (e.g.
frequency, period, duty cycle, positive pulse width, and negative pulse width) of the
external input signal and make statistics of measurement results. When the
statistical function is enabled, the instrument calculates the maximum, minimum,
average, and standard deviation of the measurement values automatically and
displays the variation tendency of the measurement values in "Digital" or "Curve"
mode. In addition, CH1 output can work normally while the frequency counter is
making measurements.

To Enable the Frequency Counter

Press Counter on the front panel (the backlight turns on) to enable the frequency
counter function and enter the frequency counter setting interface.


## Figure 2-15 Frequency Counter Parameter Setting Interface

If the frequency counter is currently turned on and the screen displays the frequency
counter interface, press Counter again to disable the frequency counter function. If
the frequency counter is currently enabled and the screen displays interfaces other
than the frequency counter interface, press Counter again to switch to the
frequency counter interface.

Note: When the frequency counter is enabled, the output of CH2 will be disabled.


RIGOL Chapter 2 Front Panel Operations
2-70                               DG800 User's Guide
To Set the Frequency Counter

## 1. Gate Time
Ta p   t h e   GateTime parameter selection field to select the gate time for the
measurement system. The default is "100ms". When "Auto" is selected, the
instrument will select an appropriate gate time automatically according to the
characteristics of the signal to be measured.

1 ms 1.048 ms
10 ms 8.389 ms
100 ms 134.218 ms
1 s 1.074 s
10 s 8.590 s
>10 s >8.590 s

- To Select the Parameters to be Measured
Ta p   t h e   Meas.Para parameter selection field to select the type of parameter to
be measured by the frequency counter. The frequency counter can measure the
following parameters: frequency, period, duty cycle, positive pulse width, and
negative pulse width. The default is "frequency".

## 3. Statistical Function
Ta p   t h e   Statistics parameter selection field to enable or disable the statistical
function of the frequency counter. When the statistical function is enabled, the
instrument calculates the maximum, minimum, average, and standard deviation
of the measurement values automatically and displays the variation tendency of
the measurement values in "Digital" or "Curve" mode. Slide left the touch screen
to switch to the statistics display interface.


## Figure 2-16 Statistics Display Interface


Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-71
(1) To Clear the Statistics Results
Ta p   t h e   "Clear" menu label, and the signal generator clears the current
statistics results.

## (2) Operating Status
Ta p   t h e   Status parameter selection field to select the running status of the
frequency counter. When you press Counter on the front panel, the
frequency counter enters "Run" state automatically and it will continuously
measure the input signal according to the current configuration. Tap the
Status menu label to select "Single". After finishing the current
measurement, it ethers the "Stop" status.

When the frequency counter enters the "Stop" status, each time you press the
Single menu label, the frequency counter executes one measurement.

Note: When the statistical function is disabled, sliding left in the frequency
counter parameter setting interface will switch to the frequency counter
parameter measurement interface.


## Figure 2-17 Frequency Counter Parameter Measurement Interface

## 4. Sensitivity
Sets the trigger sensitivity of the measurement system. Tap the Sensitivity
parameter selection field to    select "High" or "Low".

## 5. Trigger Level
Sets the trigger level of the measurement system. The system triggers and gets
the measurement readings when the input signal reaches the specified trigger
level. The default is 0 V, and the range available is from -2.5 V to 2.5 V. Tap the
Trig Lev parameter input field to input the desired value by using the numeric
keypad and select the unit "V" or "mV" from the pop-up menu.

## 6. Coupling
Sets the coupling mode of the input signal to "AC" or "DC". The default is "DC".


RIGOL Chapter 2 Front Panel Operations
2-72                               DG800 User's Guide
## 7. High Frequency Rejection
High frequency rejection can be used to filter out the high-frequency
components and improve the measurement accuracy in low-frequency signal
measurement. Tap the High Freq Rejection parameter selection field to
enable or disable the high frequency rejection function.

Note: Enable the high frequency rejection when low-frequency signal with less
than 200 kHz frequency is measured to filter out the high-frequency noise
interference. Disable the high frequency rejection when high-frequency signal
with greater than 200 kHz frequency is measured. At this time, the maximum
input frequency can be 240 MHz.



Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-73
Store and Recall

DG800 can store the current instrument state and user-defined Sequence waveforms
in the internal or external memory. You can recall them when needed. DG800 can
also seamlessly interconnect with RIGOL's oscilloscopes that support USB-TMC;
rebuild and output the waveform data collected by the oscilloscope losslessly.

Press Store on the front panel or tap the
icon in the information setting area at
the lower-right corner of the user interface to enable the Store/Recall function and
open the Store/Recall interface as shown in the figure below.


Figure 2-18 Store and Recall Interface

## Storage System

DG800 can store the current instrument state and user-defined Sequence waveforms
in the internal or external memory. You can recall them when needed. DG800
provides an internal non-volatile memory (Disk C) and an external memory (Disk D).

1． Disk C: You can store instrument states and Sequence waveform files (created
by users or downloaded through remote commands) to Disk C. Also, you can
copy the files from Disk C to the USB storage device.

2． Disk D: available when the USB storage device is detected by the rear-panel
USB HOST interface.
You can store state files or arbitrary waveform files to Disk D. The number of the
files that can be stored is determined by the storage capacity of the USB storage
device.
The Csv files and Bmp files stored in the USB storage device can also be read.

Note: DG800 can only identify the file whose filename is named in the filename
input interface. If other characters are used to name the file, the name might not be
normally displayed in the store and recall interface.

RIGOL Chapter 2 Front Panel Operations
2-74                               DG800 User's Guide
## File Type

The file types supported by DG800 include State File, Arb File, Csv File, and Bmp File.

## 1. State File
Stores the instrument state in the internal or external memory in "*.RSF" format.

The state file stored includes the dual-channel selected waveform, frequency,
amplitude, offset, duty cycle, symmetry, phase, modulation, sweep, burst
parameters, frequency counter parameters, as well as utility function parameters
and system parameters under the Utility menu.

## 2. Arb File
Stores the user-defined arbitrary waveform in the internal or external memory in
"*.RAF" format.

For the arbitrary waveform file, the voltage values corresponding to each
waveform point are stored in binary data format. The voltage value at each point
takes up 2 bytes (16 bits). DG800 only uses 14 bits, and the higher 14 bits are
used to represent voltage and the lower 2 bits are not used. Therefore, its format
of the binary data is from 0x0000 to 0xFFFC.

The stored arbitrary waveform files can be read by the DG800 series. Besides,
the arbitrary waveform files stored in the USB storage device can be opened and
edited by data editing tools (e.g. WinHex or UltraEdit) on the PC.

## 3. Csv File
Reads the data file in Csv format from the external memory. After finishing
reading the file, the instrument automatically enters the arb waveform function
interface. The arbitrary waveforms that have been read are stored in the RAM.

## 4. Bmp File
Reads the "*BMP" format bitmap file from the external memory. It is only
available when you self-define splash screen.


## Categories

In the Store and Recall interface, tap the "Arb File" or "State File" under the
Categories menu label to view the arb file or state file in the first-level folder of Disk
C and D (when inserted with a USB storage device).
You can also use the Left arrow key to locate the cursor to the left side of the user
interface, and then rotate the knob to select the "Arb File" or the "State File"
folder. Press down the knob to enter the current directory.


Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-75
## File Operation

In the Disk C or D (when inserted with a USB storage device), you can perform a
series of operations on the files, including Save, Read, Copy, Paste, and Delete.

## Save

- To Select the Save Path
Selects Disk C or D (when inserted with a USB storage device) as the current
save path.
You can tap Disk C or D to enter the current directory. You can also use the Left
arrow key to locate the cursor to the left side of the user interface, and then
rotate the knob to select Disk C or D. Press down the knob to enter the current
directory.

Only the state file and the arb file can be saved locally. If the current file is "Arb
File", press Menu  Advanced  "Sequence". In the Sequence editing
interface, tap "Store" to save the file.

- To Open the Filename Input Interface
After selecting the path, tap Save to enter the filename input interface, as
shown in the following figure.




Figure 2-19 Filename Input Interface (English)

- To Input a Filename
The length of the filename is limited to 7 characters.

##  Input English Letters:
Ta p
in the filename input interface to select English input method (EN
is highlighted). Tap
to switch between the upper-case and lower-case
letters.
## Filename Input Area

RIGOL Chapter 2 Front Panel Operations
2-76                               DG800 User's Guide
Tap the desired character, and the selected character will be displayed in the
filename input area. Use the same method to input all the characters of the
filename. You can also tap
the delete the unwanted characters in the
filename input area.

##  Input Numbers
Ta p
in the filename input interface to switch to the numbers and
symbols selection interface, as shown in the following figure. The input
method is similar with that of the English input.


Figure 2-20 Filename Input Interface (Numbers)

##  Input Chinese
Ta p
in the filename input interface to select Chinese input method
(CH is highlighted). Note that if the current interface is number input
interface, tap
to switch to English input interface. Then, select
Chinese input.




Figure 2-21 Filename Input Interface (Chinese)

Tap the desired character, and the selected character will be displayed in
## Filename Input Area    Pinyin Input Area Chinese Character Display Area

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-77
the Pinyin input area. After inputting the Pinyin for a Chinese character, tap
the desired Chinese character in the Chinese character display area (if no
proper Chinese character exists, tap
or   to page down to search for
the desired Chinese character). The selected Chinese character will be
displayed in the filename input area. Use the same method to input all the
Chinese characters of the filename. You can also tap
the delete the
unwanted characters in the Pinyin input area, and then delete the Chinese
character located ahead of the cursor in the filename input area.

- To Save a File
After finishing inputting filename in the filename input interface, press "Ok", and
the generator will save the file with the specified filename to the currently
selected directory. Tap "Cancel" to cancel the save operation.


## Read

- To Select the Read Path
Selects Disk C or D (when inserted with a USB storage device) as the current
read path.
You can tap Disk C or D to enter the current directory. You can also use the Left
arrow key to locate the cursor to the left side of the user interface, and then
rotate the knob to select Disk C or D. Press down the knob to enter the current
directory.

- To Select the File to be Read
In the selected path, tap or use the knob to select the file to be read.
For Disk C, only state file and arb file can be read. For Disk D, the state files, arb
waveform files, Csv files, and bitmap files can be read. Note: the bitmap file can
only be read when you self-define splash screen.

- Read a file
Press Read, and the generator will read the currently selected file and display
the corresponding prompt message when the file is read successfully.


Copy and Paste

- To Select a File to be Copied
In the selected path, tap or use the knob to select the file to be copied.

- To Copy a File
Ta p   Copy, the generator will copy the currently selected file.

- To Select a Paste Location

RIGOL Chapter 2 Front Panel Operations
2-78                               DG800 User's Guide
 When copying file from Disk C to Disk D, tap or use the knob to select the
Disk D directory.
 When copying file from Disk D to Disk C, tap or use the knob to select the
Disk C directory.

- To Paste a File
Ta p   Paste, the generator will paste the copied file to the currently selected
directory. After that, a corresponding prompt message will be displayed,
indicating that the paste operation is completed.


## Delete

- To Select a File to be Deleted
In the selected path, tap or use the knob to select the file to be deleted.

- To Delete a File or Folder
Ta p   Delete, the generator will delete the currently selected file.



Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-79
Seamless Interconnection with Oscilloscope

DG800 can also seamlessly interconnect with RIGOL's oscilloscopes that support
USB-TMC; rebuild and output the waveform data collected by the oscilloscope
losslessly. The connection method between the instruments is as shown in the figure
below.







## Operation Procedures:
- Make sure the signal under test is displayed stably on the screen of DS1.

- Connect the USB HOST interface of DG800 with the USB DEVICE interface of
DS1 by using the USB cable. Now, DS1 will enter the remote mode
automatically.

- Use DG800 to read the signal under test that is displayed currently on the screen
of DS1: Press Store on the front panel of DG800 to enter the store and recall
interface. At this time, the Oscilloscope menu label is displayed below the
Categories menu label, and the model identifier of DS1 will be displayed under
Oscilloscope. Tap or use the knob of DG800 to select the DS1 model identifier
to enter the seamless interconnection operation interface.

## Figure 2-22 Seamless Interconnection Operation Interface

All the channels of DS1 and their  on/off status are displayed at the left section of
the interface. The parameter settings are displayed at the right section of the
interface. Tap the first parameter selection field to set the data type of the
current channel to be read to "Screen Data" or "Ram Data". Tap the second
parameter selection field to set the data position (only available when data type
## DG800
## DS1
## DS2
USB  DEVICE                  USB  HOST                    Output  Terminal                Input  Terminal
USB  Cable                                                    BNC  Cable

RIGOL Chapter 2 Front Panel Operations
2-80                               DG800 User's Guide
is set to "Ram Data"), and its available choices include "Head Pos", "Trig Pos",
and "Tail Pos".
Tap or use the knob to select the channel to be read, and then set the
parameters of the corresponding channel. Tap Read. At this time, DS1 will enter
the "Stop" status automatically, and DG800 will read the arbitrary waveform
data (i.g. the waveform data collected by DS1) automatically. After reading the
data, the instrument saves them to the internal RAM of the current channel and
switches to Sequence mode (if the current mode is not Sequence mode)
automatically.

- Use the BNC cable to connect the output of the current channel of DG800 to the
input of DS2. Turn on the channel output and DG800 will output the arbitrary
waveform collected by DS1. You can observe the waveform collected by DS1
from DS2 by setting DS2.



Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-81
## Channel Setting

The function and setting methods of CH2 are the same as that of CH1. This section
takes CH1 as an example to introduce the channel setting method. To set the CH2
channel output parameters, select CH2 (refer to "To Select Output Channel") and
then set the channel according to the descriptions in this section.

Tap the channel output configuration status bar
or   under
the user interface to enter the channel setting interface. Tap the corresponding menu
label to set the parameters related with the channel.


## Figure 2-23 Channel Setting Interface

## Output Setting

- Output On/Off
Enable or disable the signal on the [CH1] connector. In the channel setting
interface, tap the OutputSet menu label, and then tap the Output parameter
selection field to select "On" or "Off" to enable or disable the signal output. By
default, it is set to "Off".

## 2. Output Polarity
Set the signal on the [CH1] connector as Normal or Inverted. Waveform is
inverted relative to the offset voltage. In the channel setting interface, tap the
OutputSet menu label, and then tap the Inverted parameter selection field to
select "On" or "Off". By default, it is set to "Off". If "Off", the instrument outputs
the normal waveform; if "On", the instrument outputs the inverted waveform.
For example, if Inverted   is "Off" (normal mode), the first half period of the
waveform in the cycle is Positive; if Inverted is "On", the first half period of the
waveform in the cycle is Negative, as shown in the figure below.


RIGOL Chapter 2 Front Panel Operations
2-82                               DG800 User's Guide

Note: When the waveform is inverted, the sync signal related to the waveform
is not inverted. To set the invert of the sync signal, tap SyncSet  Polarity to
select "Negative".

## 3. Output Impedance
The output impedance setting affects the output amplitude and DC offset. The
instrument has a 50 Ω fixed serial output impedance for the front-panel [CH1]
connector. If the actual load is different from the specified value, then the
displayed voltage level will not match the voltage level of the components under
test. To ensure a correct voltage level, ensure that the load impedance setting
must match the actual load.

In the channel setting interface, tap the OutputSet menu label, and then tap
the HighZ parameter selection field to select "On" or "Off". The default is "On".
When "Off", tap the Impedance menu label, and input the desired value by
using the numeric keypad. You can also use the arrow keys and the knob to set
the impedance. The default is 50 Ω, and the range is from 1 Ω to 10 kΩ.
Impedance setting will be displayed on the screen.

The generator will adjust the output amplitude and offset voltage automatically
once the impedance setting is modified. For example, the current amplitude is 5
Vpp. At this point, modify the output impedance from "50Ω" to "HighZ". Then,
the amplitude value displayed on the screen will be doubled to 10 Vpp. If the
output impedance is modified from "HighZ" to "50Ω", the amplitude value will be
reduced to half of the previous value (i.g. 2.5 Vpp). Note that only the displayed
values change with the parameter and the actual output from the generator
does not change.

## 4. Level Limit
Enables or disables the level limit function.
In the channel setting interface, tap the OutputSet menu label, and then tap
the Level Limit parameter selection field to select "On" or "Off". By default, it is
set to "Off". When "On", the set high level and low level values will be limited
within the range of the "HighL Limit" and "LowL Limit".

Ta p   HighL Limit and LowL Limit respectively, and then use the numeric
keypad to set the desired high level limit and low level limit. The settable ranges
of the high level limit and low level limit are determined by the currently set
amplitude and offset values.

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-83
## Sync Setting

DG800 can output the basic waveforms (except Noise and DC), arb waveforms,
harmonics, sweep waveforms, burst waveforms, and the sync signal of the
modulated waveforms from a single channel or the dual channels at the same time.
The signal will be output from the rear-panel [CH1/Sync/Ext Mod/Trig/FSK]
connector.

## 1. Sync Switch
Enables or disables the sync signal on the [CH1/Sync/Ext Mod/Trig/FSK]
connector. In the channel setting interface, tap the SyncSet menu label, and
then tap the SyncState parameter selection field to select "On" or "Off" to
enable or disable the sync signal output. By default, it is "On". That is, send the
sync signal to the [CH1/Sync/Ext Mod/Trig/FSK] connector. When
disabling the sync signal, the output level on the [CH1/Sync/Ext
Mod/Trig/FSK] connector is the logic low level.

## 2. Sync Polarity
Sets the signal on the [CH1/Sync/Ext Mod/Trig/FSK] connector as
"Normal" or "Inverted". In the channel setting interface, tap the SyncSet menu
label, and then tap the Polarity parameter selection field to select "Positive" or
"Negative".
 Positive: outputs the normal sync signal.
 Negative: outputs the inverted sync signal.

## Key Points:

Sync signals of various waveforms:

## 1. Basic Waveforms
1) When the frequency of the basic waveform is less than or equal to 100
kHz:
The sync signal is a Square with 50% duty cycle, and the same frequency
as that of the basic waveform. When the first waveform point is output,
the sync signal is TTL high level.
2) When the frequency of the basic waveform is greater than 100 kHz:
 Sine and Ramp: the sync signal is a Square with 50% duty cycle.
 Square and Pulse: the sync signal is a Square with a variable duty
cycle. The duty cycle varies with the duty cycle of the output signal.
Take 0 V voltage or the DC offset of the basic waveform as the reference,
the sync signal is TTL high level when the corresponding value of the
output signal is greater than the reference value. When the frequency of
the basic waveform is less than or equal to 30 MHz, the sync signal has
the same frequency as the basic waveform. When the frequency of the
basic waveform is greater than 30 MHz, the frequency of the sync signal

RIGOL Chapter 2 Front Panel Operations
2-84                               DG800 User's Guide
is (the basic waveform frequency÷2
n
). Wherein, n represents the
frequency dividing coefficient and it is 1 when the frequency of the basic
waveform is greater than 30 MHz and less than or equal to 60 MHz.
3) Noise: there is no sync signal output.

## 2. Harmonic
For harmonics, the sync signal is a Square with 50% duty cycle, and its
frequency is the same as that of the fundamental waveform. When the first
waveform point is output, the sync signal is TTL high level.

## 3. Arbitrary Waveform
For arbitrary waveforms, the sync signal is a Square with 50% duty cycle, and
its frequency is the same as that of the arbitrary waveform. When the first
waveform point is output, the sync signal is TTL high level.

## 4. Modulated Waveform
1) When internal modulation source is selected, the sync signal is a Square
with 50% duty cycle.
 For AM, FM, PM, and PWM, the frequency of the sync signal is the
modulating frequency.
 For ASK, FSK, and PSK, the frequency of the sync signal is the
modulating rate.
2) When external modulation source is selected:
The terminal is used to receive the external modulation signal, and there
is no sync signal output.

## 5. Sweep Output Waveform
1) When the internal or manual trigger source is selected:
 For the sweep with "Marker Freq" off:
The sync signal is a Square with 50% duty cycle. The sync signal is
TTL high level at the start of the sweep and changes to low level at
the mid-point of the sweep. The frequency of the sync signal is the
reciprocal of the sum of the specified sweep time, return time, start
hold, and stop hold time.
 For the sweep with "Marker Freq" on:
For linear and log sweep, the sync signal is TTL high level at the start
of the sweep and changes to low level at the marker frequency.

For step sweep (the sweep points determined by the start frequency,
stop frequency, and step respectively are f
## 1
, f
## 2
, ......, f
n
, f
n+1
......), if
the marker frequency setting is one of the sweep points values, the
sync signal is TTL high level at the start of the sweep and will change
to low level at the marker frequency point. If the set marker
frequency is not equal to the value at the sweep point, the sync
signal will change to low level at the sweep point which is closest to

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-85
this marker frequency.
2) When external trigger source is selected:
The terminal is used to receive the external trigger signal, and there is no
sync signal output.

## 6. Burst Waveform
1) When the internal or manual trigger source is selected:
 Infinite burst: the sync signal is the same as that of the basic
waveform.
 N cycle burst: the sync signal is TTL high level at the start of the
burst and will change to TTL low level after the specified number of
cycles is finished. For the sync signal, the frequency is the
reciprocal of the Burst Period and the duty cycle is Carrier
Period*Cycles/Burst Period.
 Gated burst: the terminal is used to receive the external gate signal,
and there is no sync signal output.
2) When external trigger source is selected:
The terminal is used to receive the external trigger signal, and there is no
sync signal output.



## Coupling Setting

DG800 supports frequency, amplitude, and phase couplings. You can set the
frequency deviation (frequency ratio), amplitude deviation (amplitude ratio), or
phase deviation (phase ratio) of the two channels. When the corresponding coupling
functions are enabled, CH1 and CH2 are mutual base sources. When the frequency,
amplitude, or phase of one channel (as the base source) is changed, the
corresponding parameter of the other channel will be changed automatically and
always keeps the specified frequency deviation (ratio), amplitude deviation (ratio), or
phase deviation (ratio) relative to the base channel.

In the channel setting interface, tap the CoupleSet menu label to enter the channel
coupling setting interface.

## Frequency Coupling

- To Enable the Coupling Function
Ta p   t h e   Freq Cpl parameter selection field to select "On" or "Off" to enable or
disable the frequency coupling function. By default, it is set to "Off".

## 2. Freq Coupling Mode
Ta p  t h e  FreqCplMode parameter selection field to select "Deviation" or "Ratio".
Then, tap the Freq Dev or Freq Ratio parameter selection field to input the

RIGOL Chapter 2 Front Panel Operations
2-86                               DG800 User's Guide
desired value by using the numeric keypad, the arrow keys, or the knob.
 Freq Deviation: indicates the frequency deviation between CH1 and CH2.
The relations among the parameters are as follows: F
## CH2
## =F
## CH1
## +F
## Dev
## (take
CH1 as the reference source); F
## CH1
## =F
## CH2
## +F
## Dev
(take CH2 as the reference
source).
 Freq Ratio: indicates the ratio of the frequencies of CH1 to that of CH2. The
relations among the parameters are as follows: F
## CH2
## =F
## CH1
## *F
## Ratio
(take CH1
as the reference source); F
## CH1
## =F
## CH2
## *F
## Ratio
(take CH2 as the reference
source).

Note: Please set this parameter before enabling the frequency coupling
function. When the frequency coupling is enabled, this menu is grayed out and
disabled. You cannot set the frequency deviation or frequency ratio.


## Amplitude Coupling

- To Enable the Coupling Function
Ta p   t h e   Ampl Cpl parameter selection field to select "On" or "Off" to enable or
disable the amplitude coupling function. By default, it is set to "Off".

## 2. Amp Coupling Mode
Ta p  t h e  AmplCplMode parameter selection field to select "Deviation" or "Ratio".
Then, tap the Ampl Dev or Ampl Ratio parameter input field to input the
desired value by using the numeric keypad.
 Ampl Deviation: indicates the amplitude deviation between CH1 and CH2.
The relations among the parameters are as follows: A
## CH2
## =A
## CH1
## +A
## Dev
## (take
CH1 as the reference source); A
## CH1
## =A
## CH2
## +A
## Dev
(take CH2 as the reference
source).
 Ampl Ratio: indicates the ratio of the amplitudes of CH1 to that of CH2. The
relations among the parameters are as follows: A
## CH2
## =A
## CH1
## *A
## Ratio
(take CH1
as the reference source); A
## CH1
## =A
## CH2
## *A
## Ratio
(take CH2 as the reference
source).
Note: Please set this parameter before enabling the amplitude coupling
function. When the amplitude coupling is enabled, this menu is grayed out and
disabled. You cannot set the amplitude deviation or amplitude ratio.


## Phase Coupling

- To Enable the Coupling Function
Ta p  t h e  Phase Cpl parameter selection field to select "On" or "Off" to enable or
disable the phase coupling function. By default, it is set to "Off".

- PhasCplMod
Ta p  t h e  PhasCplMode parameter selection field to select "Deviation" or "Ratio".

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-87
Then, tap the Phase Dev or Phase Ratio parameter input field to input the
desired value by using the numeric keypad.
 Phase Deviation: indicates the phase deviation between CH1 and CH2. The
relations among the parameters are as follows: P
## CH2
## =P
## CH1
## +P
## Dev
(take CH1
as the reference source); P
## CH1
## =P
## CH2
## +P
## Dev
(take CH2 as the reference
source).
 Phase Ratio: indicates the ratio of the phases of CH1 to that of CH2. The
relations among the parameters are as follows: P
## CH2
## =P
## CH1
## *P
## Ratio
(take CH1
as the reference source); P
## CH1
## =P
## CH2
## *P
## Ratio
(take CH2 as the reference
source).

Note: Please set this parameter before enabling the phase coupling function.
When the phase coupling is enabled, this menu is grayed out and disabled. You
cannot set the phase deviation or phase ratio.


## Trigger Coupling

Ta p the Trig Coupling parameter selection field to select "On" or "Off" to enable or
disable the trigger coupling function. By default, it is set to "Off".

When enabling the output of the two channels at the same time and enabling the
trigger coupling, if one channel executes the trigger, then another channel will be
triggered automatically.

When the corresponding coupling function is enabled, there will be a blue mark
at
the left side of the frequency, amplitude, and phase of the two channels. As shown in
the following figure, the frequency, amplitude, and phase are in the coupling state.
For example, when the frequency, amplitude, and phase deviations are set to
"100Hz", "1Vpp", and "10°" respectively, and the frequency, amplitude, phase of CH1
are modified to "200Hz", "2Vpp", and "20°", then the corresponding parameters of
CH2 will be automatically modified to "300Hz", "3Vpp", and "30°". Switch to CH2 and
modify the frequency, amplitude, phase of CH2 to "200Hz", "2Vpp", and "20°", then,
the corresponding parameters of CH1 will be automatically modified to "100Hz",
"1Vpp", and "10°".


RIGOL Chapter 2 Front Panel Operations
2-88                               DG800 User's Guide

## Figure 2-24 Channel Coupling

## Key Points:

 Channel coupling is only available when both the waveforms of the two
channels are basic waveforms (Sine, Square, Ramp, or Arbitrary waveform).
 The generator will adjust the frequency, phase, or amplitude of the channel to
avoid parameter over-limit if the following conditions occur: 1. the result of the
frequency, amplitude or phase value of CH1 plus (or multiply) the set deviation
(or ratio) exceeds the upper limit of frequency, amplitude or phase of CH2; 2.
the result of the frequency, amplitude or phase value of CH2 minus (or is
divided by) the set deviation (or ratio) is below the lower limit of frequency,
amplitude or phase of CH1.
 When the phase of the one channel is modified, the phase (phase displayed
on the interface) of the other channel will be modified accordingly. At this
point, aligning phase between the two channels can be realized without
executing the Align Phase operation.


## Track Mode

Ta p   t h e   Track Mode parameter selection field and select the track type to "On",
"Inverted", or "Off".
 On: enables the track function. The instrument copies the various parameters
and states (except the channel output state) of CH1 to CH2 automatically. When
the parameters or states of CH1 are modified, the corresponding parameters or
states of CH2 (except the channel output state) will be adjusted to the same
values or states automatically. At this time, the dual channels (if currently
enabled) can output the same signal.
 Inverted: the track function has been enabled. The instrument copies the
various parameters and states (except the channel output state) of CH1 to CH2
automatically. When the parameters or states of CH1 are modified, the
corresponding parameters or states of CH2 (except the channel output state)
will be adjusted to the same values or states automatically. At this time, CH2

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-89
outputs the inverted signal of the output signal of CH1 (if channels are currently
enabled).
 Off: disables the track function. This is the default state.

Note: When the track function is enabled, the coupling function is  disabled.


## Waveform Combination

- To Enable the Waveform Combination Function
In the channel setting interface, tap the CombineSet menu label and then tap
the Combine parameter selection field to select "On" to enable the waveform
combine function. Then, you can combine the specified waveforms based on the
current fundamental waveform. If you select "Off", the waveform combine
function is disabled.

Note: This function is only valid for the basic waveforms.

- To Select the Waveform to be Combined
In the channel setting interface, tap the CombineSet menu label and then tap
the Waveform parameter selection field to select a waveform to be combined
to the current basic waveform.

## 3. Freq Combination
Sets the frequency of the waveform to be combined to the current basic
waveform. In the channel setting interface, tap the CombineSet menu label
and then tap the Freq parameter input field to input the desired value by using
the numeric keypad. The range is related to the currently selected basic
waveform.

## 4. Ratio
Sets the ratio of the amplitude of the waveform to be combined to that of the
current basic waveform. In the channel setting interface, tap the CombineSet
menu label and then tap the Ratio parameter input field to input the desired
value by using the numeric keypad.










RIGOL Chapter 2 Front Panel Operations
2-90                               DG800 User's Guide
## Common Settings
Press Utility on the front panel or tap the   icon in the information setting area
at the lower-right corner of the user interface to open the following operation
interface. The interface displays the system parameters of the currently selected
channel.


## Figure 2-25 Utility Interface

## System Setting

To Set the System Language

At present, DG800 supports menus in multiple languages. Both Chinese and English
are available for the display of the help information, prompt messages, and interface
display. Chinese and English input methods are also supported.

Press Utility  System Setting  Language to select the desired language. This
setting is stored in non-volatile memory and will not be affected by the "restore to
defaults" operation.


## Power-on

Selects "Default" or "Last" as the power-on system state. The default setting is
"Default".
 Last: includes all system parameters and states, except channel output state
and clock source.
 Default: denotes the factory defaults except certain parameters (e.g.
## Language).

Press Utility  System Setting  Power-on to select the desired configuration
type. This setting is stored in non-volatile memory and will not be affected by the
"restore to defaults" operation.

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-91
## Clock Source

DG800 provides an internal 10MHz clock source and receives the external clock
source from the rear-panel [10MHz In/Out] connector. It can also output clock
source from the [10MHz In/Out] connector for other devices.

Press Utility  System Setting  Clk Source to select "Internal" or "External".
The default is "Internal". If "External" is selected, the instrument will detect whether
a valid external clock signal is input from the rear-panel [10MHz Out/In] connector.
If no valid clock source is detected, a prompt message "No valid external clock is
detected!" is displayed, and the clock source will be switched to "Internal".

You can synchronize two or multiple instruments by setting the clock source. When
two instruments are synchronized, the "Align Phase" function cannot be used. It is
only applicable in adjusting the phase relations between two output channels of the
same instrument and cannot be used to change the phase relations between the
output channels of two instruments. Of course, you can change the phase relations
between two instruments by modifying the "Start Phase" of each output channel.

Sync methods for two or multiple instruments:
 Synchronization between two instruments:
Connect the [10MHz In/Out] connector of Generator A ("Internal" clock) to
the [10MHz In/Out] connector of Generator B ("External" clock) and set the
output frequencies of A and B as the same value to realize synchronization
between two instruments.
 Synchronization among multiple instruments:
Divide the 10MHz clock source of a Generator ("Internal" clock) into multiple
channels, and then connect them to the [10MHz In/Out] connectors of other
generators ("External" clock) respectively, and finally set the output frequencies
of all the generators as the same value to realize synchronization among
multiple instruments.


## Beeper

When the beeper in DG800 is enabled, a beep sound is generated when an error
occurs during front-panel operation, touch screen operation, or remote operation.

Press Utility  System Setting  Beeper to select "On" or "Off". The default is
"On".


## Decimal Point

Press Utility  System Setting  Decimal to set the display format of the

RIGOL Chapter 2 Front Panel Operations
2-92                               DG800 User's Guide
decimal point in the number parameter. It can be set to a decimal "." or a comma ",".
By default, it is a decimal ".". This setting is stored in non-volatile memory and will
not be affected by the "restore to defaults" operation.


## Delimiter

Press Utility  System Setting  Delimiter to set the display format of the
delimiter in the number parameter. This setting is stored in non-volatile memory and
will not be affected by the "restore to defaults" operation.

When the decimal is set to ".", the delimiter can be set to "," "Space", or "None";
when the decimal point is set to ",", the delimiter can be set to ".", "Space", or
"None". The decimal point and the delimiter cannot be set to a decimal "." or a
comma "," at the same time.


## System Log

Enables or disables the system log function. When enabled, the keys and prompt
messages can be recorded, and they will be saved to the internal memory in
Syslog.log file format.

Press Utility  System Setting  System Log to select "On" or "Off". The
default is "Off".


## Interface

Press Utility  Interface to select a different interface type. You can set the GPIB
address, LAN interface parameters, or select the type of the device connected to the
USB interface. The interface selection is stored in the non-volatile memory.


To Set the GPIB Address

Each device connected to GPIB interface must have a unique address.

Press Utility  Interface  GPIB, and then use the numeric keypad to set the
GPIB address to any value ranging from 0 to 30. The default is "2". The selected
address is stored in the non-volatile memory.




Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-93
To Set the LAN Parameters

DG800 only uses the following model of the USB-LA  N interface converter to expand
the LAN interface.

## Manufacturer Model Feature
## TP-LINK TL-UF2101.0
## 177TL-UF210 1.0
## 177TH2

USB2.0, 100Mbps
## UGREEN 20254

Press Utility  Interface  LAN to open the LAN parameters configuration
interface as shown in the figure below. You can view the network status and
configure the network parameters.


Figure 2-26 LAN Setting Interface

## Network Status

Different prompt messages will be displayed based on the current network status.
 Connected: indicates that the network connection is successful.
 Disconnect: indicates that the network connection is failed.
 Adapter not found: indicates that the network is not connected.


IP Configuration

IP configuration mode can be DHCP, AutoIP, or ManualIP. In different IP
configuration modes, the configurations for the IP address and other network
parameters are different.

## 1. DHCP
 In DHCP mode, the DHCP server in the current network assigns the network
parameters (e.g. IP address) for the signal generator.

RIGOL Chapter 2 Front Panel Operations
2-94                               DG800 User's Guide
 Ta p   t h e   DHCP parameter selection field to select "On" or "Off" to turn
DHCP mode on or off.

- AutoIP
 In Auto IP mode, the generator acquires IP address within the range from
169.254.0.1 to 169.254.255.254, and gets the subnet mask 255.255.0.0
automatically according to the current network configuration.
 Ta p   the AutoIP parameter selection field to select "On" or "Off" to turn the
AutoIP mode on or off. When DHCP and AutoIP modes are turned on at the
same time, the DHCP mode takes precedence. Therefore, to enable this
mode, set DHCP to "Off".

- ManualIP
 In ManualIP mode, the network parameters of the generator, e.g. IP
address, are defined by users.
 Ta p   t h e   ManualIP parameter selection field to select "On" or "Off" to turn
the ManualIP mode on or off. If all the three IP configuration modes are set
to "On", the priority of parameters configuration from high to low is "DHCP",
"AutoIP", and "ManualIP". Therefore, to enable this mode, set DHCP and
AutoIP to "Off".
 The format of the IP address is "nnn.nnn.nnn.nnn". The range for the first
segment (nnn) of the address is from 1 to 223 (except 127); and the range
for the other three segments is from 0 to 255. You are recommended to ask
your network administrator for an IP address available.
 Ta p  t h e  IP parameter input field in the LAN setting interface, and then input
a desired IP address by using the numeric keypad. The setting is stored in
the non-volatile memory and will be loaded automatically at next power-on
if DHCP and AutoIP are set to "Off".

## Tip:
 If all the three IP configuration modes are set to "On", the priority of
parameters configuration from high to low is "DHCP", "AutoIP", and
"ManualIP".
 The three IP configuration modes cannot be set to "Off" at the same time.


VISA Address

VISA (Virtual Instrument Software Architecture), developed by NI (National
Instrument), provides an advanced programming interface to communicate with
various instruments through their bus lines. VISA enables you to communicate with
the instrument in the same way, regardless of the interface type of the instrument
(e.g. GPIB, USB, LAN/Ethernet, or RS232). The GPIB, USB, LAN/Ethernet or RS232
instrument which wants to communicate with VISA is called "resource".


Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-95
VISA descriptor is the resource name and it describes the accurate name and
location of the VISA resource. If LAN interface is currently used for communication
with the instrument, the VISA descriptor is TCPIP0::192.168.001.102::INSTR.


To Set the Subnet Mask

In ManualIP mode, the subnet mask can be manually set.
 The format of the subnet mask is nnn.nnn.nnn.nnn. Wherein, the range of "nnn"
is from 0 to 255. You are recommended to ask your network administrator for a
subnet mask available.
 Ta p   t h e   Sub parameter input field in the LAN setting interface, and then input a
desired subnet mask by using the numeric keypad. The setting is stored in
non-volatile memory and will be automatically loaded when the generator is
powered on the next time if DHCP and AutoIP are set as "Off".



## To Set Default Gateway

In ManualIP mode, the default gateway can be manually set.
 The format of the default gateway is "nnn.nnn.nnn.nnn". The range for the first
segment (nnn) is from 1 to 223 (except 127); and the range for the other three
segments is from 0 to 255. You are recommended to ask your network
administrator for a gate address available.
 Ta p  t h e  Gate parameter input field in the LAN setting interface, and then input a
desired gateway address by using the numeric keypad. The setting is stored in
non-volatile memory and will be automatically loaded when the generator is
powered on the next time if DHCP and AutoIP are set to "Off".


To Set DNS

In ManualIP mode, the DNS can be manually set.
 The format of the DNS address is "nnn.nnn.nnn.nnn". The range for the first
segment (nnn) of the address is from 1 to 223 (except 127); and the range for
the other three segments is from 0 to 255. You are recommended to ask your
network administrator for an address available.
 Tap the DNS parameter input field in the LAN setting interface, and then input a
desired address by using the numeric keypad, the arrow keys, and the knob.
The setting is stored in the non-volatile memory and will be automatically loaded
when the generator is powered on the next time if DHCP and AutoIP are set to
"Off".





RIGOL Chapter 2 Front Panel Operations
2-96                               DG800 User's Guide
## Default Settings

Ta p   Default to restore the network parameters to the default settings. By default,
DHCP and AutoIP are enabled and ManualIP is disabled.


## Apply

Ta p   Apply to apply the currently set network parameters.


## System Info

Press Utility  System Info, and the model, serial number, and software version
number of the current instrument are displayed in the system information interface.


## Option

Press Utility  Option, and the installation status of the options for the current
instrument is displayed in the system information interface (for the installation of the
option, refer to "
To Install the Option").


## Display Setting

Press Utility  DispSet to enter the display setting interface.

## 1. Brightness Setting
Ta p   t h e   Brightness parameter input field and use the numeric keypad to
modify the brightness. The range is from 1% to 100%. The default is 50%. This
setting is stored in non-volatile memory and will not be affected by the "restore
to defaults" operation.

## 2. Screen Saver
Enables or disables the screen saver mode. Tap the Screen Saver parameter
selection field to select "On" or "Off" to enable or disable the screen saver
function. By default, it is set to "Off".

## 3. Splash Screen
DG800 allows you to self-define the splash screen. You can save the contents
displayed on the screen to the USB storage device in BMP format. Insert a USB
storage device into the USB HOST interface on the rear panel. Tap "Recall" at
the right side of the Splash Screen menu label to enter the store and recall

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-97
interface. Select the desired file in BMP format and tap Read.

Note: The internal memory cannot store the file in BMP format. You need to
store the contents in the USB storage device in BMP format first. The size of the
image cannot exceed 480*272  .


## Print Setting

You can store the contents displayed on the screen in the external USB storage
device in picture format.

- Insert a USB storage device into the USB HOST interface on the rear panel.

- Press Utility Print  Format to select "BMP" or "PNG".

- Switch the content displayed on the screen to the interface to be printed. Tap
at the lower-right corner of the user interface. The system will store the
screen in the USB storage device in the image format according to the preset
settings.



RIGOL Chapter 2 Front Panel Operations
2-98                               DG800 User's Guide
## System Utility Function

## To Restore Preset

Press Preset to restore the preset status interface, as shown in the figure below.

## Figure 2-27 Preset Status Restore Interface

 Factory: Tap the Def icon, then a dialog box is displayed, tap "Apply" to restore
the system to its factory defaults.

 User save: Tap any one of the items from "User1" to "User10". Then a dialog
box is displayed. Tap "Save"   to save the current system status to the internal
non-volatile memory as user-defined settings. To use the state again, tap the
icon (any one of the items from "User1" to "User10") to quickly recall the
setting. You can store up to 10 system states.

The defaults are shown in the following table. Note that the item with "*" is the
factory default value, and its value is related to the user setting during its usage but
not affected by the factory default restore operation.

Ta b l e   2-4 Factory Defaults
## Parameter Factory Settings
## Channel Parameter
## Current Carrier Waveform Sine
Output Impedance HighZ
## Output Load 50 Ω
## Channel Output Off
## Output Inverted Off
## Level Limit Off
HighL Limit 0 V
LowL Limit 0 V
SyncState Off
## Sync Polarity Negative
## Freq Cpl Off

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-99
FreqCplMode Deviation
Freq Dev 0 μHz
## Freq Ratio 1
## Ampl Cpl Off
AmplCplMode Deviation
## Ampl Dev 0 Vpp
## Ampl Ratio 1
## Phase Cpl Off
PhaseCplMode Deviation
## Phase Dev 0°
## Phase Ratio 1
## Trig Coupling Off
## Track Mode Off
## Combine Off
## Waveform Sine
Freq 1 kHz
## Ratio 10%

## Basic Waveforms
Frequency 1 kHz
## Amplitude 5 Vpp
## Amplitude Unit Vpp
## Offset 0 Vdc
## Phase 0°
## Square Duty Cycle 50%
## Ramp Waveform Symmetry 50%
## Pulse Duty Cycle 50%
Pulse Width 500 μs
Pulse Rising Edge 10 ns
Pulse Falling Edge 10 ns
## Harmonic Type Even
## Harmonic Order 2
## Harmonic Phase (7) 0°
## Harmonic No. 2
## Harmonic Amplitude (7) 1.2647 Vpp
## User X0000000
DC Offset 0 V
dc

## Built-in Arbitrary Waveforms Sinc

## Advanced Waveform
## Amplitude 5 Vpp
## Offset 0 Vdc
PRBS Bit Rate 2 kbps
PRBS Data PRBS7

RIGOL Chapter 2 Front Panel Operations
2-100                               DG800 User's Guide
RS232 Baud Rate 9600
RS232 Data Bits 8
RS232 Stop Bits 1
RS232 Parity Bit None
RS232 Data 85
## Sequence Filter Interpolation
Sequence Sample Rate 1 MSa/s
## Sequence Phase 0°

## Modulation
AM Modulation
## Source Internal
Mod.Wave Sine
Mod.Freq 100 Hz
Mod.Depth 100%
DSSC Off
FM Modulation
## Source Internal
Mod.Wave Sine
Mod.Freq 100 Hz
Freq.Dev 1 kHz
PM Modulation
## Source Internal
Mod.Wave Sine
Mod.Freq 100 Hz
Phas.Dev 90°
ASK Modulation
## Source Internal
Mod.Rate 100 Hz
Mod.Ampl 2 Vpp
## Polarity Positive
FSK Modulation
## Source Internal
Mod.Rate 100 Hz
Hop Freq 10 kHz
## Polarity Positive
PSK Modulation
## Source Internal
Mod.Rate 100 Hz
## Phase 180°
## Polarity Positive
PWM Modulation
## Source Internal
Mod.Wave Sine

Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-101
Mod.Freq 100 Hz
Width Deviation 200 μs
## Duty Deviation 20%

## Sweep
Sweep Time 1 s
Return Time 0 ms
## Start Freq 100 Hz
Stop Freq 1 kHz
## Center Frequency 550 Hz
## Frequency Span 900 Hz
Start Hold Time 0 ms
Stop Hold Time 0 ms
## Marker Off
## Marker Freq 550 Hz
## Trigger Source Internal
Tr ig I n RisEdge
## Step 2

## Burst
## Cycles 1
Period 10 ms
## Gated Polarity Positive
## Idle Level 1
st
## Point
## Trigger Source Internal
## Trig Out Off
Tr ig I n RisEdge
Delay 0 ns

## Interface Focus Items
Freq/Period Freq
Ampl/HighL Ampl
Offset/LowL Offset
Duty/Width Duty
Start/Center Start
Stop/Span Stop
Default Channel CH1

## Frequency Counter
Meas.Para Freq
GateTime 100 ms
## Statistics Off
## Sensitivity Low
## Trig Level 0 V

RIGOL Chapter 2 Front Panel Operations
2-102                               DG800 User's Guide
Coupling DC
## High Freq Rejection Off

## System Parameter
## System Setting
Language* Determined by Factory Delivery Setting
## Power-on Default
## Clk Source Internal
## Beeper On
## Decimal Dot
## Delimiter Comma
## System Log Off
DispSet
## Screen Saver Off
## Brightness* 100
## Print Setting
Location USB Storage Device
Format* PNG
## Interface
## GPIB* 2
DHCP* On (default setting in LAN)
Auto IP* On (default setting in LAN)
Manual IP* Off (default setting in LAN)


## Channel Copy

DG800 supports states and waveform copy function between its two channels, i.g.
copying all parameters and states (except the channel output state), as well as the
arbitrary waveform data of one channel to the other one.

Modify the channel setting of CH1, and then tap
at the lower-right corner of the
user interface to copy all parameters and states (except the channel output state), as
well as the arbitrary waveform data of CH1 to CH2.
Modify the channel setting of CH2, and then tap
at the lower-right corner of the
user interface to copy all parameters and states (except the channel output state), as
well as the arbitrary waveform data of CH2 to CH1.


Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-103
To Install the Option

DG800 provides various options (for option information, refer to "Accessories and
Options") to expand the function of the signal generator. If you need to purchase
the option, please contact RIGOL sales representative. If you have ordered this
option, you can obtain the corresponding key. Perform the following operations to
install the option.

- Acquire the license of the option
 Log in to the RIGOL official website (www.rigol.com),   click License
Activation at the bottom of the webpage to enter the "Registered product
license code" interface.
 Input  the  correct  key,  serial  number  (press  Utility  System  Info  to
acquire  the  serial  number  of  the  instrument)  and  verification  code.  Click
Generate to acquire the option license. In the license generation interface,
click Download to download and save the license file to the PC.

- In  stall the Option
You can install the option via the following 2 methods.

1) Install the option by reading the license file from the USB storage device
The content and format requirements of the option installation file are as
follows.



 The filename suffix must be ".lic".
 Contents requirement:
Line 1: option license code;
Line 2:  empty line (cannot be omitted).
Note: When inputting the option license obtained in Step 1, omit the
hyphens.

Procedures for installing the option:
 Edit the option installation file that meets the above requirements and
save it to the USB storage device.。

 Power  on  the  instrument  and  insert  the  USB  storage  device.  Press
Store to enter the store and recall interface.

 In the store and recall interface, refer to "Store and Recall" to complete
reading the option installation file according to the following step.
Select "Disk D" to select the above file, and tap the Read menu label.
## Filename Suffix
## Option  License  Code (license)
## Empty  Line

RIGOL Chapter 2 Front Panel Operations
2-104                               DG800 User's Guide
2) Install the option by sending SCPI Commands
Open the remote control window and send the following option installation
commands by referring to "Remote Control
## ".
:LICense:SET <license>
or    :LICense:INSTall <license>
## Wherein, <license>
is the option license (note that the hyphens should be
omitted).

For example, :LICense:INSTall
## 0A485CC695F5A7EC1116D598FF5F4DFFF7D3359266C6A400DA3DE9A5EE
## 6F58758BC25E0FA8CAC3D115D3267C419A3496E80629FAA2E8FA632D19
## 2E344B1285BB

If the option has been successfully installed, a prompt message will be
displayed; otherwise, a message indicating a failed installation will be
displayed.







Chapter 2 Front Panel Operations RIGOL
DG800 User's Guide 2-105
To Lock the Keyboard

You can lock any key or all the keys on the front panel by using the keyboard lock
command.

## 1. Keyboard Lock Command Introduction

:SYSTem:KLOCk <key>,{ON|OFF|0|1}    /*Locks or unlocks the specified key.*/
:SYSTem:KLOCk?  <key>            /*Queries whether the specified key is locked.*/

Wherein, <key> is used to specify the key, and its range is as follows:
## HOME|MENU|PRESET|STORE|UTILITY|HELP|
## LOCK|TRIG|
/*Function keys*/
LEFT|RIGHT|KNOB| /*Arrow keys and knob*/
OUTPUt1|OUTPUt2| /*Output control keys*/
COUNTER| /*Frequency counter key*/
ALL /*All the keys and the knob
on the front panel*/

{ON|OFF|0|1} is used to lock or unlock the keys. ON|1 denotes locking the
specified key and OFF|0 denotes unlocking the specified key.

- Lock the Specified Key by Sending the Command through Ultra Sigma
 Build the communication between the generator and the computer.
 Run Ultra Sigma and search for the instrument resource.
 Open SCPI Panel Control and send the command.
For the details, refer to "Remote Control".







Chapter 3 Remote Control  RIGOL
DG800 User's Guide 3-1
## Chapter 3 Remote Control

DG800 can communicate with PC through USB, LAN, and GPIB (with the USB to GPIB
interface converter provided by RIGOL) interface. The remote control can be
realized by using SCPI (Standard Commands for Programmable Instruments)
commands. It can be realized through the following two methods:

- User-defined programming
You can program and control the instrument by using the SCPI commands on the
basis of NI-VISA (National Instrument – Virtual Instrument Software Architecture)
library. For details about the SCPI commands and programming, refer to
## DG800
## Programming Guide
## .

- PC software
You can use the RIGOL PC software (Ultra Sigma) to send the SCPI commands to
remotely control the instrument.

This chapter will illustrate how to use the Ultra Sigma software to remotely control
the signal generator (take DG832 as an example) via the various interfaces. Please
refer to Ultra Sigma help documentation to install the software and the required
components correctly. You can download the latest version of the software from
www.rigol.com.

When the instrument is in remote control, the front panel keys (except the Power key
and Help/L  ocal key) and the touch screen are locked. At this time, you can
press Help/Local to exit the remote mode.


Contents in this chapter:

 Remote Control via USB
 Remote Control via LAN
 Remote Control via GPIB











RIGOL Chapter 3 Remote Control
3-2                               DG800 User's Guide
Remote Control via USB

- Connect the device
Use the USB cable to connect the rear-panel USB DEVICE interface of the signal
generator to the USB HOST interface of the PC.

- Search for the device resource
Start up the Ultra Sigma and the software will automatically search for the
generator resources currently connected to the PC. You can also click
to search the resources.

- View the device resource
The resources found will appear under the "RIGOL Online Resource" directory,
and the model number and USB interface information of the instrument will also
be displayed.
For example, DG832 (USB0::0x1AB1::0x0642::DG80000000001::INSTR).

- Communication test
Right-click the resource name "DG83  2
(USB0::0x1AB1::0x0642::DG80000000001::INSTR)" and select "SCPI Panel
Control" to turn on the remote command control panel, through which you can
send commands and read data. For details about the SCPI commands and
programming, refer to
DG800 Programming Guide.


Remote Control via LAN

- Connect the device
Use the USB-LAN interface converter to extend the LAN interface for the signal
generator. Use the network cable to connect the signal generator to your local
area network (LAN).

- Configure network parameters
Configure the network parameters of the signal generator according to "To Set
the LAN Parameters".

- Search for the device resource
Start up Ultra Sigma and click
. The window as shown in figure (a)
is displayed. Click
and the software searches for the instrument
resources currently connected to the LAN and the resources found are displayed
at the right section of the window as shown in figure (b). Click
to
add it.

Chapter 3 Remote Control RIGOL
DG800 User's Guide 3-3

## (a)

## (b)

- View the device resource
The resources found are shown under the "RIGOL Online Resource" directory.
For example, DG832 (TCPIP::172.16.3.82::INSTR).

- Communication test
Right-click the resource name "DG83  2 (TCPIP::172.16.3.82::INSTR)" and select
"SCPI Panel Control" to turn on the remote command control panel, through
which you can send commands and read data.













RIGOL Chapter 3 Remote Control
3-4                               DG800 User's Guide
Remote Control via GPIB

- Connect the device
Connect the generator to your computer by using a USB-GPIB interface
converter.

Note: Please make sure that a GPIB card has been installed to your PC. Connect
the USB terminal of the USB-GPIB interface converter to the USB HOST interface
on the rear panel of the generator. Connect its GPIB terminal to the GPIB card
terminal of the PC.

- Install the driver of GPIB card
Correctly install the driver of the GPIB card which has been connected to the PC.

- Set the GPIB address
Press Utility  Interface  GPIB set the GPIB address of the generator.

- Search for the device resource
Start up the Ultra Sigma and click
to open the GPIB resource
search panel as shown in figure (a). Click "Search" and the software will search
the GPIB instrument resources connected to the PC. The device resources found
will be displayed on the right side of the panel as shown in figure (b). Click "OK"
to add the resource.

## (a)


Chapter 3 Remote Control RIGOL
DG800 User's Guide 3-5

## (b)
If the resource cannot be searched automatically:
 Select the GPIB card address of the PC from the drop-down box of
"GPIB0::" and select the GPIB address set in the signal generator from the
drop-down box of "0::INSTR".
 Click "Test" to check whether the GPIB communication works normally. If
not, please follow the corresponding prompt messages to solve the
problem.

- View the device resource
## Click
to go back to the main interface of Ultra Sigma. The GPIB
resources found will appear under the "RIGOL Online Resource" directory.
For example, DG832 (GPIB0::16::INSTR).

- Communication test
Right-click the resource name "DG83  2 (GPIB0::16::INSTR)", and select "SCPI
Panel Control" to open the remote command control panel. Then you can send
commands and read data through the panel.






Chapter 4 Troubleshooting  RIGOL
DG800 User's Guide 4-1
## Chapter 4 Troubleshooting

The commonly encountered failures of DG800 and their solutions are listed below. If
the following problems occur, locate and resolve the problems according to the
following steps. If the problems still persist, contact RIGOL and provide your
instrument information to us. (For instrument information, press Utility  System
## Info.)

- When I power on the instrument, the instrument stays black and does
not display anything.
1) Check whether the power is correctly connected.
2) Check whether the power key is really pressed.
3) Restart the instrument after finishing the above inspections.
4) If the problem still persists, please contact RIGOL.

- The screen is too dark to see the contents on the screen clearly.
1) Check whether the brightness settings is too low.
2) Press Utility  DispSet to enter the display setting menu. Tap the
Brightness menu label and use the numeric keypad to adjust the
brightness of the screen to an optimal state. You can also use the arrow
keys and the knob to adjust the brightness.

- The generator is locked.
1) Check whether the generator is working in remote mode (in remote mode,
is displayed in the status bar of the user interface). Press Help/Local
to exit the remote control mode, unlock the front panel and the touch
screen.
2) Restarting the generator can also unlock the generator.

- The settings are correct but no waveform is generated.
1) Check whether the BNC cable is connected to the corresponding channel
output terminal ([CH1] or [CH2]) tightly.
2) Check whether the BNC cable has internal damage.
3) Check whether the BNC cable is connected to the test instrument tightly.
4) Check whether the backlight of Output1 or Output2 is turned on. If not,
press the corresponding key to illuminate the backlight.
5) After finishing the above inspections, press Utility  System Setting 
Power-on to select "Last" and then restart the instrument.
6) If the problem still persists, please contact RIGOL.

- The USB storage device cannot be recognized.
1) Check whether the USB storage device can work normally when connected
to other instruments or PC.
2) Make sure that the USB storage device is FAT32 format and flash type. The
generator doesn’t support hardware USB storage device.

RIGOL Chapter 4 Troubleshooting
4-2                               DG800 User's Guide
3) After restarting the instrument, insert the USB storage device again to
check whether it can work normally.
4) If the USB storage device still cannot work normally, please contact RIGOL.

- How do you set the amplitude of the waveform in dBm?
1) Select the desired channel.
2) In the channel setting interface, check whether OutputSet  HighZ is set
to "On". If yes, you cannot set the amplitude of the waveform in dBm at this
time. Select "Off" to disable the HighZ, and use the numeric keypad, the
arrow keys, and knob to set it to a proper value.
3) Select the desired waveform, tap the Ampl menu label, and then input the
desired value by using the numeric keypad. Then select the unit "dBm" from
the pop-up menu.

- Performance verification test is failed.
1) Check whether the generator is within calibration period (1 year).
2) Check whether the generator has been warmed up for at least 30 minutes
before the test.
3) Check whether the generator is under the specified temperature.
4) Check whether the test is under strong-magnetism environment.
5) Check whether the power supplies of the generator and test system have a
strong interference.
6) Check whether the performance of the test device used meets the
requirement.
7) Make sure that the test device used is within the calibration period.
8) Check whether the test devices used meets the required conditions of the
manual.
9) Check whether all the connections are tight.
10) Check whether any cable has internal damage.
11) Make sure that the operations conform to settings and processes which are
required by the performance verification manual.
12) Check whether the error calculation has faults.
13) Correctly understand the definition of "typical value" for this product: the
performance specification of this product under specified conditions.




Chapter 5 Appendix RIGOL
DG800 User's Guide 5-1
## Chapter 5 Appendix

Appendix A: Accessories and Options

## Description Order No.
## Model
DG812 (10 MHz, Dual-channel) DG812
DG822 (25MHz, Dual-channel) DG822
DG832 (35MHz, Dual-channel) DG832
DG811 (10MHz, Single-channel) DG811
DG821 (25MHz, Single-channel) DG821
DG831 (35MHz, Single-channel) DG831
## Standard
## Accessories
1 Power Cord conforming to the standard
of the destination country
## -
1 BNC Cable (only provided by
## DG832/DG831/DG822/DG821)
## CB-BNC-BNC-MM-100
## 1 Quick Guide -
## 1 Product Warranty Card -
## Option
Single-dual CH Upgrade Option (only for
## DG831/DG821/DG811)
## DG800  -DCH
Memory Depth Upgrade Option DG800-ARB8M
## Optional
## Accessories
40 dB Attenuator RA5040K
USB-GPIB Interface Converter USB-GPIB-L







RIGOL Chapter 5 Appendix
5-2                               DG800 User's Guide
## Appendix B: Warranty

RIGOL (SUZHOU) TECHNOLOGIES INC. (hereinafter referred to as RIGOL)
warrants that the product will be free from defects in materials and workmanship
within the warranty period. If a product proves defective within the warranty period,
RIGOL guarantees free replacement or repair for the defective product.

To   get repair service, please contact with your nearest RIGOL sales or   service office.

There is no other warranty, expressed or implied, except such as is expressly set
forth herein or other applicable warranty card. There is no implied warranty of
merchantability or fitness for a particular purpose. Under no circumstances shall
RIGOL be liable for any consequential, indirect, ensuing, or special damages for any
breach of warranty in any case.



Index RIGOL
DG800 User's Guide 1
## Index

## *.RAF ...................................... 2-74
## *.RSF ...................................... 2-74
## Align Phase .............................. 2-14
## AM .......................................... 2-34
## Amplitude .................................. 2-5
## Amplitude Coupling ................... 2-86
## Arb File .................................... 2-74
## ASK ......................................... 2-44
AutoIP ..................................... 2-94
## Bmp File .................................. 2-74
## Built-in Waveform ..................... 2-18
## Burst ....................................... 2-63
## Burst Delay .............................. 2-65
## Burst Period ............................. 2-66
## Carrier Waveform Suppression ...    2-37
## Center Frequency ..................... 2-59
## Channel Copy ......................... 2-102
## Clock Source ............................ 2-91
Copy files ................................. 2-77
## Coupling .................................. 2-71
## Csv File .................................... 2-74
DC Offset ................................... 2-7
## Default Gateway ....................... 2-95
## Delete ..................................... 2-78
## DHCP....................................... 2-93
## DNS ........................................ 2-95
## Duty Cycle ................................. 2-9
factory defaults......................... 2-98
FallEdge ................................... 2-12
## FM .......................................... 2-38
## Freq Dev .................................. 2-39
## Frequency .................................. 2-4
## Frequency Counter .................... 2-69
## Frequency Coupling .................. 2-85
## Frequency Span ........................ 2-59
## FSK ......................................... 2-47
## Gate Time ................................ 2-70
## Gated Burst .............................. 2-65
## Gated Polarity ........................... 2-68
GPIB address............................ 2-92
## Harmonic ................................. 2-23
## Harmonic Amplitude .................. 2-25
## Harmonic Order ........................ 2-24
## Harmonic Phase ........................ 2-25
## Harmonic Type .......................... 2-24
## High Frequency Rejection ........... 2-72
## Idle Level ................................. 2-66

## Infinite Burst ............................ 2-64
## Linear Sweep ............................ 2-56
## Log Sweep ................................ 2-57
Manual configuration ................. 2-94
## Marker Freq .............................. 2-61
## Modulation Depth ...................... 2-36
## Modulation Polarity .................... 2-46
## N Cycle .................................... 2-63
## Network Status ......................... 2-93
## Output Setting .......................... 2-81
Paste a File ............................... 2-78
## Phase Coupling ......................... 2-86
## Phase Dev ................................ 2-43
## PM ........................................... 2-41
## Print ......................................... 2-97
## PSK .......................................... 2-50
## Pulse ........................................ 2-11
## PWM ........................................ 2-53
## Return Time .............................. 2-58
RisEdge .................................... 2-12
## Seamless Interconnection .......... 2-79
Self-define the Splash Screen ..... 2-97
## Sensitivity ................................. 2-71
## Start Freq ................................. 2-59
## Start Hold ................................. 2-62
## Start Phase ................................ 2-8
## State File .................................. 2-74
## Statistical Function .................... 2-70
## Step Sweep .............................. 2-57
## Stop Freq ................................. 2-59
## Stop Hold ................................. 2-62
Subnet mask ............................. 2-95
## Sweep ...................................... 2-56
## Sweep Time .............................. 2-58
## Sweep Trigger Source ................ 2-60
## Symmetry ................................. 2-10
## Synchronous Output .................. 2-83
Trac k ........................................ 2-88
## USB HOST ................................. 1-9

RIGOL Index
2                               DG800 User's Guide
VISA Address ........................... 2-94
## Waveform Combination ............. 2-89
## Width Deviation ........................ 2-55

