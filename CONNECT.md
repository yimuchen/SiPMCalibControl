# Connecting to the Control Host device

The host device should be configured so that the connection over the ethernet
interface is all automatic. Then we should be able to connect to the host device
over a single ethernet cable from your laptop to the host device.

## Linux device

For the connection, you should set the connection type to "share to other computers",
then you should be able to connect to the host device via ssh:

```bash
ssh [user]@[hostname]
```

If for whatever reason, you need to connect via a direct IP address, you may try
the [`nmap` program](https://nmap.org/) to help you find the host device.

## Windows device

The connect should work out of the box with a ssh client (e.x. MobaXTerm). Just
set up the correct user name and host name.

## Mac device

Go into System Preferences and into the sharing tab. Under internet sharing,
Share you connection from the ethernet device to your ethernet device. In the
terminal, the command `ifconfig` should give you a new connection like
`bridge100` with an IPv4 that looks like a standard sharing IP address (like
192.168.2.1). To ssh to the raspberry pi, ssh to the IP address with the last
digit incremented by 1.

If you are running into trouble with commands that open OpenCV windows, try
enabling indirect rendering for [xquartz](https://www.xquartz.org/):

```bash
defaults write org.macosforge.xquartz.X11 enable_iglx -bool true
```

You will need to reboot (or at least restart xquartz) for the command to take
effect.
