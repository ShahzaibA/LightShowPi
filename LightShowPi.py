import pigpio
import RPi.GPIO as GPIO
import time
import datetime
import requests
import json
import subprocess
import os
from multiprocessing import Process

###GPIO PINS###
red = 26
green = 19
blue = 13

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(13,GPIO.OUT)
GPIO.setup(19,GPIO.OUT)
GPIO.setup(26,GPIO.OUT)




#pi = pigpio.pi()
t = time.time()
dlqueue = []
musicList = []
timeLeft = 1



###############GROUPME KEYS/DETAILS######################
#########################################################
accesstoken = ''
botid = ''
groupid = ''
getfunction = '/groups/' + groupid + '/messages'
postfunction = '/bots/post?bot_id=' + botid + '&text='
url = 'https://api.groupme.com/v3'
#########################################################
#########################################################

def runStandardLights():
	print("inside run")
	GPIO.output(13,GPIO.HIGH)
	GPIO.output(19,GPIO.HIGH)
	GPIO.output(26,GPIO.HIGH)



def killStandardLights():
	print("inside kill lights")
	GPIO.output(13,GPIO.LOW)
	GPIO.output(19,GPIO.LOW)
	GPIO.output(26,GPIO.LOW)

def countDown(originalTime):
	global timeLeft
	timeLeft = originalTime
	time.sleep(5)
	while timeLeft > 0:
		timeLeft = timeLeft - 1
		time.sleep(1)



def getInfo(link):
	print("inside get info")
	###Fetch URL###
	Url = str(link)
	Url = Url.split('/', 3)
	Url = Url[3]


	###Fetch Title###
	YTApiKey = ''
	TitleURL = 'https://www.googleapis.com/youtube/v3/videos?part=snippet&id=' + Url + '&key=' + YTApiKey
	get_title = requests.get(TitleURL)
	load_title = json.loads(get_title.text)
	title = (load_title['items'][0]['snippet']['title'])
	PItitle = title.replace(" ", "")
	PItitle = PItitle.replace("-", "")
	PItitle = PItitle.replace("(", "")
	PItitle = PItitle.replace(")", "")

	###Fetch Duration###
	DurationURL = 'https://www.googleapis.com/youtube/v3/videos?id=' + Url + '&key=' + YTApiKey + '&part=contentDetails'
	get_duration = requests.get(DurationURL)
	load_duration = json.loads(get_duration.text)
	duration = (load_duration['items'][0]['contentDetails']['duration']) #Unformatted duration
	duration = duration.replace("P", "")
	duration = duration.replace("T", "")
	duration = duration.replace("S", "")
	duration = duration.split("M")
	minutes = int(duration[0])
	seconds = int(duration[1])
	totalDuration = (minutes * 60) + seconds


	newEntry = [Url, title, PItitle, totalDuration]
	dlqueue = []
	dlqueue.append(newEntry)
	musicList.append(newEntry)

	return dlqueue, musicList


def downloadYT(last_message):
	print("inside downloadYt")
	x = 0
	dlqueue, musicList = getInfo(last_message)

	while x < len(dlqueue):
		print("Inside while loop of DownloadYT")
		requests.post(url + postfunction + dlqueue[x][1] + ' is being processed and will play shortly.')

		###Download MP3###
		DLUrl = 'https://www.youtubeinmp3.com/fetch/?video=http://www.youtube.com/watch?v=' + dlqueue[x][0]
		r = requests.get(DLUrl, stream=True)
		with open(dlqueue[x][2] + '.mp3', 'wb') as f:
			for chunk in r.iter_content(chunk_size=1024):
				if chunk:
					f.write(chunk)
					f.flush()
		b = os.path.getsize("/home/pi/" + dlqueue[x][2] + '.mp3')
		while b<1000000:
			DLUrl = 'https://www.youtubeinmp3.com/fetch/?video=http://www.youtube.com/watch?v=' + dlqueue[x][0]
			r = requests.get(DLUrl, stream=True)
			with open(dlqueue[x][2] + '.mp3', 'wb') as f:
				for chunk in r.iter_content(chunk_size=1024):
					if chunk:
						f.write(chunk)
						f.flush()
			b = os.path.getsize("/home/pi/" + dlqueue[x][2] + '.mp3')
		x = x + 1
	print("Downloaded")
	return musicList

def play(musicList):
	print("inside playmusic")
	killStandardLights()
	global p
	p = subprocess.Popen(["sudo", "python", "lightshowpi/py/synchronized_lights.py", "--file=/home/pi/" + musicList[0][2] + ".mp3"])
	duration = int(musicList[0][3])
	print("After subprocess")
	P3 = Process(target = countDown(duration))
	P3.start()
	musicList.pop(0)
	print("after process")

def getGroupMeMessages():
	try:
		while True:
			get_messages = requests.get(url + getfunction + '?token=' + accesstoken)
			load_messages = json.loads(get_messages.text)
			last_message = (load_messages['response']['messages'][0]['text'])
			if last_message.startswith('https://youtu'):
				musicList = downloadYT(last_message)
				play(musicList)

			if last_message.startswith("/stop"):
				p.terminate()

			if timeLeft == 0:
				p.terminate()
				time.sleep(2)
				runStandardLights()
				print("time set to 1")


	except:
		getGroupMeMessages()



def main():
	global P1
	P1 = Process(target = getGroupMeMessages)
	P1.start()
	P2 = Process(target = runStandardLights)
	P2.start()

main()
