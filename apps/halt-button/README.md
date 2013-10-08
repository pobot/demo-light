This tree contains a Python script which monitors a push button
connected to a RasPi GPIO (GPIO4 by default), used to fire the 
system halt process when depressed for at least 4 seconds.

It is accompanied by an init script responsible for automatically
activation at system startup.

Such an extension is useful for a RasPi used in headless mode, 
ie without screen and keyboard (nor ssh connection or alike), 
typically as the brain of a robot or some embedded device. It
lets you shutdown the system cleanly, and not risking to corrupt
the SD card by a sudden power off. 

Note that this is required only if data are written on the SD card while
the system is running. If the SD card is mounted in read-only, or
its write-protect tab is used, you can safely remove the power without halting
the system before.
