#!/bin/bash

source .env
ssh -p 2522 -fN root@$SERVER -L 27018:127.0.0.1:27017
cd /APP/pgrass-jobs
cd /APP/pgrass-jobs && python start_sched.py
