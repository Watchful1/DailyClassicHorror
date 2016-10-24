#!/usr/bin/python3

import praw
import OAuth2Util
import os
import logging.handlers
from lxml import html
import requests
import time
import sys
import traceback
import json

### Config ###
LOG_FOLDER_NAME = "logs"
SUBREDDIT = "ClassicHorror"
USER_AGENT = "ClassicHorrorSidebarUpdater (by /u/Watchful1)"

### Logging setup ###
LOG_LEVEL = logging.DEBUG
if not os.path.exists(LOG_FOLDER_NAME):
    os.makedirs(LOG_FOLDER_NAME)
LOG_FILENAME = LOG_FOLDER_NAME+"/"+"bot.log"
LOG_FILE_BACKUPCOUNT = 5
LOG_FILE_MAXSIZE = 1024 * 256

log = logging.getLogger("bot")
log.setLevel(LOG_LEVEL)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
log_stderrHandler = logging.StreamHandler()
log_stderrHandler.setFormatter(log_formatter)
log.addHandler(log_stderrHandler)
if LOG_FILENAME is not None:
	log_fileHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=LOG_FILE_MAXSIZE, backupCount=LOG_FILE_BACKUPCOUNT)
	log_formatter_file = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	log_fileHandler.setFormatter(log_formatter_file)
	log.addHandler(log_fileHandler)

log.debug("Connecting to reddit")

once = False
if len(sys.argv) > 1 and sys.argv[1] == 'once':
	once = True

r = praw.Reddit(user_agent=USER_AGENT, log_request=0)
o = OAuth2Util.OAuth2Util(r)
o.refresh(force=True)

while True:
	startTime = time.perf_counter()
	log.debug("Starting run")

	strList = []
	try:
		page = requests.get("http://www.fearshop.com/podcast/this-day-in-horror.asp")
		tree = html.fromstring(page.content)

		strList.append("This day in horror - ")
		date = tree.xpath("//div[@id='blog']/h2[not(@*)]/text()")
		strList.append(date[0])
		strList.append("\n-\n\n")

		for i, element in enumerate(tree.xpath("//div[@id='blog']/div[@class='thih_event']/text()")):
			strList.append(element.strip())
			strList.append("  \n")

		strList.append("\n\n")
		strList.append("*****")
		strList.append("\n\n")
	except Exception as err:
		log.warning("Exception parsing page")
		log.warning(traceback.format_exc())

	try:
		resp = requests.get(url="https://www.reddit.com/r/"+SUBREDDIT+"/wiki/sidebar-template.json", headers={'User-Agent': USER_AGENT})
		jsonData = json.loads(resp.text)
		baseSidebar = jsonData['data']['content_md']

		strList.append(baseSidebar)
	except Exception as err:
		log.warning("Exception parsing schedule")
		log.warning(traceback.format_exc())

	if len(strList) > 0:
		subreddit = r.get_subreddit(SUBREDDIT)
		subreddit.update_settings(description=''.join(strList))

	log.debug("Run complete after: %d", int(time.perf_counter() - startTime))
	if once:
		break
	time.sleep(60 * 60)
