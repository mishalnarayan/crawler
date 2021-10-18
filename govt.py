from bs4 import BeautifulSoup as soup
import re
import pandas as pd
import requests
import datetime
import time
import os
import json
import glob
import random

#declaring base open and colsed docket link
open_docket_base_link = "https://www.gao.gov/legal/bid-protests/search?processed=1&closed=0#s-skipLinkTargetForMainSearchResults"
closed_docket_base_link = "https://www.gao.gov/legal/bid-protests/search?processed=1&closed=1#s-skipLinkTargetForMainSearchResults"

#declaring chrome header
hdr1 = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
	   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
	   'Accept-Encoding': 'none',
	   'Accept-Language': 'en-US,en;q=0.8',
	   'Connection': 'keep-alive'}

log_file_name_with_path = "resume_helper_logs.txt"


def html_data_grabber(given_page_link,header = hdr1) : 
	""" 
		This function returns dict of information after browsing 
		any given link having soup content of page, status code,
		was it able to grab page data or not with "grabbed data" 
		key and additional helpful message of how url opening went. 
  
		Parameters: 
			given_page_link    (str)    :  url to browse
										   ex input : https://www.gao.gov/products/b-419833.2
			header             (dict)   :  dict of browser header information default is set to chrome
		Returns: 
			dict: dict of information after browsing any given link having soup content of page,
			status code,was it able to grab page data or not with "grabbed data" key and
			additional helpful message of how url opening went.
		"""
	request_made = requests.get(given_page_link,headers = header)

	#time.sleep(random.randint(3, 8)) #random sleep as per MS guidelines although recommended Crawl-delay on https://www.gao.gov/robots.txt is 10s

	status_code = int(request_made.status_code)
	data = ""
	grabbed_data = False
	if status_code == 200 :
		grabbed_data = True
		data = request_made.text
		message = "Success"
	elif status_code >= 403 :
		message = "banned"
	elif status_code >= 500 :
		message = "Government Server is down"
	else :
		message = "your internet connection is down"
		
	if grabbed_data :
		data = soup(data,"html.parser")
		
	return {"content":data, "status_code":status_code, "grabbed_data":grabbed_data, "message": message}
		
def available_search_result_page_links(base_link) :
	""" 
		This function returns list of all search result 
		pages link that can be browsed from base page
  
		Parameters: 
			base_link    (str)    :  base search page link 
									 ex input : https://www.gao.gov/legal/bid-protests/search?processed=1&closed=1#s-skipLinkTargetForMainSearchResults
		Returns: 
			list: A list of all seach pages results links that can be browsed from base search page
				  Also will raise an error if it couldn't browse or open search page.
		"""
	base_link_content = html_data_grabber(base_link)
	if base_link_content["grabbed_data"] :
		last_page_link = "https://www.gao.gov/legal/bid-protests/search" + base_link_content["content"].findAll("a",{"title" : "Go to last page"})[0]["href"]
	else :
		print(base_link,base_link_content["message"],base_link_content["status_code"])
		raise

	last_page_no = int(last_page_link.split("&")[-1].replace("page=",""))
	all_links = [last_page_link.split("page=")[0] + "page=" + str(i) for i in range(0,last_page_no + 1)]
	return all_links

def docket_page_links_from_search_page(page_link) :
	""" 
		This function returns list of all docket page links 
		present on a open/closed docket search filter result.
  
		Parameters: 
			page_link    (str)    :  single docket search page link 
									 ex input : https://www.gao.gov/legal/bid-protests/search?processed=1&closed=1&page=82
		Returns: 
			list: A list of all docket page links present of a docket search page
				  Also will raise an error if it couldn't browse or open search page.
		"""
	browse_link = html_data_grabber(page_link)
	if browse_link["grabbed_data"] :
		docket_content = browse_link["content"].findAll("article",{"class" : "node node--type-bid-protest-docket node--view-mode-teaser-search"})
	else :
		print(page_link,browse_link["message"],browse_link["status_code"])
		raise
	all_links = []
	base_link = "https://www.gao.gov"
	all_links = [base_link + i["about"] for i in docket_content]
	if len(all_links) == 0 :
		raise
	return all_links

