#!/usr/bin/env python

from mu import Mu_Error
from mu_debug import *
from Tkinter import *
from ScrolledText import ScrolledText
import time

class Mu_Text(Text):
  MODE_INSERT = 0
  MODE_DEBUG = 1
  def __init__(self, *args, **keywords):
    self.mode = self.MODE_INSERT
    Text.__init__(self, *args, **keywords)
    self.c = 0

  def insert(self, *args):
    print self.c, self.mode
    self.c += 1
    if self.mode == self.MODE_INSERT:
      Text.insert(self, *args)
    else:
      print "INSERT", args

  def delete(self, *args):
    if self.mode == self.MODE_INSERT:
      Text.delete(self, *args)
    else:
      print "DELETE", args

  def set_debug_mode(self):
    self.mode = self.MODE_DEBUG

  def set_insert_mode(self):
    self.mode = self.MODE_INSERT

class Mu_XBoardDebugger_Widget(Frame):
  def __init__(self, root, mu_board_debugger):
    self.root = root
    self.mu_board_debugger = mu_board_debugger
    self.mu_debugger = self.mu_board_debugger.mu_debugger
    self.mu = self.mu_debugger.mu
    self.mu_board = self.mu_board_debugger.mu_board

    Frame.__init__(self, self.root)
    self.button_frame = Frame(self)
    self.button_set_max = Button(self.button_frame,
			width=3,
			repeatinterval=10,
			repeatdelay=10,
			text="M",
			command=self.set_height_max
    )
    self.button_set_max.pack(side=TOP)
    self.button_increase_2 = Button(self.button_frame,
			width=3,
			repeatinterval=10,
			repeatdelay=10,
			text="++",
			command=self.increase_height_2
    )
    self.button_increase_2.pack(side=TOP)
    self.button_increase_1 = Button(self.button_frame,
			width=3,
			repeatinterval=10,
			repeatdelay=10,
			text="+",
			command=self.increase_height_1
    )
    self.button_increase_1.pack(side=TOP)
    self.button_decrease_1 = Button(self.button_frame,
			width=3,
			repeatinterval=10,
			repeatdelay=10,
			text="-",
			command=self.decrease_height_1
    )
    self.button_decrease_1.pack(side=TOP)
    self.button_decrease_2 = Button(self.button_frame,
			width=3,
			repeatinterval=10,
			repeatdelay=10,
			text="--",
			command=self.decrease_height_2
    )
    self.button_decrease_2.pack(side=TOP)
    self.button_set_min = Button(self.button_frame,
			width=3,
			repeatinterval=10,
			repeatdelay=10,
			text="m",
			command=self.set_height_min
    )
    self.button_set_min.pack(side=TOP)
    self.button_frame.pack(side=RIGHT)
    self.field_frame = Frame(self)
    self.field = ScrolledText(self.field_frame, width=self.mu_board.max_j, height=1+self.mu_board.max_i, highlightthickness=2)
    self.field.tag_config("unseen", background="white", foreground="dark gray")
    self.field.tag_config("seen", background="yellow", foreground="blue", borderwidth=1)
    self.field.tag_config("current_active", background="orange", foreground="black", borderwidth=1)
    self.field.tag_config("current_held", background="black", foreground="white", borderwidth=1)
    self.field.tag_config("current_waiting", background="blue", foreground="white", borderwidth=1)
    self.field.tag_config("error", background="red", foreground="yellow", borderwidth=1)
    self.field.tag_config("breakpoint_in", background="red", foreground="green", borderwidth=1)
    self.field.tag_config("breakpoint_out", background="green", foreground="red", borderwidth=1)
    for row_num, row in enumerate(self.mu_board.matrix):
      line = "%s\n" % ''.join(self.mu.i2a(i) for i in row)
      self.field.insert("%d.0" % (row_num+1), line, "unseen")
    #self.field.set_debug_mode()
    self.field.pack(padx = 5, pady = 5, fill = 'both', expand = 1)
    self.field_frame.pack(side=LEFT)
    self.bind("<Return>", self.event_press_enter)
    self.bind("<Key>", self.event_press_key)
    self.focus_set()

  def increase_height_1(self):
    self.field["height"] += 1

  def decrease_height_1(self):
    self.field["height"] -= 1

  def increase_height_2(self):
    self.field["height"] += 2

  def decrease_height_2(self):
    self.field["height"] -= 2

  def set_height_max(self):
    self.field["height"] = self.mu_board.max_i

  def set_height_min(self):
    self.field["height"] = 5

  def event_press_enter(self, event):
    return self.mu_debugger.xdebugger.event_press_enter(event)

  def event_press_key(self, event):
    return self.mu_debugger.xdebugger.event_press_key(event)

