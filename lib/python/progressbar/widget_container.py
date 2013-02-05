#!/usr/bin/env python
# -*- coding: utf-8 -*-

import terminal
from container import *
import sys
import time

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

class Formatter(object):
  def __init__(self, color=None, bg_color=None, underline=False, bold=False):
    self.formats = []
    if color is not None:
      self.formats.append(getattr(terminal, color.upper()))
    if bg_color is not None:
      self.formats.append(getattr(terminal, ("bg_%s"%bg_color).upper()))
    if underline:
      self.formats.append(getattr(terminal, "UNDERLINE"))
    if bold:
      self.formats.append(getattr(terminal, "BOLD"))

  def format(self, out):
    if isinstance(out, tuple):
      out = list(out)
    if self.formats:
      f = ''.join(self.formats)
      out.insert(0, f)
      out.append(terminal.NORMAL)
    return out

  def __call__(self, out):
    return self.format(out)
  
class Color(Formatter):
  def __init__(self, color, bg_color=None):
    super(Color, self).__init__(color=color, bg_color=None)

class Widget(object):
  def __init__(self, children=None, formatter=None, width=None, container=None):
    self.set_formatter(formatter)
    self.children = []
    self.parent = None
    if container is None:
      if width is None:
        container = FillContainer()
      elif isinstance(width, int):
        container = FixedContainer(width)
      elif isinstance(width, float):
        container = PercentageContainer(width)
    self.container = container
    if children:
      for child in children:
        if isinstance(child, basestring):
          child = Text(child)
        self.add_child(child)
    self.started = False

  def start(self):
    self.started = True
    for child in self.children:
      child.start()

  def stop(self):
    self.started = True
    for child in self.children:
      child.stop()

  def set_formatter(self, formatter):
    if formatter is None:
      self.formatter = None
      self.format = self._default_formatter
    else:
      self.formatter = formatter
      self.format = self.formatter.format
  def _default_formatter(self, out):
    return out

  def add_child(self, child):
    assert isinstance(child, Widget)
    assert child.parent is None
    child.parent = self
    self.children.append(child)
    child.parent.container.add_child(child.container)
      
  def reset(self):
    self.container.reset()
    self.container.dump()

  def get_width(self):
    return self.container.width

  def content(self):
    out = []
    for child in self.children:
      out.extend(child.content())
    return self.format(out)

class TextFiller(Widget):
  LEFT = "left"
  CENTER = "center"
  RIGHT = "right"
  def __init__(self, width, text="", justify=None, fill=' ', cut_marker='...', cut=None, formatter=None):
    self.fixed_width = width
    if width is None:
      # force a fixed container
      width = 0
    super(TextFiller, self).__init__(formatter=formatter, width=width)
    if justify is None:
      justify = self.LEFT
    self.justify = justify
    self.fill = fill
    if cut is None:
      cut = self.LEFT
    self.cut = cut
    self.cut_marker = cut_marker
    self.fill = fill

  def set_text(self, text):
    self.text = self._justify(text)
    if self.fixed_width is None:
      self.container.set_fixed_width(len(self.text))

  def _justify(self, text):
    if self.fixed_width is None:
      return text
    if self.container.width is None:
      width = self.fixed_width
    else:
      width = self.container.width
    if width is None:
      return text
    if len(text) <= width:
      if self.justify is self.LEFT:
        return text.ljust(width, self.fill)
      elif self.justify is self.CENTER:
        return text.center(width, self.fill)
      elif self.justify is self.RIGHT:
        return text.rjust(width, self.fill)
    else:
      n = len(text)-(width-len(self.cut_marker))
      if self.cut is self.LEFT:
        return self.cut_marker + text[n:]
      elif self.cut is self.CENTER:
        k = (self._width-len(self.cut_marker))
        k2 = k//2
        k3 = (k+1)//2
        return text[:k2] + self.cut_marker + text [-k3:]
      elif self.cut is self.RIGHT:
        return text[:-n] + self.cut_marker
    
  def content(self):
    return self.format([self.text])

class Text(Widget):
  def __init__(self, text, *largs, **dargs):
    container = FixedContainer(len(text))
    super(Text, self).__init__(container=container, *largs, **dargs)
    self.set_text(text)

  def set_text(self, text):
    self.text = text
    self.container.set_fixed_width(len(text))

  def content(self):
    return self.format([self.text])

