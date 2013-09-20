A demonstrator of goniometric location computation by using
tange finders based scanning beacons.

Developed for illustrating the application of simple
trigonometric functions for young students.

The application is composed of :

- a hardware part, made of two scanning beacons built
around AX12 Dynamixel servos (Robotis) and infra-red
range finders. 

- a Python controlling sofware, managing servos and sensors,
running on a headless RasPi

- a PC application, featuring a real-time animated
graphical representation of the contraption and displaying
the tracked object location, computed on the basis of 
echos detected by the sensors

PC software and RasPi embedded code communicate over the network.

Note that a simple zeroconf like mechanism is builtin to relieve
from knowning the IP address of the RasPi, or using a DNS somewhere.
It is strongly inspired on the SLP protocol 
(http://en.wikipedia.org/wiki/Service_Location_Protocol).

See contraption details od POBOT robotics association web site
(http://www.pobot.org)
