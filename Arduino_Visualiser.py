import os
import pprint
import random
import sys
import wx
import time

REFRESH_INTERVAL_MS = 1

# The recommended way to use wx with mpl is with the WXAgg
# backend.
#
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import numpy as np
import pylab
#Data comes from here
from Arduino_Interfacer import ArduinoData as DataGen

class ControlPanel(wx.Panel):
    def __init__(self, parent, ID, label, init_val):
        wx.Panel.__init__(self, parent, ID)
        
        self.value = init_val
        
        
        self.manual_text = wx.TextCtrl(self, -1,
            size=(35,-1),
            value=str(init_val),
            style=wx.TE_PROCESS_ENTER)
        
        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter, self.manual_text)
    
    def on_text_enter(self, event):
        self.value = self.manual_text.GetValue()
        
    def manual_value(self):
        return self.value
        
        


class GraphFrame(wx.Frame):
    title = 'Demo: dynamic matplotlib graph'
    def __init__(self):
        wx.Frame.__init__(self, None, -1, self.title)
        
        self.data = DataGen()
        
        self.xdata = [0]
        self.ydata = [0]
        self.paused = False
        
        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()
        
        print "Starting visualiser..."
        self.start_time = time.time()
        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        self.redraw_timer.Start(REFRESH_INTERVAL_MS)
        

    def create_menu(self):
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
                
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def create_main_panel(self):
        self.panel = wx.Panel(self)

        self.init_plot()
        self.canvas = FigCanvas(self.panel, -1, self.fig)

        self.pause_button = wx.Button(self.panel, -1, "Pause")
        self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)
        
        self.cb_grid = wx.CheckBox(self.panel, -1,
            "Show Grid",
            style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)
        self.cb_grid.SetValue(True)
        
        self.xlen_control = ControlPanel(self.panel, -1, "x_len", 4)
        
        self.xlen_ctrl_text = wx.StaticText(self.panel, -1, "Set x axis time:")
        self.xlen_ctrl_text.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.BOLD))
        self.xlen_ctrl_text.SetSize(self.xlen_ctrl_text.GetBestSize())
        
        
        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.cb_grid, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.xlen_ctrl_text,0,wx.ALL,10)
        self.hbox1.Add(self.xlen_control, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)
        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
    
    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()

    def init_plot(self):
        self.dpi = 100
        self.fig = Figure((5.0, 3.0), dpi=self.dpi)

        self.axes = self.fig.add_subplot(111)
        self.axes.set_axis_bgcolor('black')
        self.axes.set_title('Arduino Serial Data', size=12)
        
        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)

        # plot the data as a line series, and save the reference
        # to the plotted line series
        #
        self.plot_data = self.axes.plot(
            self.xdata,self.ydata,
            linewidth=1,
            color=(1, 1, 0),
            )[0]

    def draw_plot(self):
        try:
            x_len = float(self.xlen_control.manual_value())
        except ValueError:
            x_len = 4

        t_max = self.xdata[-1]
        if t_max > x_len:
            xmax = t_max
            xmin = t_max - x_len
        else:
            xmax = x_len
            xmin = 0
        
        ymax = 5.5
        ymin = -0.5

        self.axes.set_xbound(lower=xmin, upper=xmax)
        self.axes.set_ybound(lower=ymin, upper=ymax)
        
        if self.cb_grid.IsChecked():
            self.axes.grid(True, color='gray')
        else:
            self.axes.grid(False)
        
        self.plot_data.set_xdata(self.xdata)
        self.plot_data.set_ydata(self.ydata)
        
        self.canvas.draw()
    
    def on_pause_button(self, event):
        self.paused = not self.paused
    
    def on_update_pause_button(self, event):
        label = "Resume" if self.paused else "Pause"
        self.pause_button.SetLabel(label)
    
    def on_cb_grid(self, event):
        self.draw_plot()
    
    def on_cb_xlab(self, event):
        self.draw_plot()
    
    def on_save_plot(self, event):
        file_choices = "PNG (*.png)|*.png"
        
        dlg = wx.FileDialog(
            self,
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)
    
    def on_redraw_timer(self, event):
        # if paused do not add data, but still redraw the plot
        # (to respond to scale modifications, grid change, etc.)
        if not self.paused:
            y_buffer_draw = self.data.get_data()
            self.data.clear_buffer()
            y_len = len(y_buffer_draw)
            current_time = time.time() - self.start_time
            last_time = self.xdata[-1]
            t_int = (current_time - last_time) / y_len
            for y in y_buffer_draw:
                self.ydata.append(y)
            x_buffer_draw = np.arange(last_time + t_int, 
                current_time + t_int, 
                t_int)
            for x in x_buffer_draw:
                self.xdata.append(x)
            if len(self.ydata) > len(self.xdata):
                lendiff = len(self.ydata) - len(self.xdata)
                del self.ydata[0:lendiff]
            if len(self.xdata) > len(self.ydata):
                lendiff = len(self.xdata) - len(self.ydata)
                del self.xdata[0:lendiff]
            if len(self.xdata) > 5000:
                self.xdata = self.xdata[-5001:-1]
                self.ydata = self.ydata[-5001:-1]
        self.draw_plot()
    
    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(
            wx.EVT_TIMER,
            self.on_flash_status_off,
            self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)
    
    def on_flash_status_off(self, event):
        self.statusbar.SetStatusText('')


if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = GraphFrame()
    app.frame.Show()
    app.MainLoop()

