#!/bin/bash

# Start the path exploration
curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 0, "y": 0}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 1, "y": 0}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 2, "y": 0}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 2, "y": 1}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 2, "y": 2}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 1, "y": 2}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 0, "y": 2}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 0, "y": 3}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 0, "y": 4}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 1, "y": 4}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 2, "y": 4}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 3, "y": 4}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 3, "y": 3}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 3, "y": 2}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 3, "y": 1}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 4, "y": 1}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 5, "y": 1}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 6, "y": 1}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 7, "y": 1}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 8, "y": 1}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 9, "y": 1}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 9, "y": 2}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 9, "y": 3}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 9, "y": 4}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 9, "y": 5}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 9, "y": 6}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 9, "y": 7}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 8, "y": 7}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 7, "y": 7}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 6, "y": 7}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 5, "y": 7}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 4, "y": 7}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 3, "y": 7}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 3, "y": 8}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 3, "y": 9}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 2, "y": 9}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 1, "y": 9}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 0, "y": 9}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 0, "y": 8}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 0, "y": 7}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 1, "y": 7}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 2, "y": 7}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 2, "y": 6}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 2, "y": 5}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 2, "y": 4}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 1, "y": 3}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 1, "y": 2}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 1, "y": 1}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 1, "y": 0}'
sleep 2

curl -X POST http://localhost:8000/position -H "Content-Type: application/json" -d '{"x": 0, "y": 0}'
sleep 2
