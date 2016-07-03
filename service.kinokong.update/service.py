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
import re, os, urllib
import xbmc
import xbmcgui
import xbmcaddon
import random
import datetime
import _strptime
import time
import traceback

# Import the module
from KinokongBase import KinokongBase
from BeautifulSoup import BeautifulSoup
from Parser import Parser
import demjson3 as json


__addon__        	= xbmcaddon.Addon()
__addonversion__ 	= __addon__.getAddonInfo('version')
__addonid__      	= __addon__.getAddonInfo('id')
__addonname__    	= __addon__.getAddonInfo('name')
__localize__		= __addon__.getLocalizedString
__db_kinokong__    	= os.path.join(xbmc.translatePath("special://profile/").decode('utf-8'), 'Database', 'kinokong')

__kp_cookies__ 		= xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'), r'resources', r'data', r'kpcookies.txt'))
__cookies__ 		= xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'), r'resources', r'data', r'cookies.txt'))
__update_p__ 		= xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'), r'resources', r'data', r'update_st'))
__post__ 			= urllib.urlencode({'login_name': __addon__.getSetting("login"), 'login_password': __addon__.getSetting("password"), 'login': "submit"})

def log(txt):
	if __addon__.getSetting("enable_logging") == "true":
		if isinstance (txt,str):
			txt = txt.decode('utf-8')
		
		message = u'%s: %s' % (__addonname__, txt)
		xbmc.log(msg=message)

def showMessage(heading, message, times = 3000):
	icon = xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'),'icon.png'))
	xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")'%(heading, message, times, icon))

def get_update_time():
	update_time = 1*60*60
		
	_1_min  = __addon__.getLocalizedString(id=62009)
	_30_min = __addon__.getLocalizedString(id=62010)
	_1_hour = __addon__.getLocalizedString(id=62011)
	_2_hour = __addon__.getLocalizedString(id=62012)
	_3_hour = __addon__.getLocalizedString(id=62013)
	_4_hour = __addon__.getLocalizedString(id=62014)
	_5_hour = __addon__.getLocalizedString(id=62015)
	
	if __addon__.getSetting("update_interval") == _1_min:
		update_time = 1*60
	if __addon__.getSetting("update_interval") == _30_min:
		update_time = 1*60*30
	elif __addon__.getSetting("update_interval") == _1_hour:
		update_time = 1*60*60
	elif __addon__.getSetting("update_interval") == _2_hour:
		update_time = 1*60*60*2
	elif __addon__.getSetting("update_interval") == _3_hour:
		update_time = 1*60*60*3
	elif __addon__.getSetting("update_interval") == _4_hour:
		update_time = 1*60*60*4
	elif __addon__.getSetting("update_interval") == _5_hour:
		update_time = 1*60*60*5
		
	return update_time
	