class Segment(Widget):
  def __init__(self, block, begin=u"", end=u"", formatter=None, length=0):
    super(Segment, self).__init__(container=FixedContainer(0), formatter=formatter)
    self.block = unicode(block)
    self.begin = begin
    self.end = end
    self.set_length(length)

  def set_length(self, length):
    self.length = length
    self.container.set_width(length)

  def content(self):
    if self.length == 0:
      return []
    l = self.length
    if len(self.begin) > 0:
      l -= len(self.begin)
    if len(self.end) > 0:
      l -= len(self.end)
    if len(self.block) == 1:
      t = self.block*l
    else:
      t = self.block*(l//len(self.block))
      t += self.block[:l-len(t)]
    return self.format([self.begin, t, self.end])

class Value(TextFiller):
  def __init__(self, width, format, none_value=""):
    super(Value, self).__init__(width=width, justify=TextFiller.RIGHT, cut_marker='')
    self._format = format
    self.none_value = none_value
    self.set_value(None)

  def set_value(self, value):
    if value is None:
      self.set_text(self.none_value)
    else:
      #print value, self._format, self._format%value, '\n\n\n\n'
      self.set_text(self._format%value)

class Integer(Value):
  def __init__(self, width=8, format=None, none_value="--"):
    if format is None:
      format = "%d"
    super(Integer, self).__init__(width=width, format=format)

class Float(Value):
  def __init__(self, width=10, format=None, none_value="--"):
    if format is None:
      format = "%%%d.2f" % width
    super(Float, self).__init__(width=width, format=format, none_value=none_value)

class Percentage(Float):
  def __init__(self, width=7, format=None, none_value="--"):
    if format is None:
      if width is None:
        format = "%.2f%%"
      else:
        format = "%%%d.2f%%%%" % width
    super(Percentage, self).__init__(width=width, format=format, none_value=none_value)

class Duration(Value):
  INF = 'inf'
  def __init__(self, width=None, format=None, none_value=None):
    #width = 10
    if format is None:
      format = "%(days)d+%(hours)02d:%(minutes)02d:%(seconds)02d.%(microseconds)02d"
    self.duration_format = format
    d = {
		'days':		0,
		'hours':	0,
		'minutes':	0,
		'seconds':	0,
		'microseconds':	0,
    }
    zero = self.duration_format % d
    if none_value is None:
      none_value = zero
    self.none_value = none_value
    super(Duration, self).__init__(width=width, format="%s", none_value=none_value)

  def set_value(self, seconds):
    if seconds is None or seconds == self.INF:
      duration = None
    #elif seconds == self.INF:
    #  w = self.container.width
    #  duration = ' '*(w-4) + "+inf"
    else:
      dd, rem = divmod(seconds, 86400)
      hh, rem = divmod(rem, 3600)
      mm, rem = divmod(rem, 60)
      ss = round(rem, 2)
      si = int(ss)
      sm = 100.0*(ss-si)
      d = {
		'days':		dd,
		'hours':	hh,
		'minutes':	mm,
		'seconds':	ss,
		'microseconds':	sm,
      }
      duration = self.duration_format % d
    super(Duration, self).set_value(duration)
      #l = []
      #l.append("%02d:%02d:%02d.%02d" % (hh, mm, si, sm))
      #if dd:
      #  l.append("+%d" % dd)
      #duration = ':'.join(l)
        
    #print seconds, duration, '\n\n\n\n'
    #time.sleep(0.4)

class ProgressBarMixIn(object):
  def __init__(self, length, max_value=None):
    self.length = length
    self.percentages = tuple(None for i in xrange(self.length))
    self.values = tuple(None for i in xrange(self.length))
    self.max_value = max_value

  def set_max_value(self, max_value):
    self.max_value = max_value
    if self.values is None:
      self.values = tuple((self.max_value*(percentage/100.0)) for percentage in self.percentages)

  def set_percentages(self, percentages):
    if len(percentages) == self.length-1:
      sum_p = sum(percentages)
      percentages = list(percentages)+[100.0-sum_p]
    assert len(percentages) == self.length, "invalid length %d != %d" % (len(percentages), self.length)
    self.percentages = tuple(percentages)
    if self.max_value is not None:
      self.values = tuple((self.max_value*(percentage/100.0)) for percentage in self.percentages)
    
  def set_values(self, values):
    assert self.max_value is not None, "cannot set by values: max_value is undefined"
    if len(values) == self.length-1:
      sum_v = sum(values)
      values = list(values)+[self.max_value-sum_v]
    assert len(values) == self.length, "invalid length %d != %d" % (len(values), self.length)
    self.values = tuple(values)
    self.percentages = tuple((value*100.0/self.max_value) for value in self.values)

class SimpleProgressBar(Widget, ProgressBarMixIn):
  DEFAULT_SEGMENTS = (
			Segment(u'▣', formatter=Color('green')),
			Segment(u'□', formatter=Color('black')),
  )
  def __init__(self, segments=None, formatter=None, container=None, width=None, max_value=None, children=None):
    children = []
    if segments is None:
      segments = self.DEFAULT_SEGMENTS
    for segment in segments:
      if isinstance(segment, basestring):
        segment = Segment(segment)
      else:
        assert isinstance(segment, Widget)
      children.append(segment)
    self.max_value = max_value
    super(SimpleProgressBar, self).__init__(container=container, children=children, formatter=formatter, width=width)
    self.segments = self.children
    ProgressBarMixIn.__init__(self, len(self.segments), max_value=max_value)

    #self.percentages = tuple(0.0 for segment in self.segments)
    #self.values = tuple(0 for segment in self.segments)
    #self.percentages = None
    #self.values = None
    #self.max_value = 100
    self.percentage_widgets = None
    self.value_widgets = None
    self.max_value_widget = None
    self.last_timing = None
    self.elapsed_seconds = 0
    self.elapsed_duration_widget = None
    self.remaining_duration_widget = None
    self.completed_percentage_widget = None

  def start(self):
    self.last_timing = time.time()
    if not self.started:
      self.set_percentages(tuple(0.0 for segment in self.segments[:-1]))
      self.elapsed_seconds = 0
    super(SimpleProgressBar, self).start()

  def stop(self):
    timing = time.time()
    self.elapsed_seconds += timing-self.last_timing
    self.last_timing = timing
    super(SimpleProgressBar, self).start()

  def get_elapsed_duration_widget(self, width=None, format=None, none_value=None):
    if self.elapsed_duration_widget is None:
      if format is None:
        format = "%(minutes)02d:%(seconds)02d"
      self.elapsed_duration_widget = Duration(width=width, format=format, none_value=none_value)
    return self.elapsed_duration_widget

  def get_remaining_duration_widget(self, width=None, format=None, none_value=None):
    if self.remaining_duration_widget is None:
      if format is None:
        format = "%(minutes)02d:%(seconds)02d"
      self.remaining_duration_widget = Duration(width=width, format=format, none_value=none_value)
    return self.remaining_duration_widget

  def get_completed_percentage_widget(self, width=None):
    if self.completed_percentage_widget is None:
      self.completed_percentage_widget = Percentage(width=width)
    return self.completed_percentage_widget

  def get_percentage_widgets(self, width=None):
    if self.percentage_widgets is None:
      self.percentage_widgets = []
      for segment in self.segments:
        widget = Percentage(width=width)
        self.percentage_widgets.append(widget)
    return tuple(self.percentage_widgets)

  def get_value_widgets(self, width=None):
    if self.value_widgets is None:
      self.value_widgets = []
      if width is None:
        width = self._get_digits()
      for segment in self.segments:
        widget = Integer(width=width)
        self.value_widgets.append(widget)
    return tuple(self.value_widgets)

  def _get_digits(self):
    if self.max_value is None:
      return None
    else:
      if self.max_value < 10:
        return 1
      elif self.max_value < 100:
        return 2
      elif self.max_value < 1000:
        return 3
      elif self.max_value < 10000:
        return 4
      elif self.max_value < 100000:
        return 5
      elif self.max_value < 1000000:
        return 6
      elif self.max_value < 10000000:
        return 7
      elif self.max_value < 100000000:
        return 8
      elif self.max_value < 1000000000:
        return 9
      elif self.max_value < 10000000000:
        return 10
      else:
        return 16

  def get_max_value_widget(self, width=None):
    if self.max_value_widget is None:
      if width is None:
        width = self._get_digits()
      self.max_value_widget = Integer(width=width)
      self.max_value_widget.set_value(self.max_value)
    return self.max_value_widget

  def set_values(self, values):
    ProgressBarMixIn.set_values(self, values)
    #if len(values) == len(self.segments)-1:
    #  values = list(values)
    #  values.append(self.max_value-sum(values))
    #assert len(values) == len(self.segments), "wrong number of values: %d != %d" % (len(values), len(self.segments))
    #self.percentages = tuple(((100.0*value)/self.max_value) for value in values)
    self._update()

  def _update(self):
    timing = time.time()
    self.elapsed_seconds += timing-self.last_timing
    self.last_timing = timing
    if self.value_widgets is not None:
      self._set_widget_values(self.value_widgets, self.values)
    if self.percentage_widgets is not None:
      self._set_widget_values(self.percentage_widgets, self.percentages)
    if self.completed_percentage_widget is not None:
      completed_percentage = sum(p for p in self.percentages[:-1])
      self.completed_percentage_widget.set_value(completed_percentage)
    elapsed_seconds = self.elapsed_seconds
    if self.elapsed_duration_widget:
      self.elapsed_duration_widget.set_value(elapsed_seconds)
    if self.remaining_duration_widget:
      percentage = sum(p for p in self.percentages[:-1])
      if percentage == 0.0:
        remaining_seconds = Duration.INF
      else:
        remaining_seconds = self.elapsed_seconds*(100.0-percentage)/percentage
      self.remaining_duration_widget.set_value(remaining_seconds)

  def _set_widget_values(self, widgets, values):
    for widget, value in zip(widgets, values):
      widget.set_value(value)

  def set_max_value(self, max_value):
    ProgressBarMixIn.set_max_value(self, max_value)
    if self.max_value_widget is not None:
      self.max_value_widget.set_value(self.max_value)

  def set_percentages(self, percentages):
    ProgressBarMixIn.set_percentages(self, percentages)
    #if len(percentages) == len(self.segments)-1:
    #  percentages = list(percentages)
    #  percentages.append(100.0-sum(percentages))
    #assert len(percentages) == len(self.segments), "wrong number of percentages: %d != %d" % (len(percentages), len(self.segments))
    #self.percentages = tuple(percentages)
    #if self.max_value is not None:
    #  self.values = tuple(percentage*(self.max_value/100.0) for percentage in self.percentages)
    self._update()

  def content(self):
    width = self.container.width
    l = zip(self.segments, self.percentages)
    sum_w = 0
    for segment, percentage in l[:-1]:
      w = int(round(width*percentage/100.0, 0))
      segment.set_length(w)
      sum_w += w
    segment, percentage = l[-1]
    segment.set_length(width-sum_w)
    out = []
    for segment in self.segments:
      out.extend(segment.content())
    return self.format(out)

class Filler(Widget):
  def __init__(self, fill=' ', before=None, after=None, container=None, width=None, formatter=None):
    super(Filler, self).__init__(container=container, formatter=formatter, width=width)
    self.fill = fill
    self.before = before
    self.after = after
 
  def content(self):
    width = self.container.width
    if self.before is not None:
      width -= len(self.before)
      b = self.before
    else:
      b = ''
    if self.after is not None:
      width -= len(self.after)
      a = self.after
    else:
      a = ''
    if len(self.fill) == 1:
      t = self.fill*width
    else:
      t = self.fill*(width//len(self.fill))
      t += self.fill[:width-len(t)]
    return self.format([b, t, a])
 
class Line(Widget):
  def __init__(self, children=None, width=None, container=None, *largs, **dargs):
    super(Line, self).__init__(children=children, container=FixedContainer(TERMINAL_W), width=width, *largs, **dargs)

class Screen(Widget):
  FORMATTER = {
	'error':	Color('red'),
	'warning':	Color('yellow'),
	'comment':	Color('blue'),
  }
  def __init__(self, lines, formatter=None, stream=sys.stderr):
    super(Screen, self).__init__(container=FixedContainer(TERMINAL_W), children=lines, formatter=formatter)
    self.lines = self.children
    self.stream = stream

  def start(self):
    self._first_time = True
    self.container.initialize()
    self.container.resize()
    super(Screen, self).start()

  def restart(self):
    self.clear()
    self.start()

  def content(self):
    out = []
    out.extend(self.clear_content())
    for line in self.lines:
      out.extend(line.content())
      out.append('\n')
    return self.format(out)

  def clear_content(self):
    if self._first_time:
      self._first_time = False
      return []
    else:
      return [len(self.lines)*(terminal.UP+terminal.BOL+terminal.CLEAR_EOL)]

  def write(self, out):
    self.stream.write((u''.join(out)).encode("utf-8"))
    self.stream.flush()
    
  def clear(self):
    self.write(self.clear_content())

  def render(self):
    self.container.root.resize()
    self.write(self.content())

  def finish(self):
    pass

  def log(self, formatter, out):
    self.clear()
    self.stop()
    self.write(formatter(out))
    self.start()

  def error(self, *out):
    self.log(self.FORMATTER['error'], out)

  def warning(self, *out):
    self.log(self.FORMATTER['warning'], out)

  def comment(self, *out):
    self.log(self.FORMATTER['comment'], out)

class ProgressBar(Widget, ProgressBarMixIn):
  def __init__(self, segments=None, before=u'◀', after=u'▶', formatter=None, container=None, width=None, max_value=None):
    self.simple_progressbar = SimpleProgressBar(segments=segments, formatter=formatter, container=FillContainer(), max_value=max_value)
    self.remaining_duration= self.simple_progressbar.get_remaining_duration_widget()
    self.completed_percentage= self.simple_progressbar.get_completed_percentage_widget()
    self.before = before
    self.after = after
    widgets = (
		self.completed_percentage,
		self.before,
		self.simple_progressbar,
		self.after,
		'[',
		self.remaining_duration,
		']',
    )
    Widget.__init__(self, children=widgets, container=container, width=width, formatter=formatter)
    #super(ProgressBar, self).__init__(children=widgets, container=container, width=width, formatter=formatter)
    ProgressBarMixIn.__init__(self, self.simple_progressbar.length, max_value=self.simple_progressbar.max_value)
			
  def set_max_value(self, max_value):
    return self.simple_progressbar.set_max_value(max_value)

  def set_values(self, values):
    return self.simple_progressbar.set_values(values)

  def set_percentages(self, percentages):
    return self.simple_progressbar.set_percentages(percentages)

if __name__ == "__main__":
  pb0 = SimpleProgressBar(
			(
				Segment(u'▣', formatter=Color('red')),
				Segment(u'▣', formatter=Color('green')),
				Segment(u'□', formatter=Color('blue')),
			),
			width=30.0,
  )
  pb1 = ProgressBar(
			(u'█', u'_'),
			#container=FillContainer(),
			width=70.0,
  )
  pb2 = SimpleProgressBar(
			(
				Segment(u'█', formatter=Color("green"), end='>'),
				Segment(u'░', begin='<'),
			),
			width=40.0,
  )
  wt0 = Text("Mondo")
  wt0 = Text("Mondo")
  screen = Screen([
			Line(
				[
					Text("Ciao"),
					Filler(),
					wt0,
					Filler('.'),
					'[', pb2, ']',
					Filler('_'),
				],
				container=FixedContainer(TERMINAL_W),
			),
			Line(
				[
					pb0,
					"<|>",
					pb1,
				],
				container=FixedContainer(TERMINAL_W),
			),
			Line(
				[
					Filler('>'),
					Text("Mondo"),
					Filler('<'),
				],
				container=FillContainer(),
			),
  ])

  #print '.'*80
  screen.start()
  print '\n'.join(screen.container.root.dump())
  #raw_input('........')
  screen.render()

  import time

  plst = [
		((0.0,	0.0), (0.0, ), "Mondo"),
		((0.0,	5.0), (3.0, ), "Saturno"),
		((0.0,	10.0), (60.0, ), "Venere"),
		((5.0,	10.0), (61.0, ), "Giove"),
		((10.0,	10.0), (63.0, ), "Alpha Centauri"),
		((10.0,	15.0), (64.0, ), "Rigel"),
		((10.0,	20.0), (65.0, ), "Mercurio"),
		((10.0,	25.0), (66.0, ), "Marte"),
		((15.0,	25.0), (66.0, ), "Plutone"),
		((15.0,	30.0), (66.0, ), "Urano"),
		((15.0,	40.0), (66.0, ), "Cerere"),
		((20.0,	45.0), (66.0, ), "Terra"),
		((25.0,	45.0), (68.0, ), "Mondo"),
		((30.0,	45.0), (70.0, ), "Mondo"),
		((30.0,	50.0), (80.0, ), "Mondo"),
		((30.0,	55.0), (90.0, ), "Mondo"),
		((30.0,	60.0), (95.0, ), "Mondo"),
		((30.0,	65.0), (98.0, ), "Mondo"),
		((35.0,	65.0), (100.0, ), "Mondo"),
  ]
  for p0, p1, t in plst:
    pb0.set_percentages(p0)
    pb1.set_percentages(p1)
    pb2.set_percentages(p1)
    wt0.set_text(t)
    if p1[0] > 61.0 and p1[0] < 66.0:
      screen.error("p1 == %s\n" % p1)
    screen.render()
    time.sleep(0.3)
    
