#!/bin/bash

for qo in quine_*.mu ; do
  qq=./${qo}.out
  mu $qo |tee $qq
  if ! diff $qo $qq ; then
    echo "ERRORE!!!"
    exit 10
  fi
  rm $qq
done
