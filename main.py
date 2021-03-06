import ctypes
import os
import shutil
import subprocess
import sys
from threading import Thread

import requests
from requests.exceptions import ConnectionError
import wx
from wx import Size, Point

# Installer configuration
REPO_URL = "https://alexisdelhaie.ovh/dlcenter/chronos-repo/installer/"
VERSION_FILE = "version"
COMPANY_NAME = "alexlegarnd"
SOFTWARE_NAME = "chronos-installer"
CACHE_FOLDER = "cache"
INSTALL_FOLDER = "{}\\{}\\{}".format(os.getenv('APPDATA'), COMPANY_NAME, SOFTWARE_NAME)
CACHE_FOLDER_PATH = "{}\\{}".format(INSTALL_FOLDER, CACHE_FOLDER)
INSTALLED_VERSION_PATH = "{}\\{}".format(INSTALL_FOLDER, VERSION_FILE)
EXECUTABLE = "Install.exe"
EXECUTABLE_PATH = "{}\\{}".format(INSTALL_FOLDER, EXECUTABLE)
FILES = ["libeay32.dll", "ssleay32.dll", "7z.dll", EXECUTABLE]
WINDOW_TITLE = "Chronos Installer"


EVT_START_ID = wx.Window.NewControlId()
EVT_UPDATE_ID = wx.Window.NewControlId()
EVT_END_ID = wx.Window.NewControlId()


def create_install_folder():
    company_directory = "{}\\{}".format(os.getenv('APPDATA'), COMPANY_NAME)
    if not os.path.exists(company_directory):
        os.mkdir(company_directory)
    if not os.path.exists(INSTALL_FOLDER):
        os.mkdir(INSTALL_FOLDER)


def get_version_from_repo():
    url = "{}{}".format(REPO_URL, VERSION_FILE)
    r = requests.get(url, allow_redirects=True)
    return r.text


def get_installed_version():
    if os.path.exists(INSTALLED_VERSION_PATH):
        file = open(INSTALLED_VERSION_PATH, "r")
        version = file.read()
        file.close()
        return version
    return "0.0.0"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


class MyApplication(wx.App):

    def OnInit(self):
        self.SetAppName(WINDOW_TITLE)
        if is_admin():
            try:
                version = get_version_from_repo()
                create_install_folder()
                if get_installed_version() != version:
                    dlg = MyDialog(None, -1, WINDOW_TITLE, version, Size(400, 120))
                    dlg.ShowModal()
                    dlg.Destroy()
                if os.path.exists(EXECUTABLE_PATH):
                    subprocess.Popen([EXECUTABLE_PATH], cwd=INSTALL_FOLDER)
                else:
                    dlg = wx.MessageDialog(None, "Installer executable not found",
                                           WINDOW_TITLE, style=wx.OK | wx.ICON_HAND)
                    dlg.ShowModal()
                    dlg.Destroy()
            except Exception as e:
                dlg = wx.MessageDialog(None, str(e),
                                       WINDOW_TITLE, style=wx.OK | wx.ICON_HAND)
                dlg.ShowModal()
                dlg.Destroy()
        else:
            dlg = wx.MessageDialog(None, "This application requires administrative privileges to run",
                                   WINDOW_TITLE, style=wx.OK | wx.ICON_HAND)
            dlg.ShowModal()
            dlg.Destroy()
        return True


class MyDialog(wx.Dialog):

    def __init__(self, parent, i, title, version, size=wx.DefaultSize):
        wx.Dialog.__init__(self)
        self.Create(parent, i, title, wx.DefaultPosition, size, wx.DEFAULT_DIALOG_STYLE, WINDOW_TITLE)
        self.Centre()
        self.panel = wx.Panel(self)
        self.status = wx.StaticText(self.panel, label="Starting...", pos=Point(17, 10))
        self.progress = wx.Gauge(self.panel, -1, size=Size(350, 25), pos=Point(17, 40))
        self.pg = 0
        self.total = 100
        self.filename = "no_name_file"
        self.Connect(-1, -1, EVT_START_ID, self.set_total)
        self.Connect(-1, -1, EVT_UPDATE_ID, self.update_progress)
        self.Connect(-1, -1, EVT_END_ID, self.end)
        self.clean()
        self.clean_folder(INSTALL_FOLDER)
        self.handler = WorkerThread(version, self)

    def update_progress(self, event):
        self.pg += event.value
        percentage = (self.pg / self.total) * 100
        self.status.SetLabelText("Downloading {} ({}%)".format(self.filename, int(percentage)))
        self.progress.SetValue(self.pg)

    def set_total(self, event):
        self.filename = event.filename
        self.pg = 0
        self.total = event.total
        self.progress.SetValue(0)
        self.progress.SetRange(event.total)

    def end(self, event):
        self.Close()

    def clean_folder(self, path):
        if os.path.exists(path):
            for filename in os.listdir(path):
                if filename != CACHE_FOLDER:
                    file_path = os.path.join(path, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        dlg = wx.MessageDialog(self, 'Failed to delete {}. Reason: {}'.format(file_path, e),
                                               WINDOW_TITLE, style=wx.OK | wx.ICON_HAND)
                        dlg.ShowModal()
                        dlg.Destroy()

    def clean(self):
        if '--clean' in sys.argv:
            self.clean_folder(INSTALL_FOLDER)
            self.clean_folder(CACHE_FOLDER_PATH)
        if '--clean-cache' in sys.argv:
            self.clean_folder(CACHE_FOLDER_PATH)
        if '--clean-installer' in sys.argv:
            self.clean_folder(INSTALL_FOLDER)


class PercentageInfo(wx.PyEvent):

    def __init__(self, filename, total):
        super().__init__()
        self.SetEventType(EVT_START_ID)
        self.filename = filename
        self.total = total


class UpdatePercentage(wx.PyEvent):

    def __init__(self, value):
        super().__init__()
        self.SetEventType(EVT_UPDATE_ID)
        self.value = value


class ProcessTerminated(wx.PyEvent):

    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_END_ID)


class WorkerThread(Thread):

    def __init__(self, version, dlg):
        Thread.__init__(self)
        self.dlg = dlg
        self.version = version
        self.start()

    def run(self):
        try:
            for file in FILES:
                self.download_file_from_repo(file)
            if os.path.exists(INSTALLED_VERSION_PATH):
                os.remove(INSTALLED_VERSION_PATH)
            file = open(INSTALLED_VERSION_PATH, "w")
            file.write(self.version)
            file.close()
        except Exception as e:
            dlg = wx.MessageDialog(None, str(e),
                                   WINDOW_TITLE, style=wx.OK | wx.ICON_HAND)
            dlg.ShowModal()
            dlg.Destroy()
        finally:
            wx.PostEvent(self.dlg, ProcessTerminated())

    def download_file_from_repo(self, filename):
        url = "{}{}".format(REPO_URL, filename)
        with open("{}\\{}".format(INSTALL_FOLDER, filename), 'wb') as f:
            response = requests.get(url, stream=True)
            total_length = response.headers.get('content-length')
            wx.PostEvent(self.dlg, PercentageInfo(filename, int(total_length)))
            if total_length is None:  # no content length header
                f.write(response.content)
            else:
                for data in response.iter_content(chunk_size=4096):
                    f.write(data)
                    wx.PostEvent(self.dlg, UpdatePercentage(len(data)))


def main():
    app = MyApplication()
    app.MainLoop()


main()