def highlights_page_content_grabber(highlights_page_link) :
	""" 
		This is a helper function for function "extract_data_from_docket_page"
		it grabs decision highlights form highlights section block from hyperlink 
		present in "file number" information on docket page.
  
		Parameters: 
			highlights_page_link    (str)    :  single highlights_page_link 
												ex input : https://www.gao.gov/products/b-419833.2
		Returns: 
			str: A string paragraph containing decision highlights
				 Also will return False if couldn't browse or open link.
		"""
	browse_link = html_data_grabber(highlights_page_link)
	if browse_link["grabbed_data"] :
		data = browse_link["content"].findAll("div",{"class" : "node__content"})[0]
	else :
		print(docket_page_link, browse_link["message"],browse_link["status_code"])
		return False
	highlight_tag = data.findAll("div",{"class" : re.compile(r'^[a-zA-Z0-9- ]+field--name-product-highlights-custom*')})[0]
	highlight_text = highlight_tag.findAll("div",{"class" : "field__item"})[0].text.strip()
	return highlight_text

def extract_data_from_docket_page(docket_page_link) :
	""" 
		This function returns dict of all docket information present
		on docket page link .
  
		Parameters: 
			docket_page_link    (str)    :  single docket page link 
											ex input : https://www.gao.gov/docket/b-418742.3
		Returns: 
			dict: A dictionary of all docket page information with key value pair
				  Also will raise an error if it couldn't browse or open docket link.
		"""
	browse_link = html_data_grabber(docket_page_link)
	if browse_link["grabbed_data"] :
		data = browse_link["content"].findAll("div",{"class" : "node__content"})[0]
	else :
		print(docket_page_link, browse_link["message"],browse_link["status_code"])
		raise
	all_data = {"docket_page_link" : docket_page_link}
	all_data_lines = data.findAll("div",{"class" : re.compile(r'^field field--')})
	for single_data in all_data_lines :
		try :
			field_name = single_data.findAll("header",{"class" : "field__label"})[0].text.strip()
		except :
			field_name = "error"
		try :
			field_tag = single_data.findAll("div",{"class" : "field__item"})[0]
			field_value = field_tag.text.strip()
			if len(field_tag.findAll("a")) != 0 and "file number" in field_name.lower() : #checking if file name has hyperlink
				highlights_page_link = "https://www.gao.gov" + field_tag.findAll("a")[0]['href']
				highlight_text = highlights_page_content_grabber(highlights_page_link)
				all_data["Decision link"] = highlights_page_link
				if highlight_text :
					all_data["Decision Highlight"] =  highlight_text
				else :
					all_data["Decision Highlight"] = "Error in opening highlights report page" 
		except :
			field_value = "error"
		all_data[field_name] =  field_value
	all_data["crawl_time"] =  str(datetime.datetime.now()).split(".")[0]

	if 'Decision Summary' in all_data.keys() : #removing decision summary key as it wasn't needed in output as per review
		del all_data['Decision Summary']

	if len(all_data) < 4 : # just checking if crawl went successsful and have valueselse will raise error
		raise
	return all_data
 
		
