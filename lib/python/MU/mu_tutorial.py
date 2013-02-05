#!/usr/bin/env python

from mu import *
import mu_config
import os
import re

from mu_debug import Mu_Debugger, Mu_BoardDebugger
try:
  from mu_x_debug import Mu_XDebugger, Mu_XBoardDebugger
  Mu_Debugger_Class = Mu_XDebugger
  Mu_BoardDebugger_Class = Mu_XBoardDebugger
except ImportError, e:
  Mu_XDebugger = Mu_Debugger
  Mu_XBoardDebugger = Mu_BoardDebugger
  Mu_Debugger_Class = Mu_Debugger
  Mu_BoardDebugger_Class = Mu_BoardDebugger

class Mu_Tutorial(object):
  def __init__(self,
			tutorial_filename=os.path.join(mu_config.MU_DOCDIR, "README"),
			mu_debugger_class=Mu_Debugger_Class,
			mu_board_debugger_class=Mu_BoardDebugger_Class,
  ):
    tutorial_file = file(tutorial_filename, 'rb')
    mu_text_lines = []
    mu_source_lines = []
    mu_result_lines = []
    mu_debug_num_steps = 1
    last_result = ""
    prev_line_type = None
    re_result = re.compile(r'\$\[result\]')
    for line in tutorial_file:
      line = line.rstrip('\n')
      if line:
        if line[0] == '@':
          new_line_type = "source"
          new_line = line[1:]
          list_lines = mu_source_lines
        elif line[0] == '=':
          new_line_type = "result"
          new_line = line[1:]
          list_lines = mu_result_lines
        else:
          new_line_type = "text"
          new_line = line
          list_lines = mu_text_lines
        try:
          if prev_line_type is not None and prev_line_type != new_line_type:
            if prev_line_type == "text":
              text = "\n".join(mu_text_lines)
              print re_result.sub(last_result, text)
              del mu_text_lines[:]
            elif prev_line_type == "source" and mu_source_lines:
              mu = Mu()
              mu_board = Mu_Board(
                mu,
                mu_source_lines,
              )
              mu_board.show()
              ans = raw_input("[ENTER] to run the code, [d] to view graphic demo, [q] to quit...")
              debug = False
              if ans in ('q', 'Q'):
                return
              elif ans in ('d', 'D'):
                debug = True
                mu_debugger = mu_debugger_class(	mu,
							debug_threads = False,
							debug_num_steps=mu_debug_num_steps,
                )
                mu_board.attach_debugger(mu_board_debugger_class(mu_board, mu_debugger))
                try:
                  mu_debugger.run()
                except Mu_Error, e:
                  e.race(sys.stderr, width=(10, 10))
              else:
                print '>>>', 
                mu.run()
              print
              if debug:
                print '>>>', last_result
              ans = raw_input('[ENTER] to continue, [q] to quit...')
              if ans in ('q', 'Q'):
                return
              last_result = "\n".join(mu_result_lines)
              if last_result != str(mu_board.console):
                print "INTERNAL ERROR: expected <%s>, found <%s>" % (last_result, str(mu_board.console))
                sys.exit(1)
              if debug:
                mu_debug_num_steps = mu_debugger.debug_num_steps
              mu_source_lines = []
              mu_result_lines = []
        finally:
          list_lines.append(new_line)
          prev_line_type = new_line_type
    
