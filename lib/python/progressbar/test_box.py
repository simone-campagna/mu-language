#!/usr/bin/env python
# -*- coding: utf-8 -*-


from widget import *

class PBar(Screen):
  ERROR_FORMATTER = Color("red")
  def __init__(self):
    self.boxes = [Text("", span=3) for i in xrange(TERMINAL_H)]
    lines = []
    self.h_size = 0
    self.v_size = 0
    self.text_tl = (u"┏", u" ")
    self.text_hh = (u"━", u" ")
    self.text_tr = (u"┓", u" ")
    self.text_bl = (u"┗", u" ")
    self.text_vv = (u"┃", u" ")
    self.text_br = (u"┛", u" ")
    self.text_cc = (u"░", u" ")
    self.box_lines = []
    for i in xrange(TERMINAL_H):
      box_line = Filler(span=FixedSpan(0))
      self.box_lines.append(box_line)
      line = Line(
			(
				Filler(u" "),
				box_line,
				Filler(u" "),
			),
      )
      lines.append(line)
    super(PBar, self).__init__(lines)
    self.set_size(0, 0)

  def set_size(self, h_size, v_size):
    self.clear_box()
    self.h_size = h_size
    self.v_size = v_size
    self.draw_box()
   
  def draw_box(self):
    self._set_box(0)

  def clear_box(self):
    self._set_box(1)

  def _set_box(self, x):
    hs = (self.h_size+1)*2
    vs = (self.v_size+1)*2
    t_row = TERMINAL_H//2-self.h_size
    b_row = t_row+hs
    #print t_row, b_row
    #raw_input()
    t_line = self.box_lines[t_row]
    t_line.before = self.text_tl[x]
    t_line.fill = self.text_hh[x]
    t_line.after = self.text_tr[x]
    t_line.span.change_size(hs)
    for c_line in self.box_lines[t_row+1:b_row]:
      c_line.before = self.text_vv[x]
      c_line.fill = self.text_cc[x]
      c_line.after = self.text_vv[x]
      c_line.span.change_size(hs)
    b_line = self.box_lines[b_row]
    b_line.before = self.text_bl[x]
    b_line.fill = self.text_hh[x]
    b_line.after = self.text_br[x]
    b_line.span.change_size(hs)

  def log(self, formatter, out):
    self.clear()
    self.write(formatter(out))
    self.start()

  def error(self, *out):
    self.log(self.ERROR_FORMATTER, out)


if __name__ == "__main__":
  pbar = PBar()

  import random
  import time

  pbar.start()
  pbar.render()
  ss_max = min((TERMINAL_H-3)//2, (TERMINAL_W-3)//2)
  growing = True
  for i in (0, 1, 2, 3):
    if growing:
      r = xrange(ss_max)
    else:
      r = xrange(ss_max-1, -1, -1)
    for s in r:
      pbar.set_size(s, s)
      pbar.render()
      time.sleep(0.05)
    growing = not growing
  pbar.finish()
