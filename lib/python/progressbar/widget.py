#!/usr/bin/env python
# -*- coding: utf-8 -*-

import terminal
from format import *
from span import *
import sys
import time
import timer


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

Color = Formatter

class Widget(object):
  def __init__(self, children=None, formatter=None, span=None):
    self.set_formatter(formatter)
    self.children = []
    self.parent = None
    if span is None:
      span = FillerSpan()
    elif isinstance(span, int):
      span = FixedSpan(span)
    elif isinstance(span, float):
      if span < 0.0:
        span = FreePercentualSpan(-span)
      else:
        span = TotalPercentualSpan(span)
    else:
      assert isinstance(span, SizedObj), "invalid span type %d" % type(span).__name__ #if isinstance(span, SizedObj):
    self.span = span
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
      self.format = self.formatter.format_string_in_place

  def _default_formatter(self, out):
    pass

  def add_child(self, child, position=None):
    assert isinstance(child, Widget)
    assert child.parent is None
    child.parent = self
    if position is None:
      self.children.append(child)
    else:
      self.children.insert(position, child)
    self.span.add_child(child.span)
      
  def reset(self):
    self.span.reset()

  def get_size(self):
    return self.span.get_size()

  def content(self):
    out = FormattedString()
    for child in self.children:
      #print '  *** ', child, repr(child.content())
      out.extend(child.content())
    self.format(out)
    return out

class Screen(Widget):
  FORMATTER = {
	'error':	Formatter('red'),
	'warning':	Formatter('yellow'),
	'comment':	Formatter('blue'),
  }
  def __init__(self, lines, span=None, formatter=None, stream=sys.stderr):
    if span is None:
      span = FixedSpan(TERMINAL_W*TERMINAL_H)
    super(Screen, self).__init__(children=lines, span=span, formatter=formatter)
    self.lines = self.children
    self.stream = stream

  #def add_child(self, child, position=None:
  #  super(Screen, self).add_child(child, position=position)

  def start(self):
    self._first_time = True
    self.span.set_root()
    self.span.update()
    super(Screen, self).start()

  def restart(self):
    self.clear()
    self.start()

  def content(self):
    out = FormattedString()
    out.extend(self.clear_content())
    if self.lines:
      for line in self.lines[:-1]:
        out.extend(line.content())
        out.append('\n')
      out.extend(self.lines[-1].content())
    self.format(out)
    return out

  def clear_content(self):
    if self._first_time:
      self._first_time = False
      return FormattedString()
    else:
      return FormattedString([Format((len(self.lines)-1)*(terminal.UP+terminal.BOL+terminal.CLEAR_EOL))])

  def write(self, out):
    self.stream.write((u''.join(unicode(e) for e in out)).encode("utf-8"))
    self.stream.flush()
    
  def clear(self):
    self.write(self.clear_content())

  def render(self):
    self.span.root.update()
    content = self.content()
    self.write(content)

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

class Line(Widget):
  def __init__(self, children=None, span=None, *largs, **dargs):
    if span is None:
      span = FixedSpan(TERMINAL_W)
    super(Line, self).__init__(span=span, children=children, *largs, **dargs)

#  def content(self):
#    text = super(Line, self).content()
#    for e in text:
#      if '`' in e and not '\\' in e:
#        print ">>> {%s}" % list(e)
#        raw_input('!!!!!')
#    return text

#RE_ANSI_ESCAPE_CODES = re.compile('|'.join(re.escape(e) for e in terminal.ANSI_ESCAPE_CODES))

