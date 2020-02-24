from datetime import datetime, timedelta
from time import sleep

from pubsub.pub import subscribe, sendMessage, unsubscribe
from serial import Serial, SerialException

from ThreadDecorators import in_new_thread


class Pulsarino(Serial):
    def __init__(self, port=None):
        super().__init__(port, timeout=1)
        self.port = port

        self.laser_state = "Off"
        self.fired_pulses = 0
        self.total_pulses = 0
        self.frequency = 0

        self.start_time = None
        self.stop_time = None
        self.eta = None

        subscribe(topicName='gui.con.connect', listener=self.connect)
        subscribe(topicName='gui.con.disconnect', listener=self.disconnect)

    def connect(self, port=None):
        if port:
            self.port = port

        if not self.is_open:
            try:
                self.open()
            except SerialException:
                sendMessage(topicName='engine.status', text='Port could not be connected')

        sleep(2)

        self.write('#Py to Pulsar'.encode())
        self.write(b'\0xD')

        sleep(0.5)

        response = self.readline().decode()

        if response == 'Pulsar to Py\r\n':
            subscribe(topicName='gui.laser.start', listener=self.start_laser)
            subscribe(topicName='gui.laser.stop', listener=self.stop_laser)
            subscribe(topicName='gui.laser.pause', listener=self.pause_laser)
            subscribe(topicName='gui.laser.cont', listener=self.continue_laser)
            subscribe(topicName='gui.request_status', listener=self.update_status)

            sendMessage(topicName='engine.status', text='Pulsarino connected!')

        else:
            sendMessage(topicName='engine.status', text='Pulsarino not found!')

    def disconnect(self):
        unsubscribe(topicName='gui.laser.start', listener=self.start_laser)
        unsubscribe(topicName='gui.laser.stop', listener=self.stop_laser)
        unsubscribe(topicName='gui.laser.pause', listener=self.pause_laser)
        unsubscribe(topicName='gui.laser.cont', listener=self.continue_laser)
        unsubscribe(topicName='gui.request_status', listener=self.update_status)

        sendMessage(topicName='engine.status', text='Pulsarino disconnected!')
        self.close()

    @in_new_thread
    def start_laser(self, pulse_count, frequency):

        self.frequency = frequency
        self.total_pulses = pulse_count

        string = '#startp{:d}f{:.1f}'.format(pulse_count, frequency)
        self.write(string.encode())
        self.write(b'\x0D')

        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=pulse_count/frequency)

        response = self.readline().decode()

        if response == '#start,{:d},{:.1f}\r\n'.format(pulse_count, frequency):
            string = 'Laser started! Firing {:d} pulses at {:.1f} Hz!'.format(pulse_count, frequency)
            sendMessage(topicName='engine.status', text=string)
            sendMessage(topicName='engine.started', start=start_time.strftime('%H:%M:%S'),
                        end=end_time.strftime('%H:%M:%S'))
        else:
            sendMessage(topicName='engine.status', text='Communication error!')

    @in_new_thread
    def stop_laser(self):

        self.total_pulses = 0

        string = '#stop'
        self.write(string.encode())
        self.write(b'\x0D')

        stop_time = datetime.now()

        response = self.readline().decode()

        if response == '#stop\r\n':
            sendMessage(topicName='engine.status', text='Laser stopped!')
            sendMessage(topicName='engine.stopped', stop=stop_time.strftime('%H:%M:%S'))
        else:
            sendMessage(topicName='engine.status', text='Communication error!')

    @in_new_thread
    def pause_laser(self):
        string = '#pause'
        self.write(string.encode())
        self.write(b'\x0D')

        response = self.readline().decode()

        if response == '#pause\r\n':
            sendMessage(topicName='engine.status', text='Laser paused!')
        else:
            sendMessage(topicName='engine.status', text='Communication error!')

    @in_new_thread
    def continue_laser(self):
        string = '#cont'
        self.write(string.encode())
        self.write(b'\x0D')

        response = self.readline().decode()

        if response == '#cont\r\n':
            sendMessage(topicName='engine.status', text='Laser continued!')
        else:
            sendMessage(topicName='engine.status', text='Communication error!')

    @in_new_thread
    def update_status(self):
        string = '#update'
        self.write(string.encode())
        self.write(b'\x0D')

        response = self.readline().decode().split(',')

        self.fired_pulses = int(response[1])
        self.total_pulses = int(response[2])

        if response[0] == '#nfire':
            self.laser_state = 'Off'

            sendMessage(topicName='engine.answer_status', status=self.laser_state, fired=self.fired_pulses,
                        total=self.total_pulses, eta=None)

        else:
            self.laser_state = 'On'
            remain_sec = int((self.total_pulses-self.fired_pulses) / self.frequency)
            self.eta = timedelta(seconds=remain_sec)

            sendMessage(topicName='engine.answer_status', status=self.laser_state, fired=self.fired_pulses,
                        total=self.total_pulses, eta='{:0>8s}'.format(str(self.eta)))
