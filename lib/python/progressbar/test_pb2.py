#!/usr/bin/env python
# -*- coding: utf-8 -*-

from progressbar import ProgressBar
import sys
import time
import terminal
p1 = ProgressBar('green', width=120, block='▣', empty='□')
p2 = ProgressBar('red', width=80, block='▣', empty='□')
first_i = True
for i in range(101):
    p1.render(i) #, 'step %s\nProcessing...\nDescription: write something.' % i)
    if first_i:
      first_i = False
    else:
      print
    for j in range(101):
        p2.render(j)
        time.sleep(0.001)
    sys.stdout.write(terminal.UP + terminal.BOL + terminal.CLEAR_EOL)
sys.stdout.write(terminal.UP + terminal.BOL + terminal.CLEAR_EOL)
