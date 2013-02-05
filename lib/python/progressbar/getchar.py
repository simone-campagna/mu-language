import os,sys
import sys
import termios

def getchar(stdin=None):
	'''
	Equivale al comando getchar() di C
	'''
        if stdin is None:
          stdin = sys.stdin
	fd = stdin.fileno()
	
	if os.isatty(fd):
		
		old = termios.tcgetattr(fd)
		new = termios.tcgetattr(fd)
		new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
		new[6] [termios.VMIN] = 1
		new[6] [termios.VTIME] = 0
		
		try:
			termios.tcsetattr(fd, termios.TCSANOW, new)
			termios.tcsendbreak(fd,0)
			ch = os.read(fd,7)

		finally:
			termios.tcsetattr(fd, termios.TCSAFLUSH, old)
	else:
		#ch = os.read(fd,7)
		ch = os.read(fd,1)
	
	return(ch)

if __name__ == '__main__':
  while True:
    print "Stampa 'Q' per uscire"
    a = getchar()
    print ">>> %r" % a
    if a == 'Q':
      print "Bravo."
      break
