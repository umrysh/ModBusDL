ModBusDL
==============

A simple program to poll PLCs for information through a TCP Connection and then dump the information either into a CSV file or a MySQL database. Requires that the PLC writes a 1 into a specified "flag" register when there is information to log. ModBusDL sets this register back to a 0 when it has grabbed the data. 

To start logging you first create a new PLC and fill in all the settings required. Once finished you will be presented with the Polling Screen, set the Polling Delay and click run. ModBusDL will now check the PLC every X seconds to see if the flag bit is set to a 1.

You can set ModBusDL to split the CSVs/Tables by day, month , or year.

You can also run ModBusDL from the command line using the following format:

python ModBusDL.py -c `<name of PLC>` -t `<time delay in seconds>`

or put a bunch of these one liners in a .bat file and have all your datalogging happen in the background.


NOTE:
* I have only tested ModBusDL on a limited number of PLCs and can not guarantee it will work out of the box for you. I have had it running for over a year polling 5 different PLCs with no issues. If you do run into an error let me know, or better yet submit a pull request :)

Some more information as well as some screen shots can be found [here](http://www.umrysh.com/modbus-dl/)


Contributing
------------

Feel free to fork and send [pull requests](http://help.github.com/fork-a-repo/).  Contributions welcome.

Credit
------------

ModBusDL would not perform without the awesome [pymodbus](http://code.google.com/p/pymodbus/) library.

License
-------

This script is open source software released under the GNU GENERAL PUBLIC LICENSE V3.