import time

filename = 'filepipe.txt'
sleeptime = 0.0
def read():
    while True:
        time.sleep(.2)
        f = open(filename, 'r')
        msg = f.read()
        if msg:
            msg = msg.strip()
        if msg:
            print msg
        f.close()

def write(msg):
    return
    written = False
    while not written:
        time.sleep(.2)
        try:
            f = open(filename, 'w')
            f.write(msg)
            f.close()
            written = True
        except:
            pass



if __name__ == "__main___":
    read()
        

