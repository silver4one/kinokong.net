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
from AbstractBase import AbstractBase
import re, hashlib, codecs, os, urllib
import Utils

from BeautifulSoup import BeautifulSoup
import demjson3 as json

import xbmc

MOVIES_TABLE 		= u'movies'
TVSHOW_TABLE		= u'tv_show'
TVSETS_TABLE		= u'tv_sets'
MULT_TABLE			= u'mult'
ALL_TABLE			= (MOVIES_TABLE, TVSHOW_TABLE, TVSETS_TABLE, MULT_TABLE)
BOOKMARK_TABLE		= u'bookmark'
LISTPLFILE_TABLE	= u'list_plfile'

__cookies__    		= os.path.join(xbmc.translatePath("special://profile/").decode('utf-8'), '..', 'addons', 'service.kinokong.update', 'resources', 'data', 'cookies.txt')
		
class KinokongBase(AbstractBase):
	def __init__(self, filename):
		AbstractBase.__init__(self, filename)
		self._cr_table = []
		pass

	def create_table(self):
		self.open()

		self.createInfoTable(MOVIES_TABLE)
		self.createInfoTable(TVSHOW_TABLE)
		self.createInfoTable(TVSETS_TABLE)
		self.createInfoTable(MULT_TABLE)
		self.create_list_plfikle_table()
		self.create_bookmark_table()
		self.create_view()
		self.create_view_bookmark
		pass
		
	def create_bookmark_table(self):
		query = u'CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY AUTOINCREMENT, bookmark VARCHAR (64), type INTEGER (1));' %BOOKMARK_TABLE
		self._execute(True, query)
		
	def create_list_plfikle_table(self):
		query = u'CREATE TABLE IF NOT EXISTS %s (hash VARCHAR (64), file VARCHAR (1000));' %LISTPLFILE_TABLE
		self._execute(True, query)
		
	def createInfoTable(self, tableName):
		query = u'CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR (1000), \
				url VARCHAR (255), content TEXT, rate VARCHAR (10), year INTEGER (4), director TEXT, \
				duration VARCHAR (20), genre VARCHAR (500), quality TEXT, sound TEXT, trailer VARCHAR (512), country TEXT, pl_list BOOLEAN, \
				imgt VARCHAR (512), img VARCHAR (512), hash VARCHAR (64) UNIQUE, kpid VARCHAR (50), date DATETIME);' %tableName
		self._execute(True, query)

	def create_view(self):
		query = u'CREATE VIEW IF NOT EXISTS "view" AS SELECT movies.name AS Name, movies.year AS Year, files.type AS Type, files.file AS File, files.hash AS Hash FROM movies LEFT JOIN files ON files.hash = movies.hash;' #WHERE movies.year>2000;
		self._execute(True, query)
		pass

	def create_view_bookmark(self):
		query = u'''CREATE VIEW IF NOT EXISTS "view_bookmark" AS
					SELECT movies.*, bookmark.type FROM movies LEFT JOIN bookmark ON bookmark = movies.hash WHERE hash in(SELECT bookmark from bookmark)
					UNION ALL
					SELECT tv_sets.*, bookmark.type FROM tv_sets LEFT JOIN bookmark ON bookmark = tv_sets.hash WHERE hash in(SELECT bookmark from bookmark)
					UNION ALL
					SELECT tv_show.*, bookmark.type FROM tv_show LEFT JOIN bookmark ON bookmark = tv_show.hash WHERE hash in(SELECT bookmark from bookmark)'''
		self._execute(True, query)
		pass
				
	def setBookmarks(self, id):
		if not self._cursor is None:
			if self.is_select_bookmark(id):
				type = 1
				if not self._is_empty_id(TVSETS_TABLE, id):
					type = 2
				elif not self._is_empty_id(TVSHOW_TABLE, id):
					type = 3
				query = u"INSERT INTO %s (id,bookmark,type) VALUES(NULL,?,?)" %(BOOKMARK_TABLE)
				self._execute(False, query, [id, type])
			
	def delBookmark(self, id):
		if not self._cursor is None:
			query = u"DELETE FROM %s WHERE bookmark='%s'" %(BOOKMARK_TABLE, id)
			self._execute(False, query)
		
	def is_select_bookmark(self, id):
		if not self._cursor is None:
			return bool(self.select(BOOKMARK_TABLE, u'bookmark', id))
		
	def getMovieInfoByID(self, id):
		if not self._cursor is None:
			for table in ALL_TABLE:
				if not self._is_empty_id(table, id):
					return self.select_all(table, u'hash', id)[0]
		return None
				
	def _insert_in_table(self, TABLE, values=[]):
		if not self._cursor is None:
			query = u'INSERT INTO %s (id,name,url,content,rate,year,director,duration,genre,quality,sound,trailer,country,pl_list,imgt,img,hash,kpid,date) VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)' % TABLE
			try:
				self._execute(False, query, values)
			except:
				pass

	def _update_in_table(self, TABLE, hash, values=[]):
		if not self._cursor is None:
			query = u'UPDATE %s SET url=?, name=?, content=?, rate=?, year=?, director=?, duration=?, genre=?, quality=?, sound=?, trailer=?, country=?, pl_list=?, imgt=?, img=?, kpid=?, date=? WHERE hash=\'%s\'' %(TABLE, hash)
			try:
				self._execute(False, query, values)
			except:
				pass

	def insert_plfile(self, hash, values=[]):
		if not self._cursor is None:
			if not self.select(LISTPLFILE_TABLE, u'hash', hash):
				query = u'UPDATE %s SET file=? WHERE hash=?;' %(LISTPLFILE_TABLE)
				self._execute(False, query, [values[1], hash])
				return
			query = u'INSERT INTO %s (hash,file) VALUES(?,?);' %(LISTPLFILE_TABLE)
			try:
				self._execute(False, query, values)
			except:
				pass
	
	def select(self, table_name, key, value):
		if not self._cursor is None:
			query = u"SELECT * FROM %s WHERE %s='%s'" %(table_name, key, value)
			try:
				self._execute(True, query)
				return not self._cursor.fetchall()
			except:
				return True

	def select_all(self, table_name, key, value):
		if not self._cursor is None:
			query = u"SELECT * FROM %s WHERE %s='%s'" %(table_name, key, value)
			try:
				self._execute(True, query)
				return self._cursor.fetchall()
			except:
				return None

	def get_page(self, sql, page):
		if not self._cursor is None:
			query = u"%s LIMIT 30 OFFSET 30*%s" %(sql, page)
			try:
				self._execute(True, query)
				return self._cursor.fetchall()
			except:
				return None
	
	def get_pages(self, sql):
		if not self._cursor is None:
			sql = sql.replace(u'*', u'COUNT(*)')
			try:
				self._execute(True, sql)
				return int(round(self._cursor.fetchall()[0][0]/30.0))
			except:
				return 1
			
	def to_hash(self, url):
		return hashlib.md5(url.encode('utf-8')).hexdigest()
		
	def _quote_id(self, s, errors=u"strict"):
		encodable = s.encode("utf-8", errors).decode(u"utf-8")

		nul_index = encodable.find(u"\x00")

		if nul_index >= 0:
			error = UnicodeEncodeError(u"NUL-terminated utf-8", encodable,
									   nul_index, nul_index + 1, u"NUL not allowed")
			error_handler = codecs.lookup_error(errors)
			replacement, _ = error_handler(error)
			encodable = encodable.replace(u"\x00", replacement)

		return u"\"" + encodable.replace(u"\"", u"\"\"") + u"\""

	def _normalise_year(self, year):
		if len(year) > 4:
			match = re.search("^[0-9]{4}-([0-9]{4})$", year)
			try:
				return match.group(1)
			except:
				pass
		return year

	def _get_genre(self, arr_genre):
		genre = ""
		for g in arr_genre:
			if not re.search(u"[0-9]{4}", g):
				genre = genre + g + " "
		return genre[0:-1]

	def movies_update(self, info_array=[]):
		self._update(MOVIES_TABLE, info_array)

	def tvshows_update(self, info_array=[]):
		self._update(TVSHOW_TABLE, info_array)

	def tvsets_update(self, info_array=[]):
		self._update(TVSETS_TABLE, info_array)

	def mult_update(self, info_array=[]):
		self._update(MULT_TABLE, info_array)

	def _update(self, TABLE, info_array=[]):
		if not self._cursor is None:
			if len(info_array) == 0:
				return

		for row in info_array:
			dt = Utils.FormatDate(row.adata)

			try:
				_year = int(self._normalise_year(row.year).strip())
			except:
				_year = 0

			genre = self._get_genre(row.genre)

			try:
				hash = self.to_hash(re.search(ur'(^http:\/\/*.+\/(?P<id>[0-9]+)-)', row.url).group('id'))
			except:
				hash = self.to_hash(row.url)

			if self._is_empty_id(TABLE, hash):
				self._insert_in_table(TABLE, [row.title, row.url, row.text, row.rating, _year, row.director, row.duration, genre, row.rip, row.sound, row.trailer, row.country, row.pl, row.imgt, row.img, hash, row.kpid, dt])
			else:
				self._update_in_table(TABLE, hash, [row.url, row.title, row.text, row.rating, _year, row.director, row.duration, genre, row.rip, row.sound, row.trailer, row.country, row.pl, row.imgt, row.img, row.kpid, dt])
			
			if row.pl == 1:
				self.insert_plfile(hash, [hash, row.plfile])
		
	def _delete_movie(self, id):
		if not self._cursor is None:
			query = u"DELETE FROM %s WHERE hash='%s'" %(MOVIES_TABLE, id)
			self._execute(False, query)
			
	def _delete_files(self, id):
		if not self._cursor is None:
			query = u"DELETE FROM %s WHERE hash='%s'" %(FILES_TABLE, id)
			self._execute(False, query)
			
	def _get_video_file(self, id):	
		values = self.select_all(MOVIES_TABLE, u'hash', id)
		if not values:
			values = self.select_all(TVSHOW_TABLE, u'hash', id)
		if not values:
			values = self.select_all(TVSETS_TABLE, u'hash', id)
		if not values:
			values = self.select_all(MULT_TABLE, u'hash', id)
		if values:
			values = values[0]
			html = Utils.get_HTML(values[2], __cookies__)
			soup = BeautifulSoup(html, fromEncoding="windows-1251")
			
			if re.search(ur'flashvars', soup.find('div', {'class': "box visible"}).text):
				for p in re.compile('var flashvars = {(.+?)}', re.MULTILINE | re.DOTALL).findall(
						soup.find('div', {'class': "box visible"}).text.replace(' ', ' ')):
					
					for v in re.findall('(http:.*?)[\"\',]+', p):
						if re.search('(.txt)', v):
							continue
						video = v
						se = re.search('\_([0-9]\S+)\.', video)
					
			return {'hash' : values[16], 'file' : video, 'name' : values[1]}
		return {'hash' : '', 'file' : '', 'name' : ''}
	
	def _get_movie_file2(self, id):
		if not self._cursor is None:
			query = u"SELECT * FROM files WHERE hash='%s' ORDER BY type DESC LIMIT 1" %id
			self._execute(True, query)
			return self._cursor.fetchall()

	def _get_files(self, id):
		if not self._cursor is None:
			query = u"SELECT file FROM list_plfile WHERE hash='%s'" %id
			self._execute(True, query)
			values = self._cursor.fetchall()
			if values:
				values = values[0]
				
				plh = Utils.get_HTML(values[0], __cookies__)
				pl = json.loads(plh.decode('utf-8'))
				list = []
				x = 0
				for rec in pl['playlist']:
					
					if 'playlist' in rec:
						for rec1 in rec['playlist']:
							x += 1
							lname = (rec['comment'] + ' - ' + rec1['comment']).replace('<b>', '').replace('</b>', '')
							lname = lname.replace('<br>', ' ').replace('</br>', ' ')
							list.append({'name': lname, 'url': Utils.normalizeFile(rec1['file']), 'id': x, 'fileid':id})
					else:
						x += 1
						lname = rec['comment'].replace('<b>', '').replace('</b>', '')
						lname = lname.replace('<br>', ' ').replace('</br>', ' ')
						list.append({'name': lname, 'url': Utils.normalizeFile(rec['file']), 'id': x, 'fileid':id})
						
				return list
		return False
			
	def _get_video_file2(self, id, video_id):
		if not self._cursor is None:
			query = u"SELECT file FROM list_plfile WHERE hash='%s'" %id
			self._execute(True, query)
			values = self._cursor.fetchall()
			if values:
				values = values[0]
				
				plh = Utils.get_HTML(values[0], __cookies__)
				pl = json.loads(plh.decode('utf-8'))
				list = []
				x = 0
				for rec in pl['playlist']:
					x += 1
					if 'playlist' in rec:
						for rec1 in rec['playlist']:
							lname = (rec['comment'] + ' - ' + rec1['comment']).replace('<b>', '').replace('</b>', '')
							lname = lname.replace('<br>', ' ').replace('</br>', ' ')
							
							list.append({'name': lname, 'url': Utils.normalizeFile(rec1['file']), 'id': x, 'fileid':id})
					else:
						lname = rec['comment'].replace('<b>', '').replace('</b>', '')
						lname = lname.replace('<br>', ' ').replace('</br>', ' ')
						
						list.append({'name': lname, 'url': Utils.normalizeFile(rec['file']), 'id': x, 'fileid':id})
	
				return list[int(video_id)-1]
		return 0
			
	def _get_tvshow_file(self, id, file_id):
		if not self._cursor is None:
			query = u"SELECT * FROM %s WHERE hash='%s' AND uniq='%s'" %(FILES_TABLE, id, file_id)
			try:
				self._execute(True, query)
				values = self._cursor.fetchall()[0]
				if len(values) >= 5:
					return {'hash' : values[0], 'file' : values[1], 'name' : values[2], 'type' : values[3], 'file_id' : values[4]}
			except:
				pass
		return {'hash':'', 'file':'', 'name':'', 'type':'', 'file_id':''}
		
	def _get_tvshow_file2(self, file_id):
		if not self._cursor is None:
			query = u"SELECT * FROM %s WHERE uniq='%s'" %(FILES_TABLE, file_id)
			try:
				self._execute(True, query)
				values = self._cursor.fetchall()[0]
				if len(values) >= 5:
					return {'hash' : values[0], 'file' : values[1], 'name' : values[2], 'type' : values[3], 'file_id' : values[4]}
			except:
				pass
		return {'hash':'', 'file':'', 'name':'', 'type':'', 'file_id':''}
		
	def get_last_update(self, table):
		try:
			query = u'SELECT date FROM %s ORDER BY date DESC LIMIT 1' %table
			self._execute(False, query)
			return Utils.FormatDate(self._cursor.fetchall()[0][0])
		except:
			return Utils.FormatDate('2000-01-01 00:00:00')
		
	def get_last_update_movies(self):
		return self.get_last_update(MOVIES_TABLE)
	
	def get_last_update_tvsets(self):
		return self.get_last_update(TVSETS_TABLE)
	
	def get_last_update_tvshows(self):
		return self.get_last_update(TVSHOW_TABLE)

	def get_last_update_mult(self):
		return self.get_last_update(MULT_TABLE)

	def _get_search_pages(self, search, tables):
		if not self._cursor is None:
			search = self._search_in_text(search)
			if tables[0] == u'ALL_TABLE':
				tables = ALL_TABLE
				
			count = u'SELECT COUNT(*) FROM (%s)' %self._get_search_query(search, tables)
			self._execute(True, count)
			return int(round(self._cursor.fetchall()[0][0]/30.0))
			
	def _get_search_query(self, search, tables):
		query = ''
		i = 0
		for table in tables:
			q = u"SELECT * FROM %s WHERE lower(name) LIKE '%%%s%%'" %(table, search)
			i += 1
			if i != len(tables):
				q = q + u' UNION ALL '
			query += q
			
		return query
	
	def _search_in_text(self, search):
		_search = re.sub(u'([^A-zА-я0-9 ]|[\^])', u'', search)
		if search == u'':
			return u''
		if _search != u'':
			search = search
		return search
				
	def _get_search_page(self, search, page, tables):
		if not self._cursor is None:
			search = self._search_in_text(search)
			if tables[0] == u'ALL_TABLE':
				tables = ALL_TABLE
				
			query = u"SELECT * FROM (%s) ORDER BY date DESC LIMIT 30 OFFSET 30*%s" %(self._get_search_query(search, tables), page)
			try:
				self._execute(True, query)
				return self._cursor.fetchall()
			except:
				return None

	def _get_by_date(self, date):
		return self.select(MOVIES_TABLE, u'date', date)

	def _get_by_url(self, url):
		return self.select(MOVIES_TABLE, u'url', url)
		
	def _set(self, item_id, item):
		pass

	def _optimize_item_count(self):
		pass

	def _is_empty(self):
		return False
		
	def _is_empty_id(self, table_name, item_id):
		return bool(self.select(table_name, u'hash', item_id))

	def _get_ids(self, oldest_first=True):
		pass

	def _get(self, item_id):
		pass