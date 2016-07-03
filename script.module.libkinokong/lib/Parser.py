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
import re, urllib2, cookielib, urlparse, sys
import xbmc

from BeautifulSoup import BeautifulSoup
from Kinopoisk import Kinopoisk
import Utils

import demjson3 as json

reload(sys)
sys.setdefaultencoding("UTF8")

class Parser(object):

	def __init__(self, pm_cookie, kp_cookie, post):
		self.__primary_cookie 	= pm_cookie
		self.__kinopoisk_cookie = kp_cookie
		self.__post_data		= post
		self.__progress_pos		= 0
		self.__progress_step 	= 0
		self.__IProgressFunc	= self.__progress
		self.__progress_max 	= 100.0
		self.__cache			= {}

	def setProgressMaxPercent(self, max_percent):
		self.__progress_max = (max_percent + 0.0)

	def setProgressFunction(self, function):
		self.__IProgressFunc = function

	def __progress(self, progress):
		pass

	def cache(function):
		def new(*args, **kwargs):
			h = hash(repr(function) + repr(args) + repr(kwargs))
			if type(args[0]) == Parser:
				self = args[0]
				if not h in self.__cache:
					self.__cache[h] = function(*args, **kwargs)

				return (self.__cache[h])
		return(new)

	@cache
	def getCountToProgress(self, url, stop_date):
		progress = 0

		for x in range(self.getPagesConut(url)):
			_getUrl = url + 'page/%i/'%(x+1)
			html = Utils.get_HTML(_getUrl, self.__primary_cookie, self.__post_data)
			soup = BeautifulSoup(html, fromEncoding="windows-1251")

			content = soup.find("div", {"id":"dle-content"})
			if content:
				for movie in content.findAll("div", {"class":"owl-item"}):
					movie_date	= movie.find('span', {'class':'main-sliders-popup'}).span.text
					progress += 1
					curr_date = Utils.FormatDate(movie_date)
					if curr_date <= stop_date:
						return progress
		return 1

	@cache
	def getPagesConut(self, url):
		html = Utils.get_HTML(url, self.__primary_cookie, self.__post_data)

		soup = BeautifulSoup(html, fromEncoding="windows-1251")
		try:
			max_pages = 0
			for rec in soup.find("div", {"class":"navigation"}).findAll('a'):
				try:
					if max_pages < int(rec.text):
						max_pages = int(rec.text)
				except:
					pass
		except:
			max_pages = 1

		return max_pages

	@cache
	def getMoviesCount(self, url):
		pages_count = self.getPagesConut(url)
		url += 'page/%i/' %pages_count
		html = Utils.get_HTML(url, self.__primary_cookie, self.__post_data)
		soup = BeautifulSoup(html, fromEncoding="windows-1251")

		try:
			movies_count = 25*(pages_count-1) + len(soup.findAll("div", {"class":"owl-item"}))
		except:
			movies_count = len(soup.findAll("div", {"class":"owl-item"}))

		return movies_count

	def __normalize_time(self, time):
		normal_t = 0
		if re.search(u'([0-9]+).*мин', time):
			normal_t = re.search(u'([0-9]+).*мин', time).group(1)
		elif re.search(u'(?P<hour>[0-9]{1,2}):(?P<min>[0-9]{2}):(?P<sec>[0-9]{2})', time):
			min = int(re.search(u'(?P<hour>[0-9]{1,2}):(?P<min>[0-9]{2}):(?P<sec>[0-9]{2})', time).group('hour')) * 60
			min = min + int(re.search(u'(?P<hour>[0-9]{1,2}):(?P<min>[0-9]{2}):(?P<sec>[0-9]{2})', time).group('min'))
			normal_t = min
		elif re.search(u'(?P<hour>[0-9]{1,2}):(?P<min>[0-9]{2})', time):
			min = int(re.search(u'(?P<hour>[0-9]{1,2}):(?P<min>[0-9]{2})', time).group('hour')) * 60
			min = min + int(re.search(u'(?P<hour>[0-9]{1,2}):(?P<min>[0-9]{2})', time).group('min'))
			normal_t = min
		elif re.search(u'(?P<hour>[0-9]{1,2}).(?P<min>[0-9]{2}).(?P<sec>[0-9]{2})', time):
			min = int(re.search(u'(?P<hour>[0-9]{1,2}).(?P<min>[0-9]{2}).(?P<sec>[0-9]{2})', time).group('hour')) * 60
			min = min + int(re.search(u'(?P<hour>[0-9]{1,2}).(?P<min>[0-9]{2})', time).group('min'))
			normal_t = min
		# elif re.search(u'(?P<hour>[0-9]{1,2})[ ч| часа]+(?P<min>[0-9]{1,2})[ м]+', time):
        elif re.search(u'(?P<hour>[0-9]{1,2}) *(ч|часа) *(?P<min>[0-9]{1,2}) *(м|минут) *?$', time):
			min = int(re.search(u'(?P<hour>[0-9]{1,2}) *(ч|часа) *(?P<min>[0-9]{1,2}) *(м|минут) *?$', time).group('hour')) * 60
			min = min + int(re.search(u'(?P<hour>[0-9]{1,2}) *(ч|часа) *(?P<min>[0-9]{1,2}) *(м|минут) *?$', time).group('min'))
			normal_t = min
		return normal_t
	
	def getPlayList(self, url):
		html = Utils.get_HTML(url, self.__primary_cookie, self.__post_data)
		list = []
		pl_list = False
		pl_file = ''

		soup = BeautifulSoup(html, fromEncoding="windows-1251")

		time = ''
		country = ''
		sound = ''
		year = ''
		rate = ''
		
		full_kino_info = soup.find('div', {'class':"full-kino-info"})
		if full_kino_info:
			for at in full_kino_info.findAll('div'):
				if at.span.text == u'Звук:':
					sound = at.b.text
					continue
				if at.span.text == u'Время:':
					time = at.b.text
					continue
				if at.span.text == u'Страна:':
					country = at.b.text
					continue
				if at.span.text == u'Год:':
					year = at.b.text
					continue

		trailer = ''
		tr = soup.find('div', {'class': "box"})
		if tr:
			__trailer = tr.find('param', {'name': "movie"})
			if __trailer:
				trailer = __trailer['value']

				__trailer = re.search(u'^\/\/(www.*)', trailer)
				if __trailer:
					trailer = 'http://' + __trailer.group(1)

				__trailer =  re.search(u'^http:/([a-zA-Z]+.*)', trailer)
				if __trailer:
					trailer = 'http://' + __trailer.group(1)

		director = ''
		div = soup.find('div', {'class':"full-kino-info1 full-kino-greybg"})
		if not div is None:
			match_d = re.search(u':(.*)$', div.text)
			if match_d:
				director = match_d.group(1)

		time = self.__normalize_time(time)

		quality = ''
		full_quality = soup.find('div', {'class':"full-quality"})
		if full_quality:
			quality = full_quality.text

		if re.search(ur'flashvars', soup.find('div', {'class': "box visible"}).text):
			for p in re.compile('var flashvars = {(.+?)}', re.MULTILINE | re.DOTALL).findall(
					soup.find('div', {'class': "box visible"}).text.replace(' ', ' ')):
				pl = re.findall('pl:\"(http:.*?)\"', p)
				if pl:
					pl_list = True
					pl_file = pl[0]
					break
		else:
			try:
				flashAll = soup.findAll('object')
				for flash in flashAll:
					try:
						flash = flash.find('param', {'name': 'flashvars'})
						pl = re.search('(?P<pre>pl[=: ]|file[:= ])(?P<url>http:.*?\.(txt|flv|mp4))', flash['value'])
						if pl.group('pre') == u'pl=':
							pl_list = True
							pl_file = pl.group('url')
					except:
						continue
			except:
				pass

		return quality, sound, time, director, trailer, country, year, pl_list, pl_file, rate

	def getArrayPages(self, url, stop_date, kin_raite=False, movie_type=0):
		html = Utils.get_HTML(url, self.__primary_cookie, self.__post_data)
		soup = BeautifulSoup(html, fromEncoding="windows-1251")
		mi = []

		if soup.find("div", {"id":"dle-content"}):
			content = soup.find("div", {"id":"dle-content"})
			for movie in content.findAll("div", {"class":"owl-item"}):
				mii = Utils.Info()
				gen = []

				self.__progress_pos += self.__progress_step
				self.__IProgressFunc(self.__progress_pos)

				# Movie text
				mii.text = movie.find('span', {'class':'main-sliders-popup'}).i.text

				# Movie URL
				mii.url		= movie.find('div', {'class':'main-sliders-title'}).a['href']

				# Data add
				mii.adata	= movie.find('span', {'class':'main-sliders-popup'}).span.text
				curr_date = Utils.FormatDate(mii.adata)
				if curr_date <= stop_date:
					self.__progress_pos = -1
					return mi

				files = []

				try:
					m_type = 0
					list 			= self.getPlayList(mii.url)
					mii.rip 		= list[0]
					mii.sound 		= list[1]
					mii.duration	= list[2]
					mii.director 	= list[3]
					mii.trailer		= list[4]
					mii.country		= list[5]
					mii.year		= list[6]
					mii.pl			= list[7]
					mii.plfile		= list[8]
					mii.rating		= list[9]
				except:
					xbmc.log('getPlayList error')
					pass

				# Movie title
				mii.title	= movie.find('div', {'class':"main-sliders-title"}).a.text

				# Movie year
				if mii.year == '':
					try:
						mii.year	= re.search('[\(|\ |-]([0-9]{4})\)', mii.title).group(1)
						# print mii.year
					except:
						# print 'error'
						xbmc.log('Movie year regex error')

				try:
					mii.title	= re.search(u'(.*?)\(.*\)', mii.title).group(1)
					mii.title	= mii.title.strip()
				except:
					# print 'error'
					xbmc.log('Movie title regex error')

				# Movie genre array
				for genre in movie.find('span', {'class':"main-sliders-popup"}).findAll("a"):
					gen.append(genre.text.replace('\n', ''))
				mii.genre 	= gen

				try:
					tst = int(mii.year)
				except:
					mii.year = u''

				if kin_raite:
					try:
						kinopoisk = Kinopoisk(self.__kinopoisk_cookie)
						kp = kinopoisk.get_search_kinopoisk2(mii.title, mii.year, '', mii.country, movie_type)
						if kp[0]:
							mii.rating = kp[0]
						mii.kpid = kp[1]
						if not mii.duration:
							mii.duration = kp[2]

						if mii.text == u'...' or mii.year == u'':
							kp = kinopoisk.get_kinopoisk(kp[1])
							mii.text = kp[3]
							if not mii.genre:
								mii.genre = kp[1]
							if not mii.year:
								mii.year = kp[0]
							if not mii.country:
								mii.country = kp[2]
					except:
						# print 'Kinopoisk error'
						xbmc.log('Kinopoisk error')

				# Movie poster thumb
				for img in movie.find('div', {'class':"main-sliders-img"}).contents:
					if str(type(img)) == u"<class 'BeautifulSoup.Tag'>" and img.name == u'img':
						mii.imgt = img['src']
						if not re.search(ur'http:', mii.imgt):
							mii.imgt = 'http://kinokong.net/%s' %mii.imgt
						break

				# Movie poster
				mii.img		= mii.imgt
				mii.img		= mii.img.replace("/thumbs","")

				# Array Info append
				mi.append(mii)
		return mi

	def getArrayPagesProgress(self, url, stop_date, kin_raite=False, movie_type=0):
		ret_arrary = []
		self.__progress_pos = 0
		self.__progress_step = self.__progress_max / self.getCountToProgress(url, stop_date)

		max_page = self.getPagesConut(url)

		for x in range(max_page):
			furl = url + 'page/%i/'%(x+1)
			ret_arrary += self.getArrayPages(furl, stop_date, kin_raite, movie_type)
			if self.__progress_pos == -1:
				break
		return ret_arrary