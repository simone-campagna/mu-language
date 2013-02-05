#!/usr/bin/env python

import resource
import time
import math
import sys

class TimerError(Exception):
  pass

class MetaTimer(type):
  def __new__(self, class_name, class_bases, class_dict):
    class_dict['TIMER'] = {}
    class_dict['CURRENT'] = None
    return type.__new__(self, class_name, class_bases, class_dict)

  def __getitem__(self, label):
    if label in self.TIMER:
      return self.TIMER[label]
    else:
      return Timer(label)

  def register_timer(self, timer):
    assert isinstance(timer, self)
    Timer.TIMER[timer.label] = timer
    Timer.CURRENT = timer
    
  def unregister_timer(self, timer):
    if timer is Timer.CURRENT:
      Timer.CURRENT = None
    del Timer.TIMER[label]

class Timer(object):
  __metaclass__ = MetaTimer
  TIMER = {}
  CURRENT = None
  def __init__(self,label, message=None, max_ticks=None, started=True):
    self.label = label
    if message is None:
      message = label
    self.message = message
    self.max_ticks = max_ticks
    self.ticks = 0
    self.started = False
    self.suspended = False
    if started:
      self.start()
    self.tot_utime = 0.0
    self.tot_etime = 0.0
    self.par_utime = 0.0
    self.par_etime = 0.0
    self.__class__.register_timer(self)
   
  def destroy(self):
    self.__class__.unregister_timer(self)

  #def __del__(self):
  #  if self.started:
  #    self.stop()

  def resume(self):
    if self.started:
      raise TimerError, "%s already started" % self
    self.utime_start = resource.getrusage(resource.RUSAGE_SELF).ru_utime
    self.etime_start = time.time()
    self.started = True
    self.suspended = True
    
  def suspend(self):
    if not self.started:
      raise TimerError, "%s not started" % self
    utime_stop = resource.getrusage(resource.RUSAGE_SELF).ru_utime
    etime_stop = time.time()
    self.par_utime = utime_stop-self.utime_start
    self.par_etime = etime_stop-self.etime_start
    self.tot_utime += self.par_utime
    self.tot_etime += self.par_etime
    self.started = False
    self.suspended = True

  def stop(self):
    self.suspend()

  def start(self):
    self.resume()

  def partial(self):
    if self.started:
      utime_stop = resource.getrusage(resource.RUSAGE_SELF).ru_utime
      etime_stop = time.time()
      self.par_utime = utime_stop-self.utime_start
      self.par_etime = etime_stop-self.etime_start
      self.tot_utime += self.par_utime
      self.tot_etime += self.par_etime
      self.utime_start = utime_stop
      self.etime_start = etime_stop
    return (self.par_utime, self.par_etime, self.tot_utime, self.tot_etime)

  def tick(self, ticks=1):
    #if not self.started:
    #  raise TimerError, "%s not started" % self
    self.ticks += ticks

  def __repr__(self):
    return "%s(%r)" % (self.__class__.__name__, self.label)
  __str__ = __repr__

