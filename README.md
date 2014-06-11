Interface utilisateur des démonstrateurs de capteurs de lumière
===============================================================

Cette application Web pour RaspberryPi fournit l'interface utilisateur des 
démonstrateurs pédagogiques utilisés pour présenter diverses
techniques de détection d'objets, de couleurs,... basés sur
des capteurs de lumière simple (LDR).

Pour plus de détails : <http://www.pobot.org>

Déploiement
-----------

Le projet inclut la chaîne de production d'un paquet Debian 
destiné à simplifier l'installation de l'application sur
une RaspberryPi tournant sous une distribution Raspbian ou 
dérivée.

La procédure est la suivante :

	$ cd dist
	$ make clean dist
	
Installation
------------

Sur la RaspberryPi il suffit d'un classique :

	$ sudo dpkg -i pobot-demo-color_1.0_all.deb
	
Dépendances
-----------
	
* Python Tornado (<http://www.tornadoweb.org/en/stable/>)