if __name__ == u"__main__":
	log('Started')
	monitor = xbmc.Monitor()
	log('Update time = %i' %get_update_time())
	
	if __addon__.getSetting("login") == '' or __addon__.getSetting("password") == '':
		log("Login or password empty")
		showMessage(__addonname__, "Не задан логин или пароль.", 10000)
		exit()
		
	monitor.waitForAbort(1*20) # 20 sec
	if __addon__.getSetting("startsys_enable") == 'false':
		log("startsys_enable:false")
		log("Stop")
		exit()
			
	pDialog = xbmcgui.DialogProgressBG()
	
	def IProgressFunctionM(progress_step):
		pDialog.update(int(progress_step), 'Обновление фильмов')
		pass
		
	def IProgressFunctionS(progress_step):
		pDialog.update(25+int(progress_step), 'Обновление сериалов')
		pass
		
	def IProgressFunctionU(progress_step):
		pDialog.update(50+int(progress_step), 'Обновление мультфильмов')
		pass
	
	def IProgressFunctionP(progress_step):
		pDialog.update(75+int(progress_step), 'Обновление передачь')
		pass

	while (True):
		if os.path.isfile(__update_p__):
			if not os.access(__update_p__, os.R_OK):
				log("Access denied to this file %s", __update_p__)
				if monitor.waitForAbort(get_update_time()):
					kinokong.close(False)
					pDialog.close()
					log("Exit")
					exit()
				continue
				
			f_update = open(__update_p__, 'r')
			if f_update.readline() == 'true':
				log("The upgrade process has already begun")
				log("Exit")
				exit()
						
		f_update = open(__update_p__, 'w')
		f_update.write('true')
		f_update.flush()
		f_update.close()
				
		Progress = pDialog.create('Kinokong', 'Обновление контента...')
		
		kinokong = KinokongBase(__db_kinokong__)
		log("Open db %s" %kinokong._filename)
		kinokong.open()
		kinokong.create_table()
		
		parser = Parser(__cookies__, __kp_cookies__, __post__) 
		
		# Фильмы
		try:
			if __addon__.getSetting("movies_enable") == 'true':
				url = 'http://kinokong.net/films/'
				parser.setProgressMaxPercent(25)
				parser.setProgressFunction(IProgressFunctionM)
				
				log(u"Обновление фильмотеки %s" %time.time())
				log(u"Обновление контента...")
				
				stop_date = kinokong.get_last_update_movies()
				log("stop_date = %s" %stop_date)
				
				info_array = parser.getArrayPagesProgress(url, stop_date, True)
				
				log(u"len(info_array) = %i" %len(info_array))
												
				if len(info_array) != 0:
					pDialog.update(25, 'Сохранение в базу фильмов')
					kinokong.movies_update(info_array)
					kinokong.sync()
					xbmc.executebuiltin(u'Container.Refresh')
		except:
			xbmc.log(msg=u'%s: %s' %(__addonname__, traceback.format_exc()))

		# Сериалы
		try:
			if __addon__.getSetting("serials_enable") == 'true':
				url = 'http://kinokong.net/serial/'
				
				parser.setProgressMaxPercent(25)
				parser.setProgressFunction(IProgressFunctionS)
				
				log(u"Обновление сериалов %s" %time.time())
				log(u"Обновление контента...")
				
				stop_date = kinokong.get_last_update_tvsets()
				log('stop_date = %s' %stop_date)
				
				info_array = parser.getArrayPagesProgress(url, stop_date, True, 1)

				log(u"len(info_array) = %i" %len(info_array))
								
				if len(info_array) != 0:
					pDialog.update(50, 'Сохранение в базу')
					kinokong.tvsets_update(info_array)
					kinokong.sync()
					xbmc.executebuiltin(u'Container.Refresh')
		except:
			xbmc.log(msg=u'%s: %s' %(__addonname__, traceback.format_exc()))

		# Мультфильмы
		try:
			if __addon__.getSetting("mult_enable") == 'true':
				url = 'http://kinokong.net/multfilm/'

				parser.setProgressMaxPercent(25)
				parser.setProgressFunction(IProgressFunctionU)

				log(u"Обновление мультфильмов %s" %time.time())
				log(u"Обновление контента...")
				stop_date = kinokong.get_last_update_mult()
				log('stop_date = %s' %stop_date)
				
				info_array = parser.getArrayPagesProgress(url, stop_date, True)

				log(u"len(info_array) = %i" %len(info_array))
				
				if len(info_array) != 0:
					pDialog.update(75, 'Сохранение в базу')
					kinokong.mult_update(info_array)
					kinokong.sync()
					xbmc.executebuiltin(u'Container.Refresh')
		except:
			xbmc.log(msg=u'%s: %s' %(__addonname__, traceback.format_exc()))

		# Передачи
		try:
			if __addon__.getSetting("shows_enable") == 'true':
				url = 'http://kinokong.net/dokumentalnyy/'

				parser.setProgressMaxPercent(25)
				parser.setProgressFunction(IProgressFunctionP)

				log(u"Обновление ТВ передачь %s" %time.time())
				log(u"Обновление контента...")
				
				stop_date = kinokong.get_last_update_tvshows()
				log('stop_date = %s' %stop_date)
				
				info_array = parser.getArrayPagesProgress(url, stop_date, True)

				log(u"len(info_array) = %i" %len(info_array))

				if len(info_array) != 0:	
					pDialog.update(99, 'Сохранение в базу')
					kinokong.tvshows_update(info_array)
					kinokong.sync()
					xbmc.executebuiltin(u'Container.Refresh')
		except:
			xbmc.log(msg=u'%s: %s' %(__addonname__, traceback.format_exc()))
		
		pDialog.update(99, 'Сохранение...')
			
		kinokong.close()
		pDialog.close()
		log(u"Сохранено")
		xbmc.executebuiltin(u'Container.Refresh')
		
		f_update = open(__update_p__, 'w')
		f_update.write('false')
		f_update.flush()
		f_update.close()

		if monitor.waitForAbort(get_update_time()):
			kinokong.close(False)
			pDialog.close()
			log("Exit")
			exit()

log("Stop")
