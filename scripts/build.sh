#! /bin/bash

root=`dirname $0`

while echo
do
   python $root/build.py -d /tmp/tmp/build/build /home/*/module[123]-day[12345].ipynb
   sleep 5
done

