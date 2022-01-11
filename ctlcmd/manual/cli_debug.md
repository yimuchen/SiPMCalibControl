@defgroup cli_debug System Debugging command and Miscelleneous commands

@ingroup cli

@brief Command developed for debugging the system (hardware and software)

@details Below are a set of commands either for miscellaneous testing or
debugging the calibration system. Notice that for most analysis related work,
the "bug" would usually be a wrong setting in the physical cabling, or in the
readout settings. Be sure to check the commands related to configuring the
[readout](@ref cli2_readout) before resorting to these commands. As these
commands have fewer fail-safes and can physically damage the system is used
improperly, only use the command listed here if you both:

- Know exactly what the command you are running will do
- Have been requested to do so by a core developer.

---

@class ctlcmd.motioncmd.rungcode

@ingroup cli_debug

@details Running a raw `gcode` via a user input string. This method is provided
to provide an interface for rapid debugging `gcod`e commands directly in the CLI
interface before being formally abstracted and finalized in the `GCoder` C++
module. As there is no easy way for specifying the wait time for a certain
command, the user should be careful that the gantry may still be physically
"busy" even after the command has been reported as "completed" by the gantry;
for example, motion command will be reported as having been "completed" after
the internal target coordinates have been updated, **not** when the gantry
fully stops moving. The user must be careful to add appropriate wait signals to
avoid damaging the hardware when using this command.

If you need to run raw `gcode` for whatever reason, the list of available
`gcode` commands are available here:

https://marlinfw.org/meta/gcode/


---

@class ctlcmd.motioncmd.moveto

@ingroup cli_debug

@details

---

@class ctlcmd.motioncmd.getcoord

@ingroup cli_debug

@details

---

@class ctlcmd.motioncmd.disablestepper

@ingroup cli_debug

@details

---

@class ctlcmd.motioncmd.enablestepper

@ingroup cli_debug

@details

---

@class ctlcmd.motioncmd.sendhome

@ingroup cli_debug

@details

---

@class ctlcmd.motioncmd.movespeed

@ingroup cli_debug

@details

---

@class ctlcmd.motioncmd.timescan

@ingroup cli_debug

@details

---

@class ctlcmd.viscmd.visualshowdet

@ingroup cli_debug

@details

---

@class ctlcmd.viscmd.visualzscan

@ingroup cli_debug

@details

---

@class ctlcmd.viscmd.visualsaveframe

@ingroup cli_debug

@details

---
