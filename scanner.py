# ISBN Scanner (Android)

from urllib import request, parse
import android

droid = android.Android()

def post(isbn):
	post_data = parse.urlencode({"isbn":isbn}).encode()
	req =  request.Request("http://10.90.100.188:8000", data=post_data)
	resp = request.urlopen(req)

def scan():
	code = droid.scanBarcode()

	post(code[1]["extras"]["SCAN_RESULT"])

while True:
	scan()