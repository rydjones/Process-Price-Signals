#!/usr/bin/python

import datetime, re, os.path, sys, pickle

def GetPriceSignals():
	"""
	Scrape price signal email messages from Dropbox file
	and return list of (date,price) tuples
	"""

	file_path = os.path.abspath(DropboxPath()+"ifttt/price_signals.txt")

	# Read file, split into separate price signals
	txt = open(file_path).read()
	price_signals = txt.split("- - - - -")

	# Date (mmddyyyy) regular expression
	re_date='((?:[0]?[1-9]|[1][012])[-:\\/.](?:(?:[0-2]?\\d{1})|(?:[3][01]{1}))[-:\\/.](?:(?:[1]{1}\\d{1}\\d{1}\\d{1})|(?:[2]{1}\\d{3})))(?![\\d])'	# MMDDYYYY 1
	rg_date = re.compile(re_date,re.IGNORECASE|re.DOTALL)

	# Price (as float) regular expression
	re1_f_price='([+-]?\\d*\\.\\d+)(?![-+0-9\\.])'	# Float 1
	re2_f_price='(\\s+)'	# White Space 1
	re3_f_price='((?:[a-z][a-z]+))'	# Word 1
	rg_f_price = re.compile(re1_f_price+re2_f_price+re3_f_price,re.IGNORECASE|re.DOTALL)

	# Price (as integer) regular expression
	re1_i_price='(\\d+)'	# Integer Number 1
	re2_i_price='.*?'	# Non-greedy match on filler
	re3_i_price='( )'	# White Space 1
	re4_i_price='((?:[a-z][a-z]+))'	# Word 1
	rg_i_price = re.compile(re1_i_price+re2_i_price+re3_i_price+re4_i_price,re.IGNORECASE|re.DOTALL)

	# Initialize list for (date,price) tuples
	prices = []

	# Initialize list for error reporting if regexs don't fit
	regex_errors = []

	for signal in price_signals:
		
		# Execute regular expression searches
		m_date = rg_date.search(signal)
		m_f_price = rg_f_price.search(signal)
		m_i_price = rg_i_price.search(signal)

		# Initialize price tuple variables
		date = 0
		price = 0

		# Extract data from regex results
		if m_date:
			month, day, year = m_date.group(1).split('/')
			date = datetime.date(int(year),int(month),int(day))
		if m_f_price:
			price = float(m_f_price.group(1))
		elif m_i_price:
			price = float(m_i_price.group(1))
		if date and price:
			prices.append((date,price))
		else:
			regex_errors.append(signal)

	# Report signals with no match in regexs
	if regex_errors:
		print 'REGEX ERRORS:\n'
		print regex_errors

	# Return list of (date,price) tuples
	return prices
	

def AveragePrice(price_signals):
	"""
	Returns the overall average price as float
	"""

	price_sum = 0

	for signal in price_signals:
		price_sum += signal[1]

	return price_sum / len(price_signals)


def MostRecentPrice(price_signals):
	"""
	Returns the latest price signal as (date,price) tuple
	"""

	#most_recent = (datetime.date(2011,1,1),0)

	#for signal in price_signals:
	#	if signal[0] >= most_recent[0]:
	#		most_recent = signal

	end_of_list = len(price_signals)-1
	most_recent = price_signals[end_of_list]

	return most_recent


def HighPriceAlert(price_signals):
	"""
	If an alert is required for today or tomorrow, write file with
	name as alert message to trigger ifttt recipe
	"""

	most_recent = MostRecentPrice(price_signals)
	most_recent_date = most_recent[0]
	
	today = datetime.date.today()
	tomorrow = datetime.date.today() + datetime.timedelta(days=1)
	str_date = str(most_recent_date)

	price = most_recent[1] / float(100)
	str_price = "$%0.2f" % price

	file_directory = DropboxPath() + 'Public/OGE Price Signals/'

	if ( most_recent_date == today or most_recent_date == tomorrow ) and price > 0.15:
		
		if not InAlertHistory(most_recent):

			# Generate file as alert trigger for ifttt
			alert_title = 'HIGH ELECTRIC PRICE of ' + str_price + ' on '+ str_date
			file_path = os.path.abspath(file_directory+alert_title+'.txt')
			open(file_path,'w').close()

			# Write signal to alert log
			WriteToAlertHistory(most_recent)


def DropboxPath():
	"""
	Return platform-specific path to Dropbox folder
	TODO: test on Vista, 7, etc for path. Probably different from my old XP box.
	"""

	# Set appropriate Dropbox filepath by platform
	if sys.platform == "darwin":
		file_directory = os.path.expanduser("~/Dropbox/")
	elif sys.platform == "win32":
		file_directory = os.path.expanduser("~\\My Documents\\My Dropbox\\")
	else:
		print "Unsupported platform, assumes file is in current working directory"
		file_directory = ""

	return file_directory


def WriteToAlertHistory(signal):
	"""
	Writes alert to a log to avoid duplication
	"""
	file_path = os.path.abspath(DropboxPath()+"ifttt/alert_log.p")
	if os.path.exists(file_path):
		alert_log = pickle.load(open(file_path,'rb'))
	else:
		alert_log = []
	alert_log.append(signal)
	pickle.dump(alert_log, open(file_path,'wb'))


def InAlertHistory(search_signal):
	"""
	Searches alert log, returns 1 if found
	"""
	file_path = os.path.abspath(DropboxPath()+"ifttt/alert_log.p")
	if os.path.exists(file_path):
		alert_log = pickle.load(open(file_path,'rb'))
		for signal in alert_log:
			if signal == search_signal:
				return 1
	return 0


if __name__ == '__main__':
	HighPriceAlert(GetPriceSignals())
