# -*- coding: utf-8 -*-
import argparse
import sys
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

SEARCH_URL = 'https://www.linkedin.com/search/results/people/?facetGeoRegion=%5B%22cn%3A0%22%2C%22za%3A0%22%2C%22us%3A0%22%2C%22in%3A0%22%2C%22gb%3A0%22%2C%22ch%3A0%22%2C%22au%3A0%22%2C%22fr%3A0%22%2C%22at%3A0%22%2C%22de%3A0%22%2C%22es%3A0%22%2C%22jp%3A0%22%2C%22kr%3A0%22%2C%22ru%3A0%22%5D&facetNetwork=%5B%22S%22%2C%22O%22%5D&origin=FACETED_SEARCH&keywords=&page='

#parse_the arguments
parser = argparse.ArgumentParser()
parser.add_argument("email", help="linkedin email")
parser.add_argument("password", help="linkedin password")
parser.add_argument("searchTerm", help="The field of interest")
args = parser.parse_args()

#load_the_note_from_file
note_linkedin = ""
f = open('note_linkedin.txt','r')
note_linkedin = f.read()
f.close()
note_linkedin = unicode(note_linkedin, errors='replace')


def scroll_down(browser):
	print "++ scrolling down"
	SCROLL_PAUSE_TIME = 0.5
	#Get scroll height
	last_height = browser.execute_script("return document.body.scrollHeight")
	while True:
		#Scroll down to bottom
		browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
		#Wait to load page
		time.sleep(SCROLL_PAUSE_TIME)
		#Calculate new scroll height and compare last scroll height
		new_height = browser.execute_script("return document.body.scrollHeight")
		if new_height == last_height:
			break
		last_height = new_height
	print "++ scrolled down"

def wait_until_page_loads(browser,count):
	if count > 9:
		return "timeout"
	try:
		time.sleep(2)
		browser.find_element_by_css_selector("button.search-result__actions--primary.button-secondary-medium.m5")
		print "++ page should be loaded now"
		return
	except NoSuchElementException as e:
		try:
			browser.find_element_by_css_selector("span.message-anywhere-button.button-secondary-medium.search-result__actions--primary.m5.link-without-visited-state")
			print "++ page should be loaded now"
			return
		except NoSuchElementException as e:
			print "-- page still loading"
			time.sleep(0.5)
			wait_until_page_loads(browser,count+1)

def wait_until_overlay_appears(browser,count = 0):
	try:
		browser.find_element_by_css_selector("div.modal-wormhole.visible.send-invite.ember-view")
		print "++ found overlay,good to go"
	except Exception as e:
		if count > 3:
			return "reclick"
		print "-- waiting for overlay"
		wait_until_overlay_appears(browser,count +1)

def click_connect(browser,button,count=0):
	if count == 3:
		return "continue"
	button.click()
	time.sleep(0.5)
	result = wait_until_overlay_appears(browser,0)
	if result == "reclick":
		print "-- reclicking connect"
		click_connect(browser,button,count+1)

def click_add_note(browser,button,count=0):
	if count == 3:
		return "continue"
	button.click()
	time.sleep(0.5)
	try:
		browser.find_elements_by_id("custom-message")
	except Exception as e:
		print "-- reclicking add note"
		click_add_note(browser,button,count+1)

def login(browser):
	print "[+] opening login page"
	browser.get("https://linkedin.com/uas/login")
	print "[+] starting login"
	emailElement = browser.find_element_by_name("session_key")
	emailElement.send_keys(args.email)
	passElement = browser.find_element_by_name("session_password")
	passElement.send_keys(args.password)
	passElement.submit()
	while browser.title != "LinkedIn":
		time.sleep(0.5)
	print "[+] login was successful"

def get_current_page_number(browser):
	try:
		page = browser.find_element_by_css_selector("li.page-list").find_element_by_css_selector("ol").find_element_by_css_selector("li.active").text
	except Exception as e:
		print "-- probably the page is still loading"
		time.sleep(0.5)
		get_current_page_number(browser)
	return int(page)

def close_overlay(browser):
	webdriver.ActionChains(browser).send_keys(Keys.ESCAPE).perform()
	time.sleep(0.5)
	print "closed overlay"

def clicking(browser,button):
	if click_connect(browser,button,0) == "continue":
	  print "skipping..."
	  return
	time.sleep(1)
	print "++ clicked connect"
	try:
		browser.find_element_by_id("email")
		print "-- oups this guy requires an email"
		close_overlay(browser)
		return "remove"
	except Exception as e:
		pass
	add_note = browser.find_element_by_css_selector("button.button-secondary-large")
	if click_add_note(browser,add_note,0) == "continue":
	  print "skipping..."
	  return
	time.sleep(0.5)
	print "++ clicked add note"

	textarea = browser.find_element_by_id("custom-message")
	textarea.send_keys(note_linkedin)
	print "++ added the note"
	time.sleep(1)

	send = browser.find_element_by_css_selector('button.button-primary-large.ml3')
	send.click()
	#close_overlay(browser)
	print "++ clicked send"
	time.sleep(3)

def send_invitations(browser,count):
	wait_until_page_loads(browser,0)
	clicked_buttons = 0
	time.sleep(0.5)
	buttons = browser.find_elements_by_css_selector("button.search-result__actions--primary.button-secondary-medium.m5")
	number_buttons = len(buttons)
	print "++ i found ",str(number_buttons)," buttons"
	time.sleep(0.5)
	for i in range(0,number_buttons):
		if "Connect" == buttons[i].text:
			clicking(browser,buttons[i])
			clicked_buttons = clicked_buttons + 1

	if number_buttons - clicked_buttons > 1:
	  print "-- i didn't click all the buttons"
	  if count > 2:
	  	print "-- but i tried many times"
		return clicked_buttons
	  print "++ refreshing page"
	  browser.refresh()
	  wait_until_page_loads(browser,0)
	  scroll_down(browser)
	  time.sleep(0.5)
	  send_invitations(browser,count+1)
	return clicked_buttons

def do_the_job(browser,page,last_crashed_page):
	try:
		print "[+] starting page: ",str(page)
		#search
		browser.get(SEARCH_URL.replace("keywords=","keywords="+args.searchTerm).replace("page=","page="+str(page)))
		#scroll_down_to_the_bottom_of_the_page_so_that_all_the_results_fully_load
		scroll_down(browser)
		time.sleep(0.2)
		#send_invitations_with_note
		x = send_invitations(browser,0)
		print "i clicked ",x," buttons in page ",str(page)
		return x
	except Exception as e:
		print "-- this was raised:"
		print e
		if last_crashed_page == page:
			print "-- skipping page ",page
			return
		else:
			last_crashed_page = page
			print "-- restarting last crashed page ", str(page)
		do_the_job(browser,page,last_crashed_page)


def main():
	reload(sys)
	sys.setdefaultencoding('utf8')

	#open_firefox_window
	browser = webdriver.Chrome()
	time.sleep(1.5)
	login(browser)
	s = 0
	for page in range(1,101):
		s = s + do_the_job(browser,page,0)
	print "-------------------------"
	print "| Total clicked buttons: ",s
	print "-------------------------"
	#close_browser_window
	browser.quit()

if __name__ == '__main__':
	main()
