import requests
from fastapi import FastAPI, File

app = FastAPI()
API_URL = 'https://api.platerecognizer.com/v1/plate-reader/'
HEADER={'Authorization': 'Token 45f3172a25b6ea562e6174ac2475b7ca26b8e2fc'}

@app.post("/verify/")
async def verify(file: bytes = File(...)):
	response = requests.post(url=API_URL, headers=HEADER, files=dict(upload=file))
	results = response.json().get('results')
	if results is not None and len(results) > 0:
		msg = results[0]['plate']	# TODO: check db
	else:
		msg = 'Fail'
	return {'msg':msg}