class Mu_XDebugger_Widget(Frame):
  def __init__(self, root, mu_debugger):
    self.root = root
    Frame.__init__(self, root)
    self.mu_debugger = mu_debugger
    self.mu = mu_debugger.mu
    self.interaction_frame = Frame(self.root)
    self.interaction_frame.pack(side=TOP)
    self.button_frame = Frame(self.interaction_frame)
    self.button_frame.pack(side=LEFT)
    self.control_frame = Frame(self.interaction_frame)
    self.control_frame.pack(side=LEFT)
    self.step_num_control_frame = Frame(self.control_frame)
    self.step_num_control_frame.pack(side=TOP)
    self.repeatinterval_control_frame = Frame(self.control_frame)
    self.repeatinterval_control_frame.pack(side=TOP)
    self.console_frame = Frame(self.root)
    self.console_frame.pack(side=TOP)
    self.boards_frame = Frame(self.root)

    self.boards_frame.grid_rowconfigure(0, weight=1)
    self.boards_frame.grid_columnconfigure(0, weight=1)

    self.boards_xscrollbar = Scrollbar(self.boards_frame, orient=HORIZONTAL)
    self.boards_xscrollbar.grid(row=1, column=0, sticky=E+W)

    self.boards_yscrollbar = Scrollbar(self.boards_frame)
    self.boards_yscrollbar.grid(row=0, column=1, sticky=N+S)

    self.boards_canvas = Canvas(	self.boards_frame,
					scrollregion=(0, 0, 1200, 10240),
					bd=0,
					xscrollcommand=self.boards_xscrollbar.set,
					yscrollcommand=self.boards_yscrollbar.set,
					confine=True,
    )

    self.boards_canvas.grid(row=0, column=0, sticky=N+S+E+W)
    self.boards_xscrollbar.config(command=self.boards_canvas.xview)
    self.boards_yscrollbar.config(command=self.boards_canvas.yview)

    self.xboard_debuggers = []
    for mu_board_debugger in reversed(mu_debugger.mu_board_debuggers):
      xboard_debugger = Mu_XBoardDebugger_Widget(self.boards_canvas, mu_board_debugger)
      mu_board_debugger.xboard_debugger = xboard_debugger
      xboard_debugger.pack(side=TOP)
    self.xboard_debuggers.append(xboard_debugger)

    #self.boards_canvas.config(scrollregion=(0, 0, 1200, 10240))
    self.boards_frame.pack(side=TOP)

    #for mu_board_debugger in reversed(mu_debugger.mu_board_debuggers):
    #  print "...", mu_board_debugger.xboard_debugger.bbox(), mu_board_debugger.xboard_debugger.size()
    #

    self.repeatinterval = 10
    self.repeatdelay = 500
    self.step_num = 1
    self.bind("<Return>", self.event_press_enter)
    self.bind("<Key>", self.event_press_key)
    self.focus_set()
    self.pack()
    self._key_int = []
    self.breakpoints = []

    #for mu_board_debugger in reversed(mu_debugger.mu_board_debuggers):
    #  print mu_board_debugger.xboard_debugger.field["width"], mu_board_debugger.xboard_debugger.field["height"]

  def run(self):
    self.running = False
    self.step_button = Button(self.button_frame,
			repeatinterval=self.repeatinterval,
			repeatdelay=self.repeatdelay,
			text="Step",
			command=self.run_steps
    )
    self.step_button.pack(side=LEFT)
    self.quit_button = Button(self.button_frame,
			text="Quit",
			command=self.mu_debugger.quit
    )
    self.quit_button.pack(side=LEFT)
    self.itn = Label( self.button_frame,
			width=16,
			height=1,
			text=self.mu_debugger.iteration()
    )
    self.itn.pack(side=LEFT)

    self.step_num_label = Label( self.step_num_control_frame,
			width=16,
			height=1,
			text="Step #",
    )
    self.step_num_label.pack(side=LEFT)
    self.step_num_decrease_10_button = Button(self.step_num_control_frame,
			text="<<",
			repeatdelay=self.repeatdelay,
			repeatinterval=self.repeatinterval,
			command=self.step_num_decrease_10,
    )
    self.step_num_decrease_10_button.pack(side=LEFT)
    self.step_num_decrease_button = Button(self.step_num_control_frame,
			text="<",
			repeatdelay=self.repeatdelay,
			repeatinterval=self.repeatinterval,
			command=self.step_num_decrease,
    )
    self.step_num_decrease_button.pack(side=LEFT)
    self.step_num_value = Label( self.step_num_control_frame,
			width=10,
			height=1,
			text=str(self.step_num),
    )
    self.step_num_value.pack(side=LEFT)
    self.step_num_increase_button = Button(self.step_num_control_frame,
			text=">",
			repeatdelay=self.repeatdelay,
			repeatinterval=self.repeatinterval,
			command=self.step_num_increase,
    )
    self.step_num_increase_button.pack(side=LEFT)
    self.step_num_increase_10_button = Button(self.step_num_control_frame,
			text=">>",
			repeatdelay=self.repeatdelay,
			repeatinterval=self.repeatinterval,
			command=self.step_num_increase_10,
    )
    self.step_num_increase_10_button.pack(side=LEFT)
			
			
    self.repeatinterval_label = Label( self.repeatinterval_control_frame,
			width=16,
			height=1,
			text="Repeat interval",
    )
    self.repeatinterval_label.pack(side=LEFT)
    self.repeatinterval_decrease_10_button = Button(self.repeatinterval_control_frame,
			text="<<",
			repeatdelay=self.repeatdelay,
			repeatinterval=self.repeatinterval,
			command=self.repeatinterval_decrease_10,
    )
    self.repeatinterval_decrease_10_button.pack(side=LEFT)
    self.repeatinterval_decrease_button = Button(self.repeatinterval_control_frame,
			text="<",
			repeatdelay=self.repeatdelay,
			repeatinterval=self.repeatinterval,
			command=self.repeatinterval_decrease,
    )
    self.repeatinterval_decrease_button.pack(side=LEFT)
    self.repeatinterval_value = Label( self.repeatinterval_control_frame,
			width=10,
			height=1,
			text=str(self.repeatinterval),
    )
    self.repeatinterval_value.pack(side=LEFT)
    self.repeatinterval_increase_button = Button(self.repeatinterval_control_frame,
			text=">",
			repeatdelay=self.repeatdelay,
			repeatinterval=self.repeatinterval,
			command=self.repeatinterval_increase,
    )
    self.repeatinterval_increase_button.pack(side=LEFT)
			
    self.repeatinterval_increase_10_button = Button(self.repeatinterval_control_frame,
			text=">>",
			repeatdelay=self.repeatdelay,
			repeatinterval=self.repeatinterval,
			command=self.repeatinterval_increase_10,
    )
    self.repeatinterval_increase_10_button.pack(side=LEFT)

    self.breakpoint_frame = Frame(self.button_frame)
    self.breakpoint_frame.pack(side=LEFT)
    self.add_breakpoint_button =  Button(self.repeatinterval_control_frame,
			text="ADD BREAK POINT",
			command=self.add_break_point,
    )

			
    self.console_text = ScrolledText(
			self.console_frame,
			width=80,
			height=3,
    )
    self.console_text.pack(side=LEFT)
    self.console_text.tag_config("line_number", background="black", foreground="light gray", borderwidth=1)
    self.console_text.tag_config("output", background="black", foreground="yellow", borderwidth=1)


  def add_break_point(self, event):
    pass

  def event_press_enter(self, event):
    self.run_steps()

  def event_press_key(self, event):
    if event.keysym_num >= ord('0') and event.keysym_num <= ord('9'):
      self._key_int.append(event.keysym)
      self._key_int.append(event.keysym)
    else:
      if self._key_int:
        ki = int(''.join(self._key_int))
        print ki
        self.step_num = ki
        self.step_num_value['text'] = str(ki)
      self._key_int = []
      if event.keysym_num == ord('+'):
        self.step_num_increase()
      elif event.keysym_num == ord('-'):
        self.step_num_decrease()
      elif event.keysym_num == ord('>'):
        self.step_num_increase_10()
      elif event.keysym_num == ord('<'):
        self.step_num_decrease_10()
      elif event.keysym_num in (ord('q'), ord('Q')):
        self.mu_debugger.quit()
      else:
        self.run_steps()

  def run_steps(self):
    if self.mu_debugger.disabled:
      return
    try:
      n = self.step_num
      while n > 0:
        self.mu_debugger.run_step()
        n -= 1
    except Mu_Error, e:
      self.exception(e)

  def exception(self, e):
    message = '\n' + '\n'.join(e.tracelines()) + '\n'
    #message, mu_board, cur, dir = e.args
    if len(e.args) == 4:
      mu_board, cur, dir = e.args[1:]
    else:
      thread = e.args[1]
      mu_board, cur, dir = thread.mu_board, thread.cur, thread.dir
  
    for mu_board_debugger in self.mu_debugger.mu_board_debuggers:
      if mu_board_debugger.mu_board is mu_board:
        cur_i, cur_j = cur
        dir_i, dir_j = dir
        pos = "%d.%d" % (cur_i+1, cur_j)
        #mu_board_debugger.xboard_debugger.field.set_insert_mode()
        mu_board_debugger.xboard_debugger.field.delete(pos)
        mu_board_debugger.xboard_debugger.field.insert(pos, self.mu.i2a(mu_board.matrix[cur_i][cur_j]), "error")
        #mu_board_debugger.xboard_debugger.field.set_debug_mode()
        self.message_window(message, title="Error", label_kw_args=dict(font=("Courier new", 6), justify=LEFT))
        #self.mu_debugger.disabled = True

  def message_window(self, message, title="", label_kw_args=None):
    window = Tk()
    window.title(title)
    frame = Frame(window)
    button = Button(frame, text="Quit", command=window.destroy)
    button.pack()
    if label_kw_args is None:
      label_kw_args = {}
    if not 'width' in label_kw_args:
      label_kw_args['width'] = max(len(l) for l in message.split('\n'))
    if not 'height' in label_kw_args:
      label_kw_args['height'] = message.count('\n')
    label = Label(window, text=message, **label_kw_args)
    label.pack()
    frame.focus_set()
    frame.bind('<q>', lambda event: window.destroy())
    self.focus_set()
    frame.pack()

  def step_num_decrease_10(self):
    self.step_num_decrease(10)

  def step_num_increase_10(self):
    self.step_num_increase(10)

  def step_num_decrease(self, value=1):
    self.step_num -= value
    if self.step_num < 1:
      self.step_num = 1
    self.step_num_value['text'] = str(self.step_num)

  def step_num_increase(self, value=1):
    self.step_num += value
    self.step_num_value['text'] = str(self.step_num)

  def repeatinterval_decrease_10(self):
    self.repeatinterval_decrease(10)

  def repeatinterval_increase_10(self):
    self.repeatinterval_increase(10)

  def repeatinterval_decrease(self, value=1):
    self.repeatinterval -= value
    if self.repeatinterval < 1:
      self.repeatinterval = 1
    self.repeatinterval_value['text'] = str(self.repeatinterval)
    for button in (	self.step_button,
			self.step_num_increase_10_button, self.step_num_increase_button,
			self.step_num_decrease_10_button, self.step_num_increase_button,
			self.repeatinterval_increase_10_button, self.repeatinterval_increase_button,
			self.repeatinterval_decrease_10_button, self.repeatinterval_increase_button,
    ):
      button['repeatinterval'] = int(self.repeatinterval)

  def repeatinterval_increase(self, value=1):
    self.repeatinterval += value
    self.repeatinterval_value['text'] = str(self.repeatinterval)
    for button in (	self.step_button,
			self.step_num_increase_10_button, self.step_num_increase_button,
			self.step_num_decrease_10_button, self.step_num_increase_button,
			self.repeatinterval_increase_10_button, self.repeatinterval_increase_button,
			self.repeatinterval_decrease_10_button, self.repeatinterval_increase_button,
    ):
      button['repeatinterval'] = int(self.repeatinterval)

