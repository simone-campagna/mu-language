#!/usr/bin/env python

import sys

mi, mj = 0, 0
ll = []
def cnv(x):
  if x:
    return '#'
  else:
    return ' '

for line in sys.stdin.readlines():
  l = list(line.strip())
  ll.append([int(x) for x in l])
  if len(l) > mj:
    mj = len(l)

mi = len(ll)
for l in ll:
  if len(ll) < mj:
    l.extend([0]*(mj-len(l)))
  

def prnt(ll):
  print '-'*80
  for l in ll:
    print ' '.join(cnv(e) for e in l)

def new(ll):
  return [l[:] for l in ll]

def step(ll):
  nn = new(ll)
  for ci in xrange(mi):
    for cj in xrange(mj):
      ngb8 = 0
      for ii, ij in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)):
        ni, nj = ci+ii, cj+ij
        if ni < 0:
          ni = mi-1
        elif ni >= mi:
          ni = 0
        if nj < 0:
          nj = mj-1
        elif nj >= mj:
          nj = 0
        ngb8 += nn[ni][nj]
      v = ll[ci][cj]
      #print ci, cj, ngb8, v
      if v:
        if not ngb8 in (2, 3):
          #print "RESET", ci, cj
          ll[ci][cj] = 0
      else:
        if ngb8 == 3:
          #print "SET", ci, cj
          ll[ci][cj] = 1

prnt(ll)
print "="*80

for i in xrange(30):
  step(ll)
  prnt(ll)
