#!/usr/bin/env python

N = 100

doors = [False for i in xrange(100)]

for i in xrange(1, 100):
  for d in xrange(0, 100, i):
    doors[d] = not doors[d]

for c, door in enumerate(doors):
  if door:
    print c
