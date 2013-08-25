from ctypes import create_string_buffer, windll, sizeof
from time import sleep
from subprocess import Popen
from smtplib import SMTP
import atexit
from ConfigParser import SafeConfigParser
from sys import exit
from getpass import getpass



def run_handbrake(command, title):
    command[2] = driveLetter
    command[4] = movieDirectory+title+movieExtension
    command[-1] = "\""+preset+"\""
    rip_process = Popen(command, shell=True)
    print "Ripping",title
    rip_process.wait()
    print "Finished ripping",title


class Messenger:
    def __init__(self, phone, gmail, password):
        self.rcpt = phone # Number to text
        self.fromAddr = gmail # Address to send with
        self.emailPass = password # Email password

    def send_text(self, message):
	# SMTP connection times out, so login at send time
        self.server = SMTP("smtp.gmail.com:587")
        self.server.starttls()
        self.server.login(self.fromAddr, self.emailPass)
        self.server.sendmail(self.fromAddr, self.rcpt, message)
        self.server.quit()
        print "Message sent"

    def send_finished(self, title):
        self.send_text(title+" is done ripping")

    def send_error(self):
        self.send_text("HELP! I'm Broken!")

def set_power(time = 10):
    # Handbrake keeps my monitor from turning back on for some reason
    # set 0 to keep from sleeping, set to n for n minutes till timeout
    Popen(["powercfg", "-X", "-monitor-timeout-ac", str(time)])
    if time == 0:
        # Make monitor timeout return to 10 at exit
        atexit.register(set_power)


def formatName(func):

    def wrapper(*args):
        # When outter function is called, run wrapper.
        # Pull in outter function arguments into args.
        dvdTitle = func(args[0])
        if not dvdTitle:
            return None
        upperTitle = dvdTitle.upper()
        noResTitle = upperTitle.replace("16X9", "")
        spaceTitle = noResTitle.replace("_", " ")
        finalTitle = spaceTitle.title()
        return finalTitle

    return wrapper

@formatName
def get_dvd_title(driveLetter):
    # Create buffer to store volume name
    buff = create_string_buffer(50)
    # Create buffer for target mount point string
    buff2 = create_string_buffer(driveLetter)
    # Load kernel32
    k32 = windll.kernel32
    # Get volume name a.k.a. DVD name
    k32.GetVolumeInformationA(buff2.value, buff, sizeof(buff), \
                                    None, None, None, None, None)
    return buff.value



if __name__ == "__main__":

    config = SafeConfigParser()
    try:
        config.read("config.txt")
        username = config.get("setup", "email")
        phone = config.get("setup", "phoneaddress")
        dvdDriveLetter = config.get("setup", "driveletter")
        movieDir = config.get("setup", "moviefolder")
        movieExtension = config.get("setup", "outputextension")
    except Exception as e:
            print "------------------------------\n"
            print "Error while parsing config. Are you sure the config file is present in the directory?\n"
            print "------------------------------"
            print "Exception:"
            print e
            exit()

    driveLetter = dvdDriveLetter
    movieDirectory = movieDir
    preset = "High Profile"
    ripCommand = ["C:\Program Files\Handbrake\HandBrakeCLI.exe", \
                  "-i", "", "-o", "", "--preset=", ""]
    password = getpass("Please enter your gmail password: ")
    sender = Messenger(phone, username, password)
    set_power(0)
    lastTitle = title = None
    try:
        while 1:
            title = get_dvd_title(driveLetter)
            sleep(.5)
            if title and title != lastTitle:
                print "Found New Title", title
                run_handbrake(ripCommand, title)
                sender.send_finished(title)
                lastTitle = title
    except KeyboardInterrupt:
        sender.send_error()
