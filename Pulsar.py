from time import sleep
from threading import Thread
from datetime import datetime, timedelta
from tkinter import Frame, Button, Tk, Label, Entry, Text, END
from serial import Serial, SerialException

starttime = datetime.now()
advancedFiring = False
advancedStep = 0
connection = False
pulseList = []
freq = 1


def read_from_port(ser):
    """Read from serial port, to be used in a separate thread"""
    while True:
        reading = ser.readline().decode()
        handle_data(reading)

arduino = Serial(None)
thread = Thread(target=read_from_port, args=(arduino,), daemon=True)


def connectserial(port):
    """Open a serial connection in a seperate thread"""
    global arduino
    global thread
    arduino.close()
    try:
        arduino.port = port
        arduino.timeout = 2.0
        arduino.open()
        sleep(2)
        arduino.write("Hello\n".encode())
        answer = arduino.read(5)
        answer = answer.decode()
        if answer == "Hello":
            arduino.timeout = None
            app.connectLabel.config(text="Arduino connected")

            thread.start()
        else:
            app.connectLabel.config(text="No arduino detected, check port.")

    except SerialException:
        app.connectLabel.config(text="Could not open COM Port!")


def setlaseron(pulses, frequency):
    """Send a command to turn on the laser, save parameters as global variables, update start time label in GUI"""
    arduino.write(("setLaserOnXX%s,%s\n" % (pulses, frequency)).encode())
    global freq
    freq = float(frequency)
    global starttime
    starttime = datetime.now()
    app.startTimeLabel.config(text="Start time:" + str(starttime.hour) + ":" + str(starttime.minute).zfill(2))


def enableadvanced():
    """Enable the advanced mode for complex pulse sequences"""
    app.frame.config(height=440)
    app.bigListText = Text(bg="white")
    app.bigListText.place(x=10, y=200, height=180, width=405)
    app.addstepButton = Button(text="Add Step", command=lambda: addpulsestep(app.advancedPulseEntry.get(),
                                                                             app.advancedFrequencyEntry.get()))
    app.addstepButton.place(x=420, y=260, height=25, width=200)
    app.clearStepButton = Button(text="Clear Steps", command=clearsteps)
    app.clearStepButton.place(x=625, y=260, height=25, width=200)
    app.advancedPulseLabel = Label(text="Number of pulses")
    app.advancedPulseLabel.place(x=420, y=200, height=25, width=200)
    app.advancedPulseEntry = Entry()
    app.advancedPulseEntry.place(x=625, y=200, height=25, width=200)
    app.advancedFrequencyLabel = Label(text="Pulse frequency")
    app.advancedFrequencyLabel.place(x=420, y=230, height=25, width=200)
    app.advancedFrequencyEntry = Entry()
    app.advancedFrequencyEntry.place(x=625, y=230, height=25, width=200)
    app.advancedStartButton = Button(text="Start Sequence", command=advancedstart)
    app.advancedStartButton.place(x=420, y=290, height=25, width=200)
    app.advancedStopButton = Button(text="Abort Sequence", command=advancedabort)
    app.advancedStopButton.place(x=625, y=290, height=25, width=200)
    app.sequenceLabel = Label(text="")
    app.sequenceLabel.place(x=420, y=320, height=25, width=200)
    app.advancedStarttimeLabel = Label(text="")
    app.advancedStarttimeLabel.place(x=420, y=350, height=25, width=200)
    app.advancedDurationLabel = Label(text="")
    app.advancedDurationLabel.place(x=625, y=320, height=25, width=200)
    app.advancedStoptimeLabel = Label(text="")
    app.advancedStoptimeLabel.place(x=625, y=350, height=25, width=200)


def addpulsestep(numberofpulses, frequency):
    """Add one pair of pulses and frequency to the list, print the step in the GUI"""
    global pulseList
    pulseList.append((numberofpulses, frequency))
    app.bigListText.insert(END, ("Step %s: %s pulses at %s Hz\n" % (len(pulseList), numberofpulses, frequency)))


def clearsteps():
    """Clear the steplist and the GUI"""
    global pulseList
    pulseList = []
    app.bigListText.delete(1.0, END)


def advancedabort():
    """Abort the running sequence, clear all steps and send the stop command to the laser"""
    setlaseroff()
    clearsteps()


