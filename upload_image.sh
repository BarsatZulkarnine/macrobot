#!/bin/bash

curl -X POST http://172.22.235.224:8000/upload \
  -F "image=@sample.jpg" \
  -F "x=3" \
  -F "y=1"
