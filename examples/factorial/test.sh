#!/bin/bash

for num in 0 1 2 3 4 5 6 7 8 9 10 ; do
  echo $num | mu factorial.mu -lmath
done