class WTimer(Timer):
  TICK_ROTATE_SYMBOLS = ['-', '\\', '|', '/']
  W_MAX_TICKS = 'W_MAX_TICKS'
  W_TICKS = 'W_TICKS'
  W_ROTATING_MARKER = 'W_ROTATING_MARKER'
  W_PERCENTAGE = 'W_PERCENTAGE'
  W_FRACTION = 'W_FRACTION'
  W_PROGRESSBAR = 'W_PROGRESSBAR'
  W_ETA = 'W_ETA'
  W_TOT_ETIME = 'W_TOT_ETIME'
  W_TOT_UTIME = 'W_TOT_UTIME'
  W_PAR_ETIME = 'W_PAR_ETIME'
  W_PAR_UTIME = 'W_PAR_UTIME'
  W_TICK_ETIME = 'W_TICK_ETIME'
  W_TICK_UTIME = 'W_TICK_UTIME'
  W_TEXT = "W_TEXT"
  def __init__(self, label, message=None, max_ticks=None, started=True, stream=None, widgets=None):
    if stream is None:
      stream = sys.stderr
    self.stream = stream
    super(WTimer, self).__init__(label=label, message=message, max_ticks=max_ticks, started=False)
    if widgets is None:
      if self.max_ticks is None:
        widgets = (
			"[",
			self.w_ticks(),
			"]",
			self.w_rotating_marker(),
        )
      else:
        widgets = (
			"[",
			self.w_ticks(),
			"|",
			self.w_percentage(),
			"%%"
			"]",
			self.w_rotating_marker(),
			'[',
			self.w_progressbar(),
			"]",
        )
    self.set_widgets(widgets)
    self.tick_rotate_symbol_index = 0
    self._cleaner = CARRIAGE_RETURN + CLEAR_EOL
    self._data = None
    self._txt = ''
    if started:
      self.start()

  @classmethod
  def w_ticks(clss, format=None):
    return (clss.W_TICKS, dict(format=format))

  @classmethod
  def w_max_ticks(clss, format='s'):
    return (clss.W_MAX_TICKS, dict(format=format))

  @classmethod
  def w_percentage(clss, format='5.1f'):
    return (clss.W_PERCENTAGE, dict(format=format))

  @classmethod
  def w_fraction(clss, format='s'):
    return (clss.W_FRACTION, dict(format=format))

  @classmethod
  def w_eta(clss, format='s'):
    return (clss.W_ETA, dict(format=format))

  @classmethod
  def w_tot_utime(clss, format='s'):
    return (clss.W_TOT_UTIME, dict(format=format))

  @classmethod
  def w_tot_etime(clss, format='s'):
    return (clss.W_TOT_ETIME, dict(format=format))

  @classmethod
  def w_par_utime(clss, format='s'):
    return (clss.W_PAR_UTIME, dict(format=format))

  @classmethod
  def w_par_etime(clss, format='s'):
    return (clss.W_PAR_ETIME, dict(format=format))

  @classmethod
  def w_tick_utime(clss, format='s'):
    return (clss.W_TICK_UTIME, dict(format=format))

  @classmethod
  def w_tick_etime(clss, format='s'):
    return (clss.W_TICK_ETIME, dict(format=format))

  @classmethod
  def w_rotating_marker(clss, format='s'):
    return (clss.W_ROTATING_MARKER, dict(format=format))

  @classmethod
  def w_progressbar(clss, format='s', size=10, done='#', todo='_'):
    return (clss.W_PROGRESSBAR, dict(format=format, size=size, done=done, todo=todo))

  @classmethod
  def w_text(clss, text, format='s'):
    return (clss.W_TEXT, dict(format=format, text=text))

  def _get_tick_digits(self):
    if self.max_ticks is None:
      return 3
    else:
      if self.max_ticks <= 0:
        return 3
      elif self.max_ticks < 10:
        return 1
      else:
        return 1+int(math.ceil(math.log(self.max_ticks-1, 10)))

  def set_widgets(self, widgets):
    self._needs_rotating_marker = False
    self._needs_percentage = False
    self._needs_tick_etime = False
    self._needs_tick_utime = False
    self._needs_eta = False
    self._needs_progressbar = False
    fmt = [self.message]
    for w in widgets:
      if isinstance(w, tuple):
        widget = w[0]
        parameters = w[1]
      else:
        widget = self.W_TEXT
        parameters = dict(text=w)
      format = parameters.get('format', 's')
      if widget == self.W_TICKS:
        if format is None:
          format = "%dd" % self._get_tick_digits()
        fmt.append("%%(ticks)%s"%format)
      elif widget == self.W_MAX_TICKS:
        if format is None:
          format = "%dd" % self._get_tick_digits()
        fmt.append("%%(max_ticks)%s"%format)
      elif widget == self.W_FRACTION:
        assert self.max_ticks is not None, "%s widget needs 'max_ticks'" % widget
        fmt.append("%%(fraction)%s"%format)
        self._needs_percentage = True
      elif widget == self.W_PERCENTAGE:
        assert self.max_ticks is not None, "%s widget needs 'max_ticks'" % widget
        fmt.append("%%(percentage)%s"%format)
        self._needs_percentage = True
      elif widget == self.W_ETA:
        assert self.max_ticks is not None, "%s widget needs 'max_ticks'" % widget
        fmt.append("%%(eta)%s"%format)
        self._needs_eta = True
        self._needs_tick_etime = True
      elif widget == self.W_TOT_ETIME:
        fmt.append("%%(tot_etime)%s"%format)
      elif widget == self.W_TOT_UTIME:
        fmt.append("%%(tot_utime)%s"%format)
      elif widget == self.W_PAR_ETIME:
        fmt.append("%%(par_etime)%s"%format)
      elif widget == self.W_PAR_UTIME:
        fmt.append("%%(par_utime)%s"%format)
      elif widget == self.W_TICK_ETIME:
        fmt.append("%%(tick_etime)%s"%format)
        self._needs_tick_etime = True
      elif widget == self.W_TICK_UTIME:
        fmt.append("%%(tick_utime)%s"%format)
        self._needs_tick_utime = True
      elif widget == self.W_ROTATING_MARKER:
        fmt.append("%%(rotating_marker)%s"%format)
        self._needs_rotating_marker = True
      elif widget == self.W_TEXT:
        fmt.append(parameters['text'])
      elif widget == self.W_PROGRESSBAR:
        assert self.max_ticks is not None, "%s widget needs 'max_ticks'" % widget
        fmt.append("%%(progressbar)%s"%format)
        self._needs_percentage = True
        self._needs_progressbar = True
        self._progressbar_parameters = parameters
      else:
        fmt.append(widget)
    self.fmt = ''.join(fmt)

  def tick(self, ticks=1):
    super(WTimer, self).tick(ticks)
    self._refresh_data()
    self._refresh_widgets()

  def refresh(self):
    if self._data is None:
      self._refresh_data()
    self._refresh_widgets()

  def _refresh_data(self):
    d = {
	'max_ticks':	self.max_ticks,
	'ticks':	self.ticks,
    }
    par_utime, par_etime, tot_utime, tot_etime = self.partial()
    d['par_utime'] = par_utime
    d['par_etime'] = par_etime
    d['tot_utime'] = tot_utime
    d['tot_etime'] = tot_etime
    if self._needs_tick_utime:
      d['tick_utime'] = float(d['tot_utime'])/self.ticks
    if self._needs_tick_utime:
      d['tick_utime'] = float(d['tot_utime'])/self.ticks
    if self._needs_eta:
      d['eta'] = d['tick_etime']*(self.max_ticks-self.ticks)
    if self._needs_percentage:
      d['fraction'] = float(self.ticks)/self.max_ticks
      d['percentage'] = 100.0*d['fraction']
    if self._needs_rotating_marker:
      d['rotating_marker'] = self.__class__.TICK_ROTATE_SYMBOLS[self.tick_rotate_symbol_index]
      self.tick_rotate_symbol_index = (self.tick_rotate_symbol_index+1)%len(self.__class__.TICK_ROTATE_SYMBOLS)
    if self._needs_progressbar:
      par = self._progressbar_parameters
      n_done = int(round(d['fraction']*par['size'], 0))
      n_todo = par['size'] - n_done
      progressbar = par['done']*n_done + par['todo']*n_todo
      d['progressbar'] = progressbar
    self._data = d

  def _txt_widgets(self):
    return self.fmt%self._data

  def _refresh_widgets(self):
    self._replace(self._txt_widgets())

  def start(self):
    super(WTimer, self).start()
    self._replace(self.message)
    self._data = None
    
  def stop(self):
    super(WTimer, self).stop()
    if self.ticks:
      t = ", #%d" % self.ticks
    else:
      t = ''
    self._refresh_data()
    self._refresh_widgets()
    #self._cleaner = ''
    self._replace("done.\n")
    self._data = None

  def suspend(self):
    #self._cleaner =''
    #self._refresh_widgets()
    self._replace("%s [suspended...]" % self._txt_widgets())
    super(WTimer, self).suspend()

  def resume(self):
    if self.suspended:
      #self._cleaner =''
      self._refresh_widgets()
      self._replace("%s [resumed]" % self._txt_widgets())
    super(WTimer, self).resume()

  def partial(self):
    self._data = None
    return super(WTimer, self).partial()

  #def _append(self, txt):
  #  self._replace("%s%s" % (self._txt, txt))

  def _replace(self, txt):
    self._txt = txt
    self.stream.write("%s%s" % (self._cleaner, txt))
    self.stream.flush()
    #self._cleaner = '\r%s\r' % ' '*len(txt)

  def _finish(self):
    #self._cleaner = ''
    self.stream.write('\n')

  def _clean(self):
    self.stream.write(self._cleaner)
    self.stream.flush()
    #self._cleaner = ''

if __name__ == "__main__":
#  widgets = (	'(',
#		WTimer.w_tot_utime(),
#		',',
#		WTimer.w_tick_utime(),
#		',',
#		WTimer.w_ticks(),
#		'/',
#		WTimer.w_max_ticks(),
#		')[',
#		WTimer.w_percentage(),
#		']',
#		WTimer.w_rotating_marker(),
#  )
  t = WTimer('alpha', max_ticks=100)
  for i in xrange(10):
    t.tick()
    time.sleep(0.1)
  t.suspend()
  time.sleep(3)
  t.resume()
  for i in xrange(90):
    t.tick()
    time.sleep(0.05)
  t.stop()
