#!/bin/ksh

out="Hello, world!"

function starting {
  typeset _arg=$(echo "$1" | tr '\n' '$')
  if [[ ${#_arg} -gt 40 ]] ; then
    _arg=$(printf '%s' "$_arg" | cut -c1-37)"..."
  fi
  printf "%s\n" "$_arg"
}

for h in $MU_HOME/examples/hello_world/hello_world_* ; do
  printf "%s:" "$h"
  a=$(mu $h)
  printf "%s\n" "$a"
  if [[ "$a" != "$out" ]] ; then
    echo "ERRORE"
    exit 1
  fi
done
