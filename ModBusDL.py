#    Built for python 2.7

#    Copyright 2012 Dave Umrysh
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pygtk,gtk,csv,string,sys,os,re,time,struct,binascii,shutil,datetime,threading
pygtk.require('2.0')
import MySQLdb as mdb
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

path = ""
textlog = ""
TheSlash = "/"
dayofWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
monthofYear = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
convertwindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
startwindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
newplcwindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
removeplcwindow = gtk.Window(gtk.WINDOW_TOPLEVEL)


class TaskThread(threading.Thread):
	"""Thread that executes a task every N seconds"""
	def __init__(self):
		threading.Thread.__init__(self)
		self._finished = threading.Event()
		self._interval = 15.0
    
	def setInterval(self, interval):
		"""Set the number of seconds we sleep between executing our task"""
		self._interval = interval

	def setType(self, typeOfThread):
		self._typeOfThread = typeOfThread
    
	def shutdown(self, button2, button3,button,textbuffer,sw,button4,plc=None):
		"""Stop this thread"""
		if(self._typeOfThread=="csv" or self._typeOfThread=="sql"):
			button3.hide()
			button2.show()
			button.show()
			button4.show()
			textbuffer.insert_at_cursor("[Halt] Data collection stopped.\n")
			while(gtk.events_pending()):
				gtk.main_iteration()
				adj = sw.get_vadjustment()
				adj.set_value( adj.upper - adj.page_size )
		else:
			print("[Halt] Data collection stopped.")
			logout = open("%s" % (textlog), "a")
			logout.writelines("%s - %s - [Halt] Data collection stopped.\n" % (datetime.datetime.now(),plc))
			logout.close()

		self._finished.set()

	def hide(self, plc):
		globals()['errorwindow' + plc].hide()

	def run(self, button2, button3, delay, textbuffer, sw,button,button4,plc):
		globals()['counter' + plc] = 1

		if(self._typeOfThread=="csv" or self._typeOfThread=="sql"):
			button2.hide()
			button3.show()
			button.hide()
			button4.hide()
			self.setInterval(delay.get_value())
			delay = delay.get_value()
			count = int(delay*10)
			while not self._finished.isSet():
				if count == int(self._interval*10):
					self.task(textbuffer,delay,sw,button,button2,button3,button4,plc)
					count = 1
				else:
					# sleep for interval or until shutdown
					time.sleep(0.1)
					count = count + 1;
					fileOUT = open("%s%s%s%sModBusDLData4" % (path,TheSlash,plc,TheSlash), "w")
					fileOUT.writelines("%s/%s/%s" % (datetime.date.today().day,datetime.date.today().month,datetime.date.today().year))
					fileOUT.close()
					while gtk.events_pending():
						gtk.main_iteration(False)
		else:
			self.setInterval(delay)
			count = int(delay*10)
			try:
				while not self._finished.isSet():
					if count == int(self._interval*10):
						self.task(None,delay,None,None,None,None,None,plc)
						count = 1
					else:
						# sleep for interval or until shutdown
						time.sleep(0.1)
						count = count + 1;
						fileOUT = open("%s%s%s%sModBusDLData4" % (path,TheSlash,plc,TheSlash), "w")
						fileOUT.writelines("%s/%s/%s" % (datetime.date.today().day,datetime.date.today().month,datetime.date.today().year))
						fileOUT.close()
			except KeyboardInterrupt:
				print("\n");
				self.shutdown(None, None,None,None,None,None,plc)
			sys.exit(0)
    
	def task(self,textbuffer,delay,sw,button,button2,button3,button4,plc):
		"""The task done by this thread - override in subclasses"""
		if(self._typeOfThread=="csvC" or self._typeOfThread=="sqlC"):
			logout = open("%s" % (textlog), "a")

		if(self._typeOfThread=="csv" or self._typeOfThread=="csvC"):
			fileIN = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "r")
			RecordNo = int(fileIN.readline())
			fileIN.close()

		client = ModbusClient(globals()['address' + plc])

		if client.connect() == False:
			if(self._typeOfThread=="csv" or self._typeOfThread=="sql"):
				textbuffer.insert_at_cursor("[IP Error] No ModBus server at %s, re-check in 5 minutes\n" % globals()['address' + plc])
			else:
				print("[IP Error] No ModBus server at %s, re-check in 5 minutes\n" % globals()['address' + plc])
				logout.writelines("%s - %s - [IP Error] No ModBus server at %s, re-check in 5 minutes\n" % (datetime.datetime.now(),plc,globals()['address' + plc]))

			noconnect = True;
			count = 1
			while (not self._finished.isSet()) and noconnect:
				if count == 3000:
					client = ModbusClient(globals()['address' + plc])
					if client.connect() == False:
						if(self._typeOfThread=="csv" or self._typeOfThread=="sql"):
							textbuffer.insert_at_cursor("[IP Error] No ModBus server at %s, re-check in 5 minutes\n" % globals()['address' + plc])
						else:
							print("[IP Error] No ModBus server at %s, re-check in 5 minutes\n" % globals()['address' + plc])
							logout.writelines("%s - %s - [IP Error] No ModBus server at %s, re-check in 5 minutes\n" % (datetime.datetime.now(),plc,globals()['address' + plc]))
						count = 1
					else:
						noconnect = False
				else:
					# sleep for interval or until shutdown
					time.sleep(0.1)
					count = count + 1;
					fileOUT = open("%s%s%s%sModBusDLData4" % (path,TheSlash,plc,TheSlash), "w")
					fileOUT.writelines("%s/%s/%s" % (datetime.date.today().day,datetime.date.today().month,datetime.date.today().year))
					fileOUT.close()
					while gtk.events_pending():
						gtk.main_iteration(False)
		else:
			if(self._typeOfThread=="csv" or self._typeOfThread=="sql"):
				textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]Checking for new data\n")
			else:
				print("[" + str(globals()['counter' + plc]) + "]Checking for new data")
				logout.writelines("%s - %s - [%s]Checking for new data\n" %(datetime.datetime.now(),plc,str(globals()['counter' + plc])))

			rr = client.read_holding_registers(globals()['StartAddress' + plc],globals()['NumOfRegisters' + plc])
			try:
				test = rr.registers[0]
			except:
				if(self._typeOfThread=="csv" or self._typeOfThread=="sql"):
					textbuffer.insert_at_cursor("[Register Error] Attempting to read outside of the server's register bounds.\n")
				else:
					print("[Register Error] Attempting to read outside of the server's register bounds.\n")
					logout.writelines("%s - %s - [Register Error] Attempting to read outside of the server's register bounds.\n" % (datetime.datetime.now(),plc))

				self.shutdown(button2, button3,button,textbuffer,sw,button4)
				return
			if rr.registers[globals()['FlagReg' + plc]] == 1:
				if(self._typeOfThread=="csv" or self._typeOfThread=="sql"):
					textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Data Found, Enter into database\n")
				else:
					print("[" + str(globals()['counter' + plc]) + "]    Data Found, Enter into database")
					logout.writelines("%s - %s - [%s]    Data Found, Enter into database\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))

				count = 0;
				NewLineStr = []
				if(self._typeOfThread=="csv" or self._typeOfThread=="csvC"):
					NewLineStr.append(RecordNo)

				while (count < globals()['NumOfRegisters' + plc]):
					if globals()['DataTypes' + plc][count] != "0" and count != globals()['FlagReg' + plc]:
						if globals()['DataTypes' + plc][count] == "1":
							temp = bin(rr.registers[count])
							NewLineStr.append(temp.lstrip('0b'))
						elif globals()['DataTypes' + plc][count] == "2":
							NewLineStr.append("%o" % rr.registers[count])
						elif globals()['DataTypes' + plc][count] == "3":
							NewLineStr.append("%0X" % rr.registers[count])
						elif globals()['DataTypes' + plc][count] == "4":
							NewLineStr.append("%u" % rr.registers[count])
						elif globals()['DataTypes' + plc][count] == "5":
							temp = "%i" % rr.registers[count]
							if (temp > 32767):
								temp = int(temp) - 65536
							NewLineStr.append(temp)
						elif globals()['DataTypes' + plc][count] == "6":
							temp = binascii.unhexlify("%0X" % rr.registers[count])
							NewLineStr.append("%s" % temp)
						elif globals()['DataTypes' + plc][count] == "7":
							first = "%s" % ("%0X" % rr.registers[count+1])
							second = "%s" % ("%0X" % rr.registers[count])
							while (len(first) < 4):
								first = "0%s" % first
							while (len(second) < 4):
								second = "0%s" % second
							temp = "%s%s" % (first,second)
							temp = struct.unpack('!f', temp.decode('hex'))
							NewLineStr.append("%e" % temp[0])
							count = count + 1
						elif globals()['DataTypes' + plc][count] == "8":
							first = "%s" % ("%0X" % rr.registers[count+1])
							second = "%s" % ("%0X" % rr.registers[count])
							while (len(first) < 4):
								first = "0%s" % first
							while (len(second) < 4):
								second = "0%s" % second
							temp = "%s%s" % (first,second)
							temp = struct.unpack('!f', temp.decode('hex'))
							NewLineStr.append(temp[0])
							count = count + 1
						elif globals()['DataTypes' + plc][count] == "9":
							first = "%s" % ("%0X" % rr.registers[count])
							second = "%s" % ("%0X" % rr.registers[count+1])
							while (len(first) < 4):
								first = "0%s" % first
							while (len(second) < 4):
								second = "0%s" % second
							temp = "%s%s" % (first,second)
							temp = struct.unpack('!f', temp.decode('hex'))
							NewLineStr.append("%e" % temp[0])
							count = count + 1

						elif globals()['DataTypes' + plc][count] == "10":
							first = "%s" % ("%0X" % rr.registers[count])
							second = "%s" % ("%0X" % rr.registers[count+1])
							while (len(first) < 4):
								first = "0%s" % first
							while (len(second) < 4):
								second = "0%s" % second
							temp = "%s%s" % (first,second)
							temp = struct.unpack('!f', temp.decode('hex'))
							NewLineStr.append(temp[0])
							count = count + 1
						elif globals()['DataTypes' + plc][count] == "11":
							temp = bin(ReverseByteOrder(rr.registers[count]))
							NewLineStr.append(temp.lstrip('0b'))
						elif globals()['DataTypes' + plc][count] == "12":
							NewLineStr.append("%o" % ReverseByteOrder(rr.registers[count]))
						elif globals()['DataTypes' + plc][count] == "13":
							NewLineStr.append("%0X" % ReverseByteOrder(rr.registers[count]))
						elif globals()['DataTypes' + plc][count] == "14":
							NewLineStr.append("%u" % ReverseByteOrder(rr.registers[count]))
						elif globals()['DataTypes' + plc][count] == "15":
							temp = "%i" % ReverseByteOrder(rr.registers[count])
							if (temp > 32767):
								temp = int(temp) - 65536
							NewLineStr.append(temp)
						elif globals()['DataTypes' + plc][count] == "16":
							temp = binascii.unhexlify("%0X" % ReverseByteOrder(rr.registers[count]))
							NewLineStr.append("%s" % temp)
						elif globals()['DataTypes' + plc][count] == "17":
							first = "%s" % ("%0X" % ReverseByteOrder(rr.registers[count+1]))
							second = "%s" % ("%0X" % ReverseByteOrder(rr.registers[count]))
							while (len(first) < 4):
								first = "0%s" % first
							while (len(second) < 4):
								second = "0%s" % second
							temp = "%s%s" % (first,second)
							temp = struct.unpack('!f', temp.decode('hex'))
							NewLineStr.append("%e" % temp[0])
							count = count + 1

						elif globals()['DataTypes' + plc][count] == "18":
							first = "%s" % ("%0X" % ReverseByteOrder(rr.registers[count+1]))
							second = "%s" % ("%0X" % ReverseByteOrder(rr.registers[count]))
							while (len(first) < 4):
								first = "0%s" % first
							while (len(second) < 4):
								second = "0%s" % second
							temp = "%s%s" % (first,second)	
							temp = struct.unpack('!f', temp.decode('hex'))
							NewLineStr.append(temp[0])
							count = count + 1
						elif globals()['DataTypes' + plc][count] == "19":
							first = "%s" % ("%0X" % ReverseByteOrder(rr.registers[count]))
							second = "%s" % ("%0X" % ReverseByteOrder(rr.registers[count+1]))
							while (len(first) < 4):
								first = "0%s" % first
							while (len(second) < 4):
								second = "0%s" % second
							temp = "%s%s" % (first,second)
							temp = struct.unpack('!f', temp.decode('hex'))
							NewLineStr.append("%e" % temp[0])
							count = count + 1
						elif globals()['DataTypes' + plc][count] == "20":
							first = "%s" % ("%0X" % ReverseByteOrder(rr.registers[count]))
							second = "%s" % ("%0X" % ReverseByteOrder(rr.registers[count+1]))
							while (len(first) < 4):
								first = "0%s" % first
							while (len(second) < 4):
								second = "0%s" % second
							temp = "%s%s" % (first,second)
							temp = struct.unpack('!f', temp.decode('hex'))
							NewLineStr.append(temp[0])
							count = count + 1



						elif globals()['DataTypes' + plc][count] == "21":
							first = "%s" % bin(rr.registers[count+1])
							first = first.lstrip('0b')
							second = "%s" % bin(rr.registers[count])
							second = second.lstrip('0b')
							while (len(first) < 16):
								first = "0%s" % first
							while (len(second) < 16):
								second = "0%s" % second
							temp = "%s%s" % (first,second)
							NewLineStr.append(int(str(temp),2))
							count = count + 1

							#NewLineStr.append("%u" % rr.registers[count])

						elif globals()['DataTypes' + plc][count] == "22":
							first = "%s" % bin(rr.registers[count])
							first = first.lstrip('0b')
							second = "%s" % bin(rr.registers[count+1])
							second = second.lstrip('0b')
							while (len(first) < 16):
								first = "0%s" % first
							while (len(second) < 16):
								second = "0%s" % second
							temp = "%s%s" % (first,second)
							NewLineStr.append(int(str(temp),2))
							count = count + 1


						elif globals()['DataTypes' + plc][count] == "23":
							first = "%s" % bin(ReverseByteOrder(rr.registers[count+1]))
							first = first.lstrip('0b')
							second = "%s" % bin(ReverseByteOrder(rr.registers[count]))
							second = second.lstrip('0b')
							while (len(first) < 16):
								first = "0%s" % first
							while (len(second) < 16):
								second = "0%s" % second
							temp = "%s%s" % (first,second)	
							NewLineStr.append(int(str(temp),2))
							count = count + 1

						elif globals()['DataTypes' + plc][count] == "24":
							first = "%s" % bin(ReverseByteOrder(rr.registers[count]))
							first = first.lstrip('0b')
							second = "%s" % bin(ReverseByteOrder(rr.registers[count+1]))
							second = second.lstrip('0b')
							while (len(first) < 16):
								first = "0%s" % first
							while (len(second) < 16):
								second = "0%s" % second
							temp = "%s%s" % (first,second)
							NewLineStr.append(int(str(temp),2))
							count = count + 1
					count = count + 1
				if(self._typeOfThread=="sql" or self._typeOfThread=="sqlC"):
					try:
							globals()['con' + plc] = mdb.connect(host=globals()['mysqladdress' + plc], port=int(globals()['mysqlport' + plc]),user=globals()['mysqlusername' + plc], passwd=globals()['mysqlpassword' + plc], db=globals()['mysqldbname' + plc])
					except:
						if(self._typeOfThread=="sql"):
							textbuffer.insert_at_cursor("[Database Error] Could not connect to MySQL database, re-check in 5 minutes.\n")
						else:
							print("[Database Error] Could not connect to MySQL database, re-check in 5 minutes.\n")
							logout.writelines("%s - %s - [Database Error] Could not connect to MySQL database, re-check in 5 minutes.\n" % (datetime.datetime.now(),plc))
						noconnect = True;
						count = 1
						while (not self._finished.isSet()) and noconnect:
							if count == 3000:
								noconnect = False
								try:
										globals()['con' + plc] = mdb.connect(host=globals()['mysqladdress' + plc], port=int(globals()['mysqlport' + plc]),user=globals()['mysqlusername' + plc], passwd=globals()['mysqlpassword' + plc], db=globals()['mysqldbname' + plc])
								except:
									if(self._typeOfThread=="sql"):
										textbuffer.insert_at_cursor("[Database Error] Could not connect to MySQL database, re-check in 5 minutes.\n")
									else:
										print("[Database Error] Could not connect to MySQL database, re-check in 5 minutes.\n")
										logout.writelines("%s - %s - [Database Error] Could not connect to MySQL database, re-check in 5 minutes.\n" % (datetime.datetime.now(),plc))
									count = 1
									noconnect = True;
							else:
								# sleep for interval or until shutdown
								time.sleep(0.1)
								count = count + 1;
								fileOUT = open("%s%s%s%sModBusDLData4" % (path,TheSlash,plc,TheSlash), "w")
								fileOUT.writelines("%s/%s/%s" % (datetime.date.today().day,datetime.date.today().month,datetime.date.today().year))
								fileOUT.close()
								if(self._typeOfThread=="sql"):
									while gtk.events_pending():
										gtk.main_iteration(False)
					globals()['con' + plc].autocommit(True)
					globals()['cur' + plc] = globals()['con' + plc].cursor()

				###################################
				## Test for new day, month, year
				###################################
				if globals()['splitby' + plc] == "1":#Day of Week
					if globals()['dayofWeek' + plc] != datetime.date.today().weekday():
						globals()['dayofWeek' + plc] = datetime.date.today().weekday()
						# Check if we are required to drop table or delete csv
						if globals()['perdroptable' + plc]:
							if(self._typeOfThread=="csv" or self._typeOfThread=="csvC"):
								if (os.path.isfile("%s%s.csv" % (globals()['LocOfCSV' + plc], dayofWeek[globals()['dayofWeek' + plc]]))):
									os.remove("%s%s.csv" % (globals()['LocOfCSV' + plc], dayofWeek[globals()['dayofWeek' + plc]]))
									if(self._typeOfThread=="csv"):
										textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Delete CSV\n")
									else:
										print("[" + str(globals()['counter' + plc]) + "]    Delete CSV\n")
										logout.writelines("%s - %s - [%s]    Delete CSV\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))
								RecordNo = 1
								NewLineStr[0] = "1"
								fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
								fileOUT.writelines("%s" % RecordNo)
								fileOUT.close()
							elif(self._typeOfThread=="sql" or self._typeOfThread=="sqlC"):
								globals()['cur' + plc].execute("drop table if exists %s%s" % (globals()['mysqltablename' + plc], dayofWeek[globals()['dayofWeek' + plc]]))
								if(self._typeOfThread=="sql"):
									textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Drop Table\n")
								else:
									print("[" + str(globals()['counter' + plc]) + "]    Drop Table")
									logout.writelines("%s - %s - [%s]    Drop Table\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))

						if(self._typeOfThread=="csv" or self._typeOfThread=="csvC"):
							try:
								fileInT = open("%s%s.csv" % (globals()['LocOfCSV' + plc], dayofWeek[globals()['dayofWeek' + plc]]))
								lines = [line for line in fileInT]
								fileInT.close()
								lastrow = string.split(lines[len(lines)-1].replace('\n', '').replace('\r', ''),',')
								if lastrow[0] == "RecordNo":
									RecordNo = 1
									NewLineStr[0] = 1
								else:
									RecordNo = int(lastrow[0])+1
									NewLineStr[0] = int(lastrow[0])+1
								fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
								fileOUT.writelines("%s" % RecordNo)
								fileOUT.close()
							except IOError as e:
								try:
									f = csv.writer(open("%s%s.csv" % (globals()['LocOfCSV' + plc], dayofWeek[globals()['dayofWeek' + plc]]), 'wb'), delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
								except IOError as e:
									if(self._typeOfThread=="csv"):
										textbuffer.insert_at_cursor("Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.\n")
									else:
										print("Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.\n")
										logout.writelines("%s - %s - Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.\n" % (datetime.datetime.now(),plc))
									return
								if(self._typeOfThread=="csv"):
									textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Create CSV\n")
								else:
									print("[" + str(globals()['counter' + plc]) + "]    Create CSV\n")		
									logout.writelines("%s - %s - [%s]    Create CSV\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))		
								f.writerow(globals()['headings' + plc])
								fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
								fileOUT.writelines("1")
								fileOUT.close()
								RecordNo = 1
						elif(self._typeOfThread=="sql" or self._typeOfThread=="sqlC"):
							#Check if table exists, then check if we are allowed to make it
							globals()['cur' + plc].execute('show tables like "%s%s"' % (globals()['mysqltablename' + plc] , dayofWeek[globals()['dayofWeek' + plc]]))
				    		if not globals()['cur' + plc].fetchall():
							# Table name doesn't exist
							if globals()['createtable' + plc]:
								# Create table
								mysqlstring = getmysqlstring(plc)
								
								globals()['cur' + plc].execute("create table %s%s(%s)" % (globals()['mysqltablename' + plc] , dayofWeek[globals()['dayofWeek' + plc]],mysqlstring))
								if(self._typeOfThread=="sql"):
									textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Create Table\n")
								else:
									print("[" + str(globals()['counter' + plc]) + "]    Create Table")
									logout.writelines("%s - %s - [%s]    Create Table\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))
							else:
								#Throw Error
								if(self._typeOfThread=="sql"):
									textbuffer.insert_at_cursor("Could not find a table \"%s%s\" in the MySQL database.\n" % (globals()['mysqltablename' + plc] , dayofWeek[globals()['dayofWeek' + plc]]))
								else:
									print("Could not find a table \"%s%s\" in the MySQL database.\n" % (globals()['mysqltablename' + plc] , dayofWeek[globals()['dayofWeek' + plc]]))
									logout.writelines("%s - %s - Could not find a table \"%s%s\" in the MySQL database.\n" % (datetime.datetime.now(),plc,globals()['mysqltablename' + plc] , dayofWeek[globals()['dayofWeek' + plc]]))
								self.shutdown(button2, button3,button,textbuffer,sw,button4)
								return

					if(self._typeOfThread=="csv" or self._typeOfThread=="csvC"):		
						f = csv.writer(open("%s%s.csv" % (globals()['LocOfCSV' + plc], dayofWeek[globals()['dayofWeek' + plc]]), 'ab'), delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
					elif(self._typeOfThread=="sql" or self._typeOfThread=="sqlC"):
						try:
							globals()['cur' + plc].execute('INSERT INTO %s%s VALUES(NULL,"%s")' % (globals()['mysqltablename' + plc] , dayofWeek[globals()['dayofWeek' + plc]],'","'.join(map(str, NewLineStr))))
						except :
							if(self._typeOfThread=="sql"):
								textbuffer.insert_at_cursor("[Database Error] Could not insert into MySQL database.\n")
							else:
								print("[Database Error] Could not insert into MySQL database.\n")
								logout.writelines("%s - %s - [Database Error] Could not insert into MySQL database.\n" % (datetime.datetime.now(),plc))
							self.shutdown(button2, button3,button,textbuffer,sw,button4)
							return

				elif globals()['splitby' + plc] == "2": # Month
					if globals()['month' + plc] != datetime.date.today().month:
						globals()['month' + plc] = datetime.date.today().month
						# Check if we are required to delete csv or drop table
						if globals()['perdroptable' + plc]:
							if(self._typeOfThread=="csv" or self._typeOfThread=="csvC"):
								if (os.path.isfile("%s%s.csv" % (globals()['LocOfCSV' + plc], monthofYear[globals()['month' + plc]]))):
									os.remove("%s%s.csv" % (globals()['LocOfCSV' + plc], monthofYear[globals()['month' + plc]]))
									if(self._typeOfThread=="csv"):
										textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Delete CSV\n")
									else:
										print("[" + str(globals()['counter' + plc]) + "]    Delete CSV\n")
										logout.writelines("%s - %s - [%s]    Delete CSV\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))
								RecordNo = 1
								NewLineStr[0] = "1"
								fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
								fileOUT.writelines("%s" % RecordNo)
								fileOUT.close()
							elif(self._typeOfThread=="sql" or self._typeOfThread=="sqlC"):
								globals()['cur' + plc].execute("drop table if exists %s%s" % (globals()['mysqltablename' + plc], monthofYear[globals()['month' + plc]]))
								if(self._typeOfThread=="sql"):
									textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Drop Table\n")
								else:
									print("[" + str(globals()['counter' + plc]) + "]    Drop Table")
									logout.writelines("%s - %s - [%s]    Drop Table\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))

						if(self._typeOfThread=="csv" or self._typeOfThread=="csvC"):
							try:
								fileInT = open("%s%s.csv" % (globals()['LocOfCSV' + plc], monthofYear[globals()['month' + plc]]))
								lines = [line for line in fileInT]
								fileInT.close()
								lastrow = string.split(lines[len(lines)-1].replace('\n', '').replace('\r', ''),',')
								if lastrow[0] == "RecordNo":
									RecordNo = 1
									NewLineStr[0] = 1
								else:
									RecordNo = int(lastrow[0])+1
									NewLineStr[0] = int(lastrow[0])+1
								fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
								fileOUT.writelines("%s" % RecordNo)
								fileOUT.close()
							except IOError as e:
								try:
									f = csv.writer(open("%s%s.csv" % (globals()['LocOfCSV' + plc], monthofYear[globals()['month' + plc]]), 'wb'), delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
								except IOError as e:
									if(self._typeOfThread=="csv"):
										textbuffer.insert_at_cursor("Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.\n")
									else:
										print("Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.\n")
										logout.writelines("%s - %s - Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.\n" % (datetime.datetime.now(),plc))
									return
								if(self._typeOfThread=="csv"):
									textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Create CSV\n")	
								else:
									print("[" + str(globals()['counter' + plc]) + "]    Create CSV\n")
									logout.writelines("%s - %s - [%s]    Create CSV\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))	

								f.writerow(globals()['headings' + plc])
								fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
								fileOUT.writelines("1")
								fileOUT.close()
								RecordNo = 1
						elif(self._typeOfThread=="sql" or self._typeOfThread=="sqlC"):
							#Check if table exists, then check if we are allowed to make it
							globals()['cur' + plc].execute('show tables like "%s%s"' % (globals()['mysqltablename' + plc] , monthofYear[globals()['month' + plc]]))
							if not globals()['cur' + plc].fetchall():
								# Table name doesn't exist
								if globals()['createtable' + plc]:
									# Create table
									mysqlstring = getmysqlstring(plc)
									
									globals()['cur' + plc].execute("create table %s%s(%s)" % (globals()['mysqltablename' + plc] , monthofYear[globals()['month' + plc]],mysqlstring))
									if(self._typeOfThread=="sql"):
										textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Create Table\n")
									else:
										print("[" + str(globals()['counter' + plc]) + "]    Create Table")
										logout.writelines("%s - %s - [%s]    Create Table\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))
							else:
								#Throw Error
								if(self._typeOfThread=="sql"):
									textbuffer.insert_at_cursor("Could not find a table \"%s%s\" in the MySQL database.\n" % (globals()['mysqltablename' + plc] , monthofYear[globals()['month' + plc]]))
								else:
									print("Could not find a table \"%s%s\" in the MySQL database.\n" % (globals()['mysqltablename' + plc] , monthofYear[globals()['month' + plc]]))
									logout.writelines("%s - %s - Could not find a table \"%s%s\" in the MySQL database.\n" % (datetime.datetime.now(),plc,globals()['mysqltablename' + plc] , monthofYear[globals()['month' + plc]]))
								self.shutdown(button2, button3,button,textbuffer,sw,button4)
								return
					if(self._typeOfThread=="csv" or self._typeOfThread=="csvC"):
						f = csv.writer(open("%s%s.csv" % (globals()['LocOfCSV' + plc], monthofYear[globals()['month' + plc]]), 'ab'), delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
					elif(self._typeOfThread=="sql" or self._typeOfThread=="sqlC"):
						try:
							globals()['cur' + plc].execute('INSERT INTO %s%s VALUES(NULL,"%s")' % (globals()['mysqltablename' + plc] , monthofYear[globals()['month' + plc]],'","'.join(map(str, NewLineStr))))
						except :
							if(self._typeOfThread=="sql"):
								textbuffer.insert_at_cursor("[Database Error] Could not insert into MySQL database.\n")
							else:
								print("[Database Error] Could not insert into MySQL database.\n")
								logout.writelines("%s - %s - [Database Error] Could not insert into MySQL database.\n" % (datetime.datetime.now(),plc))
							self.shutdown(button2, button3,button,textbuffer,sw,button4)
							return


				elif globals()['splitby' + plc] == "3": # Year
					if globals()['year' + plc] != datetime.date.today().year:
						globals()['year' + plc] = datetime.date.today().year
						# Check if we are required to delete csv
						if globals()['perdroptable' + plc]:
							if(self._typeOfThread=="csv" or self._typeOfThread=="csvC"):
								if (os.path.isfile("%s%s.csv" % (globals()['LocOfCSV' + plc], str(globals()['year' + plc])))):
									os.remove("%s%s.csv" % (globals()['LocOfCSV' + plc], str(globals()['year' + plc])))
									if(self._typeOfThread=="csv"):
										textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Delete CSV\n")
									else:
										print("[" + str(globals()['counter' + plc]) + "]    Delete CSV\n")
										logout.writelines("%s - %s - [%s]    Delete CSV\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))
								RecordNo = 1
								NewLineStr[0] = "1"
								fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
								fileOUT.writelines("%s" % RecordNo)
								fileOUT.close()
							elif(self._typeOfThread=="sql" or self._typeOfThread=="sqlC"):
								globals()['cur' + plc].execute("drop table if exists %s%s" % (globals()['mysqltablename' + plc] , str(globals()['year' + plc])))
								if(self._typeOfThread=="sql"):
									textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Drop Table\n")
								else:
									print("[" + str(globals()['counter' + plc]) + "]    Drop Table")	
									logout.writelines("%s - %s - [%s]    Drop Table\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))

						if(self._typeOfThread=="csv" or self._typeOfThread=="csvC"):
							try:
								fileInT = open("%s%s.csv" % (globals()['LocOfCSV' + plc], str(globals()['year' + plc])))
								lines = [line for line in fileInT]
								fileInT.close()
								lastrow = string.split(lines[len(lines)-1].replace('\n', '').replace('\r', ''),',')
								if lastrow[0] == "RecordNo":
									RecordNo = 1
									NewLineStr[0] = 1
								else:
									RecordNo = int(lastrow[0])+1
									NewLineStr[0] = int(lastrow[0])+1
								fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
								fileOUT.writelines("%s" % RecordNo)
								fileOUT.close()
							except IOError as e:
								try:
									f = csv.writer(open("%s%s.csv" % (globals()['LocOfCSV' + plc], str(globals()['year' + plc])), 'wb'), delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
								except IOError as e:
									if(self._typeOfThread=="csv"):
										textbuffer.insert_at_cursor("Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.\n")
									else:
										print("Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.\n")
										logout.writelines("%s - %s - Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.\n" % (datetime.datetime.now(),plc))
									return
								if(self._typeOfThread=="csv"):
									textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Create CSV\n")
								else:
									print("[" + str(globals()['counter' + plc]) + "]    Create CSV\n")
									logout.writelines("%s - %s - [%s]    Create CSV\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))	
								f.writerow(globals()['headings' + plc])
								fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
								fileOUT.writelines("1")
								fileOUT.close()
								RecordNo = 1
						elif(self._typeOfThread=="sql" or self._typeOfThread=="sqlC"):
							#Check if table exists, then check if we are allowed to make it
							globals()['cur' + plc].execute('show tables like "%s%s"' % (globals()['mysqltablename' + plc] , str(globals()['year' + plc])))
				    		if not globals()['cur' + plc].fetchall():
							# Table name doesn't exist
							if globals()['createtable' + plc]:
								# Create table
								mysqlstring = getmysqlstring(plc)
								
								globals()['cur' + plc].execute("create table %s%s(%s)" % (globals()['mysqltablename' + plc] , str(globals()['year' + plc]),mysqlstring))
								if(self._typeOfThread=="sql"):
									textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    Create Table\n")
								else:
									print("[" + str(globals()['counter' + plc]) + "]    Create Table")
									logout.writelines("%s - %s - [%s]    Create Table\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))
							else:
								#Throw Error
								if(self._typeOfThread=="sql"):
									textbuffer.insert_at_cursor("Could not find a table \"%s%s\" in the MySQL database.\n" % (globals()['mysqltablename' + plc] , str(globals()['year' + plc])))
								else:
									print("Could not find a table \"%s%s\" in the MySQL database.\n" % (globals()['mysqltablename' + plc] , str(globals()['year' + plc])))
									logout.writelines("%s - %s - Could not find a table \"%s%s\" in the MySQL database.\n" % (datetime.datetime.now(),plc,globals()['mysqltablename' + plc] , str(globals()['year' + plc])))
								self.shutdown(button2, button3,button,textbuffer,sw,button4)
								return

					if(self._typeOfThread=="csv" or self._typeOfThread=="csvC"):
						f = csv.writer(open("%s%s.csv" % (globals()['LocOfCSV' + plc], str(globals()['year' + plc])), 'ab'), delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
					elif(self._typeOfThread=="sql" or self._typeOfThread=="sqlC"):
						try:
							globals()['cur' + plc].execute('INSERT INTO %s%s VALUES(NULL,"%s")' % (globals()['mysqltablename' + plc] , str(globals()['year' + plc]),'","'.join(map(str, NewLineStr))))
						except :
							if(self._typeOfThread=="sql"):
								textbuffer.insert_at_cursor("[Database Error] Could not insert into MySQL database.\n")
							else:
								print("[Database Error] Could not insert into MySQL database.\n")
								logout.writelines("%s - %s - [Database Error] Could not insert into MySQL database.\n" % (datetime.datetime.now(),plc))
							self.shutdown(button2, button3,button,textbuffer,sw,button4)
							return


				else:
					if(self._typeOfThread=="csv" or self._typeOfThread=="csvC"):
						f = csv.writer(open("%s.csv" % globals()['LocOfCSV' + plc], 'ab'), delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
						f.writerow(NewLineStr)
						RecordNo = RecordNo +1
						fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
						fileOUT.writelines("%s" % RecordNo)
						fileOUT.close()
					elif(self._typeOfThread=="sql" or self._typeOfThread=="sqlC"):
						try:
							globals()['cur' + plc].execute('INSERT INTO %s VALUES(NULL,"%s")' % (globals()['mysqltablename' + plc],'","'.join(map(str, NewLineStr))))
						except :
							if(self._typeOfThread=="sql"):
								textbuffer.insert_at_cursor("[Database Error] Could not insert into MySQL database.\n")
							else:
								print("[Database Error] Could not insert into MySQL database.\n")
								logout.writelines("%s - %s - [Database Error] Could not insert into MySQL database.\n" % (datetime.datetime.now(),plc))
							self.shutdown(button2, button3,button,textbuffer,sw,button4)
							return
						globals()['con' + plc].close()
				###################################
				if(self._typeOfThread=="csv" or self._typeOfThread=="sql"):
					textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    ")
					for i in NewLineStr:
						textbuffer.insert_at_cursor('"%s" ' % i)
					textbuffer.insert_at_cursor("\n")
				else:
					tempstring = "[" + str(globals()['counter' + plc]) + "]    "
					for i in NewLineStr:
						tempstring = tempstring + '"%s" ' % i
					print(tempstring)
					logout.writelines("%s - %s - %s\n" % (datetime.datetime.now(),plc,tempstring))


				rq = client.write_register(globals()['StartAddress' + plc]+globals()['FlagReg' + plc], 0)
				if (rq.function_code >= 0x80):
					if(self._typeOfThread=="csv" or self._typeOfThread=="sql"):
						textbuffer.insert_at_cursor("[Register Error] Cannot write to 'new data available' register.\n")
					else:
						print("[Register Error] Cannot write to 'new data available' register.\n")
						logout.writelines("%s - %s - [Register Error] Cannot write to 'new data available' register.\n" % (datetime.datetime.now(),plc))
					self.shutdown(button2, button3,button,textbuffer,sw,button4)
					return
			else:
				if(self._typeOfThread=="csv" or self._typeOfThread=="sql"):
					textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]    No New Data\n")
				else:
					print("[" + str(globals()['counter' + plc]) + "]    No New Data")
					logout.writelines("%s - %s - [%s]    No New Data\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc])))
			client.close()		
			#Wait the delay
			if(self._typeOfThread=="csv" or self._typeOfThread=="sql"):
				textbuffer.insert_at_cursor("[" + str(globals()['counter' + plc]) + "]Sleep for %s seconds\n" % delay)
				while(gtk.events_pending()):
					gtk.main_iteration()
					adj = sw.get_vadjustment()
					adj.set_value( adj.upper - adj.page_size )
			else:
				print("[" + str(globals()['counter' + plc]) + "]Sleep for %s seconds\n" % delay)
				logout.writelines("%s - %s - [%s]Sleep for %s seconds\n" % (datetime.datetime.now(),plc,str(globals()['counter' + plc]),delay))
				logout.close()
			globals()['counter' + plc] = globals()['counter' + plc] + 1


def getmysqlstring(plc):
	counter = 1;
	mysqlstring = "RecordNo INT PRIMARY KEY AUTO_INCREMENT"
	for count in range(0,globals()['NumOfRegisters' + plc]):
		if globals()['DataTypes' + plc][count] != "0" and globals()['DataTypes' + plc][count-1] != "7" and globals()['DataTypes' + plc][count-1] != "8" and globals()['DataTypes' + plc][count-1] != "9" and globals()['DataTypes' + plc][count-1] != "10" and globals()['DataTypes' + plc][count-1] != "17" and globals()['DataTypes' + plc][count-1] != "18" and globals()['DataTypes' + plc][count-1] != "19" and globals()['DataTypes' + plc][count-1] != "20" and globals()['DataTypes' + plc][count-1] != "21" and globals()['DataTypes' + plc][count-1] != "22" and globals()['DataTypes' + plc][count-1] != "23" and globals()['DataTypes' + plc][count-1] != "24" and count != globals()['FlagReg' + plc]:

			# what type of data are we storing?
			if globals()['DataTypes' + plc][count] == "1" or globals()['DataTypes' + plc][count] == "11":
				mysqlstring = mysqlstring + ",%s varchar(16)" %  ''.join(e for e in globals()['headings' + plc][counter].replace(" ", "_") if e.isalnum())
			elif globals()['DataTypes' + plc][count] == "2" or globals()['DataTypes' + plc][count] == "12":
				mysqlstring = mysqlstring + ",%s varchar(16)" % ''.join(e for e in globals()['headings' + plc][counter].replace(" ", "_") if e.isalnum())
			elif globals()['DataTypes' + plc][count] == "3" or globals()['DataTypes' + plc][count] == "13":
				mysqlstring = mysqlstring + ",%s varchar(16)" % ''.join(e for e in globals()['headings' + plc][counter].replace(" ", "_") if e.isalnum())
			elif globals()['DataTypes' + plc][count] == "4" or globals()['DataTypes' + plc][count] == "14":
				mysqlstring = mysqlstring + ",%s decimal" % ''.join(e for e in globals()['headings' + plc][counter].replace(" ", "_") if e.isalnum())
			elif globals()['DataTypes' + plc][count] == "5" or globals()['DataTypes' + plc][count] == "15":
				mysqlstring = mysqlstring + ",%s decimal" % ''.join(e for e in globals()['headings' + plc][counter].replace(" ", "_") if e.isalnum())
			elif globals()['DataTypes' + plc][count] == "6" or globals()['DataTypes' + plc][count] == "16":
				mysqlstring = mysqlstring + ",%s varchar(2)" % ''.join(e for e in globals()['headings' + plc][counter].replace(" ", "_") if e.isalnum())
			elif globals()['DataTypes' + plc][count] == "7" or globals()['DataTypes' + plc][count] == "17":
				mysqlstring = mysqlstring + ",%s real" % ''.join(e for e in globals()['headings' + plc][counter].replace(" ", "_") if e.isalnum())
			elif globals()['DataTypes' + plc][count] == "8" or globals()['DataTypes' + plc][count] == "18":
				mysqlstring = mysqlstring + ",%s real" % ''.join(e for e in globals()['headings' + plc][counter].replace(" ", "_") if e.isalnum())
			elif globals()['DataTypes' + plc][count] == "9" or globals()['DataTypes' + plc][count] == "19":
				mysqlstring = mysqlstring + ",%s real" % ''.join(e for e in globals()['headings' + plc][counter].replace(" ", "_") if e.isalnum())
			elif globals()['DataTypes' + plc][count] == "10" or globals()['DataTypes' + plc][count] == "20":
				mysqlstring = mysqlstring + ",%s real" % ''.join(e for e in globals()['headings' + plc][counter].replace(" ", "_") if e.isalnum())
			elif globals()['DataTypes' + plc][count] == "21" or globals()['DataTypes' + plc][count] == "22" or globals()['DataTypes' + plc][count] == "23" or globals()['DataTypes' + plc][count] == "24":
				mysqlstring = mysqlstring + ",%s decimal" % ''.join(e for e in globals()['headings' + plc][counter].replace(" ", "_") if e.isalnum())
			counter=counter +1;

	return mysqlstring;

def throwError(usingGTK,message,plc):
	if(usingGTK):
		globals()['window3' + plc] = gtk.Window(gtk.WINDOW_TOPLEVEL)
		globals()['window3' + plc].connect("destroy", lambda w: gtk.main_quit())
		globals()['window3' + plc].set_title("ModBus DL")
		globals()['window3' + plc].set_default_size(150, 150)
		globals()['window3' + plc].set_property("allow-grow", 0)
		globals()['window3' + plc].set_position(gtk.WIN_POS_CENTER)

		main_vbox = gtk.VBox(False, 5)
		main_vbox.set_border_width(10)
		globals()['window3' + plc].add(main_vbox)

		mainlabel = gtk.Label("%s\n" % message)
		mainlabel.set_alignment(0.5, 0.5)
		mainlabel.set_line_wrap(True)
		main_vbox.pack_start(mainlabel, True, True, 0)

		button = gtk.Button("Close")
		button.connect("clicked", lambda w: gtk.main_quit())
		main_vbox.pack_start(button, False, True, 5)

		globals()['window3' + plc].show_all()
	else:
		print ("%s\n" % message)
		logout.writelines("%s - %s\n" % (datetime.datetime.now(),message))

def ReverseByteOrder(data):
    """
    Method to reverse the byte order of a given unsigned data value
    Input:
        data:   data value whose byte order needs to be swap
                data can only be as big as 4 bytes
    Output:
        revD: data value with its byte order reversed
    """
    s = "Error: Only 'unsigned' data of type 'int' or 'long' is allowed"
    if not ((type(data) == int)or(type(data) == long)):
        s1 = "Error: Invalid data type: %s" % type(data)
        print(''.join([s,'\n',s1]))
        return data
    if(data < 0):
        s2 = "Error: Data is signed. Value is less than 0"
        print(''.join([s,'\n',s2]))
        return data

    seq = ["0x"]

    while(data > 0):
        d = data & 0xFF     # extract the least significant(LS) byte
        seq.append('%02x'%d)# convert to appropriate string, append to sequence
        data >>= 8          # push next higher byte to LS position

    revD = int(''.join(seq),16)

    return revD
def is_valid_ipv4(ip):
    """Validates IPv4 addresses.
    """
    pattern = re.compile(r"""
        ^
        (?:
          # Dotted variants:
          (?:
            # Decimal 1-255 (no leading 0's)
            [3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}
          |
            0x0*[0-9a-f]{1,2}  # Hexadecimal 0x0 - 0xFF (possible leading 0's)
          |
            0+[1-3]?[0-7]{0,2} # Octal 0 - 0377 (possible leading 0's)
          )
          (?:                  # Repeat 0-3 times, separated by a dot
            \.
            (?:
              [3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}
            |
              0x0*[0-9a-f]{1,2}
            |
              0+[1-3]?[0-7]{0,2}
            )
          ){0,3}
        |
          0x0*[0-9a-f]{1,8}    # Hexadecimal notation, 0x0 - 0xffffffff
        |
          0+[0-3]?[0-7]{0,10}  # Octal notation, 0 - 037777777777
        |
          # Decimal notation, 1-4294967295:
          429496729[0-5]|42949672[0-8]\d|4294967[01]\d\d|429496[0-6]\d{3}|
          42949[0-5]\d{4}|4294[0-8]\d{5}|429[0-3]\d{6}|42[0-8]\d{7}|
          4[01]\d{8}|[1-3]\d{0,9}|[4-9]\d{0,8}
        )
        $
    """, re.VERBOSE | re.IGNORECASE)
    return pattern.match(ip) is not None
def is_valid_ipv6(ip):
    """Validates IPv6 addresses.
    """
    pattern = re.compile(r"""
        ^
        \s*                         # Leading whitespace
        (?!.*::.*::)                # Only a single whildcard allowed
        (?:(?!:)|:(?=:))            # Colon iff it would be part of a wildcard
        (?:                         # Repeat 6 times:
            [0-9a-f]{0,4}           #   A group of at most four hexadecimal digits
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
        ){6}                        #
        (?:                         # Either
            [0-9a-f]{0,4}           #   Another group
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
            [0-9a-f]{0,4}           #   Last group
            (?: (?<=::)             #   Colon iff preceeded by exacly one colon
             |  (?<!:)              #
             |  (?<=:) (?<!::) :    #
             )                      # OR
         |                          #   A v4 address with NO leading zeros 
            (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            (?: \.
                (?:25[threading0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            ){3}
        )
        \s*                         # Trailing whitespace
        $
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL)
    return pattern.match(ip) is not None
def is_valid_ip(ip):
    """Validates IP addresses.
    """
    return is_valid_ipv4(ip) or is_valid_ipv6(ip)

def make_menu_item(named, callback, data1, data2,plc):
    item = gtk.MenuItem(named)
    item.connect("activate", callback, data1, data2,plc)
    item.show()
    return item

def make_menu_item_database(named, callback, data1, data2, data3, data4, data5, data6,data7,plc):
    item = gtk.MenuItem(named)
    item.connect("activate", callback, data1, data2, data3, data4, data5, data6,data7,plc)
    item.show()
    return item



def startpoll(widget, button2, button3, spinner, textbuffer, sw,button,button4,plc):
	globals()['polling' + plc] = TaskThread()
	globals()['polling' + plc].setType("csv")
	globals()['polling' + plc].run(button2, button3, spinner, textbuffer, sw,button,button4,plc)

def stoppoll(widget, button2, button3,button,textbuffer,sw,button4,plc):
	globals()['polling' + plc].shutdown(button2, button3,button,textbuffer,sw,button4)

def startpollMySQL(widget, button2, button3, spinner, textbuffer, sw,button,button4,plc):
	globals()['polling' + plc] = TaskThread()
	globals()['polling' + plc].setType("sql")
	globals()['polling' + plc].run( button2, button3, spinner, textbuffer, sw,button,button4,plc)

def stoppollMySQL(widget, button2, button3,button,textbuffer,sw,button4,plc):
	globals()['polling' + plc].shutdown( button2, button3,button,textbuffer,sw,button4)

def startpollC(widget, button2, button3, spinner, textbuffer, sw,button,button4,plc):
	globals()['polling' + plc] = TaskThread()
	globals()['polling' + plc].setType("csvC")
	globals()['polling' + plc].run( button2, button3, spinner, textbuffer, sw,button,button4,plc)

def startpollMySQLC(widget, button2, button3, spinner, textbuffer, sw,button,button4,plc):
	globals()['polling' + plc] = TaskThread()
	globals()['polling' + plc].setType("sqlC")
	globals()['polling' + plc].run( button2, button3, spinner, textbuffer, sw,button,button4,plc)

########################################################
class MainProg:
    def restart(self, widget, plc):
		globals()['window3' + plc].hide()
		StartScript(plc)
		return
    def __init__(self,plc,usingGTK,delay=None):
		#global proc
		#Set current dates
		self.usingGTK = usingGTK
		globals()['day' + plc] = datetime.date.today().day
		globals()['dayofWeek' + plc] = datetime.date.today().weekday()
		globals()['month' + plc] = datetime.date.today().month
		globals()['year' + plc] = datetime.date.today().year
		if(self.usingGTK): 
			logout = open("%s" % (textlog), "a")
		#Read dates
		# If Data4 does not exist we set it to yesterday
		if not os.path.isfile("%s%s%s%sModBusDLData4" % (path,TheSlash,plc,TheSlash)):
			self.fileOUT = open("%s%s%s%sModBusDLData4" % (path,TheSlash,plc,TheSlash), "w")
			self.fileOUT.writelines("%s/%s/%s" % ((datetime.date.today() - datetime.timedelta( days = 1 )).day,datetime.date.today().month,datetime.date.today().year))
			self.fileOUT.close()
		self.fileIN = open("%s%s%s%sModBusDLData4" % (path,TheSlash,plc,TheSlash), "r")
		globals()['lastdate' + plc] = string.split(self.fileIN.readline().replace('\n', '').replace('\r', ''),'/')
		self.fileIN.close()
		if len(globals()['lastdate' + plc]) < 3:
			# There was an error during shutdown, set to today
			self.fileOUT = open("%s%s%s%sModBusDLData4" % (path,TheSlash,plc,TheSlash), "w")
			self.fileOUT.writelines("%s/%s/%s" % (datetime.date.today().day,datetime.date.today().month,datetime.date.today().year))
			self.fileOUT.close()
		###load in variables and update globals###
		self.fileIN = open("%s%s%s%sModBusDLData2" % (path,TheSlash,plc,TheSlash), "r")
		self.new_strings=string.split(self.fileIN.readline(),'|')
		globals()['StartAddress' + plc] = int(self.new_strings[0])
		globals()['NumOfRegisters' + plc] = int(self.new_strings[1])
		globals()['databasetouse' + plc] = self.new_strings[2]
		globals()['address' + plc] = self.new_strings[3]
		if globals()['databasetouse' + plc] == "1":
			globals()['LocOfCSV' + plc] = self.new_strings[4]
			globals()['CSVName' + plc] = self.new_strings[5]
			if self.new_strings[6] == "1":
				globals()['perdroptable' + plc] = True
			else:
				globals()['perdroptable' + plc] = False
			globals()['splitby' + plc] = self.new_strings[7]
			globals()['FlagReg' + plc] = int(self.new_strings[8])
			globals()['DataTypes' + plc] = string.split(self.new_strings[9].replace('\n', '').replace('\r', ''),',')
		else:
			globals()['mysqladdress' + plc] = self.new_strings[4]
			globals()['mysqlport' + plc] = self.new_strings[5]
			globals()['mysqlusername' + plc] = self.new_strings[6]
			globals()['mysqlpassword' + plc] = self.new_strings[7]
			globals()['mysqldbname' + plc] = self.new_strings[8]
			####
			if self.new_strings[9] == "1":
				globals()['perdroptable' + plc] = True
			else:
				globals()['perdroptable' + plc] = False
			globals()['splitby' + plc] = self.new_strings[10]
			globals()['mysqltablename' + plc] = ''.join(e for e in self.new_strings[11].replace(" ", "_") if e.isalnum())
			if self.new_strings[12] == "1":
				globals()['createtable' + plc] = True
			else:
				globals()['createtable' + plc] = False
			####
			globals()['FlagReg' + plc] = int(self.new_strings[13])
			globals()['DataTypes' + plc] = string.split(self.new_strings[14].replace('\n', '').replace('\r', ''),',')
		if(self.usingGTK): 
			self.label = gtk.Label("Polling Delay in Seconds :  ")
			self.label.get_settings().set_string_property('gtk-font-name', 'serif 10','');
		self.fileIN = open("%s%s%s%sModBusDLData1" % (path,TheSlash,plc,TheSlash), "r")
		self.tempstring = self.fileIN.readline()
		globals()['headings' + plc] = string.split(self.tempstring.replace('\n', '').replace('\r', ''),',')
		# Open Database or CSV
		if globals()['databasetouse' + plc] == "1":
			###################################
			## Test for new day, month, year
			###################################
			if globals()['splitby' + plc] == "1":#Day of Week
				if globals()['dayofWeek' + plc] != datetime.date.today().weekday():
					globals()['dayofWeek' + plc] = datetime.date.today().weekday()
					# Check if we are required to delete csv
					if (str(globals()['day' + plc])!=globals()['lastdate' + plc][0] or  str(globals()['month' + plc])!=globals()['lastdate' + plc][1] or str(globals()['year' + plc])!=globals()['lastdate' + plc][2])and globals()['perdroptable' + plc]:
						if (os.path.isfile("%s%s.csv" % (globals()['LocOfCSV' + plc], dayofWeek[globals()['dayofWeek' + plc]]))):
							os.remove("%s%s.csv" % (globals()['LocOfCSV' + plc], dayofWeek[globals()['dayofWeek' + plc]]))
							RecordNo = 1
							fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
							fileOUT.writelines("%s" % RecordNo)
							fileOUT.close()
				try:
		   			fileInT = open("%s%s.csv" % (globals()['LocOfCSV' + plc], dayofWeek[globals()['dayofWeek' + plc]]))
					lines = [line for line in fileInT]
					fileInT.close()
					lastrow = string.split(lines[len(lines)-1].replace('\n', '').replace('\r', ''),',')
					if lastrow[0] == "RecordNo":
						RecordNo = 1
					else:
						RecordNo = int(lastrow[0])+1
					fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
					fileOUT.writelines("%s" % RecordNo)
					fileOUT.close()
				except IOError as e:
					try:
						self.f = csv.writer(open("%s%s.csv" % (globals()['LocOfCSV' + plc], dayofWeek[globals()['dayofWeek' + plc]]), 'wb'), delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
					except IOError as e:
						throwError(self.usingGTK,"Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.",plc)
						return				
					self.f.writerow(globals()['headings' + plc])
					self.fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
					self.fileOUT.writelines("1")
					self.fileOUT.close()

			elif globals()['splitby' + plc] == "2": # Month
				if globals()['month' + plc] != datetime.date.today().month:
					globals()['month' + plc] = datetime.date.today().month
					# Check if we are required to delete csv
					if (str(globals()['month' + plc])!=globals()['lastdate' + plc][1] or str(globals()['year' + plc])!=globals()['lastdate' + plc][2]) and globals()['perdroptable' + plc]:
						if (os.path.isfile("%s%s.csv" % (globals()['LocOfCSV' + plc], monthofYear[globals()['month' + plc]]))):
							os.remove("%s%s.csv" % (globals()['LocOfCSV' + plc], monthofYear[globals()['month' + plc]]))
							RecordNo = 1
							fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
							fileOUT.writelines("%s" % RecordNo)
							fileOUT.close()
				try:
		   			fileInT = open("%s%s.csv" % (globals()['LocOfCSV' + plc], monthofYear[globals()['month' + plc]]))
					lines = [line for line in fileInT]
					fileInT.close()
					lastrow = string.split(lines[len(lines)-1].replace('\n', '').replace('\r', ''),',')
					if lastrow[0] == "RecordNo":
						RecordNo = 1
					else:
						RecordNo = int(lastrow[0])+1
					fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
					fileOUT.writelines("%s" % RecordNo)
					fileOUT.close()
				except IOError as e:
					try:
						self.f = csv.writer(open("%s%s.csv" % (globals()['LocOfCSV' + plc], monthofYear[globals()['month' + plc]]), 'wb'), delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
					except IOError as e:
						throwError(self.usingGTK,"Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.",plc)
						return				
					self.f.writerow(globals()['headings' + plc])
					self.fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
					self.fileOUT.writelines("1")
					self.fileOUT.close()
			elif globals()['splitby' + plc] == "3": # Year
				if globals()['year' + plc] != datetime.date.today().year:
					globals()['year' + plc] = datetime.date.today().year
					# Check if we are required to delete csv
					if str(globals()['year' + plc])!=globals()['lastdate' + plc][2] and globals()['perdroptable' + plc]:
						if (os.path.isfile("%s%s.csv" % (globals()['LocOfCSV' + plc], str(globals()['year' + plc])))):
							os.remove("%s%s.csv" % (globals()['LocOfCSV' + plc], str(globals()['year' + plc])))
							RecordNo = 1
							fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
							fileOUT.writelines("%s" % RecordNo)
							fileOUT.close()
				try:
		   			fileInT = open("%s%s.csv" % (globals()['LocOfCSV' + plc], str(globals()['year' + plc])))
					lines = [line for line in fileInT]
					fileInT.close()
					lastrow = string.split(lines[len(lines)-1].replace('\n', '').replace('\r', ''),',')
					if lastrow[0] == "RecordNo":
						RecordNo = 1
					else:
						RecordNo = int(lastrow[0])+1
					fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
					fileOUT.writelines("%s" % RecordNo)
					fileOUT.close()
				except IOError as e:
					try:
						self.f = csv.writer(open("%s%s.csv" % (globals()['LocOfCSV' + plc], str(globals()['year' + plc])), 'wb'), delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
					except IOError as e:
						throwError(self.usingGTK,"Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.",plc)
						return				
					self.f.writerow(globals()['headings' + plc])
					self.fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
					self.fileOUT.writelines("1")
					self.fileOUT.close()
			else:
				try:
		   			open("%s.csv" % globals()['LocOfCSV' + plc])
				except IOError as e:
					try:
						self.f = csv.writer(open("%s.csv" % globals()['LocOfCSV' + plc], 'wb'), delimiter=',',
			       		      		 quotechar='"', quoting=csv.QUOTE_MINIMAL)
					except IOError as e:
						throwError(self.usingGTK,"Could not create CSV file.\nDid the folder name change?\nTry deleting the .ModBusDL folder in the root of your user directory and restart the program.",plc)
						return			
					self.f.writerow(globals()['headings' + plc])
					self.fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
					self.fileOUT.writelines("1")
		else:
			#MySQL
			try:
				globals()['con' + plc] = mdb.connect(host=globals()['mysqladdress' + plc], port=int(globals()['mysqlport' + plc]),user=globals()['mysqlusername' + plc], passwd=globals()['mysqlpassword' + plc], db=globals()['mysqldbname' + plc])
			except mdb.Error, e:
				throwError(self.usingGTK,"Could not connect to MySQL database.\nError %d: %s" % (e.args[0],e.args[1]),plc)
				return
			globals()['con' + plc].autocommit(True)
			globals()['cur' + plc] = globals()['con' + plc].cursor()


			if globals()['splitby' + plc] == "1": #DayofWeek
				## Check for startscript delete or (dates differ & persistant delete)
				if 'droptable' + plc in globals():
					# Check if we are required to drop table
					if globals()['droptable' + plc]:
						globals()['cur' + plc].execute("drop table if exists %s%s" % (globals()['mysqltablename' + plc], dayofWeek[globals()['dayofWeek' + plc]]))
				if  (str(globals()['day' + plc])!=globals()['lastdate' + plc][0] or  str(globals()['month' + plc])!=globals()['lastdate' + plc][1] or str(globals()['year' + plc])!=globals()['lastdate' + plc][2])and globals()['perdroptable' + plc]:
					globals()['cur' + plc].execute("drop table if exists %s%s" % (globals()['mysqltablename' + plc], dayofWeek[globals()['dayofWeek' + plc]]))
				#Check if table exists, then check if we are allowed to make it
				globals()['cur' + plc].execute('show tables like "%s%s"' % (globals()['mysqltablename' + plc],dayofWeek[globals()['dayofWeek' + plc]]))
				if not globals()['cur' + plc].fetchall():
					# Table name doesn't exist
					if globals()['createtable' + plc]:
						# Create table
						self.mysqlstring = getmysqlstring(plc)
						
						globals()['cur' + plc].execute("create table %s%s(%s)" % (globals()['mysqltablename' + plc],dayofWeek[globals()['dayofWeek' + plc]],self.mysqlstring))
					else:
						#Throw Error
						throwError(self.usingGTK,"Could not find a table \"%s\" in the MySQL database.\n" % globals()['mysqltablename' + plc],plc)
						return
			elif globals()['splitby' + plc] == "2": # Month
				## Check for startscript delete or (dates differ & persistant delete)
				if 'droptable' + plc in globals():
					# Check if we are required to drop table
					if globals()['droptable' + plc]:
						globals()['cur' + plc].execute("drop table if exists %s%s" % (globals()['mysqltablename' + plc] , monthofYear[globals()['month' + plc]]))
				if (str(globals()['month' + plc])!=globals()['lastdate' + plc][1] or str(globals()['year' + plc])!=globals()['lastdate' + plc][2]) and globals()['perdroptable' + plc]:
					globals()['cur' + plc].execute("drop table if exists %s%s" % (globals()['mysqltablename' + plc] , monthofYear[globals()['month' + plc]]))

				#Check if table exists, then check if we are allowed to make it
				globals()['cur' + plc].execute('show tables like "%s%s"' % (globals()['mysqltablename' + plc],monthofYear[globals()['month' + plc]]))
		    		if not globals()['cur' + plc].fetchall():
					# Table name doesn't exist
					if globals()['createtable' + plc]:
						# Create table
						self.mysqlstring = getmysqlstring(plc)
						
						globals()['cur' + plc].execute("create table %s%s(%s)" % (globals()['mysqltablename' + plc], monthofYear[globals()['month' + plc]],self.mysqlstring))
					else:
						#Throw Error
						throwError(self.usingGTK,"Could not find a table \"%s\" in the MySQL database.\n" % globals()['mysqltablename' + plc],plc)
						return
			elif globals()['splitby' + plc] == "3": # Year
				## Check for startscript delete or (dates differ & persistant delete)
				if 'droptable' + plc in globals():
					# Check if we are required to drop table
					if globals()['droptable' + plc]:
						globals()['cur' + plc].execute("drop table if exists %s%s" % (globals()['mysqltablename' + plc] , str(globals()['year' + plc])))
				if str(globals()['year' + plc])!=globals()['lastdate' + plc][2] and globals()['perdroptable' + plc]:
					globals()['cur' + plc].execute("drop table if exists %s%s" % (globals()['mysqltablename' + plc] , str(globals()['year' + plc])))

				#Check if table exists, then check if we are allowed to make it
				globals()['cur' + plc].execute('show tables like "%s%s"' % (globals()['mysqltablename' + plc] , str(globals()['year' + plc])))
		    		if not globals()['cur' + plc].fetchall():
					# Table name doesn't exist
					if globals()['createtable' + plc]:
						# Create table
						self.mysqlstring = getmysqlstring(plc)
						
						globals()['cur' + plc].execute("create table %s%s(%s)" % (globals()['mysqltablename' + plc] ,str(globals()['year' + plc]),self.mysqlstring))
					else:
						#Throw Error
						throwError(self.usingGTK,"Could not find a table \"%s\" in the MySQL database.\n" % globals()['mysqltablename' + plc],plc)
						return
			else:
				# Check if we have to drop table
				if 'droptable' + plc in globals():
					if globals()['droptable' + plc]:
						globals()['cur' + plc].execute("drop table if exists %s" % globals()['mysqltablename' + plc])
				#Check if table exists, then check if we are allowed to make it
				globals()['cur' + plc].execute('show tables like "%s"' % globals()['mysqltablename' + plc])
		    		if not globals()['cur' + plc].fetchall():
					# Table name doesn't exist
					if globals()['createtable' + plc]:
						# Create table
						self.mysqlstring = getmysqlstring(plc)
						
						globals()['cur' + plc].execute("create table %s(%s)" % (globals()['mysqltablename' + plc],self.mysqlstring))
					else:
						#Throw Error
						throwError(self.usingGTK,"Could not find a table \"%s\" in the MySQL database.\n" % globals()['mysqltablename' + plc],plc)
						return	

			globals()['con' + plc].close()
		if(self.usingGTK):
			globals()['window3' + plc] = gtk.Window(gtk.WINDOW_TOPLEVEL)
			globals()['window3' + plc].connect("destroy", lambda w: gtk.main_quit())
			globals()['window3' + plc].set_title("ModBus DL - %s" % plc)
			globals()['window3' + plc].set_default_size(200, 200)
			globals()['window3' + plc].set_position(gtk.WIN_POS_CENTER)

			self.main_vbox = gtk.VBox(False, 5)
			self.main_vbox.set_border_width(10)
			globals()['window3' + plc].add(self.main_vbox)

			self.frame = gtk.Frame("Data Logging")
			self.main_vbox.pack_start(self.frame, False, False, 0)

			self.vbox = gtk.VBox(False, 0)
			self.vbox.set_border_width(5)
			self.frame.add(self.vbox)

			### Global Variables ####
			self.hbox = gtk.HBox(False, 0)
			self.vbox.pack_start(self.hbox, True, True, 5)

			self.label.set_alignment(0, 0.5)
			self.hbox.pack_start(self.label, True, True, 0)

			self.adj = gtk.Adjustment(300.0, 0.1, 999.0, 0.1, 5.0, 0.0)
			self.spinner = gtk.SpinButton(self.adj, 0.1, 1)
			self.spinner.set_wrap(True)
			self.hbox.pack_start(self.spinner, True, True, 0)
			#
			#hbox2 = gtk.HBox(False, 0)
			    #vbox.pack_start(hbox2, True, True, 5)
			#mainlabel = gtk.Label("\nClick Run to start the data logging.")
			    #mainlabel.set_alignment(0.5, 0.5)
			#mainlabel.set_line_wrap(True)
			#hbox2.pack_start(mainlabel, True, True, 0)

			#
			self.textview = gtk.TextView()
			self.textview.set_editable(False)
			self.textview.set_cursor_visible(False)
			self.textview.set_wrap_mode(gtk.WRAP_WORD)
			self.textbuffer = self.textview.get_buffer()

			self.hbox3 = gtk.HBox(False, 0)
			self.vbox.pack_start(self.hbox3, False, False, 5)

			self.button2 = gtk.Button("Run")
			self.button3 = gtk.Button("Stop")

			self.sw = gtk.ScrolledWindow()
			self.button = gtk.Button("Quit")
			self.button4 = gtk.Button("Re-Enter Global Information")
		else:
			print ("Start Data Logging (Ctrl+C to Stop)\n")



		if globals()['databasetouse' + plc] == "1":
			if(self.usingGTK):
				self.button2.connect("clicked", startpoll, self.button2, self.button3, self.spinner, self.textbuffer,self.sw,self.button,self.button4,plc)
				self.button3.connect("clicked", stoppoll , self.button2, self.button3,self.button,self.textbuffer,self.sw,self.button4,plc)
			else:
				startpollC("enter", None, None, delay, None,None,None,None,plc)

		else:
			if(self.usingGTK):
				self.button2.connect("clicked", startpollMySQL, self.button2, self.button3, self.spinner, self.textbuffer,self.sw,self.button,self.button4,plc)
				self.button3.connect("clicked", stoppollMySQL , self.button2, self.button3,self.button,self.textbuffer,self.sw,self.button4,plc)
			else:
				startpollMySQLC("enter", None, None, delay, None,None,None,None,plc)
	       
		if(self.usingGTK): 
			self.button2.set_flags(gtk.CAN_DEFAULT)
			self.hbox3.pack_start(self.button2, True, True, 5)
			self.button2.grab_default()

			self.hbox3.pack_start(self.button3, True, True, 5)

			self.frame = gtk.Frame("Output")
			self.main_vbox.pack_start(self.frame, False, False, 0)

			self.vbox = gtk.VBox(False, 0)
			self.vbox.set_border_width(5)
			self.frame.add(self.vbox)

			self.hbox = gtk.HBox(False, 0)
			self.vbox.pack_start(self.hbox, False, True, 5)

			self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
			self.sw.set_size_request(400, 200)
			self.sw.add(self.textview)
			self.hbox.pack_start(self.sw, False, True, 0)

			###End Global Variables####

			self.hbox = gtk.HBox(False, 0)
			self.main_vbox.pack_start(self.hbox, False, True, 0)

			self.button4.connect("clicked", self.restart,plc)
			self.hbox.pack_start(self.button4, True, True, 5)

			self.button.connect("clicked", lambda w: gtk.main_quit())
			self.hbox.pack_start(self.button, True, True, 5)

			globals()['window3' + plc].show_all()
			self.button3.hide()
		else:
			logout.close()

class StartScript:
	def second_quit(self,widget,plc):
		os.remove("%s%s%s%sModBusDLData2" % (path,TheSlash,plc,TheSlash))
		os.remove("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash))
		globals()['window2' + plc].hide()
	def savedata2(self, widget, plc,data1=None,data2=None,data3=None):
		fileOUT = open("%s%s%s%sModBusDLData1" % (path,TheSlash,plc,TheSlash), "w")
		fileOUT.writelines('RecordNo')
		for count in range(0,globals()['NumOfRegisters' + plc]):
			if globals()['DataTypes' + plc][count] != "0" and globals()['DataTypes' + plc][count-1] != "7" and globals()['DataTypes' + plc][count-1] != "8" and globals()['DataTypes' + plc][count-1] != "9" and globals()['DataTypes' + plc][count-1] != "10" and globals()['DataTypes' + plc][count-1] != "17" and globals()['DataTypes' + plc][count-1] != "18" and globals()['DataTypes' + plc][count-1] != "19" and globals()['DataTypes' + plc][count-1] != "20" and globals()['DataTypes' + plc][count-1] != "21" and globals()['DataTypes' + plc][count-1] != "22" and globals()['DataTypes' + plc][count-1] != "23" and globals()['DataTypes' + plc][count-1] != "24" and count != globals()['FlagReg' + plc]:
				fileOUT.writelines(',%s' % globals()['entry' + str(count)].get_text())
		
		fileOUT = open("%s%s%s%sModBusDLData2" % (path,TheSlash,plc,TheSlash), "a")
		fileIN = open("%s%s%s%sModBusDLData1" % (path,TheSlash,plc,TheSlash), "r")
		tempstring = fileIN.readline()
		globals()['headings' + plc] = string.split(tempstring.replace('\n', '').replace('\r', ''),',')
		if globals()['databasetouse' + plc] == "2":
			# MySQL
			fileOUT.writelines("%s|" % data1.get_text())
			if data2.get_active():
				fileOUT.writelines("1|")
			else:
				fileOUT.writelines("0|")
			if data3.get_active():
				globals()['droptable' + plc] = True
			else:
				globals()['droptable' + plc] = False
		else:
			#make headings
			f = csv.writer(open("%s.csv" % globals()['LocOfCSV' + plc], 'wb'), delimiter=',',
	                      quotechar='"', quoting=csv.QUOTE_MINIMAL)
			f.writerow(globals()['headings' + plc])
		fileOUT.writelines("%s|" % globals()['FlagReg' + plc])
		fileOUT.writelines("%s" % globals()['DataTypes' + plc][0])
		for count in range(1,globals()['NumOfRegisters' + plc]):
			fileOUT.writelines(",%s" % globals()['DataTypes' + plc][count])
		fileOUT.close()
		globals()['window2' + plc].hide()
		MainProg(plc,True)

	def fileselect(self, widget, entryLOC,plc):
		dialog = gtk.FileChooserDialog("Open..",None,gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		response = dialog.run()
		if response == gtk.RESPONSE_OK:
	    		globals()['LocOfCSV' + plc] = dialog.get_filename() + TheSlash
			globals()['csvpath' + plc] = dialog.get_filename() + TheSlash
			entryLOC.set_text(globals()['LocOfCSV' + plc])
			dialog.destroy()
	def SetReg(self, widget, spinner,plc):
		LOC = spinner.get_value_as_int()- int(globals()['StartAddress' + plc])
		if LOC != globals()['FlagReg' + plc] and globals()['checkH' + str(LOC)].get_active() and globals()['DataTypes' + plc][LOC-1] != "7" and globals()['DataTypes' + plc][LOC-1] != "8" and globals()['DataTypes' + plc][LOC-1] != "9" and globals()['DataTypes' + plc][LOC-1] != "10" and globals()['DataTypes' + plc][LOC-1] != "17" and globals()['DataTypes' + plc][LOC-1] != "18" and globals()['DataTypes' + plc][LOC-1] != "19" and globals()['DataTypes' + plc][LOC-1] != "20" and globals()['DataTypes' + plc][LOC-1] != "21" and globals()['DataTypes' + plc][LOC-1] != "22" and globals()['DataTypes' + plc][LOC-1] != "23" and globals()['DataTypes' + plc][LOC-1] != "24":

			temp = globals()['FlagReg' + plc] +1
			temp2 = LOC-1
			temp3 = globals()['FlagReg' + plc] -1
			globals()['entry' + str(LOC)].set_text("New Data Flag")
			globals()['entry' + str(LOC)].set_editable(False)
			globals()['entry' + str(LOC)].modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("#ff0000"))
			globals()['checkH' + str(LOC)].hide()
			globals()['menu' + str(LOC)] = gtk.Menu()
			item = make_menu_item ("Decimal            ", self.cb_pos_menu_select, "4", LOC,plc)
			globals()['menu' + str(LOC)].append(item)
			globals()['opt' + str(LOC)].set_menu(globals()['menu' + str(LOC)])
			globals()['wordhbox' + str(LOC)].hide()
			globals()['bytehbox' + str(LOC)].hide()
			globals()['spacerhbox' + str(LOC)].show()
			if globals()['DataTypes' + plc][LOC] == "7" or globals()['DataTypes' + plc][LOC] == "8" or globals()['DataTypes' + plc][LOC] == "9" or globals()['DataTypes' + plc][LOC] == "10" or globals()['DataTypes' + plc][LOC] == "17" or globals()['DataTypes' + plc][LOC] == "18" or globals()['DataTypes' + plc][LOC] == "19" or globals()['DataTypes' + plc][LOC] == "20" and globals()['DataTypes' + plc][LOC-1] == "21" and globals()['DataTypes' + plc][LOC-1] == "22" and globals()['DataTypes' + plc][LOC-1] == "23" and globals()['DataTypes' + plc][LOC-1] == "24":

				#unhide count+1 register
				globals()['checkH' + str(LOC+1)].show()
				globals()['wordhbox' + str(LOC)].hide()
				if globals()['DataTypes' + plc][LOC+1] != "0":
					globals()['entry' + str(LOC+1)].show()
					globals()['opt' + str(LOC+1)].show()
					globals()['entryAdd' + str(LOC+1)].show()
					globals()['bytehbox' + str(LOC+1)].show()
			#set array value to decimal
			globals()['DataTypes' + plc][LOC] = "4"
			if LOC != 0: #not the first in the list
				globals()['menu' + str(temp2)] = gtk.Menu()

				item = make_menu_item ("Binary", self.cb_pos_menu_select, "1", temp2,plc)
				globals()['menu' + str(temp2)].append(item)

				item = make_menu_item ("Octal", self.cb_pos_menu_select, "2", temp2,plc)
				globals()['menu' + str(temp2)].append(item)

				item = make_menu_item ("Hex", self.cb_pos_menu_select, "3", temp2,plc)
				globals()['menu' + str(temp2)].append(item)

				item = make_menu_item ("Decimal", self.cb_pos_menu_select, "4", temp2,plc)
				globals()['menu' + str(temp2)].append(item)

				item = make_menu_item ("Signed Decimal", self.cb_pos_menu_select, "5", temp2,plc)
				globals()['menu' + str(temp2)].append(item)

				item = make_menu_item ("Text", self.cb_pos_menu_select, "6", temp2,plc)
				globals()['menu' + str(temp2)].append(item)

				globals()['opt' + str(temp2)].set_menu(globals()['menu' + str(temp2)])
			#restore the old one
			globals()['entry' + str(globals()['FlagReg' + plc])].set_text("%s %s" % (globals()['textwording' + plc],temp))
			globals()['entry' + str(globals()['FlagReg' + plc])].set_editable(True)
			globals()['entry' + str(globals()['FlagReg' + plc])].modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("#000000"))
			globals()['checkH' + str(globals()['FlagReg' + plc])].show()
			globals()['DataTypes' + plc][globals()['FlagReg' + plc]] = "1"
			if globals()['FlagReg' + plc] != temp2:
				globals()['menu' + str(globals()['FlagReg' + plc])] = gtk.Menu()

				item = make_menu_item ("Binary", self.cb_pos_menu_select, "1", globals()['FlagReg' + plc],plc)
				globals()['menu' + str(globals()['FlagReg' + plc])].append(item)

				item = make_menu_item ("Octal", self.cb_pos_menu_select, "2", globals()['FlagReg' + plc],plc)
				globals()['menu' + str(globals()['FlagReg' + plc])].append(item)

				item = make_menu_item ("Hex", self.cb_pos_menu_select, "3", globals()['FlagReg' + plc],plc)
				globals()['menu' + str(globals()['FlagReg' + plc])].append(item)

				item = make_menu_item ("Decimal", self.cb_pos_menu_select, "4", globals()['FlagReg' + plc],plc)
				globals()['menu' + str(globals()['FlagReg' + plc])].append(item)

				item = make_menu_item ("Signed Decimal", self.cb_pos_menu_select, "5", globals()['FlagReg' + plc],plc)
				globals()['menu' + str(globals()['FlagReg' + plc])].append(item)

				item = make_menu_item ("Text", self.cb_pos_menu_select, "6", globals()['FlagReg' + plc],plc)
				globals()['menu' + str(globals()['FlagReg' + plc])].append(item)
	        	
				if globals()['FlagReg' + plc] != (globals()['NumOfRegisters' + plc]-1):
					item = make_menu_item ("Exponential", self.cb_pos_menu_select, "7", globals()['FlagReg' + plc],plc)
					globals()['menu' + str(globals()['FlagReg' + plc])].append(item)

					item = make_menu_item ("Real", self.cb_pos_menu_select, "8", globals()['FlagReg' + plc],plc)
					globals()['menu' + str(globals()['FlagReg' + plc])].append(item)

					item = make_menu_item ("DWORD-Decimal", self.cb_pos_menu_select, "21", globals()['FlagReg' + plc],plc)
					globals()['menu' + str(globals()['FlagReg' + plc])].append(item)

				globals()['opt' + str(globals()['FlagReg' + plc])].set_menu(globals()['menu' + str(globals()['FlagReg' + plc])])
			if globals()['FlagReg' + plc] != 0:
				#### The Menu ####
				globals()['menu' + str(temp3)] = gtk.Menu()

				item = make_menu_item ("Binary", self.cb_pos_menu_select, "1", temp3,plc)
				globals()['menu' + str(temp3)].append(item)

				item = make_menu_item ("Octal", self.cb_pos_menu_select, "2", temp3,plc)
				globals()['menu' + str(temp3)].append(item)

				item = make_menu_item ("Hex", self.cb_pos_menu_select, "3", temp3,plc)
				globals()['menu' + str(temp3)].append(item)

				item = make_menu_item ("Decimal", self.cb_pos_menu_select, "4", temp3,plc)
				globals()['menu' + str(temp3)].append(item)

				item = make_menu_item ("Signed Decimal", self.cb_pos_menu_select, "5", temp3,plc)
				globals()['menu' + str(temp3)].append(item)

				item = make_menu_item ("Text", self.cb_pos_menu_select, "6", temp3,plc)
				globals()['menu' + str(temp3)].append(item)

				if temp3 != (globals()['NumOfRegisters' + plc]-1):
					item = make_menu_item ("Exponential", self.cb_pos_menu_select, "7", temp3,plc)
					globals()['menu' + str(temp3)].append(item)

					item = make_menu_item ("Real", self.cb_pos_menu_select, "8", temp3,plc)
					globals()['menu' + str(temp3)].append(item)

					item = make_menu_item ("DWORD-Decimal", self.cb_pos_menu_select, "21", temp3,plc)
					globals()['menu' + str(temp3)].append(item)
			
				globals()['opt' + str(temp3)].set_menu(globals()['menu' + str(temp3)])
			globals()['opt' + str(globals()['FlagReg' + plc])].show()
			globals()['bytehbox' + str(globals()['FlagReg' + plc])].show()
			globals()['spacerhbox' + str(globals()['FlagReg' + plc])].hide()
			globals()['bytecheck' + str(globals()['FlagReg' + plc])].set_active(True)
			globals()['FlagReg' + plc] = LOC

	def entry_toggle_editable(self, checkbutton, entry, opt, entryAdd,spacerhbox,bytehbox,count,plc):
		if checkbutton.get_active():
			entry.show()
			opt.set_history(0)
			opt.show()
			entryAdd.show()
			bytehbox.show()
			spacerhbox.hide()
			globals()['DataTypes' + plc][count] = "1"
		else:
			entry.hide()
			opt.hide()
			entryAdd.hide()
			bytehbox.hide()
			spacerhbox.show()
			globals()['DataTypes' + plc][count] = "0"
	def word_toggle(self, checkbutton, count, plc):
		if checkbutton.get_active():
			if globals()['DataTypes' + plc][count] == "7" or globals()['DataTypes' + plc][count] == "9":
				globals()['DataTypes' + plc][count] = "7"
			elif globals()['DataTypes' + plc][count] == "8" or globals()['DataTypes' + plc][count] == "10":
				globals()['DataTypes' + plc][count] = "8"
			elif globals()['DataTypes' + plc][count] == "21" or globals()['DataTypes' + plc][count] == "22":
				globals()['DataTypes' + plc][count] = "21"
		else:
			if globals()['DataTypes' + plc][count] == "7" or globals()['DataTypes' + plc][count] == "9":
				globals()['DataTypes' + plc][count] = "9"
			elif globals()['DataTypes' + plc][count] == "8" or globals()['DataTypes' + plc][count] == "10":
				globals()['DataTypes' + plc][count] = "10"
			elif globals()['DataTypes' + plc][count] == "21" or globals()['DataTypes' + plc][count] == "22":
				globals()['DataTypes' + plc][count] = "22"
	def byte_toggle(self, checkbutton, count,plc):
		if checkbutton.get_active():
			if globals()['DataTypes' + plc][count] == "1" or globals()['DataTypes' + plc][count] == "11":
				globals()['DataTypes' + plc][count] = "1"
			elif globals()['DataTypes' + plc][count] == "2" or globals()['DataTypes' + plc][count] == "12":
				globals()['DataTypes' + plc][count] = "2"
			elif globals()['DataTypes' + plc][count] == "3" or globals()['DataTypes' + plc][count] == "13":
				globals()['DataTypes' + plc][count] = "3"
			elif globals()['DataTypes' + plc][count] == "4" or globals()['DataTypes' + plc][count] == "14":
				globals()['DataTypes' + plc][count] = "4"
			elif globals()['DataTypes' + plc][count] == "5" or globals()['DataTypes' + plc][count] == "15":
				globals()['DataTypes' + plc][count] = "5"
			elif globals()['DataTypes' + plc][count] == "6" or globals()['DataTypes' + plc][count] == "16":
				globals()['DataTypes' + plc][count] = "6"
			elif globals()['DataTypes' + plc][count] == "7" or globals()['DataTypes' + plc][count] == "17":
				globals()['DataTypes' + plc][count] = "7"
			elif globals()['DataTypes' + plc][count] == "8" or globals()['DataTypes' + plc][count] == "18":
				globals()['DataTypes' + plc][count] = "8"
			elif globals()['DataTypes' + plc][count] == "9" or globals()['DataTypes' + plc][count] == "19":
				globals()['DataTypes' + plc][count] = "9"
			elif globals()['DataTypes' + plc][count] == "10" or globals()['DataTypes' + plc][count] == "20":
				globals()['DataTypes' + plc][count] = "10"

			elif globals()['DataTypes' + plc][count] == "21" or globals()['DataTypes' + plc][count] == "23":
				globals()['DataTypes' + plc][count] = "21"

			elif globals()['DataTypes' + plc][count] == "22" or globals()['DataTypes' + plc][count] == "24":
				globals()['DataTypes' + plc][count] = "22"
		else:
			if globals()['DataTypes' + plc][count] == "1" or globals()['DataTypes' + plc][count] == "11":
				globals()['DataTypes' + plc][count] = "11"
			elif globals()['DataTypes' + plc][count] == "2" or globals()['DataTypes' + plc][count] == "12":
				globals()['DataTypes' + plc][count] = "12"
			elif globals()['DataTypes' + plc][count] == "3" or globals()['DataTypes' + plc][count] == "13":
				globals()['DataTypes' + plc][count] = "13"
			elif globals()['DataTypes' + plc][count] == "4" or globals()['DataTypes' + plc][count] == "14":
				globals()['DataTypes' + plc][count] = "14"
			elif globals()['DataTypes' + plc][count] == "5" or globals()['DataTypes' + plc][count] == "15":
				globals()['DataTypes' + plc][count] = "15"
			elif globals()['DataTypes' + plc][count] == "6" or globals()['DataTypes' + plc][count] == "16":
				globals()['DataTypes' + plc][count] = "16"
			elif globals()['DataTypes' + plc][count] == "7" or globals()['DataTypes' + plc][count] == "17":
				globals()['DataTypes' + plc][count] = "17"
			elif globals()['DataTypes' + plc][count] == "8" or globals()['DataTypes' + plc][count] == "18":
				globals()['DataTypes' + plc][count] = "18"
			elif globals()['DataTypes' + plc][count] == "9" or globals()['DataTypes' + plc][count] == "19":
				globals()['DataTypes' + plc][count] = "19"
			elif globals()['DataTypes' + plc][count] == "10" or globals()['DataTypes' + plc][count] == "20":
				globals()['DataTypes' + plc][count] = "20"

			elif globals()['DataTypes' + plc][count] == "21" or globals()['DataTypes' + plc][count] == "23":
				globals()['DataTypes' + plc][count] = "23"

			elif globals()['DataTypes' + plc][count] == "22" or globals()['DataTypes' + plc][count] == "24":
				globals()['DataTypes' + plc][count] = "24"
			

	def CreateTable_toggle_editable(self, checkbutton, plc):
		if checkbutton.get_active():
			globals()['createtable' + plc] = True
		else:
			globals()['createtable' + plc] = False
	def DropTable_toggle_editable(self, checkbutton, plc):
		if checkbutton.get_active():
			globals()['droptable' + plc] = True
		else:
			globals()['droptable' + plc] = False
	def cb_pos_menu_select(self, item, pos, count,plc):
		if pos == "7" or pos == "8" or pos == "21":
			#hide count+1 register
			globals()['entry' + str(count+1)].hide()
			globals()['opt' + str(count+1)].hide()
			globals()['checkH' + str(count+1)].hide()
			globals()['entryAdd' + str(count+1)].hide()
			globals()['wordhbox' + str(count+1)].hide()
			globals()['bytehbox' + str(count+1)].hide()
			# Set checkbox for word ordering
			globals()['wordhbox' + str(count)].show()
			globals()['wordcheck' + str(count)].set_active(True)
		elif (globals()['DataTypes' + plc][count] == "7" or globals()['DataTypes' + plc][count] == "8" or globals()['DataTypes' + plc][count] == "9" or globals()['DataTypes' + plc][count] == "10" or globals()['DataTypes' + plc][count] == "17" or globals()['DataTypes' + plc][count] == "18" or globals()['DataTypes' + plc][count] == "19" or globals()['DataTypes' + plc][count] == "20" or globals()['DataTypes' + plc][count] == "21" or globals()['DataTypes' + plc][count] == "22" or globals()['DataTypes' + plc][count] == "23" or globals()['DataTypes' + plc][count] == "24") and pos != "7" and pos != "8" and pos != "21":

			#unhide count+1 register
			globals()['checkH' + str(count+1)].show()
			globals()['wordhbox' + str(count)].hide()
			if globals()['DataTypes' + plc][count+1] != "0":
				globals()['entry' + str(count+1)].show()
				globals()['opt' + str(count+1)].show()
				globals()['entryAdd' + str(count+1)].show()
				globals()['bytehbox' + str(count+1)].show()
				globals()['bytecheck' + str(count+1)].set_active(True)
		globals()['bytecheck' + str(count)].set_active(True)
		globals()['DataTypes' + plc][count] = pos;

	def cb_database_menu_select(self, item, pos,hbox6,hbox2,hbox10,hbox11,hbox12,hbox13,plc):
		globals()['databasetouse' + plc] = pos
		if pos == "1":
			hbox6.show()
			hbox2.show()
			hbox10.hide()
			hbox11.hide()
			hbox12.hide()
			hbox13.hide()
			globals()['textwording' + plc] = "Name of Register"
		else:
			hbox6.hide()
			hbox2.hide()
			hbox10.show()
			hbox11.show()
			hbox12.show()
			hbox13.show()
			globals()['textwording' + plc] = "SQL Column Name"
	def cb_splitby_menu_select(self, item, pos,perdrophbox,plc):
		globals()['splitby' + plc] = pos
		if pos == "0":
			perdrophbox.hide()
		else:
			perdrophbox.show()
	def converthex(self,widget,hexnum,decnum):
		decnum.set_text(str(int("%s" % hexnum.get_text(), 16)))
	def convertoctal(self,widget,octalnum,decnum):
		decnum.set_text(str(int("%s" % octalnum.get_text(), 8)))
	def hide(self, data=None):
		global convertwindow
		convertwindow.hide()
	def converter(self, data=None):
		global convertwindow
		convertwindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
		convertwindow.connect("destroy", self.hide)
		convertwindow.set_title("Octal/Hex Converter")
		convertwindow.set_default_size(100, 100)
		convertwindow.set_property("allow-grow", 0)
		convertwindow.set_position(gtk.WIN_POS_CENTER)

		main_vbox = gtk.VBox(False, 5)
		main_vbox.set_border_width(10)
		convertwindow.add(main_vbox)

		hbox = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox, False, True, 5)

		decnum = gtk.Entry()

		octallabel = gtk.Label("Octal : ")
		octallabel.set_alignment(0, 0.5)
		hbox.pack_start(octallabel, True, True, 0)

		octalnum = gtk.Entry()
		octalnum.set_max_length(15)
		octalnum.set_text("")
		octalnum.select_region(0, len(octalnum.get_text()))
		hbox.pack_start(octalnum, True, True, 0)

		Convertoctal = gtk.Button("Convert")
		Convertoctal.connect("clicked", self.convertoctal,octalnum,decnum)
		hbox.pack_start(Convertoctal, True, True, 5)

		#
		hbox2 = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox2, False, True, 5)

		hexlabel = gtk.Label("Hex : ")
		hexlabel.set_alignment(0, 0.5)
		hbox2.pack_start(hexlabel, True, True, 0)

		hexnum = gtk.Entry()
		hexnum.set_max_length(15)
		hexnum.set_text("")
		hexnum.select_region(0, len(hexnum.get_text()))
		hbox2.pack_start(hexnum, True, True, 0)

		Converthex = gtk.Button("Convert")
		Converthex.connect("clicked", self.converthex,hexnum,decnum)
		hbox2.pack_start(Converthex, True, True, 5)
		#
		hbox3 = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox3, False, True, 5)
		hseparator = gtk.HSeparator()
		hbox3.pack_start(hseparator)
		#
		hbox4 = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox4, False, True, 5)

		declabel = gtk.Label("Base 10 : ")
		declabel.set_alignment(0, 0.5)
		hbox4.pack_start(declabel, True, True, 0)

		decnum.set_max_length(15)
		decnum.set_text("")
		decnum.select_region(0, len(decnum.get_text()))
		hbox4.pack_start(decnum, True, True, 0)

		convertwindow.show_all()

	def savedata(self, widget, spinner, spinner2, entryip, warning,entryname,mysqlserver,mysqluser,mysqlpass,mysqldb,warning2,mysqlportspinner,plc):
		globals()['address' + plc] = entryip.get_text()
		globals()['mysqladdress' + plc] = mysqlserver.get_text()
		globals()['mysqlport' + plc] = mysqlportspinner.get_value_as_int()
		EndingAddressBten = spinner.get_value_as_int()
		globals()['StartAddress' + plc] = spinner2.get_value_as_int()
		globals()['NumOfRegisters' + plc] = EndingAddressBten - globals()['StartAddress' + plc] + 1;
		if globals()['NumOfRegisters' + plc] < 3:
			warning2.show()
		else:
			if is_valid_ip(globals()['address' + plc]) and ((globals()['databasetouse' + plc] == "1") or (globals()['databasetouse' + plc] == "2" and is_valid_ip(globals()['mysqladdress' + plc]))):

				if globals()['FlagReg' + plc] >= globals()['NumOfRegisters' + plc]:
					globals()['FlagReg' + plc] = globals()['NumOfRegisters' + plc]-1
				fileOUT = open("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash), "w")
				fileOUT.writelines("1")
				fileOUT = open("%s%s%s%sModBusDLData2" % (path,TheSlash,plc,TheSlash), "w")
				fileOUT.writelines("%s|" % globals()['StartAddress' + plc])
				fileOUT.writelines("%s|" % globals()['NumOfRegisters' + plc])
				fileOUT.writelines("%s|" % globals()['databasetouse' + plc])
				fileOUT.writelines("%s|" % globals()['address' + plc])
				globals()['window2' + plc] = gtk.Window(gtk.WINDOW_TOPLEVEL)
				globals()['window2' + plc].connect("destroy", lambda w: gtk.main_quit())
				globals()['window2' + plc].set_title("ModBus DL - %s" % plc)
				globals()['window2' + plc].set_default_size(530, 200)
				globals()['window2' + plc].set_property("allow-grow", 0)
				globals()['window2' + plc].set_position(gtk.WIN_POS_CENTER)

				main_vbox2 = gtk.VBox(False, 5)
				main_vbox2.set_border_width(10)
				globals()['window2' + plc].add(main_vbox2)

				hboxlabel = gtk.HBox(False, 0)
				main_vbox2.pack_start(hboxlabel, True, True, 5)

				mainlabel = gtk.Label("You must select one register to be the 'new data available' register. A value of zero in this register tells ModBus DL there is no new data and a one tells ModBus DL to read the data. ModBus DL will set this register to zero once it pulls the data.")
				mainlabel.set_alignment(0.5, 0.5)
				mainlabel.set_line_wrap(True)

				hboxlabel.pack_start(mainlabel, True, True, 0)
				if globals()['databasetouse' + plc] == "1":
					# CSV
					globals()['LocOfCSV' + plc] = globals()['csvpath' + plc] + entryname.get_text()
					globals()['CSVName' + plc] = entryname.get_text()
					fileOUT.writelines("%s|" % globals()['LocOfCSV' + plc])
					fileOUT.writelines("%s|" % globals()['CSVName' + plc])
					hboxheadingslabel = gtk.Label("For each register select whether you wish to collect data from it, enter a name for the register, select the type of data the register will be storing, and lastly the byte/word ordering. The register address is displayed to ease this process.")
				else:
					globals()['mysqlusername' + plc] = mysqluser.get_text()
					globals()['mysqlpassword' + plc] = mysqlpass.get_text()
					globals()['mysqldbname' + plc] = mysqldb.get_text()
					fileOUT.writelines("%s|" % globals()['mysqladdress' + plc])
					fileOUT.writelines("%s|" % globals()['mysqlport' + plc])
					fileOUT.writelines("%s|" % globals()['mysqlusername' + plc])
					fileOUT.writelines("%s|" % globals()['mysqlpassword' + plc])
					fileOUT.writelines("%s|" % globals()['mysqldbname' + plc])

					hboxlabel2 = gtk.HBox(False, 0)
					main_vbox2.pack_start(hboxlabel2, True, True, 5)

					mainlabel2 = gtk.Label("MySQL Table Name : ")
					mainlabel2.set_alignment(0.5, 0.5)
					mainlabel2.set_line_wrap(True)

					hboxlabel2.pack_start(mainlabel2, False, False, 0)

					tablename = gtk.Entry()
					tablename.set_max_length(15)
					tablename.set_text(globals()['mysqltablename' + plc])
					tablename.select_region(0, len(tablename.get_text()))
					hboxlabel2.pack_start(tablename, False, False, 0)
					#
					hboxlabel3 = gtk.HBox(False, 0)
					main_vbox2.pack_start(hboxlabel3, True, True, 5)


					createtablecheck = gtk.CheckButton()
					createtablecheck.connect("toggled", self.CreateTable_toggle_editable,plc)
					createtablecheck.set_active(True)	

					mainlabel3 = gtk.Label("Create Table If It Doesn't Exist")
					mainlabel3.set_alignment(0.5, 0.5)
					mainlabel3.set_line_wrap(True)

					droptablecheck = gtk.CheckButton()
					droptablecheck.connect("toggled", self.DropTable_toggle_editable,plc)
					droptablecheck.set_active(False)	

					mainlabeldrop = gtk.Label("     Drop Table If It Exists")
					mainlabeldrop.set_alignment(0.5, 0.5)
					mainlabeldrop.set_line_wrap(True)

					hboxlabel3.pack_start(mainlabel3, False, False, 0)
					hboxlabel3.pack_start(createtablecheck, False, False, 0)
					hboxlabel3.pack_start(mainlabeldrop, False, False, 0)
					hboxlabel3.pack_start(droptablecheck, False, False, 0)
		
					hboxheadingslabel = gtk.Label("For each register select whether you wish to collect data from it, select the type of data the register will be storing, and enter the column name for the register in the MySQL table. The register address is displayed to ease this process.")

					####
				if globals()['perdroptable' + plc]:
					fileOUT.writelines("%s|" % "1")
				else:
					fileOUT.writelines("%s|" % "0")
				fileOUT.writelines("%s|" % globals()['splitby' + plc])
				vboxtitle = gtk.VBox(False, 0)
				hboxlabel.pack_start(vboxtitle, True, True, 0)
				adj = gtk.Adjustment(float(globals()['StartAddress' + plc]), float(globals()['StartAddress' + plc]), float(int(globals()['StartAddress' + plc])+globals()['NumOfRegisters' + plc]-1), 1.0, 5.0, 0.0)
				Flagspinner = gtk.SpinButton(adj, 0, 0)
				Flagspinner.set_wrap(True)
				vboxtitle.pack_start(Flagspinner, False, True, 0)

				SetRegbutton = gtk.Button("Set")
				SetRegbutton.connect("clicked", self.SetReg,Flagspinner,plc)
				vboxtitle.pack_start(SetRegbutton, True, True, 5)


				frame = gtk.Frame("Register Information")
				main_vbox2.pack_start(frame, True, True, 0)

				vbox = gtk.VBox(False, 0)
				vbox.set_border_width(5)
				frame.add(vbox)

				##loop through heading code####
				hboxheadings = gtk.HBox(False, 0)
				vbox.pack_start(hboxheadings, True, True, 5)

				hboxheadingslabel.set_alignment(0.5, 0.5)
				hboxheadingslabel.set_line_wrap(True)
				hboxheadings.pack_start(hboxheadingslabel, True, True, 0)

				Registervbox = gtk.VBox(False, 0)
				Registervbox.set_border_width(5)
				RegisterScroll = gtk.ScrolledWindow()
				RegisterScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
				RegisterScroll.set_size_request(530, 250)
				RegisterScroll.add_with_viewport(Registervbox)
				vbox.pack_start(RegisterScroll, False, True, 0)

				oldDataTypes = globals()['DataTypes' + plc];
				for count in range(len(oldDataTypes),globals()['NumOfRegisters' + plc]):
					oldDataTypes.append("0")
				globals()['DataTypes' + plc] = []
				for count in range(0,globals()['NumOfRegisters' + plc]):
					globals()['DataTypes' + plc].append("1")
				headingscount = 1;
				for count in range(0,globals()['NumOfRegisters' + plc]):
					count1 = count + 1
				
					CurrAddress = int(globals()['StartAddress' + plc])+count
					globals()['hbox' + str(count)] = gtk.HBox(False, 0)
					Registervbox.pack_start(globals()['hbox' + str(count)], False, True, 5)

					globals()['entry' + str(count)] = gtk.Entry()
					globals()['opt' + str(count)] = gtk.OptionMenu()
					globals()['entryAdd' + str(count)] = gtk.Entry()

					globals()['entry' + str(count)].set_max_length(50)
					# byte/word ordering
					globals()['bytewordvbox' + str(count)] = gtk.VBox(False, 0)
					globals()['bytehbox' + str(count)] = gtk.HBox(False, 0)
					globals()['bytewordvbox' + str(count)].pack_start(globals()['bytehbox' + str(count)], False, True, 0)
					globals()['wordhbox' + str(count)] = gtk.HBox(False, 0)
					globals()['bytewordvbox' + str(count)].pack_start(globals()['wordhbox' + str(count)], False, True, 0)
					globals()['spacerhbox' + str(count)] = gtk.HBox(False, 0)
					globals()['bytewordvbox' + str(count)].pack_start(globals()['spacerhbox' + str(count)], False, True, 0)
					globals()['bytelabel' + str(count)] = gtk.Label("High byte/ Low byte   ")
					globals()['bytelabel' + str(count)].set_alignment(0, 0.5)
					globals()['bytecheck' + str(count)] = gtk.CheckButton()
					globals()['bytehbox' + str(count)].pack_start(globals()['bytecheck' + str(count)], True, True, 0)
					globals()['bytehbox' + str(count)].pack_start(globals()['bytelabel' + str(count)], True, True, 0)
					globals()['bytecheck' + str(count)].connect("toggled", self.byte_toggle, count,plc)
					globals()['bytecheck' + str(count)].set_active(True)
					#
					globals()['wordlabel' + str(count)] = gtk.Label("High word/ Low word")
					globals()['wordlabel' + str(count)].set_alignment(0, 0.5)
					globals()['wordcheck' + str(count)] = gtk.CheckButton()
					globals()['wordhbox' + str(count)].pack_start(globals()['wordcheck' + str(count)], True, True, 0)
					globals()['wordhbox' + str(count)].pack_start(globals()['wordlabel' + str(count)], True, True, 0)

					globals()['wordcheck' + str(count)].connect("toggled", self.word_toggle, count,plc)
					globals()['wordcheck' + str(count)].set_active(True)

					globals()['hbox' + str(count)].pack_end(globals()['bytewordvbox' + str(count)], False, True, 0)
					#
					globals()['spacerlabel' + str(count)] = gtk.Label("                                         ")
					globals()['wordlabel' + str(count)].set_alignment(0, 0.5)
					globals()['spacerhbox' + str(count)].pack_start(globals()['spacerlabel' + str(count)], True, True, 0)
					###
					globals()['menu' + str(count)] = gtk.Menu()
					if count == globals()['FlagReg' + plc]:
						item = make_menu_item ("Decimal            ", self.cb_pos_menu_select, "4", count,plc)
						globals()['menu' + str(count)].append(item)
					else:

						item = make_menu_item ("Binary", self.cb_pos_menu_select, "1", count,plc)
						globals()['menu' + str(count)].append(item)
		  
						item = make_menu_item ("Octal", self.cb_pos_menu_select, "2", count,plc)
						globals()['menu' + str(count)].append(item)

						item = make_menu_item ("Hex", self.cb_pos_menu_select, "3", count,plc)
						globals()['menu' + str(count)].append(item)

						item = make_menu_item ("Decimal", self.cb_pos_menu_select, "4", count,plc)
						globals()['menu' + str(count)].append(item)

						item = make_menu_item ("Signed Decimal", self.cb_pos_menu_select, "5", count,plc)
						globals()['menu' + str(count)].append(item)

						item = make_menu_item ("Text", self.cb_pos_menu_select, "6", count,plc)
						globals()['menu' + str(count)].append(item)

						if count1 != globals()['NumOfRegisters' + plc] and count1 != globals()['FlagReg' + plc]:
							item = make_menu_item ("Exponential", self.cb_pos_menu_select, "7", count,plc)
							globals()['menu' + str(count)].append(item)

							item = make_menu_item ("Real", self.cb_pos_menu_select, "8", count,plc)
							globals()['menu' + str(count)].append(item)

							item = make_menu_item ("DWORD-Decimal", self.cb_pos_menu_select, "21", count,plc)
							globals()['menu' + str(count)].append(item)

		  
					globals()['opt' + str(count)].set_menu(globals()['menu' + str(count)])
					globals()['hbox' + str(count)].pack_end(globals()['opt' + str(count)], False, True, 0)
					#
					if globals()['headings' + plc] and oldDataTypes:
						if oldDataTypes[count] != "0" and count != globals()['FlagReg' + plc]:
							if count==0:
								globals()['entry' + str(count)].set_text("%s" % globals()['headings' + plc][headingscount])
								headingscount = headingscount + 1
							elif oldDataTypes[count-1] != "7" and oldDataTypes[count-1] != "8" and oldDataTypes[count-1] != "9" and oldDataTypes[count-1] != "10" and oldDataTypes[count-1] != "17" and oldDataTypes[count-1] != "18" and oldDataTypes[count-1] != "19" and oldDataTypes[count-1] != "20" and oldDataTypes[count-1] != "21" and oldDataTypes[count-1] != "22" and oldDataTypes[count-1] != "23" and oldDataTypes[count-1] != "24":
								globals()['entry' + str(count)].set_text("%s" % globals()['headings' + plc][headingscount])
								headingscount = headingscount + 1
							else:
								globals()['entry' + str(count)].set_text("%s %s" % (globals()['textwording' + plc],count1))
						else:
						
							globals()['entry' + str(count)].set_text("%s %s" % (globals()['textwording' + plc],count1))
					else:
						globals()['entry' + str(count)].set_text("%s %s" % (globals()['textwording' + plc],count1))
					globals()['entry' + str(count)].select_region(0, len(globals()['entry' + str(count)].get_text()))
					globals()['hbox' + str(count)].pack_end(globals()['entry' + str(count)], False, True, 0)
		       			
		  			#
					globals()['entryAdd' + str(count)].set_text("%s" % CurrAddress)
					globals()['entryAdd' + str(count)].set_editable(False)
					globals()['hbox' + str(count)].pack_end(globals()['entryAdd' + str(count)], False, True, 0)
					#

					globals()['checkH' + str(count)] = gtk.CheckButton()
					globals()['hbox' + str(count)].pack_end(globals()['checkH' + str(count)], True, True, 0)
					globals()['checkH' + str(count)].connect("toggled", self.entry_toggle_editable, globals()['entry' + str(count)], globals()['opt' + str(count)], globals()['entryAdd' + str(count)],globals()['spacerhbox' + str(count)],globals()['bytehbox' + str(count)], count,plc)
					globals()['checkH' + str(count)].set_active(True)

				hbox = gtk.HBox(False, 0)
				main_vbox2.pack_start(hbox, False, True, 0)
		  
				button = gtk.Button("Quit")
				button.connect("clicked", self.second_quit,plc)
				hbox.pack_start(button, True, True, 5)

				button1 = gtk.Button("Continue")
				if globals()['databasetouse' + plc] == "1":
					# CSV
					button1.connect("clicked", self.savedata2,plc)
				else:
					button1.connect("clicked", self.savedata2,plc,tablename,createtablecheck,droptablecheck)
				hbox.pack_start(button1, True, True, 5)
				button1.set_flags(gtk.CAN_DEFAULT)
				button1.grab_default()

				globals()['window' + plc].hide()
				globals()['window2' + plc].show_all()
				#hide FlagReg
				globals()['entry' + str(globals()['FlagReg' + plc])].set_text("New Data Flag")
				globals()['entry' + str(globals()['FlagReg' + plc])].set_editable(False)
				globals()['entry' + str(globals()['FlagReg' + plc])].modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("#ff0000"))
				globals()['checkH' + str(globals()['FlagReg' + plc])].hide()
				globals()['bytehbox' + str(globals()['FlagReg' + plc])].hide()
				for count in range(0,globals()['NumOfRegisters' + plc]):
					globals()['wordhbox' + str(count)].hide()
					if count != globals()['FlagReg' + plc]:
						globals()['spacerhbox' + str(count)].hide()
			else:
				warning.show()
	def perdrop_toggle_editable(self, checkbutton, plc):
		if checkbutton.get_active():
			globals()['perdroptable' + plc] = True
		else:
			globals()['perdroptable' + plc] = False
	def make_menu_item_splitby(self,named, callback, data1,data2,plc):
		item = gtk.MenuItem(named)
		item.connect("activate", callback, data1, data2,plc)
		item.show()
		return item
	def __init__(self,plc):
		# Test is globals exist
		if 'address' + plc not in globals():
			globals()['address' + plc] = '127.0.0.1'
		if 'CSVName' + plc not in globals():
			globals()['CSVName' + plc] = "data"
		if 'FlagReg' + plc not in globals():
			globals()['FlagReg' + plc] = 0
		if 'mysqladdress' + plc not in globals():
			globals()['mysqladdress' + plc] = '127.0.0.1'
		if 'mysqlusername' + plc not in globals():
			globals()['mysqlusername' + plc] = "root"
		if 'mysqlport' + plc not in globals():
			globals()['mysqlport' + plc] = "3306"
		if 'mysqlpassword' + plc not in globals():
			globals()['mysqlpassword' + plc] = "******"
		if 'databasetouse' + plc not in globals():
			globals()['databasetouse' + plc] = "1" #CSV
		if 'mysqldbname' + plc not in globals():
			globals()['mysqldbname' + plc] = "ModBus"
		if 'mysqltablename' + plc not in globals():
			globals()['mysqltablename' + plc] = "ModBus"
		if 'createtable' + plc not in globals():
			globals()['createtable' + plc] = True
		if 'droptable' + plc not in globals():
			globals()['droptable' + plc] = False
		if 'con' + plc not in globals():
			globals()['con' + plc] = None
		if 'cur' + plc not in globals():
			globals()['cur' + plc] = None
		if 'textwording' + plc not in globals():
			globals()['textwording' + plc] = "Name of Register"
		if 'DataTypes' + plc not in globals():
			globals()['DataTypes' + plc] = []
		if 'headings' + plc not in globals():
			globals()['headings' + plc] = []
		if 'NumOfRegisters' + plc not in globals():
			globals()['NumOfRegisters' + plc] = 7
		if 'StartAddress' + plc not in globals():
			globals()['StartAddress' + plc] = 2560
		if 'LocOfCSV' + plc not in globals():
			globals()['LocOfCSV' + plc] = ""
		if 'csvpath' + plc not in globals():
			globals()['csvpath' + plc] = ""
		if 'perdroptable' + plc not in globals():
			globals()['perdroptable' + plc] = False
		if 'splitby' + plc not in globals():
			globals()['splitby' + plc] = "0"
		
		globals()['window' + plc] = gtk.Window(gtk.WINDOW_TOPLEVEL)
		globals()['window' + plc].connect("destroy", lambda w: gtk.main_quit())
		globals()['window' + plc].set_title("ModBus DL - %s" % plc)
		globals()['window' + plc].set_default_size(200, 300)
		globals()['window' + plc].set_property("allow-grow", 0)
		globals()['window' + plc].set_position(gtk.WIN_POS_CENTER)

		main_vbox = gtk.VBox(False, 5)
		main_vbox.set_border_width(10)
		globals()['window' + plc].add(main_vbox)

		hbox8 = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox8, False, True, 5)

		Toplabel = gtk.Label("Welcome to ModBus DL\n\nOn the next two screens you will enter basic information about your ModBus connection. The next time you start the program it will jump directly into the main data logging screen.")
		Toplabel.set_alignment(0.5, 0.5)
		Toplabel.get_settings().set_string_property('gtk-font-name', 'serif 10','');
		Toplabel.set_line_wrap(True)
		hbox8.pack_start(Toplabel, True, True, 0)
		#
		hbox9 = gtk.HBox(False, 0)
		hbox2 = gtk.HBox(False, 0)
		hbox6 = gtk.HBox(False, 0)
		hbox10 = gtk.HBox(False, 0)
		hbox11 = gtk.HBox(False, 0)
		hbox12 = gtk.HBox(False, 0)
		hbox13 = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox9, False, True, 5)
		DataStoreMenu = gtk.Menu()
		if globals()['databasetouse' + plc] == "1":
			item = make_menu_item_database ("CSV File", self.cb_database_menu_select, "1",hbox6,hbox2,hbox10,hbox11,hbox12,hbox13,plc)
	        	DataStoreMenu.append(item)
			item = make_menu_item_database ("MySQL Database", self.cb_database_menu_select, "2",hbox6,hbox2,hbox10,hbox11,hbox12,hbox13,plc)
	        	DataStoreMenu.append(item)
		else:
			item = make_menu_item_database ("MySQL Database", self.cb_database_menu_select, "2",hbox6,hbox2,hbox10,hbox11,hbox12,hbox13,plc)
	        	DataStoreMenu.append(item)
			item = make_menu_item_database ("CSV File", self.cb_database_menu_select, "1",hbox6,hbox2,hbox10,hbox11,hbox12,hbox13,plc)
	        	DataStoreMenu.append(item)
		DataStoreOpt = gtk.OptionMenu()
		DataStoreOpt.set_menu(DataStoreMenu)
		hbox9.pack_start(DataStoreOpt, False, True, 0)
		#
		frame = gtk.Frame("Global Variables")
		main_vbox.pack_start(frame, False, True, 0)

		vbox = gtk.VBox(False, 0)
		vbox.set_border_width(5)
		frame.add(vbox)

		### Global Variables ####
		hbox7 = gtk.HBox(False, 0)
		vbox.pack_start(hbox7, True, True, 5)

		Formatlabel = gtk.Label("Note: Address Locations in base 10.")
		Formatlabel.set_alignment(0.5, 0.5)
		Formatlabel.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#4169E1'))
		hbox7.pack_start(Formatlabel, True, True, 0)

		#
		converthbox = gtk.HBox(False, 0)
		vbox.pack_start(converthbox, True, True, 5)
		Convertbutton = gtk.Button("Octal/Hex Converter")
		Convertbutton.connect("clicked", self.converter)
		converthbox.pack_start(Convertbutton, True, False, 5)
		#
		hbox3 = gtk.HBox(False, 0)
		vbox.pack_start(hbox3, True, True, 5)

		label2 = gtk.Label("Starting Address of Registers : ")
		label2.set_alignment(0, 0.5)
		hbox3.pack_start(label2, True, True, 0)

		adj2 = gtk.Adjustment(float(globals()['StartAddress' + plc]), 1.0, 999999.0, 1.0, 5.0, 0.0)
		spinner2 = gtk.SpinButton(adj2, 0, 0)
		spinner2.set_wrap(True)
		hbox3.pack_start(spinner2, True, True, 0)

		#
		hbox = gtk.HBox(False, 0)
		vbox.pack_start(hbox, True, True, 5)

		label = gtk.Label("Ending Address of Registers : ")
		label.set_alignment(0, 0.5)
		hbox.pack_start(label, True, True, 0)

		adj = gtk.Adjustment(float(int(globals()['StartAddress' + plc])+globals()['NumOfRegisters' + plc]-1), 1.0, 999999.0, 1.0, 5.0, 0.0)
		spinner = gtk.SpinButton(adj, 0, 0)
		spinner.set_wrap(True)
		hbox.pack_start(spinner, True, True, 0)

		#
		hbox5 = gtk.HBox(False, 0)
		vbox.pack_start(hbox5, True, True, 5)

		label3 = gtk.Label("IP of ModBus : ")
		label3.set_alignment(0, 0.5)
		hbox5.pack_start(label3, True, True, 0)

		entryip = gtk.Entry()
		entryip.set_max_length(15)
		entryip.set_text(globals()['address' + plc])
		entryip.select_region(0, len(entryip.get_text()))
		hbox5.pack_start(entryip, True, True, 0)
		#
		splithbox = gtk.HBox(False, 0)
		perdrophbox = gtk.HBox(False, 0)
		vbox.pack_start(splithbox, True, True, 5)

		splitlabel = gtk.Label("Split Data Files By : ")
		splitlabel.set_alignment(0, 0.5)
		splithbox.pack_start(splitlabel, True, True, 0)


		splitMenu = gtk.Menu()
		if globals()['splitby' + plc] == "0":
			item = self.make_menu_item_splitby ("No Split", self.cb_splitby_menu_select, "0",perdrophbox,plc)
	        	splitMenu.append(item)
			item = self.make_menu_item_splitby ("Weekday", self.cb_splitby_menu_select, "1",perdrophbox,plc)
	        	splitMenu.append(item)
			item = self.make_menu_item_splitby ("Month", self.cb_splitby_menu_select, "2",perdrophbox,plc)
	        	splitMenu.append(item)
			item = self.make_menu_item_splitby ("Year", self.cb_splitby_menu_select, "3",perdrophbox,plc)
	        	splitMenu.append(item)
		elif globals()['splitby' + plc] == "1":
			item = self.make_menu_item_splitby ("Weekday", self.cb_splitby_menu_select, "1",perdrophbox,plc)
	        	splitMenu.append(item)
			item = self.make_menu_item_splitby ("No Split", self.cb_splitby_menu_select, "0",perdrophbox,plc)
	        	splitMenu.append(item)
			item = self.make_menu_item_splitby ("Month", self.cb_splitby_menu_select, "2",perdrophbox,plc)
	        	splitMenu.append(item)
			item = self.make_menu_item_splitby ("Year", self.cb_splitby_menu_select, "3",perdrophbox,plc)
	        	splitMenu.append(item)
		elif globals()['splitby' + plc] == "2":
			item = self.make_menu_item_splitby ("Month", self.cb_splitby_menu_select, "2",perdrophbox,plc)
	        	splitMenu.append(item)
			item = self.make_menu_item_splitby ("No Split", self.cb_splitby_menu_select, "0",perdrophbox,plc)
	        	splitMenu.append(item)
			item = self.make_menu_item_splitby ("Weekday", self.cb_splitby_menu_select, "1",perdrophbox,plc)
	        	splitMenu.append(item)
			item = self.make_menu_item_splitby ("Year", self.cb_splitby_menu_select, "3",perdrophbox,plc)
	        	splitMenu.append(item)
		else:
			item = self.make_menu_item_splitby ("Year", self.cb_splitby_menu_select, "3",perdrophbox,plc)
	        	splitMenu.append(item)
			item = self.make_menu_item_splitby ("No Split", self.cb_splitby_menu_select, "0",perdrophbox,plc)
	        	splitMenu.append(item)
			item = self.make_menu_item_splitby ("Weekday", self.cb_splitby_menu_select, "1",perdrophbox,plc)
	        	splitMenu.append(item)
			item = self.make_menu_item_splitby ("Month", self.cb_splitby_menu_select, "2",perdrophbox,plc)
	        	splitMenu.append(item)
		splitOpt = gtk.OptionMenu()

		splitOpt.set_menu(splitMenu)
		####hbox9.pack_start(splitOpt, False, True, 0)####
		splithbox.pack_start(splitOpt, True, True, 0)
		#
		vbox.pack_start(perdrophbox, True, True, 5)
		perdropcheck = gtk.CheckButton()
		perdropcheck.connect("toggled", self.perdrop_toggle_editable,plc)
		if globals()['perdroptable' + plc]:
			perdropcheck.set_active(True)
		else:
			perdropcheck.set_active(False)	

		mainlabelperdrop = gtk.Label("Drop CSV/Table If Name Exists")
		mainlabelperdrop.set_alignment(0.5, 0.5)
		mainlabelperdrop.set_line_wrap(True)

		perdrophbox.pack_start(mainlabelperdrop, False, True, 0)
		perdrophbox.pack_start(perdropcheck, False, True, 0)
		#
		vbox.pack_start(hbox6, True, True, 5)

		label4 = gtk.Label("Name of CSV file : ")
		label4.set_alignment(0, 0.5)
		hbox6.pack_start(label4, True, True, 0)

		entryname = gtk.Entry()
		entryname.set_max_length(15)
		entryname.set_text(globals()['CSVName' + plc])
		entryname.select_region(0, len(entryname.get_text()))
		hbox6.pack_start(entryname, True, True, 0)
		#
		vbox.pack_start(hbox2, True, True, 5)

		button3 = gtk.Button("Location of CSV file")
		entryLOC = gtk.Entry()
		entryLOC.set_text(globals()['csvpath' + plc])
		entryLOC.set_editable(False)
		button3.connect("clicked", self.fileselect, entryLOC)
		hbox2.pack_start(button3, True, True, 5)
		hbox2.pack_start(entryLOC, True, True, 0)
		#
		#MySQL Data
		vbox.pack_start(hbox10, True, True, 5)

		mysqlserverl = gtk.Label("Address of MySQL Server : ")
		mysqlserverl.set_alignment(0, 0.5)
		hbox10.pack_start(mysqlserverl, True, True, 0)

		mysqlserver = gtk.Entry()
		mysqlserver.set_max_length(15)
		mysqlserver.set_text(globals()['mysqladdress' + plc])
		mysqlserver.select_region(0, len(mysqlserver.get_text()))
		hbox10.pack_start(mysqlserver, True, True, 0)

		adj = gtk.Adjustment(3306, 1.0, 999999.0, 1.0, 5.0, 0.0)
		mysqlportspinner = gtk.SpinButton(adj, 0, 0)
		mysqlportspinner.set_wrap(True)
		hbox10.pack_start(mysqlportspinner, True, True, 0)
		#
		#
		vbox.pack_start(hbox11, True, True, 5)

		mysqluserl = gtk.Label("User Name : ")
		mysqluserl.set_alignment(0, 0.5)
		hbox11.pack_start(mysqluserl, True, True, 0)

		mysqluser = gtk.Entry()
		mysqluser.set_max_length(15)
		mysqluser.set_text(globals()['mysqlusername' + plc])
		mysqluser.select_region(0, len(mysqluser.get_text()))
		hbox11.pack_start(mysqluser, True, True, 0)
		#
		#
		vbox.pack_start(hbox12, True, True, 5)

		mysqlpassl = gtk.Label("Password : ")
		mysqlpassl.set_alignment(0, 0.5)
		hbox12.pack_start(mysqlpassl, True, True, 0)

		mysqlpass = gtk.Entry()
		mysqlpass.set_max_length(15)
		mysqlpass.set_text(globals()['mysqlpassword' + plc])
		mysqlpass.select_region(0, len(mysqlpass.get_text()))
		hbox12.pack_start(mysqlpass, True, True, 0)
		#
		#
		vbox.pack_start(hbox13, True, True, 5)

		mysqldbl = gtk.Label("Database : ")
		mysqldbl.set_alignment(0, 0.5)
		hbox13.pack_start(mysqldbl, True, True, 0)

		mysqldb = gtk.Entry()
		mysqldb.set_max_length(15)
		mysqldb.set_text(globals()['mysqldbname' + plc])
		mysqldb.select_region(0, len(mysqldb.get_text()))
		hbox13.pack_start(mysqldb, True, True, 0)
		#
		hbox4 = gtk.HBox(False, 0)
		vbox.pack_start(hbox4, True, True, 5)

		warning = gtk.Label("Please Enter a Valid IP")
		warning.set_alignment(0, 0.5)
		warning.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#ff0000'))
		hbox4.pack_start(warning, True, True, 0)
		#
		hbox14 = gtk.HBox(False, 0)
		vbox.pack_start(hbox14, True, True, 5)

		warning2 = gtk.Label("You Need At Least 2 Registers")
		warning2.set_alignment(0, 0.5)
		warning2.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#ff0000'))
		hbox14.pack_start(warning2, True, True, 0)
		###End Global Variables####

		hbox = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox, False, True, 0)

		button = gtk.Button("Quit")
		button.connect("clicked", lambda w: gtk.main_quit())
		hbox.pack_start(button, True, True, 5)

		button1 = gtk.Button("Continue")
		button1.connect("clicked", self.savedata, spinner, spinner2, entryip, warning,entryname,mysqlserver,mysqluser,mysqlpass,mysqldb,warning2,mysqlportspinner,plc)
		hbox.pack_start(button1, True, True, 5)
		button1.set_flags(gtk.CAN_DEFAULT)
		button1.grab_default()

		globals()['window' + plc].show_all()
		warning.hide()
		warning2.hide()
		if globals()['splitby' + plc] == "0":
			perdrophbox.hide()
		else:
			perdrophbox.show()
		if globals()['databasetouse' + plc] == "1":
			hbox6.show()
			hbox2.show()
			hbox10.hide()
			hbox11.hide()
			hbox12.hide()
			hbox13.hide()
			globals()['textwording' + plc] = "Name of Register"
		else:
			hbox6.hide()
			hbox2.hide()
			hbox10.show()
			hbox11.show()
			hbox12.show()
			hbox13.show()
			globals()['textwording' + plc] = "SQL Column Name"

class startupwindow():
	def __init__(self):
		self.startthewindow()
	def startthewindow(self):
		global startwindow
		# open start window
		startwindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
		startwindow.connect("destroy", lambda w: gtk.main_quit())
		startwindow.set_title("PLC Selector")
		startwindow.set_default_size(100, 100)
		startwindow.set_property("allow-grow", 0)
		startwindow.set_position(gtk.WIN_POS_CENTER)

		main_vbox = gtk.VBox(False, 5)
		main_vbox.set_border_width(10)
		startwindow.add(main_vbox)

		hbox = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox, False, True, 5)

		# top labels
		Toplabel = gtk.Label("Select an existing PLC or create a new one.")
		Toplabel.set_alignment(0.5, 0.5)
		Toplabel.get_settings().set_string_property('gtk-font-name', 'serif 10','');
		Toplabel.set_line_wrap(True)
		hbox.pack_start(Toplabel, True, True, 0)


		#scrolled selectionbox

		selectvbox = gtk.VBox(False, 0)
		selectvbox.set_border_width(5)
		selectScroll = gtk.ScrolledWindow()
		selectScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		selectScroll.set_size_request(530, 250)
	   	selectScroll.add_with_viewport(selectvbox)
		main_vbox.pack_start(selectScroll, False, True, 0)


		directories=[d for d in os.listdir("%s" % path) if os.path.isdir(os.path.join("%s" % path,d))]
		for count in range(0,len(directories)):
			globals()['plcselecthbox' + str(count)] = gtk.HBox(False, 0)
			globals()['plcselectbutton' + str(count)] = gtk.Button(directories[count])
			globals()['plcselectbutton' + str(count)].connect("clicked", self.open_plc, directories[count])
			globals()['plcselecthbox' + str(count)].pack_start(globals()['plcselectbutton' + str(count)], True, True, 5)
			selectvbox.pack_start(globals()['plcselecthbox' + str(count)], False, True, 5)
			globals()['plcactive' + directories[count]] = False


		hbox2 = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox2, False, True, 0)

		button = gtk.Button("Create New PLC")
		button.connect("clicked", self.newplc)
		hbox2.pack_start(button, True, True, 5)

		button1 = gtk.Button("Delete An Existing PLC")
		button1.connect("clicked", self.removeplc)
		hbox2.pack_start(button1, True, True, 5)
		
   		startwindow.show_all()
	def newplc(self, widget):
		# Global newplc window.User enters name. Sanitize the name. Create folder. Send back to main screen
		global newplcwindow
		global startwindow
		startwindow.hide()

		newplcwindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
		newplcwindow.connect("delete-event", self.close_newwindow)
		newplcwindow.set_title("Create New PLC")
		newplcwindow.set_default_size(100, 100)
		newplcwindow.set_property("allow-grow", 0)
		newplcwindow.set_position(gtk.WIN_POS_CENTER)

		main_vbox = gtk.VBox(False, 5)
		main_vbox.set_border_width(10)
		newplcwindow.add(main_vbox)

		hbox = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox, False, True, 5)

		# top labels
		Toplabel = gtk.Label("Enter the Name of the PLC.")
		Toplabel.set_alignment(0.5, 0.5)
		Toplabel.get_settings().set_string_property('gtk-font-name', 'serif 10','');
		Toplabel.set_line_wrap(True)
		hbox.pack_start(Toplabel, True, True, 0)

		#entry
		hbox3 = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox3, False, True, 0)

		newplcname = gtk.Entry()
		newplcname.set_max_length(15)
		newplcname.set_text("New PLC")
		newplcname.select_region(0, len(newplcname.get_text()))
		hbox3.pack_start(newplcname, True, True, 0)

		hbox2 = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox2, False, True, 0)

		button = gtk.Button("Cancel")
		button.connect("clicked", self.close_newwindow)
		hbox2.pack_start(button, True, True, 5)

		button1 = gtk.Button("Create PLC")
		button1.connect("clicked", self.makeplc, newplcname)
		hbox2.pack_start(button1, True, True, 5)

		newplcwindow.show_all()

	def removeplc(self,widget):
		# Global removeplc window.Show list like startscreen. WHen clicked on verify delete. Then remove folder. Send back to main screen
		global startwindow
		startwindow.hide()
		global removeplcwindow
		# open start window
		removeplcwindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
		removeplcwindow.connect("delete-event", self.close_removewindow)
		removeplcwindow.set_title("Remove PLC")
		removeplcwindow.set_default_size(100, 100)
		removeplcwindow.set_property("allow-grow", 0)
		removeplcwindow.set_position(gtk.WIN_POS_CENTER)

		main_vbox = gtk.VBox(False, 5)
		main_vbox.set_border_width(10)
		removeplcwindow.add(main_vbox)

		hbox = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox, False, True, 5)

		# top labels
		Toplabel = gtk.Label("Select an existing PLC to Delete it.")
		Toplabel.set_alignment(0.5, 0.5)
		Toplabel.get_settings().set_string_property('gtk-font-name', 'serif 10','');
		Toplabel.set_line_wrap(True)
		hbox.pack_start(Toplabel, True, True, 0)


		#scrolled selectionbox

		selectvbox = gtk.VBox(False, 0)
		selectvbox.set_border_width(5)
		selectScroll = gtk.ScrolledWindow()
		selectScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		selectScroll.set_size_request(530, 250)
		selectScroll.add_with_viewport(selectvbox)
		main_vbox.pack_start(selectScroll, False, True, 0)


		directories=[d for d in os.listdir("%s" % path) if os.path.isdir(os.path.join("%s" % path,d))]
		for count in range(0,len(directories)):
			globals()['plcselecthbox' + str(count)] = gtk.HBox(False, 0)
			globals()['plcselectbutton' + str(count)] = gtk.Button(directories[count])
			globals()['plcselectbutton' + str(count)].connect("clicked", self.delete_plc, directories[count])
			globals()['plcselecthbox' + str(count)].pack_start(globals()['plcselectbutton' + str(count)], True, True, 5)
			selectvbox.pack_start(globals()['plcselecthbox' + str(count)], False, True, 5)
			globals()['plcactive' + directories[count]] = False


		hbox2 = gtk.HBox(False, 0)
		main_vbox.pack_start(hbox2, False, True, 0)

		button = gtk.Button("Cancel")
		button.connect("clicked", self.close_removewindow)
		hbox2.pack_start(button, True, True, 5)
		
   		removeplcwindow.show_all()
	def makeplc(self,widget,newplcname):
		name = ''.join(e for e in newplcname.get_text().replace(" ", "_") if e.isalnum())
		if not os.path.exists("%s%s%s" % (path,TheSlash,name)):
    			os.makedirs("%s%s%s" % (path,TheSlash,name))
		self.close_newwindow()

	def delete_plc(self, widget, name):
		shutil.rmtree("%s%s%s" % (path,TheSlash,name))
		self.close_removewindow()

	def close_newwindow(self, Data1=None, Data2=None):
		global newplcwindow
		newplcwindow.hide()
		self.startthewindow()

	def close_removewindow(self, Data1=None, Data2=None):
		global removeplcwindow
		removeplcwindow.hide()
		self.startthewindow()

	def open_plc(self,widget,plc):
		global startwindow
		globals()['csvpath' + plc] = os.path.abspath(os.path.dirname(sys.argv[0])) + TheSlash
    		#globals()['LocOfCSV' + plc] = globals()['csvpath' + plc] + globals()['CSVName' + plc] + ".csv"
		if os.path.isfile("%s%s%s%sModBusDLData2" % (path,TheSlash,plc,TheSlash)) and os.path.isfile("%s%s%s%sModBusDLData1" % (path,TheSlash,plc,TheSlash)) and os.path.isfile("%s%s%s%sModBusDLData3" % (path,TheSlash,plc,TheSlash)):
			startwindow.hide()
			MainProg(plc,True)
		else:
			startwindow.hide()
			StartScript(plc)
def main():
    # Set for OS
    global path
    global TheSlash
    global textlog
    platform = sys.platform
    if platform.find('win') >= 0:
		TheSlash = '\\'
    else:
		TheSlash = '/'
    path = os.path.expanduser(os.path.join("~",".ModBusDL")) + TheSlash
    textlog = os.path.expanduser(os.path.join("~",".ModBusDL")) + TheSlash + "log.txt"
    if not os.path.exists(os.path.expanduser(os.path.join("~",".ModBusDL"))):
    	os.makedirs(os.path.expanduser(os.path.join("~",".ModBusDL")))
    
    if len(sys.argv) >= 3:
	if sys.argv[1] == "-c":
		directories=[d for d in os.listdir("%s" % path) if os.path.isdir(os.path.join("%s" % path,d))]
		if sys.argv[2] in directories:
			if platform.find('win') >= 0:
				if len(sys.argv) >= 4:
					if sys.argv[3] == "-t" and len(sys.argv) >= 5:
						delay = str(sys.argv[4])
						teststring = delay.replace('.', '')
						if teststring.isdigit():
							delay = round(float(delay), 1)
							MainProg(sys.argv[2],False,delay)

						else:
							startupwindow()

					else:
			   			startupwindow()

		      		else:
					startupwindow()

		   	else: 
			    	if len(sys.argv) >= 4:
					if sys.argv[3] == "-t" and len(sys.argv) >= 5:
						delay = str(sys.argv[4])
						teststring = delay.replace('.', '')
						while not teststring.isdigit():
							print ("Enter a Valid Number\n")
							delay = raw_input("Polling Delay in Seconds : ")
							teststring = delay.replace('.', '')
						delay = round(float(delay), 1)
			  			MainProg(sys.argv[2],False,delay)

		      			else:
						delay = raw_input("Polling Delay in Seconds : ")
						teststring = delay.replace('.', '')
						while not teststring.isdigit():
							print ("Enter a Valid Number\n")
							delay = raw_input("Polling Delay in Seconds : ")
							teststring = delay.replace('.', '')
						delay = round(float(delay), 1)
			  			MainProg(sys.argv[2],False,delay)
	       			else:
		       			delay = raw_input("Polling Delay in Seconds : ")
		       			teststring = delay.replace('.', '')
		       			while not teststring.isdigit():
			       			print ("Enter a Valid Number\n")
			       			delay = raw_input("Polling Delay in Seconds : ")
			       			teststring = delay.replace('.', '')
	       				delay = round(float(delay), 1)
			  		MainProg(sys.argv[2],False,delay)
		else:
			startupwindow()
	else:
		startupwindow()
    else:

	startupwindow()
    gtk.main()
    return 0

if __name__ == "__main__":
    main()