class Mu_XBoardDebugger(Mu_BoardDebugger):
  def __init__(self, mu_board, mu_debugger, *l_args, **d_args):
    super(Mu_XBoardDebugger, self).__init__(mu_board, mu_debugger, *l_args, **d_args)
    self.new_seen = []
    self.prev_seen = []

  def set_seen_cur(self, thread, cur_i, cur_j):
    self.new_seen.append((thread, cur_i, cur_j))

  def set_seen_thread(self, thread):
    cur_i, cur_j = thread.cur
    self.new_seen.append((thread, thread.cur))

  def update(self):
    for cur_thread, cur_i, cur_j in self.prev_seen:
      pos = "%d.%d" % (cur_i+1, cur_j)
      self.xboard_debugger.field.delete(pos)
      self.xboard_debugger.field.insert(pos, self.mu.i2a(self.mu_board.matrix[cur_i][cur_j]), "seen")
    if self.new_seen:
      ave_i, ave_j = 0, 0
      for cur_thread, cur_i, cur_j in self.new_seen:
        if cur_thread:
          if cur_thread.is_held:
            style = "current_held"
          elif cur_thread.is_waiting:
            style = "current_waiting"
          else:
            style = "current_active"
            ave_i += cur_i
            ave_j += cur_j
        else:
          style = "seen"
        pos = "%d.%d" % (cur_i+1, cur_j)
        self.xboard_debugger.field.delete(pos)
        self.xboard_debugger.field.insert(pos, self.mu.i2a(self.mu_board.matrix[cur_i][cur_j]), style)
        self.xboard_debugger.focus_set()
      ave_i /= float(len(self.new_seen))
      ave_j /= float(len(self.new_seen))
      self.xboard_debugger.field.see("%d.%d" % (ave_i+1, ave_j))
      self.prev_seen = self.new_seen[:]
      del self.new_seen[:]

