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
import re, os, urllib, urllib2, cookielib, time, sqlite3, hashlib, datetime, json
from datetime import timedelta
from time import gmtime, strftime, time
import urlparse
import threading

#-- by bigbax :) ------------------
reload(sys)
sys.setdefaultencoding("UTF8")
#----------------------------------

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

__heading__		= u'Кинопортал kinokong.net'
__kino_host__		= u'http://kinokong.net/'
__view_mode__		= u'59'
__addon__        	= xbmcaddon.Addon()
__addonversion__ 	= __addon__.getAddonInfo('version')
__addonid__      	= __addon__.getAddonInfo('id')
__addonname__    	= __addon__.getAddonInfo('name')
__localize__		= __addon__.getLocalizedString


icon = xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'),'icon.png'))
ifilm = xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'),'mzl.ogryctqw.png'))
ifilms = xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'),'TV Movies.png'))
iserials = xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'),'TV Series.png'))
fan = xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'), '1920x1080_opasnost-linii-zhyoltyij.jpg'))

__cookies__ 	= xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'), r'resources', r'data', r'cookies.txt'))
__db_kinokong__ = os.path.join(xbmc.translatePath("special://profile/").decode('utf-8'), 'Database', 'kinokong')
__menu_file__ 	= xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'), r'resources', r'data', r'menu.mn'))
__cache_dir__	= xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'), r'resources', r'data', r'cache'))

from BeautifulSoup import BeautifulSoup
from MovieItem import MovieItem
from KinokongBase import KinokongBase
from Menu import Menu
import Utils
	
#-------------------------------------------------------------------------------
def get_params(paramstring):
	param=[]
	if len(paramstring)>=2:
		params=paramstring
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]
	return param

params=get_params(sys.argv[2])
xbmc.log('params=%s' %sys.argv[0])
xbmc.log('__addonname__=%s' %__addonid__)

h = int(sys.argv[1])

item = MovieItem(h);

__db_tables__ = {'MOVIES_TABLE' : u'movies', 'TVSHOW_TABLE' : u'tv_show', 'TVSETS_TABLE' : 'tv_sets', 'MULT_TABLE' : 'mult', 'BOOKMARK_VIEW' : 'view_bookmark'}

def get_level2(menu_a, _dir):
	def get_level(menu_a, uri):
		for me in menu_a:
			if me[1]['URI'] == uri:
				level = 0
				if len(me) > 2:
					level = 2
				return me[level:]
	menu = menu_a
	for __dir in _dir:
		menu = get_level(menu, __dir)

	return menu
	
def CombineQualityPlotTxt(video, audio, plot):
	if re.search(u'(^[BD|BR|DVD|HD|HDTV]+.Rip+|HDTV)', video):
		vrate = u'[COLOR FF00FF00]Отличное[/COLOR]'
	elif re.search(u'(^[TV|SAT|TS|WEB|DL|WEB-]+.Rip+|TS|DVDScr|WEBDL)', video):
		vrate = u'[COLOR FFFFE80A]Хорошее[/COLOR]'
	elif re.search(u'(^[CAM]+.Rip+)', video):
		vrate = u'[COLOR FFFF0040]Плохое[/COLOR]'
	else:
		vrate = ''
		
	audio = re.sub(u'(&[#]?[A-z0-9]+;)', u'', audio)
	plot  = re.sub(u'(&[#]?[A-z0-9]+;)', u'', plot)
	
	if vrate == u'' and audio != u'':
		return plot + u'\r\n[COLOR FF01ADAD]Перевод: ' + audio + u'[/COLOR]'
	
	if vrate == u'' and audio == u'':
		return plot
		
	return  u'[COLOR FF01ADAD]Кчество видео: ' + vrate + u' ['+ video +']' + u'\r\nПеревод: ' + audio + u'[/COLOR]\r\n' + plot

	# return plot + u'\r\n[COLOR FF01ADAD]Качество видео: ' + vrate + u' ['+ video +']' + u',   Перевод: ' + audio + u'[/COLOR]'
	
