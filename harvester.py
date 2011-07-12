'''
harvester.py
Created on 09/07/2011
@author: Tim Sherratt (tim@discontents.com.au)

Provides a GUI for easy Trove newspaper harvesting.

Copyright (C) 2011 Tim Sherratt
This file is part of the TroveNewspapers package.

The TroveNewspapers package is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The TroveNewspapers package is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with the TroveNewspapers package. If not, see <http://www.gnu.org/licenses/>.
'''

from __future__ import with_statement
import wx, threading, Queue, sys, re, string, datetime, os
from wx.lib.newevent import NewEvent
import wx.html as html
import ConfigParser

import harvest
import icons
import help

ID_BEGIN = 100
wxStdOut, EVT_STDDOUT = NewEvent()
wxWorkerDone, EVT_WORKER_DONE = NewEvent()

def do_harvest(**kwargs):
    '''
    Initiate the harvest, log the details and display results.
    '''
    project_name = kwargs['project_name']
    directory = kwargs['directory']
    # Convert the project name to a valid filename
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = project_name.lower().replace(' ', '_')
    filename = ''.join(c for c in filename if c in valid_chars)
    cfg_file = os.path.join(directory, '%s.ini' % filename)
    log_file = os.path.join(directory, '%s.log' % filename)
    # Add datestamp to filename
    filename = '%s_%s.csv' % ( filename, datetime.datetime.now().strftime('%Y-%m-%d'))
    filename = os.path.join(directory, filename)
    query = kwargs['url']
    text = kwargs['text']
    pdf = kwargs['pdf']
    zip_dir = kwargs['zip_dir']
    start = '0'
    # Write the project config file.
    config = ConfigParser.RawConfigParser()
    config.add_section('harvest')
    config.set('harvest', 'project_name', project_name)
    config.set('harvest', 'directory', directory)
    config.set('harvest', 'query', query)
    config.set('harvest', 'text', text)
    config.set('harvest', 'pdf', pdf)
    config.set('harvest', 'order_by', zip_dir)
    config.set('harvest', 'start', start)
    with open(cfg_file, 'w') as configfile:
        config.write(configfile)
    # Write log entry
    status_message = '%s: Harvest commenced.\n' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    status_message += 'Project path: %s\n' % filename
    status_message += 'Query: %s\n' % query
    status_message += 'Starting at record number:%s' % start
    write_log_entry(log_file, status_message)
    # Create a harvest object and set it going
    harvester = harvest.TroveNewspapersHarvester()
    results = harvester.harvest(query, filename, start, text, pdf, zip_dir, gui=True)
    # If it's a successful harvest, display some details
    if not results['error'] or results['total'] == results['completed']:
        status_message = '%s: Harvest completed - %s of %s articles processed.' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), results['completed'], results['total'])
        write_log_entry(log_file, status_message)
        # Make sure start value is set back at 0
        config.set('harvest', 'start', 0)
        with open(cfg_file, 'w') as configfile:
            config.write(configfile)
    # If it was unsuccessful
    else:
        if results['completed'] > 0:
            #Print error
            status_message = '%s: Harvest interrupted - %s of %s articles processed.\n\n' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), results['completed'], results['total'])
            status_message += 'Error: %s\n' % results['error']
            write_log_entry(log_file, status_message)
            # Change the start value in config file and gui
            config.set('harvest', 'start', results['completed'])
            with open(cfg_file, 'w') as configfile:
                config.write(configfile)
            wx.GetApp().frame.start_at.SetValue(results['completed'])
            # Add extra message
            print '\nClick GO! to restart harvest.'
        else:
            status_message = '%s: Harvest failed.\n' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            status_message += 'Error: %s\n' % results['error']
            write_log_entry(log_file, status_message)

def write_log_entry(log_file, message):
    '''
    Write the supplied message both to standard output and to a log file.
    '''
    print message
    with open(log_file, 'a') as log:
        log.write(message)

