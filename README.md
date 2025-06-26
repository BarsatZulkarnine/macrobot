python3 -m venv myenv

myenv\Scripts\activate

pip install -r requirements.txt

pyhton3 app.py



example:
```
curl -X POST http://<YOUR_PC_IP>:8000/upload \
  -F "image=@sample.jpg" \
  -F "x=3" \
  -F "y=1"
  
```

