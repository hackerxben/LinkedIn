# -*- coding: utf-8 -*-
import argparse, os,sys, time
import urlparse, random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def getPeopleLinks(page):
	links = []
	for link in page.find_all('a'):
		url = link.get('href')
		if url:
			if 'profile/view?id=' in url:
				links.append(url)
	return links

def getJobLinks(page):
	links = []
	for link in page.find_all('a'):
		url = link.get('href')
		if url:
			if '/jobs' in url:
				links.append(url)
	return links

def getID(url):
	pUrl = urlparse.urlparse(url)
	return urlparse.parse_qs(pUrl.query)['id'][0]


def ViewBot(browser):
	visited = {}
	pList = []
	count = 0
	while True:
		#sleep to make sure everything loads, add random to make us look human.
		time.sleep(random.uniform(3.5,6.9))
		page = BeautifulSoup(browser.page_source)
		people = getPeopleLinks(page)
		if people:
			for person in people:
				ID = getID(person)
				if ID not in visited:
					pList.append(person)
					visited[ID] = 1
		if pList: #if there is people to look at look at them
			person = pList.pop()
			browser.get(person)
			count += 1
		else: #otherwise find people via the job pages
			jobs = getJobLinks(page)
			if jobs:
				job = random.choice(jobs)
				root = 'http://www.linkedin.com'
				roots = 'https://www.linkedin.com'
				if root not in job or roots not in job:
					job = 'https://www.linkedin.com'+job
				browser.get(job)
			else:
				print "I'm Lost Exiting"
				break

		#Output (Make option for this)
		print "[+] "+browser.title+" Visited! \n("\
			+str(count)+"/"+str(len(pList))+") Visited/Queue)"

def search(browser,searchTerm):
	browser.get('https://www.linkedin.com/search/results/people/?facetGeoRegion=%5B%22tn%3A0%22%5D&keywords='+searchTerm+'&origin=FACETED_SEARCH')
	print "[+] Search Done"

def get_list_people(browser):
	tunisians = []
	time.sleep(5)
	page = BeautifulSoup(browser.page_source,"html.parser")
	people = page.find_all("li",{"class","search-result search-entity search-result--person ember-view"})
	for person in people:
		if "Tunis" in str(person) or "Tunisia" in str(person) or "Tunisie" in str(person):
			#print person.get('id')
			tunisians.append(person.get('id'))
	return tunisians

def send_invitations(browser,msg_linkedin):
	all_poeple = list(browser.find_elements_by_css_selector('.search-result.search-entity.search-result--person.ember-view'))
	tunisians = get_list_people(browser)
	print len(tunisians)
	for person in all_poeple:
		for id in tunisians:
			person = browser.find_element_by_id(id)
			buttons = list(person.find_elements_by_css_selector('.search-result__actions--primary.button-secondary-medium.m5'))
			for button in buttons:
				if "Se connecter" in str(button.text):
					button.click()
					secondButton = person.find_element_by_css_selector('.button-secondary-large')
					if "Ajouter une note" in str(secondButton.text):
						secondButton.click()
						textarea = browser.find_element_by_id('custom-message').send_keys(msg_linkedin)
						sendButton = browser.find_element_by_css_selector('.button-primary-large.ml3')
						sendButton.click()
						time.sleep(2)
						break
	print "[+] Success! Invitation sent"

def get_current_page(browser):
	pages = browser.find_element_by_css_selector('.page-list')
	current_page = pages.find_element_by_css_selector('.active')
	return int(str(current_page.text))

def next_page(browser):
	browser.find_element_by_css_selector('.next').click()
	time.sleep(5)

def login(browser,args):
	emailElement = browser.find_element_by_id("session_key-login")
	emailElement.send_keys(args.email)
	passElement = browser.find_element_by_id("session_password-login")
	passElement.send_keys(args.password)
	passElement.submit()
	time.sleep(5)

def Main():
	reload(sys)
	sys.setdefaultencoding('utf8')

	#parse_the arguments
	parser = argparse.ArgumentParser()
	parser.add_argument("email", help="linkedin email")
	parser.add_argument("password", help="linkedin password")
	parser.add_argument("searchTerm", help="The field of interest")
	args = parser.parse_args()

	#open_firefox_window
	browser = webdriver.Firefox()

	#open_linkedin_login_url
	browser.get("https://linkedin.com/uas/login")

	#type_the_login_and_pass_and_submit
	login(browser,args)

	#search_for_the_desired_field
	search(browser,args.searchTerm)

	#load_the_note_from_file
	msg_linkedin = ""
	f = open('msg_linkedin.txt','r')
	msg_linkedin = f.read()
	f.close()
	msg_linkedin = unicode(msg_linkedin, errors='replace')
	time.sleep(5)

	#send_invitation_with_note
	for i in range(1,6):
		print "Starting page "+ str(i)
		send_invitations(browser,msg_linkedin)
		liste = get_list_people(browser)
		if liste:
			print "found "+str(len(liste))+" Tunisians"
		print "[+] Success! Page " + str(i) + " Done"
		next_page(browser)

	#close_browser_window
	browser.close()

if __name__ == '__main__':
	Main()
