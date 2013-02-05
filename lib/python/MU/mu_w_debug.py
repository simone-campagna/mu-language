from progressbar import widget, span, terminal, getchar
from mu_debug import *
import time
import sys

class Mu_WDebugger(Mu_Debugger, widget.Screen):
  COMMAND_LIST = (
	(
		'help',
		(
			('h', 'H', '?'),
			"print this help",
		),
	),
	(
		'quit',
		(
			('q', 'Q'),
			"quit debugger",
		),
	),
	(
		'step',
		(
			(' ', '\n'),
			"advance 1 step",
		),
	),
	(
		'increase_num_steps',
		(
			('+', ),
			"increase number of steps",
		),
	),
	(
		'decrease_num_steps',
		(
			('-', ),
			"decrease number of steps",
		),
	),
	(
		'set_num_steps',
		(
			('s', ),
			"set number of steps",
		),
	),
	(
		'advance_num_steps',
		(
			('a', ),
			"advance <A> of steps",
		),
	),
	(
		'goto_iteration',
		(
			('g', ),
			"go to iteration number <I>",
		),
	),
	(
		'set_sleep',
		(
			('S', ),
			"set seconds to sleep for non-interactive mode",
		),
	),
	(
		'print_console',
		(
			('p', ),
			"print console",
		),
	),
	(
		'run',
		(
			('r', ),
			"run to end",
		),
	),
	(
		'left',
		(
			('\x1b[D', ),
			"move center to left",
		),
	),
	(
		'right',
		(
			('\x1b[C', ),
			"move center to right",
		),
	),
	(
		'up',
		(
			('\x1b[A', ),
			"move center up",
		),
	),
	(
		'down',
		(
			('\x1b[B', ),
			"move center down",
		),
	),
	(
		'shift_boards',
		(
			('b', '\t'),
			"shift boards",
		),
	),
	(
		'select_thread',
		(
			('t', ),
			"select thread",
		),
	),
	(
		'esc',
		(
			('\x1b', ),
			"clean buffer",
		),
	),
	(
		'backspace',
		(
			('\x7f', ),
			"remove 1 element  from buffer",
		),
	),
	(
		'batch_advance',
		(
			('B', ),
			"switch batch advance on/off",
		),
	),
  )
  COMMANDS = dict(COMMAND_LIST)
  COMMAND_NAME = {
	COMMANDS['left'][0]:	'<left>',
	COMMANDS['right'][0]:	'<right>',
	COMMANDS['down'][0]:	'<down>',
	COMMANDS['up'][0]:	'<up>',
	' ':			'<space>',
	'\t':			'<tab>',
	'\n':			'<enter>',
  }


  def __init__(		self,
			mu,
                        debug_threads=False,
                        debug_num_steps=1,
			num_console_lines=2,
    ):
    Mu_Debugger.__init__(	self,
				mu,
				debug_threads=debug_threads,
				debug_num_steps=debug_num_steps,
    )
    self._interactive = True
    self._sleep_non_interactive = 0.0
    self.num_console_lines = num_console_lines
    self._reset_num_steps = None
    self._batch_advance = True
    self._buffer = []
    self.board_wlines = []
    self.board_wtexts = []
    for i in xrange(widget.TERMINAL_H-(1+self.num_console_lines)):
      text = widget.Text(span=span.TotalPercentualSpan(100.0)) #, fill=str(i%9))
      line = widget.Line(
		(
			text,
		),
		span=widget.TERMINAL_W,
      )
      self.board_wlines.append(line)
      self.board_wtexts.append(text)
    self.width = (len(self.board_wlines)-3, widget.TERMINAL_W-8)
    fmt_ok = widget.Formatter(color="blue", bg_color="white")
    fmt_ko = widget.Formatter(color="red", bg_color="white")
    self.wconsole = []
    for x in xrange(self.num_console_lines):
      self.wconsole.append(
			(
				widget.Text(span=span.FixedSpan(0), formatter=widget.Formatter(reverse=True)),
				widget.Text(span=span.FillerSpan(), formatter=fmt_ok),
			)
      )
    self.witn = widget.Integer(span=10, formatter=fmt_ok)
    self.wsteps = widget.Integer(span=None, formatter=fmt_ok)
    self.wlast_command = widget.Text(span=None, formatter=fmt_ok)
    self.wbatch_advance = widget.Boolean(span=None, formatter=fmt_ok)
    self.wbuffer = widget.Text(span=None, formatter=fmt_ok)
    self.wconsole_lines = [
		widget.Line(
			(
				"Console[",
				wconsole_lineno,
				"]> ",
				wconsole,
			),
		) for wconsole_lineno, wconsole in self.wconsole
     ]
    self.last_command = (True, ' ')
    self.last_command_formatter = {
	True:	fmt_ok,
	False:	fmt_ko,
		
    }
    self.command_line = widget.Line(
		(
			"itn=",
			self.witn,
			" num_steps=",
			self.wsteps,
			" batch_advance=",
			self.wbatch_advance,
			" last_command=",
			self.wlast_command,
			widget.Filler(),
			"buffer=",
			self.wbuffer,
		),
		#span = widget.TERMINAL_W-10,
    )
    lines = self.board_wlines + self.wconsole_lines + [self.command_line]
    widget.Screen.__init__(self, lines)

  def add_board_debugger(self, board_debugger):
    Mu_Debugger.add_board_debugger(self, board_debugger)

  def start(self):
    widget.Screen.start(self)
    Mu_Debugger.start(self)

  def finish(self):
    widget.Screen.finish(self)
    Mu_Debugger.finish(self)

  def _update(self, refresh=True):
    n_mu_boards = len(self.mu_board_debuggers)
    tot_h = len(self.board_wtexts)
    h, rem = divmod(tot_h, n_mu_boards)
    num_lines = {}
    n_sum = 0
    for mu_board_debugger in self.mu_board_debuggers:
      n = min(h, len(mu_board_debugger.mu_board.board))
      num_lines[mu_board_debugger] = n
      n_sum += n
    diff = tot_h - n_sum
    for mu_board_debugger in self.mu_board_debuggers:
      n = num_lines[mu_board_debugger]
      l = len(mu_board_debugger.mu_board.board)
      num_lines[mu_board_debugger] += min(diff, max(0, l-n))
      mu_board_debugger.set_width((num_lines[mu_board_debugger]-5, self.width[1]))
    #n_lines_list = [h for i in self.mu_board_debuggers[:-1]] + [h+rem]
    offset = 0
    for mu_board_debugger in self.mu_board_debuggers:
      h = num_lines[mu_board_debugger]
      texts = self.board_wtexts[offset:offset+h]
      offset += h
      mu_board_debugger.update_wtexts(texts, widget.TERMINAL_W)
    self.witn.set_value(self.mu.itn)
    self.wsteps.set_value(self.debug_num_steps)
    if self.mu.console:
      console_lines = str(self.mu.console).split('\n')
      ll = console_lines[-self.num_console_lines:]
      console_lst = [(str((len(console_lines)-len(ll))+c), console_line) for c, console_line in enumerate(ll)]
    else:
      console_lst = []
    for i in xrange(self.num_console_lines-len(console_lst)):
      console_lst.append(('', ''))
    size = max(len(e[0]) for e in console_lst)
    for (c_num, c_line), (w_num, w_line) in zip(console_lst, self.wconsole):
      w_num.set_text(str(c_num), size)
      w_line.set_text(c_line)
    #self.wconsole.set_text(console_line)
    #self.wconsole_line.set_value(num_console_lines)
    self.wbatch_advance.set_value(self._batch_advance)
    self.wbuffer.set_text(repr(''.join(self._buffer)))
    self.render()
    if refresh:
      #raw_input('HERE')
      self._refresh_seen()

  def update_completed(self, completed):
    if (not self._batch_advance) or self._debug_skip_num_steps <= 1:
      self._update()
    if not self._interactive:
      if self._sleep_non_interactive > 0.0:
        time.sleep(self._sleep_non_interactive)
      #if len(sys.stdin) > 0:
      #  self._interactive = True
    if self._interactive and (completed or self._debug_skip_num_steps <= 1):
      while True:
        try:
          command = getchar.getchar()
          command_status = True
          #self.last_command = (True, command)
          if command in self.COMMANDS['help'][0]:
            self.clear()
            self.print_help()
            getchar.getchar()
            self.render()
            continue
          elif command in self.COMMANDS['quit'][0]:
            self.finish()
            return False
          elif command in self.COMMANDS['step'][0]:
            break
          elif command in self.COMMANDS['increase_num_steps'][0]:
            self.debug_num_steps += 1
            self.wsteps.set_value(self.debug_num_steps)
            self.render()
          elif command in self.COMMANDS['decrease_num_steps'][0]:
            self.debug_num_steps -= 1
            self.wsteps.set_value(self.debug_num_steps)
            self.render()
          elif command in self.COMMANDS['set_num_steps'][0]:
            self.clear()
            self.debug_num_steps = self.get_value("Set number of steps", int, self.debug_num_steps)
            self.wsteps.set_value(self.debug_num_steps)
            self.render()
          elif command in self.COMMANDS['set_sleep'][0]:
            self.clear()
            self._sleep_non_interactive = self.get_value("Set seconds to sleep", float, self._sleep_non_interactive)
            self.wsteps.set_value(self.debug_num_steps)
            self.render()
          elif command in self.COMMANDS['advance_num_steps'][0]:
            self.clear()
            self._reset_num_steps = self.debug_num_steps
            self.debug_num_steps = self.get_value("Advance number of steps", int)
            self.wsteps.set_value(self.debug_num_steps)
            self.render()
            break
          elif command in self.COMMANDS['goto_iteration'][0]:
            self.clear()
            n = self.get_value("Go to iteration: ", int)
            debug_num_steps = max(0, n-self.mu.itn)
            if debug_num_steps == 0:
              self.render()
              continue
            self._reset_num_steps = self.debug_num_steps
            self.debug_num_steps = debug_num_steps
            self.wsteps.set_value(self.debug_num_steps)
            self.render()
            break
          elif command in self.COMMANDS['run'][0]:
            self._interactive = False
            break
          elif command in self.COMMANDS['print_console'][0]:
            self.clear()
            lines = str(self.mu.console).split('\n')
            format_g = widget.Formatter(color="black", bg_color="white").str_format()
            format_r = widget.Formatter(color="red", bg_color="white").str_format()
            format_n = widget.Formatter.NORMAL
            if len(lines) <= 10:
              ffmt = "%s%%d|%s%%s"
            elif len(lines) <= 100:
              ffmt = "%s%%2d|%s%%s"
            elif len(lines) <= 1000:
              ffmt = "%s%%3d|%s%%s"
            elif len(lines) <= 10000:
              ffmt = "%s%%4d|%s%%s"
            else:
              ffmt = "%s%%8d|%s%%s"
            fmt = ffmt % (format_g, format_n)
            for line_no, line in enumerate(lines):
              print fmt % (line_no, line)
            sys.stdout.write("\n%s[PRESS ANY KEY]%s" % (format_r, format_n))
            sys.stdout.flush()
            getchar.getchar()
            self.render()
            continue
          elif command in self.COMMANDS['left'][0]:
            self.shift_centers((0, -1))
            self._update(refresh=False)
            continue
          elif command in self.COMMANDS['right'][0]:
            self.shift_centers((0, +1))
            self._update(refresh=False)
            continue
          elif command in self.COMMANDS['up'][0]:
            self.shift_centers((-1, 0))
            self._update(refresh=False)
            continue
          elif command in self.COMMANDS['down'][0]:
            self.shift_centers((+1, 0))
            self._update(refresh=False)
            continue
          elif command in self.COMMANDS['shift_boards'][0]:
            self.mu_board_debuggers = self.mu_board_debuggers[1:] + self.mu_board_debuggers[:1]
            self._selected_thread_num = 0
            self._update(refresh=False)
            continue
          elif command in self.COMMANDS['select_thread'][0]:
            self.mu_board_debuggers[0].shift_threads()
            self._update(refresh=False)
            continue
          elif command in self.COMMANDS['batch_advance'][0]:
            self._batch_advance = not self._batch_advance
            self._update(refresh=False)
            continue
          elif command in self.COMMANDS['esc'][0]:
            del self._buffer[:]
            self._update(refresh=False)
            continue
          elif command in self.COMMANDS['backspace'][0]:
            if self._buffer:
              self._buffer.pop()
              self._update(refresh=False)
            continue
          else:
            self._buffer.append(command)
            command_status = False
            self._update(refresh=False)
            #self.render()
            continue
        finally:
          self.set_command(command, command_status)
          self._debug_skip_num_steps = self.debug_num_steps
    else:
      if self._reset_num_steps is not None:
        self.debug_num_steps = self._reset_num_steps
        self._reset_num_steps = None
      self._debug_skip_num_steps -= 1
    return True

  def shift_centers(self, dir):
    for mu_board_debugger in self.mu_board_debuggers:
      mu_board_debugger.shift_center(dir)

  def set_command(self, command, status):
    if status:
      self.last_command = (status, command)
      self.wlast_command.set_text(repr(command))
      self.wlast_command.set_formatter(self.last_command_formatter[status])

  def get_value(self, message, type_converter=None, default=None):
    if default is None:
      m = "%s: " % message
    else:
      m = "%s[%s]: " % (message, default)
    while True:
      if self._buffer:
        value = ''.join(self._buffer)
        del self._buffer[:]
      else:
        value = raw_input(m)
      if value == '':
        value = default
      elif type_converter is not None:
        try:
          conv_value = type_converter(value)
          value = conv_value
        except ValueError, e:
          print "ERR: invalid value '%s'" % value
          continue
        break
    return value


  @classmethod
  def print_help(clss):
    print "HELP"
    lines = []
    for command_name, (command_keys, command_description) in clss.COMMAND_LIST:
      l = [clss.COMMAND_NAME.get(command_key, command_key) for command_key in command_keys]
      lines.append((command_name, '|'.join(l), command_description))
    if lines:
      maxl = [max(len(line[i]) for line in lines) for i in xrange(3)]
      fmt = '%%%ds %%%ds %%%ds' % tuple(maxl)
      for line in lines:
        print fmt % line