def all_docket_data_from_search_page_link(search_page_link,log_file_name_with_path = False) :
	""" 
		This function returns list of dict docket data for open/closed 
		docket search filter result with provided parameters. Also writes a log in
		form of links that it has visited if "log_file_name_with_path" variable 
		provided with log file path or file name
  
		Parameters: 
			search_page_link         (str)    : single docket search page link 
												ex input : https://www.gao.gov/legal/bid-protests/search?processed=1&closed=1&page=82
			log_file_name_with_path  (str)    : initialize with Flase, takes input file path in form of string
												helpful while resuming when crawl interrupts midway
												ex input "resume_helper_logs.txt"(not required input though) 
		Returns: 
			list: A list of all docket data in dictionaries
		"""
	all_docket_data = []
	all_docket_page_links = docket_page_links_from_search_page(search_page_link)
	for single_docket in all_docket_page_links :
		if log_file_name_with_path :
			if not log_file_presence_checker(single_docket,log_file_name_with_path) :
				all_docket_data.append(extract_data_from_docket_page(single_docket))
			else :
				pass
		else :
			all_docket_data = [extract_data_from_docket_page(i) for i in all_docket_page_links]
	if log_file_name_with_path :
		write_log = log_file_writer(all_docket_page_links,log_file_name_with_path)
	return all_docket_data

#functions below to be used only in production

def log_file_presence_checker(link_to_check,log_file_name_with_path) :
	""" 
		This function checks if a links is present
		in log file,it's a helper for implenting crawl resume
  
		Parameters: 
			link_to_check               (str)  :  single link
			log_file_name_with_path     (str)  :  log filename to check 
		Returns: 
			Boolean : Returns either True or False based on if a given 
					  link is present in log file or not i.e indicating
					  if it is already browsed by crawler or not
		"""
	if not os.path.isfile(log_file_name_with_path) :
		return False
	with open(log_file_name_with_path,"r")as f :
		content = f.read()
	if link_to_check in content :
		return True
	else :
		return False
	
def log_file_writer(link_to_write,log_file_name_with_path) :
	""" 
		This function writes links as a log to given file.
		helps in resuming crawl
  
		Parameters: 
			link_to_write               (str/list)  :  single link or list of links
			log_file_name_with_path     (str)       :  log filename to write 
		Returns: 
			null
		"""
	with open(log_file_name_with_path,"a") as f :
		if isinstance(link_to_write, list) :
			for single_link in link_to_write :
				f.write(str(single_link) + "\n")
		else :
			f.write(str(link_to_write) + "\n")
		
def temp_file_writer(all_data,temp_file_with_path) :
	""" 
		This function writes current crawl data which are list of dict docket data
		provided by "temp_open_close_all_docket_data_downloader" function.
		This is a helper function and benefits in resuming crawl during interruptions.
  
		Parameters: 
			all_data                (list) :  list of dicts docket data
			temp_file_with_path     (str)  :  temp json store filename with path 
		Returns: 
			null
		"""
	with open(temp_file_with_path,"a") as f :
		for single_data in all_data :
			f.write(json.dumps(single_data) + "\n") 

def temp_open_close_all_docket_data_downloader(docket_type, base_open_close_link) :
	""" 
		This function first checks if a given docket type(open/close) crawl csv file has
		been created or not on todays date if so then it simply returns false (thus limiting only
		one complete crawl on a given day); if not then it takes base open/close search page
		result link and crawl each page result and every docket link present on them, grabs their
		information and write them to docket_type + "_temp_data.json" named json file. 
		But before it crawl any page it checks if that docket or search link is present
		in "log_file_name_with_path" or not. If it's present there then it wont crawl it,
		if not then proceed with the crawl and then write those links to log file after the
		successful crawl. This helps in resuming the crawl from where it left off if the
		crawling gets interrupted midway due to any issue for a given docket type.
		Log file and json file are created in current working directory
  
		Parameters: 
			docket_type           (str)    : takes docket type name either open or close
												ex input : "open" or "close"
			base_open_close_link  (str)    : base search page link for either open or close
											 docket search result
											 ex input : https://www.gao.gov/legal/bid-protests/search?processed=1&closed=1#s-skipLinkTargetForMainSearchResults 
		Returns: 
			str: Succesfully crawled temp json file name or False
				 if a final csv for the day is already generated.
		"""
	today = datetime.datetime.now().date()
	already_created_files = glob.glob(str(docket_type)+"*.csv")
	for single_file in already_created_files :
		date = re.search("([0-9]{4}\-[0-9]{2}\-[0-9]{2})", single_file)[0]
		date = datetime.datetime.strptime(date, '%Y-%m-%d')
		if date.date() == today :
				return False
			
	temp_file_name = str(docket_type) + "_temp_data.json"

	file_count = 0
	all_search_pages_results = available_search_result_page_links(base_open_close_link)
	for single_link in all_search_pages_results :
		print(single_link)
		if not log_file_presence_checker(single_link,log_file_name_with_path) :
			data = all_docket_data_from_search_page_link(single_link,log_file_name_with_path)
			temp_file_writer(data,temp_file_name)
			log_file_writer(str(single_link),log_file_name_with_path)

		file_count = file_count + 1 
		percent_calci = (float(file_count)/float(len(all_search_pages_results)))*100.0
		print ("working on link no " + str(file_count) + " of total links " + str(len(all_search_pages_results)) + " " + str(percent_calci) + " % completed")
	return temp_file_name
   
