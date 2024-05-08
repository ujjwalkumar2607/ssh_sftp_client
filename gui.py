import tkinter
import tkinter.messagebox
import os

THIS_DIR = os.path.dirname(__file__)


class Control:
    def __init__(self):
        try:
            with open(os.path.join(THIS_DIR, "__version__")) as f:
                git_hash = f.readline()
        except:
            git_hash = "UNKNOWN"

        git_hash = git_hash[:7]

        window = tkinter.Tk()
        window.geometry("300x200")
        window.title("Cube Finishing Tool - {}".format(git_hash))

        self.hostname = tkinter.StringVar()
        self.hostname.set("")

        help_text = tkinter.Label(window, text="Enter hostname\n and hit 'Finish Cube'").pack()

        label = tkinter.Label(window, text="Hostname: ").pack()
        hostname_entry = tkinter.Entry(window, textvariable=self.hostname).pack()

        self.go_button = tkinter.Button(window, text="Finish Cube", command=self.finish_cube)
        self.go_button.pack()

        self.check_button = tkinter.Button(window, text="Check Cube", command=self.check_cube)
        self.check_button.pack()

        window.mainloop()

    def disable_button(self):
        self.go_button.config(state=tkinter.DISABLED)
        self.check_button.config(state=tkinter.DISABLED)
    def enable_button(self):
        self.go_button.config(state=tkinter.NORMAL)
        self.check_button.config(state=tkinter.NORMAL)

    def finish_cube(self):
        import cli
        hostname = self.hostname.get()
        if not hostname.endswith(".local"):
            hostname = hostname + ".local"
        if hostname.startswith('s') or hostname.startswith('S'):
            CUBE_TYPE = "R2"
        else:
            CUBE_TYPE = "R3"

        print("Finishing {} cube".format(CUBE_TYPE))
        print("Finishing {}".format(hostname))

        self.disable_button()
        try:
            cli.do_main_work(hostname, CUBE_TYPE)
            tkinter.messagebox.showinfo("Done Finishing", "{} Done. Wait for reboot (~30 seconds and light go blue) and run 'Check Cube'".format(hostname))
        except:
            import traceback
            traceback.print_exc()
            tkinter.messagebox.showerror("Error Finishing", "{} Error. See command prompt for logging info".format(hostname))
        finally:
            self.enable_button()
        
    def check_cube(self):
        import finisher
        hostname = self.hostname.get()
        if not hostname.endswith(".local"):
            hostname = hostname + ".local"

        self.disable_button()
        try:
            import warnings
            warnings.filterwarnings(action='ignore', module='.*paramiko.*')
            print("Running Final Test")
            finisher.done_check(hostname)
            tkinter.messagebox.showinfo("Final Check Done", "{} PASS".format(hostname))
        except:
            import traceback
            traceback.print_exc()
            tkinter.messagebox.showerror("Final Check Fail", "{} Error. See command prompt for logging info".format(hostname))
        finally:
            self.enable_button()

        

if __name__ == "__main__":
    c = Control()



