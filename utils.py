import pdb
import os

log_path = './zlog.log'
try:
    os.remove(log_path)
except:
    pass

#returns filepath
def FenToFile(fenStr):
    filename = 'fen.game'
    f = open(filename, 'w')
    f.write(fenStr)
    f.close()
    return filename

def FenToXBoard(fenStr):
    filename = FenToFile(fenStr)
    import os
    import multiprocessing as mp
    def go ():
        os.system('xboard -lpf %s' % filename)
    p = mp.Process()
    p.run = go
    p.start()

class zlog ():
    pageWidth = 165
    line_buffer = []
    buffer_size = 300

    @staticmethod
    def log(msg, indent=-1):
        msg = str(msg)
        firstChar = '| ' if indent != -1 else '  '
        #pdb.set_trace()
        lines = zlog._makeLineBreaks(msg, zlog.pageWidth-1)
        lines = map(lambda line: firstChar + line, lines)
        zlog._write(lines)
        for line in lines:
            print '# ' + line
        
    @staticmethod 
    def _makeLineBreaks(msg, page_width = -1):
        page_width = page_width if page_width != -1 else zlog.pageWidth

        _lines = msg.split('\n')
        lines = []
        for line in _lines:
            while len(line) > page_width:
                lines.append(line[:page_width])
                line = line[page_width:]
            lines.append(line)
        return lines
     
    @staticmethod 
    def _write(lines, force=True):
        zlog.line_buffer.extend(lines)
        if force or len(zlog.line_buffer) > zlog.buffer_size:
            zlog.Flush()

    @staticmethod 
    def Flush():
        log_file = open(log_path, 'a')
        log_file.write('\n'.join(zlog.line_buffer) + '\n')
        log_file.close()
        zlog.line_buffer = []
        

        
            
            


                