def final_csv_generator(docket_type,temp_file_name_with_path = False,writepath = False) :
	""" 
		This function reads temp json file provided by function
		"temp_open_close_all_docket_data_downloader";Should be used 
		only after above functions successful execution.This convert 
		the given json file "temp_file_name_with_path" to a pandas 
		dataframe and writes it to csv with filename having docket 
		type and system current time. Then deletes temporary json file 
		and current docket log file.
  
		Parameters: 
			docket_type               (str)          : takes docket type name either open or close
													   ex input : "open" or "close"
			temp_file_name_with_path  (str)          : temp json store filename with path return by func
													   "temp_open_close_all_docket_data_downloader
			writepath                 (str)          : currently not implemented 
		Returns: 
			pandas dataframe : Succesfully execution will return a pandas dataframe else 
							   will return null if final crawl csv file is present in root
							   directory.
		"""
	if not temp_file_name_with_path :
		return
	with open(temp_file_name_with_path,"r") as f :
		all_data_to_be_written = [json.loads(i) for i in f.readlines() if json.loads(i) != False]
	df_docket = pd.DataFrame(all_data_to_be_written)
	if "Decision Highlight" in df_docket : #just putting "Decision Highlight" column to last
		df1 = df_docket.pop('Decision Highlight')
		df_docket['Decision Highlight'] = df1
	#df_docket = df_docket.drop_duplicates()  
	current_date = str(datetime.datetime.now()).split(" ")[0]
	if writepath :
		df_docket.to_csv(writepath + docket_type +"_" + current_date + ".csv", index = False)
	else :
		df_docket.to_csv(docket_type + "_" + current_date + ".csv", index = False)
		
	if os.path.isfile(log_file_name_with_path) :
		os.remove(log_file_name_with_path)
	if os.path.isfile(temp_file_name_with_path) :
		os.remove(temp_file_name_with_path)
	return df_docket

if __name__ == "__main__":

	#grabbing data of all open docket
	start_time = datetime.datetime.now() 
	print("grabbing data for open docket")
	temp_file_name_with_path = temp_open_close_all_docket_data_downloader("open_docket", open_docket_base_link)
	df = final_csv_generator("open_docket",temp_file_name_with_path)
	print("completed")
	if (datetime.datetime.now() - start_time).seconds < 5 :
		print("Already crawled todays file, only one time crawl is allowed in a day")
	print("Execution time = %s" % (datetime.datetime.now() - start_time)) 



	#grabbing data of all close docket
	start_time = datetime.datetime.now() 
	print("grabbing data for close docket")
	temp_file_name_with_path = temp_open_close_all_docket_data_downloader("close_docket", closed_docket_base_link)
	df2 = final_csv_generator("close_docket",temp_file_name_with_path)
	print("completed")
	if (datetime.datetime.now() - start_time).seconds < 5 :
		print("Already crawled todays file, only one time crawl is allowed in a day")
	print("Execution time = %s" % (datetime.datetime.now() - start_time))   
	print("Today's crawl completed")

