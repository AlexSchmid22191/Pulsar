import wx
from pubsub.pub import subscribe, sendMessage
from serial.tools.list_ports import comports

from ThreadDecorators import in_main_thread


class PulsarGUI(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER, *args, **kwargs)

        self.SetBackgroundColour('white')

        # Menu Bar
        self.menu_bar = Menubar()
        self.SetMenuBar(self.menu_bar)
        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_CLOSE)

        # Status Bar
        self.status_bar = self.CreateStatusBar()
        self.clear_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, source=self.clear_timer, handler=self.clear_status_bar)
        subscribe(listener=self.update_status_bar, topicName='engine.status')

        # Main Sizer
        self.control_panel = ControlGrid(parent=self)
        self.status_panel = StatusGrid(parent=self)

        main_sizer = wx.BoxSizer(orient=wx.VERTICAL)
        main_sizer.Add(self.control_panel, flag=wx.EXPAND | wx.ALL, border=5)
        main_sizer.Add(self.status_panel, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(main_sizer)

        main_sizer.Fit(self)
        self.SetMaxSize(self.GetSize())
        self.SetMinSize(self.GetSize())
        self.Show()

    @in_main_thread
    def update_status_bar(self, text):
        """Display a text on the status bar for 3 secons"""
        self.status_bar.SetStatusText(text)
        self.clear_timer.Start(milliseconds=3000, oneShot=wx.TIMER_ONE_SHOT)

    def clear_status_bar(self, *args):
        self.status_bar.SetStatusText('')

    def on_quit(self, *args):
        self.Close()


class Menubar(wx.MenuBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        filemenu = wx.Menu()
        filemenu.Append(item='Quit', id=wx.ID_CLOSE)

        self.com_menu = PortMenu()

        self.Append(filemenu, 'File')
        self.Append(self.com_menu, 'Serial Connection')


class StatusGrid(wx.Panel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.timer = wx.Timer()
        self.timer.Bind(event=wx.EVT_TIMER, handler=self.request_status)
        self.timer.Start(milliseconds=1000)

        subscribe(topicName='engine.answer_status', listener=self.update_status)
        subscribe(topicName='engine.started', listener=self.update_started)
        subscribe(topicName='engine.stopped', listener=self.update_stopped)

        self.status_label_desc = wx.StaticText(parent=self, label='Fired pulses: ')
        self.status_label_val = wx.StaticText(parent=self, label='--/--')
        self.start_label_desc = wx.StaticText(parent=self, label='Start time: ')
        self.start_label_val = wx.StaticText(parent=self, label='--:--:--')
        self.eta_label_desc = wx.StaticText(parent=self, label='Remaining: ')
        self.eta_label_val = wx.StaticText(parent=self, label='--:--:--')
        self.end_label_desc = wx.StaticText(parent=self, label='End time: ')
        self.end_label_val = wx.StaticText(parent=self, label='--:--:--')

        status_grid = wx.GridSizer(rows=2, cols=4, vgap=5, hgap=5)

        status_grid.Add(self.status_label_desc, flag=wx.ALIGN_CENTER_VERTICAL, proportion=1)
        status_grid.Add(self.status_label_val, flag=wx.ALIGN_CENTER_VERTICAL, proportion=1)
        status_grid.Add(self.start_label_desc, flag=wx.ALIGN_CENTER_VERTICAL, proportion=1)
        status_grid.Add(self.start_label_val, flag=wx.ALIGN_CENTER_VERTICAL, proportion=1)
        status_grid.Add(self.eta_label_desc, flag=wx.ALIGN_CENTER_VERTICAL, proportion=1)
        status_grid.Add(self.eta_label_val, flag=wx.ALIGN_CENTER_VERTICAL, proportion=1)
        status_grid.Add(self.end_label_desc, flag=wx.ALIGN_CENTER_VERTICAL, proportion=1)
        status_grid.Add(self.end_label_val, flag=wx.ALIGN_CENTER_VERTICAL, proportion=1)

        self.red_laser_image = wx.Image(name='Icons/Laser_Red.png', type=wx.BITMAP_TYPE_ANY).\
            Scale(width=50, height=50, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
        self.green_laser_image = wx.Image(name='Icons/Laser_Green.png', type=wx.BITMAP_TYPE_ANY).\
            Scale(width=50, height=50, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()

        self.laser_icon = wx.StaticBitmap(parent=self, bitmap=self.red_laser_image)

        box = wx.StaticBox(parent=self, label='Laser status')
        status_sizer = wx.StaticBoxSizer(box, orient=wx.HORIZONTAL)
        status_sizer.Add(status_grid, border=5, flag=wx.EXPAND | wx.ALL, proportion=1)
        status_sizer.Add(self.laser_icon, border=5, flag=wx.GROW | wx.ALL)

        status_sizer.Fit(self)

        self.SetSizer(status_sizer)

    def request_status(self, *args):
        sendMessage(topicName='gui.request_status')
        self.timer.Start(1000)

    @in_main_thread
    def update_status(self, status, fired, total, eta):
        self.status_label_val.SetLabel('{:d}/{:d}'.format(fired, total))

        if status == 'Off':
            self.eta_label_val.SetLabel('--:--:--')
            self.laser_icon.SetBitmap(self.red_laser_image)
        else:
            self.eta_label_val.SetLabel(eta)
            self.laser_icon.SetBitmap(self.green_laser_image)

    @in_main_thread
    def update_started(self, start, end):
        self.start_label_val.SetLabel(start)
        self.end_label_val.SetLabel(end)

    @in_main_thread
    def update_stopped(self, stop):
        self.end_label_val.SetLabel(stop)


class ControlGrid(wx.Panel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Grid for entries
        self.pulse_entry = wx.SpinCtrl(parent=self, value='0', min=0, max=1e6, style=wx.SP_ARROW_KEYS, size=(70, -1))
        self.freq_entry = wx.SpinCtrlDouble(parent=self, value='0', min=0, max=15, inc=0.1, style=wx.SP_ARROW_KEYS, size=(70, -1))

        pulse_label = wx.StaticText(parent=self, label='Pulses')
        freq_label = wx.StaticText(parent=self, label='Frequency (Hz)')

        entry_sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)

        entry_sizer.Add(pulse_label, flag=wx.ALIGN_CENTER_VERTICAL)
        entry_sizer.Add(self.pulse_entry, flag=wx.ALIGN_CENTER_VERTICAL)
        entry_sizer.Add(freq_label, flag=wx.ALIGN_CENTER_VERTICAL)
        entry_sizer.Add(self.freq_entry, flag=wx.ALIGN_CENTER_VERTICAL)

        # Grid for Buttons
        self.start_button = wx.Button(parent=self, label='Start')
        self.stop_button = wx.Button(parent=self, label='Stop')
        self.pause_button = wx.Button(parent=self, label='Pause')
        self.continue_button = wx.Button(parent=self, label='Resume')

        self.start_button.Bind(event=wx.EVT_BUTTON, source=self.start_button, handler=self.start_laser)
        self.stop_button.Bind(event=wx.EVT_BUTTON, source=self.stop_button, handler=self.stop_laser)
        self.pause_button.Bind(event=wx.EVT_BUTTON, source=self.pause_button, handler=self.pause_laser)
        self.continue_button.Bind(event=wx.EVT_BUTTON, source=self.continue_button, handler=self.continue_laser)

        button_sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)

        button_sizer.Add(self.start_button, flag=wx.EXPAND, proportion=1)
        button_sizer.Add(self.stop_button, flag=wx.EXPAND, proportion=1)
        button_sizer.Add(self.pause_button, flag=wx.EXPAND, proportion=1)
        button_sizer.Add(self.continue_button, flag=wx.EXPAND, proportion=1)

        # Static Box Sizer for Laser Control
        box = wx.StaticBox(parent=self, label='Laser control')
        control_sizer = wx.StaticBoxSizer(box, orient=wx.HORIZONTAL)

        control_sizer.Add(entry_sizer, flag=wx.ALL, border=5)
        control_sizer.Add(button_sizer, flag=wx.ALL, border=5)
        control_sizer.Fit(self)

        self.SetSizer(control_sizer)

    def start_laser(self, *args):
        sendMessage(topicName='gui.laser.start', pulse_count=self.pulse_entry.GetValue(),
                    frequency=self.freq_entry.GetValue())

    @staticmethod
    def stop_laser(*args):
        sendMessage(topicName='gui.laser.stop')

    @staticmethod
    def pause_laser(*args):
        sendMessage(topicName='gui.laser.pause')

    @staticmethod
    def continue_laser(*args):
        sendMessage(topicName='gui.laser.cont')


class PortMenu(wx.Menu):
    def __init__(self):
        super().__init__()

        self.selected_port = None

        self.refresh_item = wx.MenuItem(id=wx.ID_ANY, text='Refresh')
        self.Append(self.refresh_item)

        self.AppendSeparator()

        self.portdict = {port[1]: port[0] for port in comports()}
        self.portItems = [wx.MenuItem(parentMenu=self, id=wx.ID_ANY, text=port, kind=wx.ITEM_RADIO)
                          for port in list(self.portdict.keys())]

        for item in self.portItems:
            self.Append(item)

        self.AppendSeparator()

        self.connect = self.Append(id=wx.ID_ANY, item='Connect', kind=wx.ITEM_CHECK)

        self.Bind(event=wx.EVT_MENU, handler=self.connect_handler, source=self.connect)
        self.Bind(event=wx.EVT_MENU, handler=self.refresh, source=self.refresh_item)

    def connect_handler(self, event):
        """Open or close the serial connection to the faradino"""
        item = self.FindItemById(event.GetId())
        if item.IsChecked():
            for port_item in self.portItems:
                if port_item.IsChecked():
                    port = self.portdict[port_item.GetItemLabelText()]
                    sendMessage(topicName='gui.con.connect', port=port)
        else:
            sendMessage(topicName='gui.con.disconnect')

    def refresh(self, *args):
        for item in self.portItems:
            self.DestroyItem(item)

        self.portdict = {port[1]: port[0] for port in comports()}
        self.portItems = [wx.MenuItem(parentMenu=self, id=wx.ID_ANY, text=port, kind=wx.ITEM_RADIO)
                          for port in list(self.portdict.keys())]

        for item in self.portItems:
            self.Insert(2, item)
