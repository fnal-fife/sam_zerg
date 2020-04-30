#!/bin/bash

FILETYPE=testfiles

# Generate a bunch of files of randome data between 0-1Kb.
for n in {000..050}
do
    rand_int=$(( RANDOM + 2048*10 ))
    f_id=$(echo "$n")
    file_name="bjwhite_testfile_${f_id}.bin"
    dd if=/dev/urandom of=data/${file_name} bs=1 count=${rand_int} > /dev/null 2>&1
    echo "{\"file_name\": \"${file_name}\",\"file_size\": \"${rand_int}\",\"file_type\": \"${FILETYPE}\", \"group\": \"sam_bjwhite\"  }" > data/${file_name}.json
done


