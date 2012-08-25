import sublime
import sublime_plugin
import thread
import subprocess
import signal
import os
import functools

class ServerController(object):

    def __new__(cls, *args, **kwargs):
        instance = object.__new__(cls)
        instance.load_settings()
        instance.proc = None
        instance.running = False

        cls.__new__ = classmethod(lambda cls, *args, **kwargs: instance)
        return cls.__new__(cls, *args, **kwargs)

    def set_listener(self, listener):
        self.listener = listener
        self.panel = self.listener.window.get_output_panel('php_builtin_server_panel')
        return self

    def start(self):
        self.running = True
        self.show_panel()
        self.proc = subprocess.Popen(self.cmd_array, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        thread.start_new_thread(self.read_stdout, ())
        thread.start_new_thread(self.read_stderr, ())

        self.append('PHP Buil-in WebServer ver 0.0.1\n')
        self.append('Server is running! - http://%s\n' % self.url)

    def stop(self):
        cmd = ' '.join(self.cmd_array)
        proc = subprocess.Popen(['ps', '-A'], stdout = subprocess.PIPE)
        out, err = proc.communicate()
        for line in out.splitlines():
            if cmd in line:
                pid = int(line.split(None, 1)[0])
                os.kill(pid, signal.SIGKILL)

        self.proc = None
        self.hide_panel()
        self.running = False

    def show_panel(self):
        self.listener.window.run_command('show_panel', {'panel': 'output.php_builtin_server_panel'})

    def hide_panel(self):
        self.listener.window.run_command('hide_panel', {'panel': 'output.php_builtin_server_panel'})

    def read_stdout(self):
        while True:
            data = os.read(self.proc.stdout.fileno(), 2 ** 15)
            if data != "":
                sublime.set_timeout(functools.partial(self.append_data, data), 0)
            else:
                self.proc.stdout.close()
                self.running = False
                break

    def read_stderr(self):
        while True:
            data = os.read(self.proc.stderr.fileno(), 2 ** 15)
            if data != "":
                sublime.set_timeout(functools.partial(self.append, data), 0)
            else:
                self.proc.stderr.close()
                self.running = False
                break

    def append(self, data):
        self.panel.set_read_only(False)
        edit = self.panel.begin_edit()
        self.panel.insert(edit, self.panel.size(), data.decode("utf-8"))
        self.scroll_to_end_view()
        self.panel.end_edit(edit)
        self.panel.set_read_only(True)

    def scroll_to_end_view(self):
        (cur_row, _) = self.panel.rowcol(self.panel.size())
        self.panel.show(self.panel.text_point(cur_row, 0))

    def is_running(self):
        return self.running

    def load_settings(self):
        s = sublime.load_settings("PHP Built-in WebServer.sublime-settings")
        address = s.get("address")
        port = s.get("port")
        document_root_path = s.get("document_root_path")
        self.url = '%s:%i' % (address, port)
        self.cmd_array = ['php', '-S', self.url, '-t', document_root_path]

class StartServerCommand(sublime_plugin.WindowCommand):

    def run(self):
        ServerController().set_listener(self).start()

    def is_enabled(self):
        return not ServerController().is_running()

class StopServerCommand(sublime_plugin.WindowCommand):

    def run(self):
        ServerController().set_listener(self).stop()

    def is_enabled(self):
        return True

class ShowPanelCommand(sublime_plugin.WindowCommand):

    def run(self):
        ServerController().set_listener(self).show_panel()

    def is_enabled(self):
        return not ServerController().is_running()

class HidePanelCommand(sublime_plugin.WindowCommand):

    def run(self):
        ServerController().set_listener(self).hide_panel()

    def is_enabled(self):
        return True