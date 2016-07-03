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
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

class MovieItem(object):
	def __init__(self, handle):
		self.handle	= handle
		self.item	= None
		pass
		
	def New(self, name, iconImg, thumbImg):
		self.item = xbmcgui.ListItem(name, iconImage=iconImg, thumbnailImage=thumbImg)
		self.item.setInfo(type=u'video', infoLabels={u'title': name})
		
	def Add(self, uri, dir=False):
		if not self.item == None:
			xbmcplugin.addDirectoryItem(self.handle, uri, self.item, dir)
			
	def AddContextMenu(self, list):
		self.item.addContextMenuItems(list, False)
	
	def SetPlayable(self, bool):
		self.item.setProperty(u'IsPlayable', str(bool))
	
	def End(self):
		xbmcplugin.endOfDirectory(self.handle, succeeded=True, cacheToDisc=False)
		
	def SetTotalTime(self, time):
		self.item.setProperty(u'TotalTime', time)
		
	def SetFanArt(self, img):
		self.item.setProperty(u'fanart_image', img)
		
	def SetDirector(self, name):
		self.item.setInfo(type=u'video', infoLabels={u'director' : name})

	def SetDuration(self, minutes):
		self.item.setInfo(type=u'video', infoLabels={u'duration' : minutes})

	def SetPremieredDate(self, date):
		self.item.setInfo(type=u'video', infoLabels={u'premiered' : date})

	def SetPlayCount(self, playcount):
		self.item.setInfo(type=u'video', infoLabels={u'playcount' : playcount})
		
	def SetMPAA(self, mpaa):
		self.item.setInfo(type=u'video', infoLabels={u'mpaa' : mpaa})

	def SetTailer(self, trailer):
		self.item.setInfo(type=u'video', infoLabels={u'trailer' : trailer})
		
	def SetAried(self, aired):
		self.item.setInfo(type=u'video', infoLabels={u'aired' : aired})
	
	def SetDate(self, date):
		self.item.setInfo(type=u'video', infoLabels={u'date' : date})
		
	def SetRating(self, rating):
		self.item.setInfo(type=u'video', infoLabels={u'rating' : rating})
	
	def SetYear(self, year):
		self.item.setInfo(type=u'video', infoLabels={u'year' : year})
	
	def SetGenre(self, genre):
		self.item.setInfo(type=u'video', infoLabels={u'genre' : genre})
		
	def SetPlot(self, plot):
		self.item.setInfo(type=u'video', infoLabels={u'plot' : plot})
	
	def SetTracknumber(self, tracknumber):
		self.item.setInfo(type=u'video', infoLabels={u'tracknumber' : tracknumber})
		
	def SetResumeTime(self, time):
		self.item.setProperty(u'ResumeTime', time)
		#self.item.setProperty(u'StartOffset', time)
	
	def GetResumeTime(self):
		return self.item.getProperty(u'StartOffset')	
		
	def GetTotalTime(self):
		return self.item.getProperty(u'TotalTime')
	
		