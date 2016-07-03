# -*- coding: utf-8 -*-
#/*
# *      Copyright (C) 2015 silver-one@ya.ru
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# */
import re, datetime, urllib2, cookielib, urlparse, sys
from datetime import timedelta
from datetime import datetime
from datetime import date
from time import mktime
import time

from BeautifulSoup import BeautifulSoup

reload(sys)
sys.setdefaultencoding("UTF8")

def FormatDate(dtimestr):
	match = re.search(ur"^([0-9]{1,2}-[0-9]{1,2}-20[0-9]{2}|Вчера|Сегодня).*([0-9]{2}:[0-9]{2})$", dtimestr)

	if match:
		if match.group(1) == u'Вчера':
			today = datetime.now()
			today = today - timedelta(hours=24)
			str = u'%s-%s-%s' %(today.day, today.month, today.year)
			return datetime.fromtimestamp(mktime(time.strptime(str+match.group(2), "%d-%m-%Y%H:%M")))
		elif match.group(1) == u"Сегодня":
			now = datetime.now().strftime(u'%d-%m-%Y')
			return datetime.fromtimestamp(mktime(time.strptime(now+match.group(2), "%d-%m-%Y%H:%M")))
		else:
			return datetime.fromtimestamp(mktime(time.strptime(match.group(1)+match.group(2), "%d-%m-%Y%H:%M")))
	elif re.search(ur"^([12]{1}[09]{1}[0-9]{2}-[0-9]{1,2}-[0-9]{1,2}) ([0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2})$", dtimestr):
		return datetime.fromtimestamp(mktime(time.strptime(dtimestr, "%Y-%m-%d %H:%M:%S")))
	return datetime.now() - timedelta(hours=24*5)

def normalizeFile(file):
	retfile = file
	ts = re.search('\.[A-z0-9]{3,5}(,)$', file)
	try:
		if ts.group(1) == u',':
			retfile = file.replace(',', '')
	except:
		pass
	
	ts = re.search(',(http:\/\/(.*?)$)', file)
	try:
		if ts.group(1):
			retfile = ts.group(1)
	except:
		pass
		
	return retfile
		
def get_HTML(url, cookie_file, post=None, referer=None, step=0):
	cj = cookielib.MozillaCookieJar(cookie_file)

	try:
		cj.load(cookie_file, True, True)
	except:
		cj.save()

	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	urllib2.install_opener(opener)

	if post is None:
		request = urllib2.Request(url)
	else:
		request = urllib2.Request(url, post)

	host = urlparse.urlsplit(url).hostname
	if host == None:
		host = url.replace('http://', '').split('/')[0]

	if referer == None:
		referer = 'http://' + host

	if step == 0:
		request.add_header('User-Agent', 'Mozilla/5.0 (Linux; U; Android 4.1.1; en-gb; Build/KLP) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30')
	elif step == 1:
		request.add_header('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240')


	request.add_header('Host',   host)
	request.add_header('Accept', '*/*')
	request.add_header('Accept-Language', 'ru-RU')
	request.add_header('Referer', referer)

	try:
		f = urllib2.urlopen(request)
	except IOError, e:
		if hasattr(e, 'reason'):
			print('We failed to reach a server.')
			print e
			if step == 0:
				return get_HTML(url, cookie_file, post, referer, 1)
			return ""
		elif hasattr(e, 'code'):
			print('The server couldn\'t fulfill the request.')

	html = f.read()
	cj.save()
	return html

def Get_Page_and_Movies_Count(url,fcookies,post):
	html = get_HTML(url, fcookies, post)
	soup = BeautifulSoup(html, fromEncoding="windows-1251")
	try:
		max_page = 0
		for rec in soup.find("div", {"class":"navigation"}).findAll('a'):
			try:
				if max_page < int(rec.text):
					max_page = int(rec.text)
			except:
				pass

		url += 'page/%i/'%max_page
		html = get_HTML(url, fcookies)
		soup = BeautifulSoup(html, fromEncoding="windows-1251")
		count = 25*(max_page-1)+len(soup.findAll("div", {"class":"new_movie15"}))+len(soup.findAll("div", {"class":"short_music"}))

	except:
		max_page = 1
		count = len(soup.findAll("div", {"class":"new_movie15"}))++len(soup.findAll("div", {"class":"short_music"}))

	return max_page, count

class Info:
	img         = ''
	imgt        = ''
	url         = '*'
	title       = ''
	year        = ''
	genre       = []
	country     = ''
	director    = ''
	text        = ''
	artist      = ''
	orig        = ''
	duration    = ''
	rating      = ''
	rip         = ''
	sound		= ''
	trailer		= ''
	adata		= ''
	kpid		= ''
	files		= []
	pl			= False
	plfile		= ''

class GenreList:
	url         = '*'
	title       = ''

class SubMenu:
	title       = ''
	url         = '*'
	count		= 0

class MenuEntry:
	title		= ''
	url			= '*'
	submenu		= []
