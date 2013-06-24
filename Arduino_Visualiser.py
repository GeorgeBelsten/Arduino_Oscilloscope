"""
Plots the data from the Arduino board over time. 

Requires Arduino_Interfacer.py in the same directory to run. 

This is a wxPython application. It allows you to pause/resume the 
plotting, enable or disable the grid, set manual values for the length of 
the x (time) axis and the maximum/minimum boundaries of the y axis.

This program is a significantly modified version of a dynamic plotting 
application produced by Eli Bendersky. Modifications were performed by 
George Belsten and Thomas Laird.
Last Modified: 24 June 2013
"""

import os
import pprint
import random
import sys
import wx
import time
from threading import Thread

# The recommended way to use wx with matplotlib is with the WXAgg backend
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import numpy as np
import pylab

# Import data generator from the Interfacer script
from Arduino_Interfacer import ArduinoData as DataGen


class ControlPanel(wx.Panel):
    """Used for creating manual variable control input boxes"""
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
    """Creates the graph frame and continuously plots the data from the
        Arduino board"""
    title = 'Arduino Oscilloscope'
    def __init__(self):
        wx.Frame.__init__(self, None, -1, self.title)
        # Set initial time axis length
        self.initial_xlen = 3
        
        # Start data generator
        self.data = DataGen()
        
        # Create lists to store x and y data
        self.xdata = [0]
        self.ydata = [0]
        self.paused = False
        
        # Create visualiser UI
        print "Loading visualiser..."
        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()
        
        # Delay for one second; prevents errors that occur when the
        # thread attempts to draw the graph before the UI is fully loaded
        time.sleep(1)
        
        print "Opening visualiser..."
        # Start timer for refreshing graph
        self.start_time = time.time()
        # Open thread to continuously redraw graph
        Thread(target=self.refresh_graph, args=()).start()
        

    def create_menu(self):
    """Creates a menu with an option to save the plot"""
        self.menubar = wx.MenuBar()
        
        # Create save option
        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
                
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def create_main_panel(self):
    """Creates the aplication's main window"""
        self.panel = wx.Panel(self)
        
        # Create graph plot
        self.init_plot()
        self.canvas = FigCanvas(self.panel, -1, self.fig)

        # Create pause button
        self.pause_button = wx.Button(self.panel, -1, "Pause")
        self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)
        
        # Create show grid checkbox
        self.cb_grid = wx.CheckBox(self.panel, -1,
            "Show Grid",
            style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)
        self.cb_grid.SetValue(True)
        
        # Create box to control length of x axis
        self.xlen_control = ControlPanel(self.panel, -1, "x_len", self.initial_xlen)
        self.xlen_ctrl_text = wx.StaticText(self.panel, -1, "Set x axis length:")
        self.xlen_ctrl_text.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.BOLD))
        self.xlen_ctrl_text.SetSize(self.xlen_ctrl_text.GetBestSize())
        
        # Create boxes to control limits of y axis
        self.ymin_control = ControlPanel(self.panel, -1, "y_min", -0.1)
        self.ymax_control = ControlPanel(self.panel, -1, "y_max", 5.1)
        self.ylim_ctrl_text = wx.StaticText(self.panel, -1, "Set y axis limits:")
        self.ylim_ctrl_text.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.BOLD))
        self.ylim_ctrl_text.SetSize(self.ylim_ctrl_text.GetBestSize())
        
        # Set position of UI elements
        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.cb_grid, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.xlen_ctrl_text,0,wx.ALL,10)
        self.hbox1.Add(self.xlen_control, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.ylim_ctrl_text,0,wx.ALL,10)
        self.hbox1.Add(self.ymin_control, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.Add(self.ymax_control, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)
        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
    
    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()

    def init_plot(self):
    """Initialises the graph plot"""
        self.dpi = 100
        self.fig = Figure((10.0, 5.0), dpi=self.dpi)

        self.axes = self.fig.add_subplot(111)
        self.axes.set_axis_bgcolor('black')
        self.axes.set_title('Arduino Oscilloscope Data', size=12)
        self.axes.set_xlabel('Time /s', size=10)
        self.axes.set_ylabel('Voltage /V', size=10)
        
        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)

        # Plot data as a line
        self.plot_data = self.axes.plot(
            self.xdata,self.ydata,
            linewidth=1,
            color=(1, 1, 0),
            )[0]

    def draw_plot(self):
    """Re-draws the graph plot."""
        # Obtain manually set value for x axis length
        try:
            x_len = float(self.xlen_control.manual_value())
        except ValueError:
            x_len = self.initial_xlen

        # Set maximum x axis value equal to maximum x point,
        # with x axis length equal to x_len
        t_max = self.xdata[-1]
        if t_max > x_len:
            xmax = t_max
            xmin = t_max - x_len
        else:
            xmax = x_len
            xmin = 0
        
        # Obtain manually set values for y axis limits
        try:
            ymax = float(self.ymax_control.manual_value())
        except ValueError:
            ymax = 5.5
        try:
            ymin = float(self.ymin_control.manual_value())
        except ValueError:
            ymin = -0.5

        # Set graph boundaries
        self.axes.set_xbound(lower=xmin, upper=xmax)
        self.axes.set_ybound(lower=ymin, upper=ymax)
        
        # Draws grid if "Show grid" is checked
        if self.cb_grid.IsChecked():
            self.axes.grid(True, color='gray')
        else:
            self.axes.grid(False)
            
        # Set x and y data
        self.plot_data.set_xdata(self.xdata)
        self.plot_data.set_ydata(self.ydata)
        
        # Redraw the plot
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
    
    def refresh_graph(self):
    """Pulls new data from the interfacer and re-draws the plot."""
        while True:
            # if paused do not add data, but still redraw the plot
            # (to respond to manual control changes)
            
            if not self.paused:
                # Pull the data from the interfacer data buffer
                y_buffer_draw = self.data.get_data()
                
                # Calculate length of data buffer
                y_len = len(y_buffer_draw)
                
                # Only attempt to update data if there is new data
                if not y_len == 0:
                    # Calculate the time difference from last redraw,
                    # and estimate time values for each y data point
                    current_time = time.time() - self.start_time
                    last_time = self.xdata[-1]
                    t_int = (current_time - last_time) / y_len
                    
                    # Add new data values to data lists
                    for y in y_buffer_draw:
                        self.ydata.append(y)
                    x_buffer_draw = np.arange(last_time + t_int, 
                        current_time + t_int, 
                        t_int)
                    for x in x_buffer_draw:
                        self.xdata.append(x)
                        
                    # Correct length of data lists if there is a difference
                    if len(self.ydata) > len(self.xdata):
                        lendiff = len(self.ydata) - len(self.xdata)
                        del self.ydata[0:lendiff]
                    if len(self.xdata) > len(self.ydata):
                        lendiff = len(self.xdata) - len(self.ydata)
                        del self.xdata[0:lendiff]
                        
                    # Limit length of data lists to maintain performance
                    if len(self.xdata) > 10000:
                        self.xdata = self.xdata[-10000:-1]
                        self.ydata = self.ydata[-10000:-1]
                        
            # Redraw the plot
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

