#!/bin/bash

for num in 77 79 60 ; do
  echo $num | mu factor.mu -lmath
done
