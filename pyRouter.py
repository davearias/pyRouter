#This looks like it will work; pick a destination and a source and it will take. No confirmation, just GO.
#Might need to switch to a background poll for lock checks instead of constant updating. Commenting out the lock inquiry on line 163-165 for now.
#Need to add a way to see a locked destination is selected, BG currently does not change.

import telnetlib, time, re, csv
from Tkinter import *
from tkFileDialog import askopenfilename
import threading
import datetime
import time

#Source list CSV file (RTR source number, Displayed name)
sourceCSV = "sources.csv"
#Destination list CSV file (RTR destination number, Displayed name)
destinationsCSV = "destinations.csv"
#Router IP address
host = "10.10.43.3"
#Router port (default 10001)
port = 10001
timeout = 120
#Router config
max_destinations = 144
max_sources = 144

#GUI Config
#Colors
destSelColor = "red"
destLockColor = "orange"
srcSelColor = "red"
winBGColor = "white"
#Button Layouts
maxColumns = 12

#Initilizations
lastSrc = -1
master = Tk()
master.wm_title("pyRouter")
winBGColor = master.cget("bg")

with open(sourceCSV, 'rU') as f:
    reader = csv.reader(f,dialect='excel')
    sources = list(reader)

with open(destinationsCSV, 'rU') as f:
    reader = csv.reader(f,dialect='excel')
    destinations = list(reader)

video_check = re.compile("^[\\r]*\*{2} V\d{1,3},\d{1,3},(\d{1,2}|-) (OK\s)?!!")
lock_check = re.compile("^[\\r]*\*{2} B\d{1,3},\d{1,4},1 (OK\s)?!!")
unlock_check = re.compile("^[\\r]*\*{2} B\d{1,3},\d{1,4},0 (OK\s)?!!")


exitFlag = 1

