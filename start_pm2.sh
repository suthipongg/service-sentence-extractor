#!/bin/bash

source venv/bin/activate 

pm2 del service-sentence-extractor
pm2 start
pm2 log service-sentence-extractor