def advancedstart():
    """Start a complex pulse sequence"""
    setlaseron(pulseList[0][0], pulseList[0][1])
    global advancedFiring
    advancedFiring = True
    global advancedStep
    advancedStep = 0
    app.sequenceLabel.config(text="Sequence in progress: Step %s/%s" % (advancedStep+1, len(pulseList)))
    app.advancedStarttimeLabel.config(text="Start time:" + str(starttime.hour) + ":" + str(starttime.minute).zfill(2))

    seconds = 0
    for step in pulseList:
        seconds += float(step[0]) / float(step[1])
    duration = timedelta(seconds=seconds)
    app.advancedDurationLabel.config(text="Expected time remaining: " +
                                          str((duration.seconds // 3600)) + ":" +
                                          str((duration.seconds % 3600) // 60).zfill(2) + ":" +
                                          str(duration.seconds % 60).zfill(2))
    app.advancedStoptimeLabel.config(text=("Expected end time: " + str((starttime + duration).hour) + ":" +
                                           str((starttime + duration).minute).zfill(2)))


def disableadvanced():
    """Disable the advanced mode"""
    app.frame.config(height=195)


def setlaseroff():
    """Send a command to turn off the laser, clear the time labels in the GUI"""
    arduino.write("setLaserOff\n".encode())
    app.startTimeLabel.config(text="")
    app.stopTimeLabel.config(text="")
    app.etaLabel.config(text="")


def setlaserpaused():
    """Send a command to pause the laser"""
    arduino.write("setLaserPause\n".encode())


def setlasercontinue():
    """Send a command to continue the laser"""
    arduino.write("setLaserContinue\n".encode())


class App:
    """GUI for controlling the laser"""
    def __init__(self, master):
        self.frame = Frame(master, width=835, height=195)
        self.frame.pack()
        master.wm_title("Pulsar Laser Control")
        self.portLabel = Label(text="COM Port:")
        self.portLabel.place(x=10, y=10, width=200, height=25)
        self.portEntry = Entry(self.frame)
        self.portEntry.place(x=215, y=10, width=200, height=25)
        self.connectButton = Button(text="Connect Arduino", command=lambda: connectserial(self.portEntry.get()))
        self.connectButton.place(x=420, y=10, width=200, height=25)
        self.connectLabel = Label(text="Arduino not connected")
        self.connectLabel.place(x=625, y=10, width=200, height=25)
        self.label1 = Label(self.frame, text="Number of pulses:")
        self.label1.place(x=10, y=40, height=25, width=200)
        self.entryPulse = Entry(self.frame)
        self.entryPulse.place(x=215, y=70, height=25, width=200)
        self.label2 = Label(self.frame, text="Pulse frequency: ")
        self.label2.place(x=10, y=70, height=25, width=200)
        self.entryFreq = Entry(self.frame)
        self.entryFreq.place(x=215, y=40, height=25, width=200)
        self.startButton = Button(text="Start Laser",
                                  command=lambda: setlaseron(self.entryFreq.get(), self.entryPulse.get()))
        self.startButton.place(x=420, y=40, height=25, width=200)
        self.stopButton = Button(text="Stop Laser", command=setlaseroff)
        self.stopButton.place(x=625, y=40, height=25, width=200)
        self.pauseButton = Button(text="Pause Laser", command=setlaserpaused)
        self.pauseButton.place(x=420, y=70, height=25, width=200)
        self.contButton = Button(text="Continue Laser", command=setlasercontinue)
        self.contButton.place(x=625, y=70, height=25, width=200)
        self.statusLabel = Label(text="")
        self.statusLabel.place(x=10, y=100, height=25, width=405)
        self.pulseLabel = Label(text="")
        self.pulseLabel.place(x=420, y=100, height=25, width=405)
        self.startTimeLabel = Label(text="")
        self.startTimeLabel.place(x=10, y=130, height=25, width=200)
        self.stopTimeLabel = Label(text="")
        self.stopTimeLabel.place(x=215, y=130, height=25, width=200)
        self.etaLabel = Label(text="")
        self.etaLabel.place(x=420, y=130, height=25, width=405)
        self.exitButton = Button(text="Exit", command=root.destroy)
        self.exitButton.place(x=410, y=160, height=25, width=405)
        self.advancedButton = Button(text="Enable advanced mode", command=enableadvanced)
        self.advancedButton.place(x=10, y=160, height=25, width=200)
        self.simpleButton = Button(text="Disbale advanced mode", command=disableadvanced)
        self.simpleButton.place(x=215, y=160, height=25, width=200)


root = Tk()
app = App(root)


def handle_data(data):
    """Process incoming serial data and pass it to the GUI"""
    if data[0] == "u":
        pulselabeltext = "Fired %s of %s pulses." % (data.split(" ")[2], data.split(" ")[4])
        app.pulseLabel.config(text=pulselabeltext)
        eta = timedelta(seconds=((int(data.split(" ")[4]) - int(data.split(" ")[2])) / freq))

        app.stopTimeLabel.config(text=("Expected end time: " +
                                       str((datetime.now() + eta).hour) + ":" +
                                       str((datetime.now() + eta).minute).zfill(2)))

        app.etaLabel.config(text="Expected time remaining: " +
                                 str((eta.seconds//3600)) + ":" +
                                 str((eta.seconds % 3600)//60).zfill(2) + ":" +
                                 str(eta.seconds % 60).zfill(2))

    elif data[0] == "p":
        app.statusLabel.config(text=data.rstrip("\n")[1:])
        global advancedStep, advancedFiring
        if data[1] == "F" and advancedFiring and advancedStep + 1 < len(pulseList):
            advancedStep += 1
            setlaseron(pulseList[advancedStep][0], pulseList[advancedStep][1])
            app.sequenceLabel.config(text="Sequence in progress: Step %s/%s" % (advancedStep+1, len(pulseList)))
        elif data[1] == "F" and advancedStep+1 == len(pulseList):
            app.sequenceLabel.config(text="Sequence finished")
            advancedFiring = False
            clearsteps()

root.resizable(width=False, height=False)
root.mainloop()
