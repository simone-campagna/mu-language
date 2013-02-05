#!/usr/bin/env python

from terminal_size import terminal_size
from progressbar import widget

_COLS, _ROWS = terminal_size()

class Mu_BoardDebugger(object):
  WIDTH = ((_ROWS//2)-7, (_COLS//2)-18)
  FORMATTERS = {
    'DEFAULT':	widget.Formatter(),
  }
  SEEN_FORMATTER = widget.Formatter(color="blue", bg_color="white")
  CUR_FORMATTER = widget.Formatter(color="red", bg_color="white", reverse=True)
  CUR_WAIT_FORMATTER = widget.Formatter(color="black", bg_color="white", reverse=True)
  SELECTED_SEEN_FORMATTER = widget.Formatter(color="blue", bg_color="green")
  SELECTED_CUR_FORMATTER = widget.Formatter(color="red", bg_color="green", reverse=True)
  SELECTED_CUR_WAIT_FORMATTER = widget.Formatter(color="black", bg_color="green", reverse=True)
  def __init__(self, mu_board, mu_debugger, width=None, thread_len=-1):
    self.mu_debugger = mu_debugger
    self.mu_debugger.add_board_debugger(self)
    self.mu_board = mu_board
    self.mu = mu_board.mu
    self._center = None
    self._last_center = None
#    self.seen = [[0 for col in xrange(self.mu_board.max_j)] for row in xrange(self.mu_board.max_i)]
    self.seen = [[[] for col in xrange(self.mu_board.max_j)] for row in xrange(self.mu_board.max_i)]
    if width is None:
      width = self.WIDTH
    self.width = width
    self.thread_len = thread_len

  def set_seen_cur(self, thread, cur_i, cur_j):
    self.seen[cur_i][cur_j].append((thread, self.thread_len, True))

  def set_seen_thread(self, thread):
    self.seen[cur_i][cur_j].append((thread, self.thread_len, True))

  def start(self):
    pass

  def finish(self):
    pass

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

  def _debug_lines__board_map(self, width, center=None, center_thread=None):
    formatter_map = []
    threads = set()
    for cur_i in xrange(self.mu_board.max_i):
      seen_row = self.seen[cur_i]
      for cur_j in xrange(self.mu_board.max_j):
        l = seen_row[cur_j]
        if l:
          thread, ln, is_current = l[-1]
          if thread is not None:
            threads.add(thread)
          cur = cur_i, cur_j
          if is_current:
            if thread is not None and thread.is_waiting:
              if thread is center_thread:
                formatter_map.append((cur, self.SELECTED_CUR_WAIT_FORMATTER))
              else:
                formatter_map.append((cur, self.CUR_WAIT_FORMATTER))
            else:
              if thread is center_thread:
                formatter_map.append((cur, self.SELECTED_CUR_FORMATTER))
              else:
                formatter_map.append((cur, self.CUR_FORMATTER))
          else:
            if thread is not None and thread is center_thread:
              formatter_map.append((cur, self.SELECTED_SEEN_FORMATTER))
            else:
              formatter_map.append((cur, self.SEEN_FORMATTER))
    return_data = {}
    if self._center is not None:
      center = self._center
    elif center is None and center_thread is not None:
      center = center_thread.cur
    lines = self.mu_board.dump_lines(width, threads=threads, center=center, formatter_map=formatter_map, return_data=return_data)
    self._last_center = return_data['center']
    return lines

  def shift_center(self, dir):
    if self._last_center:
      center_i = max(0, min(self.mu_board.max_i-1, self._last_center[0]+dir[0]))
      center_j = max(0, min(self.mu_board.max_j-1, self._last_center[1]+dir[1]))
      self._center = center_i, center_j

  def _debug_lines(self):
    lines = []
    lines.append("Mu_Board<%s>" % self.mu_board.filename)
    lines.extend(self._debug_lines__board_map(self.width))
    if self.mu_debugger.debug_threads:
      for thread_num, thread in enumerate(self.mu.threads.union(self.mu.waiting_threads, self.mu.held_threads)):
        lines.extend((' Thread[%2d]> %s' % (thread_num, line)) for line in [
		"   THREAD:%s" % str(thread),
		"LOC_STACK:%s" % str(thread.local_stack),
		"CUR_STACK:%s" % str(thread.stack)]
        )
    return lines

class Mu_Debugger(object):
  def __init__(self,	mu,
			debug_threads=False,
			debug_num_steps=1
    ):
    self.mu = mu
    self.mu_board_debuggers = []
    self.debug_threads = debug_threads
    self.debug_num_steps = debug_num_steps
    self._debug_skip_num_steps = self.debug_num_steps
    self.prev_threads = set()

  def add_board_debugger(self, mu_board_debugger):
    self.mu_board_debuggers.append(mu_board_debugger)

  def update(self):
    if self.mu.completed or len(self.mu.threads)==0:
      completed = True
    else:
      completed = False
    return self.update_completed(completed)

  def update_completed(self, completed):
    if completed or self._debug_skip_num_steps <= 1:
      hdr = "%4d]" % self.mu.itn
      steps = self.debug_num_steps-self._debug_skip_num_steps+1
      print '\n'.join("%s%s" % (hdr, ''.join(line)) for line in self._debug_lines())
      if completed: 
        return False
      else:
        if steps > 1:
          m = '%d steps' % steps
        else:
          m = '1 step'
        ans = raw_input('Press [Q] to quit, [ENTER] to make %s, <INT> to change step number...'%m)
        if ans in ('Q', 'q'):
          return False
        try:
          n = int(ans)
          self.debug_num_steps = n
        except ValueError, e:
          pass
        self._debug_skip_num_steps = self.debug_num_steps
    else:
      self._debug_skip_num_steps -= 1
    self._refresh_seen()
    return True

  def _refresh_seen(self):
    for mu_board_debugger in self.mu_board_debuggers:
      mu_board_debugger._refresh_seen()
  def start(self):
    for mu_board_debugger in self.mu_board_debuggers:
      mu_board_debugger.start()

  def finish(self):
    for mu_board_debugger in self.mu_board_debuggers:
      mu_board_debugger.finish()

  def run_init(self):
    self.mu.parse()
    return self.update()

  def run(self):
    self.run_init()
    while (not self.mu.completed) and self.mu.threads:
      if not self.run_step():
        break

  def run_step(self):
    if self.mu.threads:
      result = self.mu.run_step()
      active_threads = self.mu.threads.union(self.mu.waiting_threads, self.mu.held_threads)
      threads = active_threads.union(self.prev_threads)
      for thread in threads:
        cur_i, cur_j = thread.cur
        thread.mu_board.board_debugger.set_seen_cur(thread, cur_i, cur_j)
      cont = self.update()
      self.prev_threads = active_threads
      self.update_console(self.mu.console.last_sym)
      return cont
    else:
      return False

  def update_console(self, c):
    pass

  def _debug_lines(self):
    lines = []
    for mu_board in self.mu_board_debuggers:
      lines.extend(mu_board._debug_lines())
    lines.append('  Console>   %s' % repr(self.mu.console))
    return lines

    
        