class KinokongPlugin(object):
	
	def __init__(self):
		self._menu			= None
		self.__Menu			= None
		self.__uri_path		= ''
		
	def showMessage(heading, message, times = 3000):
		xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")'%(heading, message, times, icon))
	
	def __get_uri_cache_file(self):
		__file =  xbmc.translatePath(os.path.join(__cache_dir__, str(hash(repr(self._menu)))))
		if not __file.endswith('.cache'):
			__file += '.cache'
		return __file
		
	def __get_uri_path(self):
		__uri_path = re.search(u'^[A-z]+:\/\/%s([0-9A-z\/]+)' %__addonid__, self.__uri_path)
		if __uri_path:
			return __uri_path.group(1)[1:-1].split('/')
			
	def __set_uri_path(self, arg):
		self.__uri_path	= arg
		
	def __is_path(self, uri):
		try:
			if re.search(u'[0-9]+', uri[0]):
				return False
		except:
			pass
		return True
		
	def __create_menu_dir(self, menu, item):
		for m in menu:
			dir = True
			if type(m) == list:			
				item.New(m[0], ifilm, ifilm)
				uri = ''
				if len(m) > 1 and type(m[1]) is dict:
					if not m[1]['URI'] is None:
						uri = sys.argv[0] + u'%s/' %m[1]['URI']
				item.Add(uri, dir)
					
	def __is_directory(self, menu):
		if len(menu) == 2:
			return False
		return True
	
	def __add_remove_favorites(self, id):
		kinokong = KinokongBase(__db_kinokong__)
		kinokong.open()
		if kinokong.is_select_bookmark(id):
			kinokong.setBookmarks(id)
		else:
			kinokong.delBookmark(id)

		kinokong.close()
		self.__refresh()
	
	def __refresh(self):
		xbmc.executebuiltin(u'Container.Refresh')
		
	def __set_view_mode(self):
		xbmcplugin.setContent(h, u'movies')
		xbmc.executebuiltin(u'Container.SetViewMode(%s)' %__view_mode__)
		
	def __get_curr_page(self):
		if 'page' in params:
			return urllib.unquote_plus(params['page'])
		return 0
		
	def __get_thumb(self, thumb):
		if not re.search(ur'http:', thumb):
			thumb = u'%s%s' %(__kino_host__, thumb)
		return thumb
		
	def __delete_rec(self, id):
		dialog = xbmcgui.Dialog()
		if dialog.yesno(__heading__, u'Действительно хотите удалить фильм?'):
			kinokong = KinokongBase(__db_kinokong__)
			kinokong.open()
			kinokong._delete_movie(id)
			#kinokong._delete_files(id)
			kinokong.sync()
			self.__refresh()
		
	def __search_in(self, search, tables):
		movies = []		
		kinokong = KinokongBase(__db_kinokong__)
		kinokong.open()
		
		page = self.__get_curr_page()
		
		movies = kinokong._get_search_page(search.decode('utf-8').lower(), page, [tables])
			
		for movie in movies:
			self.__set_item(movie, not kinokong.is_select_bookmark(movie[16]))
			
		self.__next_page_button(u'Поиск', 1, kinokong._get_search_pages(search, [tables]), page, search)
			
		item.End()
		kinokong.close(False)
		self.__set_view_mode()
		
	def run(self):
		self.load_menu(__menu_file__)
		self.__set_uri_path(sys.argv[0])

		page = self.__get_curr_page()
		__uri_path = self.__get_uri_path()
		
		menu = self._menu
	
		if not __uri_path[0] is '' and self.__is_path(__uri_path):
			menu = get_level2(self._menu, __uri_path)
			
		if 'play' in __uri_path:
			if 'video_id' in params:
				self.play(params['video_id'])
			elif 'file_id' in params:
				self.play(params['file_id'], 1, params['id'],)
			return		
		
		if 'sets' in __uri_path:
			if 'video_id' in params:
				self.sets(params['video_id'])
			return		
			
		if 'fav' in __uri_path:
			if 'video_id' in params:
				self.__add_remove_favorites(params['video_id'])
			return
				
		if 'search' in __uri_path:
			if len(__uri_path) == 2:
				if self.__get_curr_page() == 0:
					if not 's' in params:
						dialog = xbmcgui.Dialog()
						search = dialog.input(u'Поиск:', type=xbmcgui.INPUT_ALPHANUM)
						if search:
							uri = 'plugin://%s/%s/%s/?s=%s' %(__addonid__, __uri_path[0], __uri_path[1], search)
							xbmc.executebuiltin('Container.Update(%s)' %uri)
						return
				self.__search_in(params['s'], self.__Menu.query_to_SQL(menu[1]['query']))
				return
				
		if 'delete' in __uri_path:
			if 'video_id' in params:
				self.__delete_rec(params['video_id'])
			return
		
		if not menu is None and not self.__is_directory(menu):
			query = self.__Menu.query_to_SQL(menu[1]['query'])
			
			if query:
				kinokong = KinokongBase(__db_kinokong__)
				kinokong.open()
				
				for movie in kinokong.get_page(query, page):
					try:
						self.__set_item(movie, not kinokong.is_select_bookmark(movie[16]))
					except:
						continue
				
				self.__next_page_button(menu[0], menu[1]['pages'], kinokong.get_pages(query), page)
				kinokong.close()
		else:
			self.__create_menu_dir(menu, item)
		
		item.End()
		self.__set_view_mode()
		
	def __set_item(self, movie, is_bookmark):
		context_menu = []
		directory = False
		
		thumb = self.__get_thumb(movie[14])
		title = movie[1]
		if movie[13] == 1:
			title = '`'+movie[1]

		if is_bookmark:
			title = u'[COLOR FFE6AE5C]'+title+'[/COLOR]'
			u = 'plugin://%s/fav/?video_id=%s' %(__addonid__, movie[16])
			context_menu.append((u'Убрать', 'XBMC.RunPlugin('+u+')') )
		else:
			u = 'plugin://%s/fav/?video_id=%s' %(__addonid__, movie[16])
			context_menu.append((u'Посмотреть позже', 'XBMC.RunPlugin('+u+')') )
						
		u = 'plugin://%s/delete/?video_id=%s' %(__addonid__, movie[16])
		context_menu.append((u'Удалить из базы', 'XBMC.RunPlugin('+u+')') )
		
		context_menu.append((u'Запустить Обновление', 'RunScript(service.kinokong.update, downloadreport)'))
		
		thumb = self.__get_thumb(movie[14])
					
		item.New(title, thumb, thumb)
		item.SetYear(movie[5])
		item.SetGenre(movie[8])
		item.SetDuration(movie[7])
		item.SetDirector(movie[6])
		item.SetRating(movie[4])
		item.SetPlayable(False)
		item.SetPlot(CombineQualityPlotTxt(movie[9], movie[10], movie[3]))
		
		if movie[17] != '':
			item.SetTailer('plugin://plugin.video.kinopoisk.trealer/?mode=trealer&id=%s&thumb=%s&title=%s' %(movie[17], urllib.quote_plus(thumb), urllib.quote_plus(title.encode('base64'))))
		
		play_file = 'plugin://%s/play/?video_id=%s&%s' %(__addonid__, movie[16], movie[9])
		if movie[13] == 1:
			play_file = 'plugin://%s/sets/?video_id=%s' %(__addonid__, movie[16])
			directory = True
		
		item.AddContextMenu(context_menu)
		item.SetPlayable(directory)
		item.Add(play_file, directory)
		
	def __next_page_button(self, section, maxpages, pages, page, search=''):
		if int(pages) < int(maxpages):
			maxpages = pages
					
		if int(maxpages) == 1:
			maxpages = pages
					
		if int(page)+1 < int(maxpages):
			u = sys.argv[0]
			u += '?page=%s'%urllib.quote_plus(str(int(page)+1))
			if search != '':
				u += '&s=%s'%urllib.quote_plus(search)
				
			item.New(u'[COLOR FF01ADAD]Далее[/COLOR]', ifilm, ifilm)
			item.SetGenre(u'Текущий раздел: %s' %section)
			item.SetPlot(u'\r\n[COLOR FF00FF00]Текущая страница %i\r\nВсего страниц %i[/COLOR]' %(int(page)+1, int(maxpages)))
			item.SetPlayable(u'false')
			item.Add(u, True)
		
	def __get_param(self, param):
		if param in params:
			return urllib.unquote_plus(params[param])
		return None
	
	def load_menu(self, menu_file):
		fileName, fileExtension = os.path.splitext(menu_file)
		
		path_cache 		= menu_file[:menu_file.rfind(os.path.basename(menu_file))]
		name_cache 		= os.path.basename(menu_file)
		noext_cache 	= name_cache[:name_cache.rfind(fileExtension)]
		name_cache		= '~'+noext_cache+'.cache'
		cache_file	 	= xbmc.translatePath(os.path.join(__cache_dir__, name_cache))
		self.__Menu		= Menu(menu_file, __db_tables__, cache_file)
		self._menu 		= self.__Menu.GetMenu()
	
	def sets(self, id):
		kinokong = KinokongBase(__db_kinokong__)
		kinokong.open()
		
		m_info = kinokong.getMovieInfoByID(id)
		thumb  = self.__get_thumb(m_info[14])
		
		for file in kinokong._get_files(id):
			item.New(file['name'] + ' ' + m_info[1], thumb, thumb)
			item.SetPlayable(False)
			#if file[5]:
			#	item.SetTotalTime(file[5])		
			
			play_file = 'plugin://%s/play/?file_id=%s&id=%s' %(__addonid__, file['fileid'], file['id'])
			item.Add(play_file, False)
		
		item.End()
		kinokong.close(False)
		self.__set_view_mode()
		
	def play(self, id, type=0, video_id=0):
		pDialog = xbmcgui.DialogProgress()
		ret = pDialog.create(__heading__, 'Воспроизведение...')
		
		kinokong = KinokongBase(__db_kinokong__)
		kinokong.open()
		
		if type == 1:
			mt = kinokong._get_video_file2(id, video_id)
			play_file = mt['url']
		
		if type == 0:
			mt = kinokong._get_video_file(id)	
			play_file = mt['file']
		
		m_info = kinokong.getMovieInfoByID(id)
			
		if not m_info is None:
			thumb = self.__get_thumb(m_info[14])
			
			info = {'title' : m_info[1], 'plot' : m_info[3], 'thumb' : thumb, 'genre' : m_info[8], 'year' : m_info[5], 'rating' : m_info[4]}
			if type == 1:
				info = {'title' : mt['name'] + '-' + m_info[1], 'plot' : m_info[3], 'thumb' : thumb, 'genre' : m_info[8], 'year' : m_info[5], 'rating' : m_info[4]}
			
			xbmc.sleep(1000)
			pDialog.update(-1, u'Открытие потока...', u'[COLOR FF83D902]: %s[/COLOR]' %info['title'])
			
			i = xbmcgui.ListItem(info['title'], thumbnailImage=info['thumb'])#, path=play_file)
			i.setInfo(type='video', infoLabels={'title' : info['title'], 'plot' : info['plot'], 'genre' : info['genre'], 'year' : info['year'], 'rating' : info['rating']})
			#i.setProperty('mimetype', 'video/mp4')
			i.setProperty('IsPlayable', 'true')
			
		playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
		playlist.clear()
		
		playlist.add(play_file, i)
		
		xbmcplugin.setResolvedUrl(handle=h, succeeded=True, listitem=i)
		
		while not xbmc.Player().isPlaying():
			xbmc.sleep(100)
		
		while xbmc.Player().isPlaying():
			xbmc.sleep(500)
			try:
				timer = xbmc.Player().getTime()
			except:
				timer = 1
			if timer > 0:
				break
		
		xbmc.sleep(1000)
		pDialog.close()
		kinokong.close(False)
		
	def _dump(self):
		xbmc.log('%s' %str(self._menu_cache))
		xbmc.log('%s' %self._menu)
		xbmc.log('%s' %hash(repr(self._menu)))
		xbmc.log('%s' %self._mode_uri)
		
if __name__ == '__main__':
	plugin = KinokongPlugin()
	plugin.run()

		
