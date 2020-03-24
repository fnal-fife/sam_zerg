#!/bin/bash

# Generate a bunch of files of randome data between 0-1Kb.
for n in {1..50}
do
    dd if=/dev/urandom of=data/file$( printf %03d "$n" ).bin bs=1 count=$(( RANDOM + 1024 ))
done