class Mu_XDebugger(Mu_Debugger):
  def __init__(self,	mu,
			debug_threads=False,
			debug_num_steps=True
    ):
    super(Mu_XDebugger, self).__init__(
						mu,
						debug_threads=debug_threads,
						debug_num_steps=debug_num_steps,
    )
    self.disabled = False

  def add_board_debugger(self, board_debugger):
    super(Mu_XDebugger, self).add_board_debugger(board_debugger)

  def quit(self):
    self.root.destroy()
    
  def iteration(self):
    return "ITN=%d" % self.mu.itn

  def update_completed(self, completed):
    self.xdebugger.itn['text'] = self.iteration() 
    #self.xdebugger.console_text.delete("1.0", END)
    #self.xdebugger.console_text.insert("1.0", str(self.mu.console), "output")
    if self.mu.itn == self.mu.console.last_itn:
      sym = self.mu.console.last_sym
      if sym == '\b':
        text_index = self.xdebugger.console_text.index(END)
        s_row, s_col = text_index.split('.')
        row = int(s_row)
        col = int(s_col)
        if col == 0:
          row = row-1
        col = "end-1c"
        self.xdebugger.console_text.delete("%s.%s" % (row, col))
      else:
        self.xdebugger.console_text.insert(END, str(sym), "output")
      self.xdebugger.console_text.see(END)
    if completed:
      if self._update is None:
        self._update = True
      else:
        self._update = False
      update = self._update
    else:
      update = True
    if update:
      #self.xdebugger.field.set_insert_mode()
      for mu_board_debugger in self.mu_board_debuggers:
        mu_board_debugger.update()
      #self.xdebugger.field.set_debug_mode()
    self.xdebugger.pack()

  def run(self):
    self._update = None
    self.root = Tk()
    self.xdebugger = Mu_XDebugger_Widget(self.root, self)
    self.xdebugger.pack()
    self.xdebugger.run()
    try:
      super(Mu_XDebugger, self).run_init()
    except Mu_Error, e:
      self.xdebugger.exception(e)
    self.root.mainloop()

  def run_step(self):
    super(Mu_XDebugger, self).run_step()