class Mu_WBoardDebugger(Mu_BoardDebugger):
  def __init__(self, mu_board, mu_debugger, *l_args, **d_args):
    Mu_BoardDebugger.__init__(self, mu_board, mu_debugger, *l_args, **d_args)
    self._selected_thread = None
    self.width = self.mu_debugger.width

  def set_width(self, width):
    self.width = width

  def shift_threads(self):
    thread_lst = list(self.mu_board.threads)
    if not thread_lst:
      return
    if self._selected_thread is None:
      self._selected_thread = thread_lst[0]
    else:
      if self._selected_thread in self.mu_board.threads:
        idx = thread_lst.index(self._selected_thread)
        self._selected_thread = thread_lst[(idx+1)%len(thread_lst)]
      else:
        self._selected_thread = thread_lst[0]

  def update_wtexts(self, wtexts, line_size):
    n_lines = len(wtexts)
    #w = n_lines-4
    #h = line_size-8
    #print self.mu_debugger.width
    #raw_input('lll')
    if self._selected_thread is not None and not self._selected_thread.completed and self._selected_thread in self.mu_board.threads:
      center_thread = self._selected_thread
    else:
      center_thread = None
    #print self.width
    #raw_input('...')
    for wtext, line in zip(wtexts, self._debug_lines__board_map(self.width, center_thread=center_thread)):
      wtext.set_text(line)

  def _refresh_seen(self):
    for seen_row in self.seen:
      for j, l in enumerate(seen_row):
        while l:
          thread, ln, is_current = l.pop(-1)
          if thread is not None and thread.completed:
            continue
          if ln > 0:
            ln -= 1
          if ln != 0:
            l.append((thread, ln, False))
            break
          
          
        