class MyThread (threading.Thread):
#http://stackoverflow.com/questions/21894705/python-tkinter-and-socket-recv-loops
#http://makeapppie.com/2014/07/15/from-apple-to-raspberry-pi-how-to-do-threading-with-python-and-tkinter/
    def __init__(self,threadID,name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        print ("Starting " + self.name) 
        readRouter2()
        print ("Exiting " + self.name)

def readRouter(e):
	global thread1
	global exitFlag
	exitFlag = 0
	thread1=MyThread(1,"thread1")
	thread1.start()
	print("Reading Router")

def stopRead(e):
    print("Stop pressed")
    global exitFlag
    if threading.active_count() >2:
        global thread1
    if thread1.isAlive():
        exitFlag = 1
        global routerSession
        routerSession.close()
        connectButton.configure(text="Connect")
        connectButton.bind('<Button-1>',connectRouter)

def connectRouter(e):
    global exitFlag
    global routerSession
    try:
        routerSession = telnetlib.Telnet(host, port, timeout)
    except socket.timeout:
        statusText.configure(text="socket timeout")
    else:
        print ("Connected!")
        statusText.configure(text="Connected!")
        time.sleep(0.3)
        readRouter(1)
        time.sleep(0.3)
        pollRouter(1)
        time.sleep(0.3)
        connectButton.configure(text="Disconnect")
        connectButton.bind('<Button-1>',stopRead)

def readRouter2():
        global routerSession
        global sources
        global destinations
        global dst_buttons
        global lastSrc
        output = ""
        command = routerSession.read_until("!!", timeout )
        command_buf = command
        print "Command received from router:" + repr(command)
        if video_check.search(command):
#This first check isn't working right, and I'm not motivated to fix it right now.
#            dest = command[command.find("V")+1:command.find(",")]
#            command = command.replace(",","X",1)
#            src = command[command.find("X")+1:command.find(",")]
#            dest = int(dest)-1
#            src = int(src)-1
#            output = destinations[dest][1]+" is now routed to "+sources[src][:-1]
            print "Dummy"
        elif lock_check.search(command):
            dest = command[command.find("B")+1:command.find(",")]
            dest = int(dest)-1
            output = destinations[dest][1]+" is now LOCKED"
            dst_buttons[dest][2].configure(highlightbackground=destLockColor)
            dst_buttons[dest][2].configure(bg=destLockColor)
            print output
        elif unlock_check.search(command):
            dest = command[command.find("B")+1:command.find(",")]
            dest = int(dest)-1
            output = destinations[dest][1]+" is now UNLOCKED"
            dst_buttons[dest][2].configure(highlightbackground=winBGColor)
            dst_buttons[dest][2].configure(bg=winBGColor)
            print output
        statusText.configure(text=output)
        command = ""
    
        while exitFlag == 0:
            command = routerSession.read_until("!!", timeout )
            if command == command_buf:
                print "Duplicate ignored"
            else:
                command_buf = command
                print "Command just received from router:" + repr(command)
                if video_check.search(command):
                    dest = command[command.find("V")+1:command.find(",")]
                    command = command.replace(",","X",1)
                    src = command[command.find("X")+1:command.find(",")]
                    print dest
                    print src
                    try:
                        dstBtnIdx = [y[0] for y in dst_buttons].index(dest)
                        srcBtnIdx = [y[0] for y in src_buttons].index(src)
                        output = destinations[dstBtnIdx][1]+" is now routed to "+sources[srcBtnIdx][1]
                        if dstBtnIdx == destPST:
                            print "Highlight"
                            src_buttons[srcBtnIdx][2].configure(highlightbackground=srcSelColor)
                            src_buttons[srcBtnIdx][2].configure(bg=srcSelColor)
                            if src_buttons[lastSrc][2].cget('highlightbackground') == srcSelColor:
                                src_buttons[lastSrc][2].configure(highlightbackground=winBGColor)
                                src_buttons[lastSrc][2].configure(bg=winBGColor)
                            lastSrc = srcBtnIdx
                        else:
                            print "Ignore"
#                        print output
                    except ValueError:
                        print "Not in list!"
                elif lock_check.search(command):
                    dest = command[command.find("B")+1:command.find(",")]
                    try:
                    	dstBtnIdx = [y[0] for y in dst_buttons].index(dest)
                    except ValueError:
                    	print "Destination not in list, skipping"
                    output = destinations[dstBtnIdx][1]+" is now LOCKED"
                    dst_buttons[dstBtnIdx][2].configure(highlightbackground=destLockColor)
                    dst_buttons[dstBtnIdx][2].configure(bg=destLockColor)
#                    print output
                elif unlock_check.search(command):
                    dest = command[command.find("B")+1:command.find(",")]
                    try:
                        dstBtnIdx = [y[0] for y in dst_buttons].index(dest)
                        output = destinations[dstBtnIdx][1]+" is now UNLOCKED"
                        if dstBtnIdx == destPST:
                            dst_buttons[dstBtnIdx][2].configure(highlightbackground=destSelColor)
                            dst_buttons[dstBtnIdx][2].configure(bg=destSelColor)
                        else:
                            dst_buttons[dstBtnIdx][2].configure(highlightbackground=winBGColor)
                            dst_buttons[dstBtnIdx][2].configure(bg=winBGColor)
#                        print output
                    except ValueError:
                        print "Not in list!"
                statusText.configure(text=output)
                print ("{0} : {1}".format(str(datetime.datetime.now()).split('.')[0],output))
                command = ""

def route1(source,button):
    global routerSession
    global destPST
    global destinations
    routerCmd = "** X"+destinations[destPST][0]+","+ source +",1 !!"
    routerSession.write(routerCmd)
    statusText.configure(text="Command Sent: " + "**X"+destinations[destPST][0]+","+ source +",0,!!")

destPST = -1
def pickDest(destination,button):
    global destPST
    global dst_buttons
    global destinations
    global routerSession
    if destPST > -1:
#Here I am clearing the indicator on the last selected destination button.
#Check the color of the last selected button (destPST). If button is destLockColor, we think it's locked, so don't turn it destSelColor
        if dst_buttons[destPST][2].cget('highlightbackground') == destLockColor:
            print "Locked not changing color"
#Otherwise, turn the button to winBGColor.
        else:
            dst_buttons[destPST][2].configure(highlightbackground=winBGColor)
            dst_buttons[destPST][2].configure(bg=winBGColor)
    if dst_buttons[button][2].cget('highlightbackground') == destLockColor:
        print "Locked not changing color"
    else:
        dst_buttons[button][2].configure(highlightbackground=destSelColor)
        dst_buttons[button][2].configure(bg=destSelColor)
    destPST = button
#Poll the router to find the current source for the selected destination. Highlight will happen in readRouter2 function.
    routerCmd = "** O"+destination+" !!"
    routerSession.write(routerCmd)
    statusText.configure(text="Command sent: " + routerCmd)

def lockDest(e):
    global destPST
    global dst_buttons
    global destinations
    routerCmd = "** B"+destinations[destPST][0]+",9999,1 !!"
    routerSession.write(routerCmd)
    statusText.configure(text="Command sent: " + routerCmd)
    
def unlockDest(e):
    global destPST
    global dst_buttons
    global destinations
    print destPST
    routerCmd = "** B"+destinations[destPST][0]+",9999,0 !!"
    routerSession.write(routerCmd)
    statusText.configure(text="Command sent: " + routerCmd)

def lockAll(e):
    for i in range(1,max_destinations+1):
        routerCmd = "** B%d,9999,1 !!" % i
        routerSession.write(routerCmd)
        
def unlockAll(e):
    for i in range(1,max_destinations+1):
        routerCmd = "** B%d,9999,0 !!" % i
        routerSession.write(routerCmd)
	    
def pollRouter(e):
    global routerSession
    routerCmd = "**U4!!"
    routerSession.write(routerCmd)
    for i in range(1,145):
        routerCmd = "** B%d,0,0 !!" % i
        routerSession.write(routerCmd)

def loadSalvo():
   global salvo
   filename = askopenfilename(parent=master)
   f = open(filename, 'rU')
   reader = csv.reader(f,dialect='excel')
   salvo = list(reader)
   print salvo
   print len(salvo)
   for i in range(len(salvo)):
    if salvo[i][0] == "" or salvo[i][1] == "":
        print "Blank DST or SRC"
    else:
        print "Dest: " + salvo[i][0] + "->Src: " + salvo[i][1]
        if salvo[i][2] == "1":
            print "LOCKED DESTINATION"

def runSalvo():
    global routerSession
    statusText.configure(text="Standby... Running Salvo!")
    for i in range(len(salvo)):
        if salvo[i][0] == "" or salvo[i][1] == "":
            print "Blank DST or SRC"
        else:
            print "Dest:" + salvo[i][0] + "->Src: " + salvo[i][1]
            routerCmd = "** X"+salvo[i][0]+","+ salvo[i][1] +",0 !!"
            routerSession.write(routerCmd)
            if salvo[i][2] == "1":
                routerCmd = "** B"+salvo[i][0]+",9999,1 !!"
                routerSession.write(routerCmd)  
                print "Locking DEST:" + salvo[i][0] 
            time.sleep(0.1)
    statusText.configure(text="Salvo Completed!")

class ToolTip(object):
#http://www.voidspace.org.uk/python/weblog/arch_d7_2006_07_01.shtml#e387

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 27
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        try:
            # For Mac OS
            tw.tk.call("::tk::unsupported::MacWindowStyle",
                       "style", tw._w,
                       "help", "noActivates")
        except TclError:
            pass
        label = Label(tw, text=self.text, justify=LEFT,
                      background="#ffffe0", relief=SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def createToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

def drawButtons():
    global dst_buttons, src_buttons
    sourceText = Label(master, text="Destinations")
    sourceText.grid(row=2,column=0,columnspan=12)
    r = 3
    c = 0
    dst_buttons = []
    for i in range(len(destinations)):
        destID=destinations[i][0]
    # For lambda sourceID=sourceID: http://stackoverflow.com/questions/10865116/python-tkinter-creating-buttons-in-for-loop-passing-command-arguments
    #    Button(text=destinations[i][1].rstrip(), width=10,command=lambda destID=destID: pickDest(destID)).grid(row=r,column=c)
        dstButton = Button(text=destinations[i][1].rstrip(), width=10,command=lambda destID=destID,dstBtn=i: pickDest(destID,dstBtn))
        dstButton.grid(row=r,column=c)
        dst_buttons.append((destID,destinations[i][1],dstButton))
        createToolTip(dstButton, "RouterOP: %s" % destID)
        if c < maxColumns:
            c = c + 1
        else:
            r = r + 1
            c = 0
    
    r = r + 1
    c = 0
    sourceText = Label(master, text="Sources")
    sourceText.grid(row=r,column=0,columnspan=12)
    r = r + 1
    c = 0
    src_buttons = []
    for i in range(len(sources)):
        sourceID=sources[i][0]
    # For lambda sourceID=sourceID: http://stackoverflow.com/questions/10865116/python-tkinter-creating-buttons-in-for-loop-passing-command-arguments
    #    Button(text=sources[i][1].rstrip(), width=10,command=lambda sourceID=sourceID: route1(sourceID)).grid(row=r,column=c)
        srcButton = Button(text=sources[i][1].rstrip(), width=10,command=lambda sourceID=sourceID,srcBtn=i: route1(sourceID,srcBtn))
        srcButton.grid(row=r,column=c)
        src_buttons.append((sourceID,sources[i][1],srcButton))
        createToolTip(srcButton, "RouterIP: %s" % sourceID)
        if c < maxColumns:
            c = c + 1
        else:
            r = r + 1
            c = 0
    
menubar = Menu(master)
salvomenu = Menu(menubar, tearoff=0)
salvomenu.add_command(label="Open",command=loadSalvo)
salvomenu.add_separator()
salvomenu.add_command(label="Run",command=runSalvo)
menubar.add_cascade(label="Salvo", menu=salvomenu)

statusText = Label(master, text="Press connect!")
statusText.grid(row=0,column=0,columnspan=12)
connectButton=Button(master,text="Connect")
connectButton.grid(row=1,column=0)
lockButton=Button(master,text="Lock")
lockButton.grid(row=1,column=4)
unlockButton=Button(master,text="Unlock")
unlockButton.grid(row=1,column=5)
lockAllButton=Button(master,text="Lock All")
lockAllButton.grid(row=1,column=6)
unlockAllButton=Button(master,text="Unlock All")
unlockAllButton.grid(row=1,column=7)
#loadSalvoButton=Button(master,text="Load Salvo")
#loadSalvoButton.grid(row=1,column=8)
#runSalvoButton=Button(master,text="Run Salvo")
#runSalvoButton.grid(row=1,column=9)

#Button bindings
connectButton.bind('<Button-1>',connectRouter)
lockButton.bind('<Button-1>',lockDest)
unlockButton.bind('<Button-1>',unlockDest)
lockAllButton.bind('<Button-1>',lockAll)
unlockAllButton.bind('<Button-1>',unlockAll)
#loadSalvoButton.bind('<Button-1>',loadSalvo)
#runSalvoButton.bind('<Button-1>',runSalvo)
createToolTip(connectButton, "Press to connect to router!")

master.config(menu=menubar)
drawButtons()
master.mainloop()