class Text(Widget):
  LEFT = "left"
  CENTER = "center"
  RIGHT = "right"
  DEFAULT_CUT = RIGHT
  DEFAULT_CUT_MARKER = ''
  DEFAULT_FILL= ' '
  DEFAULT_JUSTIFY= LEFT
  
  def __init__(self, text="", justify=None, fill=None, cut_marker=None, cut=None, formatter=None, span=None):
    if span is None:
      span = AdaptiveSpan()
    super(Text, self).__init__(formatter=formatter, span=span)
    if justify is None:
      justify = self.DEFAULT_JUSTIFY
    if fill is None:
      fill = self.DEFAULT_FILL
    if cut is None:
      cut = self.DEFAULT_CUT
    if cut is None:
      cut = self.DEFAULT_CUT_MARKER
    if cut_marker is None:
      cut_marker = ''
    self.justify = justify
    self.fill = FormattedString(fill)
    self.cut = cut
    self.cut_marker = FormattedString(cut_marker)
    self.set_text(text)

  def set_text(self, text, size=None):
    self.text = FormattedString(text)
    if isinstance(self.span, AdaptiveSpan):
      self.span.set_size(len(self.text))
    elif size is not None:
      self.span.set_size(size)

  def get_text(self):
    return self.text

  def _justify(self, text):
    size = self.span.get_size()
    if size is None:
      return text
    if len(text) <= size:
      if self.justify == self.LEFT:
        return text.ljust(size, self.fill)
      elif self.justify == self.CENTER:
        return text.center(size, self.fill)
      elif self.justify == self.RIGHT:
        return text.rjust(size, self.fill)
    else:
      n = len(text)-(size-len(self.cut_marker))
      if self.cut == self.LEFT:
        txt = self.cut_marker + text[n:]
      elif self.cut == self.CENTER:
        k = (self._size-len(self.cut_marker))
        k2 = k//2
        k3 = (k+1)//2
        txt = text[:k2] + self.cut_marker + text [-k3:]
      elif self.cut == self.RIGHT:
        txt = text[:-n] + self.cut_marker
      assert len(txt) == size, "len(txt) != size: %d != %d" % (len(txt), size)
      #print ">>> {%s}" % text
      #print "<<< {%s}" % txt
      #raw_input('ss')
      return txt
    
  def content(self):
    text = self._justify(self.text)
    assert self.span.get_size() >= len(text)
    out = FormattedString(text)
    self.format(out)
    return out

