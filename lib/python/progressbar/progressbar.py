#!/usr/bin/env python
# -*- coding: utf-8 -*-

import terminal
from container import *
import sys

TERMINAL_H = None
TERMINAL_W = None


def _set_terminal_size():
  import terminal_size
  w, h = terminal_size.terminal_size()
  global TERMINAL_H
  TERMINAL_H = h
  global TERMINAL_W
  TERMINAL_W = w

_set_terminal_size()
Container.DEFAULT_WIDTH = TERMINAL_W

class TLine(object):
  def __init__(self, widgets, width=None):
    if width is None:
      width = TERMINAL_W
    self.width = width
    self.widgets = []
    self.widgets_hstatic = []
    self.widgets_hdynamic = []
    for widget in widgets:
     self._add_widget(widget)

  def _add_widget(self, widget):
    if isinstance(widget, basestring):
      widget = TWText(widget)
    assert isinstance(widget, TWidget)
    self.widgets.append(widget)
    if isinstance(widget, TWidgetHDynamic):
      self.widgets_hdynamic.append(widget)
    elif isinstance(widget, TWidgetHStatic):
      self.widgets_hstatic.append(widget)

  def content(self):
    wcontent = {}
    tot_width = 0
    for widget in self.widgets_hstatic:
      content = widget.content()
      wcontent[widget] = content
      tot_width += len(content)
    rem_width = self.width - tot_width
    wsum = float(sum(w.weight for w in self.widgets_hdynamic))
    if self.widgets_hdynamic:
      for widget in self.widgets_hdynamic[:-1]:
        percentage = widget.weight/wsum
        width = int(round(rem_width*percentage, 0))
        content = widget.content(width)
        wcontent[widget] = content
        tot_width += len(content)
      widget = self.widgets_hdynamic[-1]
      width = self.width - tot_width
      content = widget.content(width)
      wcontent[widget] = content
      tot_width += len(content)
    return ''.join(wcontent[widget] for widget in self.widgets)

 
     
      
    
class TWidget(object):
  def __init__(self):
    pass

  def width(self):
    return None

class TWidgetHStatic(TWidget):
  def __init__(self):
    TWidget.__init__(self)

class TWidgetHDynamic(TWidget):
  def __init__(self, weight=1):
    TWidget.__init__(self)
    self.weight = weight

  def content(self, width):
    return None

class TWidgetHFixed(TWidgetHStatic):  
  def __init__(self, width):
    TWidget.__init__(self)
    self.width = width

class TWidgetHVariable(TWidgetHStatic):  
  def __init__(self):
    TWidget.__init__(self)

class TextMixIn(object):
  def __init__(self, text=""):
    self.set_text(text)

  def set_text(self, text):
    self._text = text
    
  def get_text(self):
    return self._text

  text = property(get_text, set_text)

class TWText(TWidgetHVariable, TextMixIn):
  def __init__(self, text=""):
    TWidgetHVariable.__init__(self)
    TextMixIn.__init__(self, text)

  def width(self):
    return len(self._text)

  def content(self):
    return self._text

class TWFixedText(TWidgetHFixed, TextMixIn):
  LEFT = "left"
  RIGTH = "rigth"
  CENTER = "center"
  def __init__(self, width, text="", justify=None, fill=' ', cut_marker='...', cut=None):
    self.fixed_width = width
    if justify is None:
      justify = self.LEFT
    self.justify = justify
    self.fill = fill
    if cut is None:
      cut = self.LEFT
    self.cut = cut
    self.cut_marker = cut_marker
    self.fill = fill
    TWidgetHFixed.__init__(self, width)
    TextMixIn.__init__(self, text)
  
  def _format(self, text):
    if len(text) <= self.width:
      if self.justify is self.LEFT:
        return text.ljust(self.fixed_width, self.fill)
      elif self.justify is self.CENTER:
        return text.center(self.fixed_width, self.fill)
      elif self.justify is self.RIGTH:
        return text.rjust(self.fixed_width, self.fill)
    else:
      n = len(text)-(self.fixed_width-len(self.cut_marker))
      if self.cut is self.LEFT:
        return self.cut_marker + text[n:]
      elif self.cut is self.CENTER:
        k = (self.fixed_width-len(self.cut_marker))
        k2 = k//2
        k3 = (k+1)//2
        return text[:k2] + self.cut_marker + text [-k3:]
      elif self.cut is self.RIGTH:
        return text[:-n] + self.cut_marker
   
  def set_text(self, text):
    TextMixIn.set_text(self, self._format(text))

  def width(self):
    return len(self.text)

  def content(self):
    return self.text

class TWHFill(TWidgetHDynamic):
  def __init__(self, fill, weight=1):
    TWidgetHDynamic.__init__(self, weight)
    self.fill = fill

  def content(self, width):
    if len(self.fill) == 1:
      return self.fill*width
    else:
      t = self.fill*(width//len(self.fill))
      m = width-len(t)
      return t + self.fill[-m:]

class TWProgressBar(TWidgetHDynamic):
  def __init__(self, weight=1, block='#', empty='_', begin="", end="", initial_percentage=0):
    TWidgetHDynamic.__init__(self, weight)
    self.block = block
    self.empty = empty
    self.begin = begin
    self.end = end
    self.percentage = initial_percentage

  def set_percentage(self, percentage):
    self.percentage = percentage
    
  def content(self, width):
    if self.begin:
      width -= len(self.begin)
    if self.end:
      width -= len(self.end)
    num_blocks = int(round(width*self.percentage/100.0, 0))
    return ''.join((self.begin, self.block*num_blocks, self.empty*(width-num_blocks), self.end))
    
class TScreen(object):
  def __init__(self, lines, stream=sys.stderr):
    self.stream = stream
    self.lines = []
    for line in lines:
      self._add_line(line)
    self._first_time = True

  def _add_line(self, line):
    if isinstance(line, (basestring, TWidget)):
      self.lines.append(TLine(line))
    else:
      assert isinstance(line, TLine)
      self.lines.append(line)
    
  def render(self):
    out = []
    if self._first_time:
      self._first_time = False
    else:
      out.append(len(self.lines)*(terminal.UP+terminal.BOL+terminal.CLEAR_EOL))
    for line in self.lines:
      out.append(line.content())
      out.append('\n')
    self.stream.write(''.join(out))

if __name__ == "__main__":
  ms = "ciao"
  ml = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
  w2 = TWHFill(weight=2, fill=':')
  w1 = TWHFill(weight=1, fill='.')
  wp = TWProgressBar(weight=4)
  ts = TScreen( 
		(
			TLine( 
				(
					"[",
					TWFixedText(10, ms, justify=TWFixedText.LEFT),
					TWFixedText(10, ms, justify=TWFixedText.CENTER),
					TWFixedText(10, ms, justify=TWFixedText.RIGTH),
					wp,
					TWFixedText(10, ml, cut=TWFixedText.LEFT),
					TWFixedText(10, ml, cut=TWFixedText.CENTER),
					TWFixedText(10, ml, cut=TWFixedText.RIGTH),
					w2,
					"|",
					w1,
					"]",
				),
			),
			"This is a text line",
			TLine(
				(
					w2, wp,w1,
				),
			)
		)
  )
  
  import time
  for p in (0.0, 1.0, 5.0, 20.0, 30.0):
    wp.set_percentage(p)
    ts.render()
    time.sleep(0.4)