class TextObjectValidator(wx.PyValidator):
    '''
    Validates text fields. First checks to make sure the field is not empty.
    Then if the 'url' flag has been passed, makes sure it's a Trove url.
    '''
    def __init__(self, flag):
        '''
        Standard constructor.
        '''
        wx.PyValidator.__init__(self)
        self.flag = flag

    def Clone(self):
        '''
        Every validator must implement the Clone() method.
        '''
        return TextObjectValidator(self.flag)


    def Validate(self, win):
        '''
        Validate the contents of the given text control.
        '''
        textCtrl = self.GetWindow()
        text = textCtrl.GetValue()
        # Make sure the field isn't empty.
        if len(text) == 0:
            wx.MessageBox("A text object must contain some text!", "Error")
            textCtrl.SetBackgroundColour("pink")
            textCtrl.SetFocus()
            textCtrl.Refresh()
            return False
        else:
            # Make sure urls look like Trove newspaper urls
            if self.flag == 'url':
                if not re.match('http://trove.nla.gov.au/newspaper/result', text):
                    wx.MessageBox("Please supply a valid Trove newspapers query.", "Error")
                    textCtrl.SetBackgroundColour("pink")
                    textCtrl.SetFocus()
                    textCtrl.Refresh()
                    return False
            textCtrl.SetBackgroundColour(
                wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
            return True


    def TransferToWindow(self):
        '''
        Transfer data from validator to window.
        '''
        return True # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        '''
        Transfer data from window to validator.
        '''
        return True # Prevent wxDialog from complaining.


class MainFrame(wx.Frame):
    '''
    The main harvester GUI.
    '''
    def __init__(self, parent, id, title):
        '''
        Create the GUI.
        '''
        wx.Frame.__init__(self, parent, id, title, size=(600, 550))
        #icon = wx.Icon('icons/small-news.png', wx.BITMAP_TYPE_PNG, 16, 16)
        wx.Frame.SetIcon(self, icons.getNewsSmallIcon())
        self.requestQ = Queue.Queue() #create queues
        self.resultQ = Queue.Queue()
        # Add menu
        menubar = wx.MenuBar()
        filemenu = wx.Menu()
        # File menu - Open and Exit
        menuOpen = wx.MenuItem(filemenu, wx.ID_OPEN, "&Open\tCtrl+O"," Open an existing project")
        #menuOpen.SetBitmap(wx.Bitmap('icons/document-open.png'))
        menuExit = wx.MenuItem(filemenu, wx.ID_EXIT,"E&xit\tCtrl+X"," Terminate the program")
        filemenu.AppendItem(menuOpen)
        filemenu.AppendItem(menuExit)
        menubar.Append(filemenu, '&File')
        # Help menu
        helpmenu = wx.Menu()
        menuAbout = helpmenu.Append(wx.ID_ABOUT, '&About', " Information about this program")
        menuHelp = helpmenu.Append(wx.ID_HELP, '&Help')
        menubar.Append(helpmenu, '&Help')
        
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.OnOpen, menuOpen)
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        self.Bind(wx.EVT_MENU, self.OnHelp, menuHelp)
        #Add the various widgets
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        # Project details box
        db = wx.StaticBox(panel, -1, label="Project details")
        vbox2 = wx.StaticBoxSizer(db, wx.VERTICAL)
        # Project name field
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        label_1 = wx.StaticText(panel, -1, label='Name:')
        hbox1.Add(label_1, flag=wx.RIGHT, border=10)
        self.project_name = wx.TextCtrl(panel,-1, validator = TextObjectValidator('text'))
        hbox1.Add(self.project_name, proportion=1)
        # Project folder selector
        hbox1.Add((10, -1))
        label_2 = wx.StaticText(panel, -1, label='Folder:')
        hbox1.Add(label_2, flag=wx.RIGHT|wx.LEFT, border=10)
        self.directory = wx.DirPickerCtrl(panel, -1)
        hbox1.Add(self.directory)
        vbox2.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        # Extra space
        vbox2.Add((-1, 10))
        # URL field
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        label_3 = wx.StaticText(panel, -1, label='Search URL:')
        hbox3.Add(label_3, flag=wx.RIGHT, border=8)
        self.url = wx.TextCtrl(panel, -1, validator = TextObjectValidator('url'))
        hbox3.Add(self.url, proportion=1)
        vbox2.Add(hbox3, proportion=1, flag=wx.EXPAND|wx.ALL, border=10)
        # Add the project details box
        vbox.Add(vbox2, flag=wx.EXPAND|wx.ALL, border=10)
        vbox.Add((-1, 10))
        # create options box
        sb = wx.StaticBox(panel, -1, label="Options")
        vbox3 =wx.StaticBoxSizer(sb, wx.VERTICAL)
        # Text checkbox
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        self.save_text = wx.CheckBox(panel, -1, label='Save text')
        hbox4.Add(self.save_text, flag=wx.ALL, border=10)
        # PDF checkbox
        self.save_pdf = wx.CheckBox(panel, -1, label='Save pdf')
        hbox4.Add(self.save_pdf, flag=wx.ALL, border=10)
        vbox3.Add(hbox4)
        # Order files by options
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        label_4 = wx.StaticText(panel, -1, label='Organise files by:')
        hbox5.Add(label_4, flag=wx.RIGHT, border=10)
        self.order_by = wx.ComboBox(panel, -1, choices=['year','newspaper'], value='year')
        hbox5.Add(self.order_by)
        vbox3.Add(hbox5, flag=wx.EXPAND|wx.ALL, border=10)
        # Start at
        hbox6 = wx.BoxSizer(wx.HORIZONTAL)
        label_5 = wx.StaticText(panel, -1, label='Start at result number:')
        hbox6.Add(label_5, flag=wx.RIGHT, border=10)
        self.start_at = wx.TextCtrl(panel, -1, value='0')
        hbox6.Add(self.start_at)
        vbox3.Add(hbox6, flag=wx.EXPAND|wx.ALL, border=10)
        # Add the options box
        vbox.Add(vbox3, flag=wx.EXPAND|wx.ALL, border=10)
        vbox.Add((-1, 10))
        # Add the GO! button
        hbox7 = wx.BoxSizer(wx.HORIZONTAL)
        self.go = wx.Button(panel, ID_BEGIN, 'GO!')
        hbox7.Add(self.go)
        vbox.Add(hbox7, flag=wx.ALIGN_RIGHT|wx.RIGHT, border=10)
        # Extra space
        vbox.Add((-1, 10))
        # Create the status box
        sm = wx.StaticBox(panel, -1, label="Status")
        vbox4 = wx.StaticBoxSizer(sm, wx.VERTICAL)
        # Add text area to contain status updates
        hbox9 = wx.BoxSizer(wx.HORIZONTAL)
        self.output_window = wx.TextCtrl(panel, -1, style=wx.TE_AUTO_SCROLL|wx.TE_MULTILINE|wx.TE_READONLY)
        hbox9.Add(self.output_window, proportion=1, flag=wx.EXPAND)
        vbox.Add(vbox4, flag=wx.EXPAND|wx.ALL, border=10)
        vbox4.Add(hbox9, proportion=1, flag=wx.ALL|wx.EXPAND, border=10)
        # Extra space
        vbox.Add((-1, 10))
        # Add all the widgets to the panel
        panel.SetSizer(vbox)
        # Create a timer for status updates
        self.output_window_timer = wx.Timer(self.output_window, -1)
        # Events
        wx.EVT_BUTTON(self, ID_BEGIN, self.OnBegin)
        self.output_window.Bind(EVT_STDDOUT, self.OnUpdateOutputWindow)
        self.output_window.Bind(wx.EVT_TIMER, self.OnProcessPendingOutputWindowEvents)
        self.Bind(EVT_WORKER_DONE, self.OnWorkerDone)
        # Thread
        self.worker = Worker(self, self.requestQ, self.resultQ)

    def OnUpdateOutputWindow(self, event):
        '''
        Update the status box.
        '''
        value = event.text
        self.output_window.AppendText(value)

    def OnBegin(self, event):
        '''
        Gets the parameters from the form and sends them off to the worker thread.
        '''
        if self.project_name.GetValidator().Validate(self.project_name) and self.url.GetValidator().Validate(self.url):
            # Disable the GO button
            self.go.Disable()
            # Get the harvest parameters
            params = {}
            params['project_name'] = self.project_name.GetValue()
            params['directory'] = self.directory.GetPath()
            params['url'] = self.url.GetValue()
            params['text'] = self.save_text.GetValue()
            params['pdf'] = self.save_pdf.GetValue()
            params['zip_dir'] = self.order_by.GetValue()
            # Start the worker thread
            self.worker.begin(do_harvest, **params)
            # Start the timer for status updates
            self.output_window_timer.Start(50)

    def OnWorkerDone(self, event):
        '''
        Clean things up when the worker thread has finished.
        '''
        # Stop the timer
        self.output_window_timer.Stop()
        # Re-enable the GO button.
        self.go.Enable()

    def OnProcessPendingOutputWindowEvents(self, event):
        '''
        Process status updates.
        '''
        self.output_window.ProcessPendingEvents()
    
    def OnOpen(self, event):
        '''
        Open an existing project config file and update the form with the values.
        '''
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.ini", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            config = ConfigParser.RawConfigParser()
            config.read(os.path.join(self.dirname, self.filename))
            self.project_name.SetValue(config.get('harvest', 'project_name'))
            self.url.SetValue(config.get('harvest', 'query'))
            self.directory.SetPath(config.get('harvest', 'directory'))
            self.save_text.SetValue(config.getboolean('harvest', 'text'))
            self.save_pdf.SetValue(config.getboolean('harvest', 'pdf'))
            self.order_by.SetValue(config.get('harvest', 'order_by'))
        dlg.Destroy()
        
    def OnAbout(self,e):
        '''
        Create a nifty looking About dialog box.
        '''
        licence_text = '''
The Trove Newspaper Harvester is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The Trove Newspaper Harvester is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with the TroveNewspapers package. If not, see <http://www.gnu.org/licenses/>.
'''
        description = 'A research tool to harvest newspaper data from Trove.'
        info = wx.AboutDialogInfo()
        info.SetIcon(icons.getNewsIcon())
        info.SetName('Trove Newspaper Harvester')
        info.SetVersion('0.9')
        info.SetDescription(description)
        info.SetWebSite('http://www.wraggelabs.com/emporium')
        info.SetLicence(licence_text)
        info.AddDeveloper('Tim Sherratt (tim@discontents.com.au)')
        wx.AboutBox(info)
        
    def OnHelp(self, event):
        dlg = HelpWindow(None)
        dlg.Show()

    def OnExit(self, event):
        '''
        Close the Harvester.
        '''
        self.Close(True)

class HelpWindow(wx.Frame):
 
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title="Trove Newspaper Harvester -- Help", size=(400,400))
        wx.Frame.SetIcon(self, icons.getNewsSmallIcon())
        toolbar = self.CreateToolBar()
        #toolbar.AddLabelTool(1, 'Exit', wx.Bitmap('icons/system-log-out.png'))
        toolbar.AddLabelTool(1, 'Exit', icons.getExitBitmap())
        toolbar.Realize()
        htmlWin = html.HtmlWindow(self, -1)
        htmlWin.SetPage(help.help_text)
        self.Bind(wx.EVT_TOOL, self.OnClose, id=1)
        
    def OnClose(self, event):
        self.Close(True)

class Worker(threading.Thread):
    '''
    Worker thread to run the actual harvest.
    '''
    requestID = 0
    def __init__(self, parent, requestQ, resultQ, **kwds):
        threading.Thread.__init__(self, **kwds)
        self.setDaemon(True)
        self.requestQ = requestQ
        self.resultQ = resultQ
        self.start()

    def begin(self, callable, *args, **kwds):
        Worker.requestID +=1
        self.requestQ.put((Worker.requestID, callable, args, kwds))
        return Worker.requestID

    def run(self):
        while True:
            requestID, callable, args, kwds = self.requestQ.get()
            self.resultQ.put((requestID, callable(*args, **kwds)))
            evt = wxWorkerDone()
            wx.PostEvent(wx.GetApp().frame, evt)

class SysOutListener:
    def write(self, string):
        sys.__stdout__.write(string)
        evt = wxStdOut(text=string)
        wx.PostEvent(wx.GetApp().frame.output_window, evt)

class HarvesterApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None, -1, 'Trove newspaper harvester')
        self.frame.Show(True)
        self.frame.Centre()
        return True

#entry point
if __name__ == '__main__':
    app = HarvesterApp(0)
    sys.stdout = SysOutListener()
    app.MainLoop()