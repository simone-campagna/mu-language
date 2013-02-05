#!/bin/bash

for num in 2 3 78 ; do
  echo $num | mu test_next_prime.mu -lmath
done
