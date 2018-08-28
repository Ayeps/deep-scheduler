#!/bin/bash
echo $1 $2 $3

PYTHON=python3
PKILL=/usr/bin/pkill

# rm -r __pycache__
if [ $1 = 'i' ]; then
  source ~/tensorflow/bin/activate
elif [ $1 = 't' ]; then
  rm log/*
  $PYTHON tutorial.py
elif [ $1 = 'tb' ]; then
  tensorboard --logdir=/home/ubuntu/deep-scheduler/log
elif [ $1 = 's' ]; then
  # $PYTHON scheduling.py
  $PYTHON learn_shortestq.py
elif [ $1 = 'r' ]; then
  $PYTHON learn_howtorep.py
elif [ $1 = 'e' ]; then
  $PYTHON howtorep_exp.py
elif [ $1 = 'c' ]; then
  $PYTHON reptod_wcancel.py
elif [ $1 = 'd' ]; then
  $PYTHON deneme.py
elif [ $1 = 'p' ]; then
  $PYTHON profile_scher.py
elif [ $1 = 'm' ]; then
  # $PYTHON mg1_wred.py
  # $PYTHON mgs_wred.py
  $PYTHON mg1.py
elif [ $1 = 'rv' ]; then
  $PYTHON rvs.py
else
  echo "Arg did not match!"
fi