class Filler(Widget):
  def __init__(self, fill=' ', before=None, after=None, span=None, size=None, formatter=None):
    super(Filler, self).__init__(span=span, formatter=formatter)
    self.fill = FormattedString(fill)
    self.before = FormattedString(before)
    self.after = FormattedString(after)
 
  def content(self):
    size = self.span.get_size()
    if self.before is not None:
      size -= len(self.before)
      b = self.before
    else:
      b = ''
    if self.after is not None:
      size -= len(self.after)
      a = self.after
    else:
      a = ''
    if len(self.fill) == 1:
      t = self.fill*size
    else:
      t = self.fill*(size//len(self.fill))
      t += self.fill[:size-len(t)]
    assert len(t) == size
    out = b + t + a
    self.format(out)
    return out
 
class Segment(Filler):
  def __init__(self, block, begin=u"", end=u"", formatter=None, length=0):
    super(Segment, self).__init__(span=FreePercentualSpan(0.0), formatter=formatter)
    self.block = FormattedString(block)
    self.begin = FormattedString(begin)
    self.end = FormattedString(end)

  def content(self):
    size = self.get_size()
    if size == 0:
      return FormattedString()
    l = size
    if len(self.begin) > 0:
      l -= len(self.begin)
    if len(self.end) > 0:
      l -= len(self.end)
    if len(self.block) == 1:
      t = self.block*l
    else:
      t = self.block*(l//len(self.block))
      t += self.block[:l-len(t)]
    assert len(t) == l, "len(t) != l: %d != %d" % (len(t), l)
    out = self.begin + t + self.end
    self.format(out)
    return out

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

class Value(Text):
  def __init__(self, span=None, formatter=None, format=None, none_value=""):
    if format is None:
      format = "%s"
    super(Value, self).__init__(span=span, formatter=formatter, justify=Text.RIGHT, cut_marker='')
    self._format = format
    self.none_value = FormattedString(none_value)
    self.set_value(None)

  def set_value(self, value):
    if value is None:
      self.set_text(self.none_value)
    else:
      self.set_text(self._format%value)

class Boolean(Value):
  def __init__(self, span=None, formatter=None, format=None, none_value=None, true_value='T', false_value='F'):
    if format is None:
      format = "%s"
    self.true_value = true_value
    self.false_value = false_value
    if none_value is None:
      none_value = self.false_value
    super(Boolean, self).__init__(span=span, formatter=formatter, format=format, none_value=none_value)

  def set_value(self, value):
    if value is None:
      self.set_text(self.none_value)
    elif value:
      self.set_text(self.true_value)
    else:
      self.set_text(self.false_value)

class Enabled(Text):
  def __init__(self, enabled, disabled=u'◉', on=u'◉', off=u'◉', disabled_formatter=None, on_formatter=None, off_formatter=None, span=1):
    if on_formatter is None:
      on_formatter = Formatter("red")
    if off_formatter is None:
      off_formatter = Formatter("green")
    if disabled_formatter is None:
      disabled_formatter = Formatter("black")
    self.on_formatter = on_formatter
    self.off_formatter = off_formatter
    self.disabled_formatter = disabled_formatter
    self.on = on
    self.off = off
    self.disabled = disabled
    
  def set_value(self, enabled):
    if enabled is None:
      self.set_formatter(self.disabled_formatter)
      self.set_text(self.disabled)
    elif enabled:
      self.set_formatter(self.on_formatter)
      self.set_text(self.on)
    else:
      self.set_formatter(self.off_formatter)
      self.set_text(self.off)

class Integer(Value):
  def __init__(self, span=None, formatter=None, format=None, none_value="--"):
    if format is None:
      format = "%d"
    super(Integer, self).__init__(span=span, formatter=formatter, format=format, none_value=none_value)

class Float(Value):
  def __init__(self, span=None, formatter=None, format=None, none_value="--"):
    if format is None:
      format = "%%%d.2f" % span
    super(Float, self).__init__(span=span, formatter=formatter, format=format, none_value=none_value)

class Percentage(Float):
  def __init__(self, span=None, formatter=None, format=None, none_value="--"):
    if format is None:
      format = "%3.2f%%"
      if span is None:
        span = FixedSpan(7)
    super(Percentage, self).__init__(span=span, formatter=formatter, format=format, none_value=none_value)

class Duration(Value):
  INF = 'inf'
  def __init__(self, span=None, formatter=None, format=None, none_value=None):
    if format is None:
      format = "%(days)d+%(hours)02d:%(minutes)02d:%(seconds)02d.%(microseconds)02d"
    self.duration_format = format
    d = {
		'days':			0,
		'hours':		0,
		'minutes':		0,
		'seconds':		0,
		'microseconds':		0,
		'tot_days':		0.0,
		'tot_hours':		0.0,
		'tot_minutes':		0.0,
		'tot_seconds':		0.0,
		'tot_microseconds':	0.0,
    }
    zero = self.duration_format % d
    if none_value is None:
      none_value = zero
    self.none_value = none_value
    super(Duration, self).__init__(span=span, formatter=formatter, format="%s", none_value=none_value)

  def set_value(self, seconds):
    if seconds is None or seconds == self.INF:
      duration = None
    else:
      dd, rem = divmod(seconds, 86400)
      hh, rem = divmod(rem, 3600)
      mm, rem = divmod(rem, 60)
      ss = round(rem, 2)
      si = int(ss)
      sm = 100.0*(ss-si)
      d = {
		'days':			dd,
		'hours':		hh,
		'minutes':		mm,
		'seconds':		ss,
		'microseconds':		sm,
		'tot_days':		seconds/86400.0,
		'tot_hours':		seconds/3600.0,
		'tot_minutes':		seconds/60.0,
		'tot_seconds':		seconds,
		'tot_microseconds':	seconds*1000000,
      }
      duration = self.duration_format % d
    super(Duration, self).set_value(duration)

class SimpleProgressBar(Widget, ProgressBarMixIn):
  DEFAULT_SEGMENTS = (
			Segment(u'▣', formatter=Color('green')),
			Segment(u'□', formatter=Color('black')),
  )
  def __init__(self, segments=None, formatter=None, span=None, max_value=None, children=None):
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
    super(SimpleProgressBar, self).__init__(span=span, children=children, formatter=formatter)
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

  def get_elapsed_duration_widget(self, span=None, format=None, none_value=None):
    if self.elapsed_duration_widget is None:
      if format is None:
        format = "%(minutes)02d:%(seconds)02d"
        if span is None:
          span = FixedSpan(5)
      self.elapsed_duration_widget = Duration(span=span, format=format, none_value=none_value)
    return self.elapsed_duration_widget

  def get_remaining_duration_widget(self, span=None, format=None, none_value=None):
    if self.remaining_duration_widget is None:
      if format is None:
        format = "%(minutes)02d:%(seconds)02d"
        if span is None:
          span = FixedSpan(5)
      self.remaining_duration_widget = Duration(span=span, format=format, none_value=none_value)
    return self.remaining_duration_widget

  def get_completed_percentage_widget(self, span=None):
    if self.completed_percentage_widget is None:
      self.completed_percentage_widget = Percentage(span=span)
    return self.completed_percentage_widget

  def get_percentage_widgets(self, span=None):
    if self.percentage_widgets is None:
      self.percentage_widgets = []
      for segment in self.segments:
        widget = Percentage(span=span)
        self.percentage_widgets.append(widget)
    return tuple(self.percentage_widgets)

  def get_value_widgets(self, span=None):
    if self.value_widgets is None:
      self.value_widgets = []
      if span is None:
        size = self._get_digits()
      for segment in self.segments:
        if span is None:
          use_span = FixedSpan(size)
        else:
          use_span = span
        widget = Integer(span=span)
        self.value_widgets.append(widget)
    return tuple(self.value_widgets)

  def _get_digits(self):
    if self.max_value is None:
      return 8
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

  def get_max_value_widget(self, span=None):
    if self.max_value_widget is None:
      if span is None:
        span = FixedSpan(self._get_digits())
      self.max_value_widget = Integer(span=span)
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
    for segment, percentage in zip(self.segments, self.percentages):
      segment.span.set_percentage(percentage)
      #segment.span.update()

  def _set_widget_values(self, widgets, values):
    for widget, value in zip(widgets, values):
      widget.set_value(value)

  def set_max_value(self, max_value):
    ProgressBarMixIn.set_max_value(self, max_value)
    if self.max_value_widget is not None:
      self.max_value_widget.set_value(self.max_value)

  def set_percentages(self, percentages):
    ProgressBarMixIn.set_percentages(self, percentages)
    self._update()

class ProgressBar(Widget, ProgressBarMixIn):
  def __init__(self, segments=None, before=u'◀', after=u'▶', formatter=None, span=None, max_value=None):
    self.simple_progressbar = SimpleProgressBar(segments=segments, formatter=formatter, span=FillerSpan(), max_value=max_value)
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
    Widget.__init__(self, children=widgets, span=span, formatter=formatter)
    #super(ProgressBar, self).__init__(children=widgets, span=span, formatter=formatter)
    ProgressBarMixIn.__init__(self, self.simple_progressbar.length, max_value=self.simple_progressbar.max_value)
			
  def set_max_value(self, max_value):
    return self.simple_progressbar.set_max_value(max_value)

  def set_values(self, values):
    return self.simple_progressbar.set_values(values)

  def set_percentages(self, percentages):
    return self.simple_progressbar.set_percentages(percentages)

class Timer(Widget, timer.Timer):
  def __init__(self, label, message=None, max_ticks=None, started=True, formatter=None, span=None):
    timer.Timer.__init__(self, label, message=message, max_ticks=max_ticks, started=started)
    self.wmessage = Text(self.message)
    self.wenabled = Enabled(self.started)
    self.welapsed = Duration()
    if self.max_ticks:
      digits = self._get_tick_digits()
      self.wticks = Integer(span=digits)
      self.wmax_ticks = Integer(span=digits)
      self.wpercentage = Percentage()
      self.wprogressbar = SimpleProgressBar()
      self.wremaining = Duration()
      children = (
			self.wmessage,
			' ',
			self.wenabled,
			' ',
			self.wticks,
			'/',
			self.wmax_ticks,
			'[',
			self.wpercentage,
			']',
			self.wprogressbar,
			' ',
			self.welapsed,
			'/',
			self.wremaining,
      )
    else:
      self.wticks = Integer(span=8)
      children = (
			self.wmessage,
			' ',
			self.wenabled,
			' ',
			self.wticks,
			' ',
			self.welapsed,
      )
    widget.__init__(self, children=children, formatter=formatter, span=span)

  

### HERE
def main():
  pb0 = SimpleProgressBar(
			(
				Segment(u'▣', formatter=Color('red')),
				Segment(u'▣', formatter=Color('green')),
				Segment(u'□', formatter=Color('blue')),
			),
			span=-30.0,
  )
  pb1 = ProgressBar(
			(u'█', u'_'),
			span=-70.0,
  )
  pb2 = SimpleProgressBar(
			(
				Segment(u'█', formatter=Color("green"), end='>'),
				Segment(u'░', begin='<'),
			),
			span=-40.0,
  )
  pb3 = SimpleProgressBar(
			(
				Segment('=', formatter=Color("green"), end='|'),
				Segment('-'),
			),
			span=-40.0,
  )
  wt0 = Text(FormattedString(("Mo", Format(terminal.RED), 'n', Format(terminal.NORMAL), "do")))
  #print wt0.text
  #print wt0.text.unformatted_string()
  #print wt0.text.formatted_string()
  #print unicode(wt0.text)
  #raw_input('...')
  screen = Screen([
			Line(
				[
					Text(FormattedString((Format(terminal.BLUE), "Ciao", Format(terminal.NORMAL), '!'))),
					Filler(),
					wt0,
					Filler('.'),
					'[', pb2, ']',
					Filler('_'),
				],
			),
			Line(
				[
					pb0,
					"<|>",
					pb1,
				],
			),
			Line(
				[
					u"alfa",
					Text(u"\\ ", formatter=Formatter("red")),
					u"beta",
				],
			),
			Line(
				[
					Filler('>'),
					Text("Tondo"),
					Filler('<'),
				],
			),
  ])

  #print '.'*80
  #print Format(terminal.BLUE), 'prova', Format(terminal.NORMAL)
  #raw_input('000')
  screen.start()
  print '\n'.join(screen.span.root.dump())
  screen.render()

  import time

  plst = [
		((0.0,	0.0), (0.0, ), "Tondo"),
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
		((25.0,	45.0), (68.0, ), "Tondo"),
		((30.0,	45.0), (70.0, ), "Tondo"),
		((30.0,	50.0), (80.0, ), "Tondo"),
		((30.0,	55.0), (90.0, ), "Tondo"),
		((30.0,	60.0), (95.0, ), "Tondo"),
		((30.0,	65.0), (98.0, ), "Tondo"),
		((35.0,	65.0), (100.0, ), "Tondo"),
  ]
  pb3.start()
  for c, (p0, p1, t) in enumerate(plst):
    if c == 6:
      screen.add_child(Line((Text('new line'), Filler(), pb3, Text('xxx'))), position=1)
    pb0.set_percentages(p0)
    pb1.set_percentages(p1)
    pb2.set_percentages(p1)
    pb3.set_percentages(p1)
    #wt0.set_text(t)
#    if p1[0] > 61.0 and p1[0] < 66.0:
#      screen.error("p1 == %s\n" % p1)
    screen.render()
    #raw_input('...')
    time.sleep(0.3)
    
if __name__ == "__main__":
  main()
