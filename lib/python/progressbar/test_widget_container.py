#!/usr/bin/env python
# -*- coding: utf-8 -*-


from widget_container import *

class PBar(Screen):
  ERROR_FORMATTER = Color("red")
  def __init__(self):
    self.ptextt = TextFiller(20, "")
    self.pbart = SimpleProgressBar(
		(
			Segment(u'▣', formatter=Color('red')),
			Segment(u'▣', formatter=Color('green')),
			Segment(u'□', formatter=Color('blue')),
		),
		width=100.0,
    )
    mv_widget = self.pbart.get_max_value_widget()
    vs_widget = self.pbart.get_value_widgets()
    ps_widget = self.pbart.get_percentage_widgets()
    self.ptextd = TextFiller(20, "")
    self.pbard = SimpleProgressBar(
		(
			Segment(u'▣', formatter=Color('red')),
			Segment(u'▣', formatter=Color('green')),
			Segment(u'□', formatter=Color('blue')),
		),
		width=70.0,
    )
    self.t = TextFiller(20, "")
    lines = (
		Line(
			(
				self.t,
			),
		),
		Line(
			(
				'[',
					ps_widget[0],
				'/',
					ps_widget[1],
				'/',
					ps_widget[2],
				']',
				self.ptextt,
				self.pbart,
				'[',
					vs_widget[0],
				'/',
					vs_widget[1],
				'/',
					vs_widget[2],
				'/',
					mv_widget,
				']',
			),
		),
		Line(
			(
				self.ptextd,
				self.pbard,
			),
		),
		Line(
		),
    )
    super(PBar, self).__init__(lines)

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

  prob_fail = 0.05
  tot_num_dirs = 20
  tot_num_tests = 120
  mean_tests_per_dir = float(tot_num_tests)/tot_num_dirs
  tot_num_ok = 0
  tot_num_ko = 0
  tot_duration = 20.0
  tot_sleep = 0.0
  mean_sleep = float(tot_duration)/tot_num_tests
  pbar.pbard.set_max_value(tot_num_tests)
  pbar.start()
  for i in xrange(tot_num_dirs):
    dir_name = "Dir[%d]" % i
    pbar.ptextd.set_text(dir_name)
    tot_num_todo = tot_num_tests-(tot_num_ok+tot_num_ko)
    if i == tot_num_dirs-1:
      num_tests = tot_num_todo
    else:
      num_tests = min(tot_num_todo, random.randrange(1, 2*int(1.0+mean_tests_per_dir)))
      mean_tests_per_dir = float(tot_num_todo-num_tests)/(tot_num_dirs-1-i)
    num_ok = 0
    num_ko = 0
    pbar.pbart.set_max_value(num_tests)
    for j in xrange(num_tests):
      pbar.t.set_text("Dir[%s]/Test[%s]" % (i, j))
      test_name = "Test[%d]" % j
      pbar.ptextt.set_text(test_name)
      pbar.render()
      t_sleep_todo = tot_duration-tot_sleep
      if i == tot_num_dirs-1 and j == num_tests-1:
        t_sleep = t_sleep_todo
      else:
        t_sleep = min(t_sleep_todo, random.uniform(0.0, 2*mean_sleep))
        mean_tests_per_dir = (tot_duration-tot_sleep)/float(tot_num_todo)
      time.sleep(t_sleep)
      tot_sleep += t_sleep
      if random.uniform(0.0, 1.0) < prob_fail:
        #pbar.clear()
        #sys.stderr.write("!!! Test %d/%d failed\n" % (i, j))
        #sys.stderr.flush()
        #pbar.start()
        pbar.error("   !!! Test %d/%d failed\n" % (i, j))
        num_ko += 1
        tot_num_ko += 1
      else:
        num_ok += 1
        tot_num_ok += 1
      pbar.pbard.set_values((tot_num_ko, tot_num_ok))
      pbar.pbart.set_values((num_ko, num_ok))
      pbar.render() 
  print pbar.children[-1].container
  print pbar.children[-1].container.width
  print "tot:", tot_num_tests, tot_num_ok, tot_num_ko, tot_num_ok+tot_num_ko
  print "dur:", tot_duration, tot_sleep
  print '\n'.join(pbar.container.root.dump())
    
