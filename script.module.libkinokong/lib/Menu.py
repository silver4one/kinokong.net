# coding=utf-8
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
import re, os, json
from datetime import timedelta
from datetime import datetime

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

default_cache_file = u'~menu.cache'

class Menu(object):
	def __init__(self, filename, tables, cache_filename=default_cache_file):
	
		self._cache_file 	= cache_filename
		self._filename 		= filename
		self._tables        = tables

		if not self._cache_file.endswith('.cache'):
			self._cache_file += '.cache'
			pass
			
		if not self._filename.endswith('.mn'):
			self._filename += '.mn'
			pass
			
		if self._is_new_menu_file():
			self._menu = self._load_from_cache()
			if len(self._menu) == 0:
				self._menu = self.ParseBuffer(self._open_menu())
				self._save_cache()
		else:
			self._menu = self.ParseBuffer(self._open_menu())
			self._save_cache()

	def GetMenu(self):
		return self._menu

	def ParseBuffer(self, text_buffer):
		var = []
		stage = 1
		pos = self._get_menu_position(text_buffer)
		while pos > 0:
			pos = self._recursion_parse(text_buffer, pos, stage, var)

			pos = pos + 1
		return var

	def _find_date(self, line):
		date = re.search(u'(D\[(>=|=|<=|!|<|>)?(([0-9]{4}-[0-9]{2}-[0-9]{2})\]|([0-9]{1,2}M\])))', line)
		if date:
			return date.group(1)

	def _find_year(self, line):
		year = re.search(u'(Y\[(>=|=|<=|!|<|>)?([0-9]{4})\])', line)
		if year:
			return year.group(0)

	def _find_genre(self, line):
		genre = re.search(ur'(?P<G>G\[(?P<genre>[A-Za-zА-Яа-я]+)\])', line)
		if genre:
			return genre.group('G')

	def _find_table(self, line):
		genre = re.search(ur'((\]|^)(?P<T>T\[(?P<table>[A-Z_]+)\]))', line)
		if genre:
			return genre.group('T')
	
	def _find_table_find(self, line):
		genre = re.search(u'(?P<F>FIND\[(?P<table>[A-Z_]+)\])', line)
		if genre:
			return genre.group('F')
		
	def _find_table_bookmark(self, line):
		genre = re.search(ur'((\]|^)?(?P<B>BOOKMARK\[(?P<table>[A-Z_]+)(?P<type>[1-9])\]))', line)
		if genre:
			return genre.group('B')		

	def _find_type_bookmark(self, line):
		genre = re.search(ur'(?P<B>(\]|^)?BOOKMARK\[(?P<table>[A-Z_]+)(?P<type>[1-9])\])', line)
		if genre:
			return genre.group('B')

	def _find_sort(self, line):
		sort = re.search(u'(?P<SORT>SORT\[(?P<cv>[DATE|YEAR|RATE]+)\])', line)
		if sort:
			return sort.group('SORT')

	def _get_type_attribute(self, line):
		_type = ''
		if re.search(u'(?P<D>D\[(?P<cv>=|<|>|<=|>=|!)?([0-9]{4}-[0-9]{2}-[0-9]{2}\])|([0-9]{1,2}M))', line):
			_type = _type + 'D'
		if re.search(u'(?P<Y>Y\[(?P<cv>=|<|>|<=|>=|!)?[0-9]{4}\])', line):
			_type = _type + 'Y'
		if re.search(u'(?P<G>G\[[A-Za-zА-Яа-я]+\])', line):
			_type = _type + 'G'
		if re.search(u'(?P<T>T\[[A-Z_]+\])', line):
			_type = _type + 'T'
		if re.search(u'(?P<SORT>SORT\[(?P<cv>[DATE|YEAR|RATE]+)\])', line):
			_type = _type + 'S'
		if re.search(u'(?P<B>(\]|^)?BOOKMARK\[(?P<table>[A-Z_]+)(?P<type>[1-9])\])', line):
			_type = _type + 'B'
		if re.search(u'(?P<F>FIND\[(?P<table>[A-Z_]+)\])', line):
			_type = _type + 'F'
		return _type

	def _find_comment(self, line):
		comment = re.search(ur'(?P<csep>#)(?P<comment>.*)?$', line)
		if comment:
			return comment.group('csep'), comment.group('comment')

	def _get_menu_name(self, line):
		menu_name = re.search('^\[(?P<name>[]A-Za-z0-9А-Яа-я]+)\]\s*', line)
		if menu_name:
			return menu_name.group('name')

	def _is_spec_symbol(self, line):
		if re.search(ur'(#.*[\r\n]+)', line) or re.search(ur'(^[\r\n|\n]+)', line):
			return True
		return False

	def _remove_comment(self, line):
		comment = re.search(ur'(?P<csep>#)(?P<comment>.*)(?P<end>[\r\n]?)?$', line)
		if comment:
			return line[:comment.start()] + comment.group('end')
		return line

	def _get_menu_position(self, text, start=0):
		pos = 0
		for line in text:
			if pos < start:
				pos = pos + 1
				continue

			if self._is_spec_symbol(line):
				pos = pos + 1
				continue

			if self._get_menu_name(line):
				return pos
			pos = pos + 1
			continue

	def _get_element_name(self, line, stage):
		for i in range(stage):
			element = re.search(ur'^\t{%i}(?P<name>[A-Za-zА-Яа-я0-9]+)$' % int(stage), line.rstrip())
			if element:
				return element.group('name')
			return None
		return None

	def _get_URI(self, line):
		uri = re.search(ur'@(?P<name>([A-Za-zА-Яа-я]+)([0-9]+)?)(\((?P<pg>[0-9]+)\))?$', line.rstrip())
		if uri:
			return uri.group('name'), uri.group('pg')
		return None

	def _is_URI(self, line):
		uri = re.search(ur'@(?P<name>([A-Za-zА-Яа-я]+)([0-9]+)?)(\((?P<pg>[0-9]+)\))?$', line.rstrip())
		if uri:
			return True
		return False

	def _find_element(self, text, start):
		pos = 0
		for line in text:
			if pos < start:
				pos = pos + 1
				continue

			if self._is_spec_symbol(line):
				pos = pos + 1
				continue

			if re.search(ur'(?P<name>^\t+[A-Za-zА-Яа-я0-9]+)$', line.rstrip()):
				return pos

			if pos > start and self._get_menu_name(line):
				break

			pos = pos + 1
		return -2

	def _recursion_parse(self, text, pos, stage, var, y=0):
		pos = self._find_element(text, pos)
		uri = None

		if self._is_URI(text[pos - 1]):
			uri = self._get_URI(text[pos - 1])

		if pos < 0:
			return pos
		el_name = self._get_element_name(text[pos], stage)
		x = 0
		if el_name is None:
			if len(var) > 1:
				x = len(var) - 1 - y
			pos = self._recursion_parse(text, pos, stage + 1, var[x + (stage - 1)], y + 1)
		elif uri is not None:
			pages = 1
			if not uri[1] is None:
				pages = uri[1]
			add = {'URI': uri[0], 'pages' : pages}
			_type = self._get_type_attribute(text[pos + 1])
			if _type is not None:
				q = self._get_query(text[pos + 1], _type)
				if not q is 'None' and not q is None:
					q = q.decode('utf8').encode('utf-8').encode('base64').replace('\n', '')
				add = {'URI': uri[0], 'pages' : pages, 'query': q}

			var.append([el_name, add])
		else:
			var.append([el_name])

		return pos

	def _get_query(self, line, _type):
		D = ''
		Y = ''
		G = ''
		S = ''
		T = ''

		for i in range(len(_type)):
			if _type[i] == 'D':
				D = self._find_date(line)
			if _type[i] == 'Y':
				Y = self._find_year(line)
			if _type[i] == 'G':
				G = self._find_genre(line)
			if _type[i] == 'S':
				S = self._find_sort(line)
			if _type[i] == 'T':
				T = self._find_table(line)
				if T is None:
					return None
			if _type[i] == 'B':
				T = self._find_table_bookmark(line)
			if _type[i] == 'F':
				T = self._find_table_find(line)

		if not T:
			return 'None'

		if len(_type):
			return D+Y+G+S+T
			
	def _date_to_SQL(self, date_array):
		date = re.search(u'(D\[(?P<spec>>=|=|<=|!|<|>)?(?P<full>([0-9]{4}-[0-9]{2}-[0-9]{2})|(?P<sm>[0-9]{1,2})M)\])', date_array)
		if date:
			if date.group('sm'):
				__days = int(date.group('sm')) * 30
				__date = (datetime.today() - timedelta(days=__days)).date()
			else:
				__date = date.group('full')
				
			spec = date.group('spec')
			if spec == u'!':
				spec = u'<>'
			if spec is None:
				spec = u'='
			sql = u"date%s'%s'" % (spec, __date)
			return sql
		return u''

	def _year_to_SQL(self, year_array):
		__year = re.search(u'(Y\[(?P<spec>>=|=|<=|!|<|>)?(?P<year>[0-9]{4})\])', year_array)
		if __year:
			spec = __year.group('spec')
			if spec == u'!':
				spec = u'<>'
			if spec is None:
				spec = u'='
			sql = u"year%s'%s'" % (spec, __year.group('year'))
			return sql
		return u''
		
	def _genre_to_SQL(self, genre):
		__genre = re.search(ur'(?P<G>G\[(?P<genre>[А-Яа-я]+)\])', genre)
		if __genre:
			sql = u"genre LIKE '%%%s%%'" % __genre.group('genre')
			return sql
		return u''

	def _table_to_SQL(self, table):
		__table = re.search(ur'((\]|^)(?P<T>T\[(?P<table>[A-Z_]+)\]))', table)
		if __table:
			table = __table.group('table')
			if table in self._tables:
				sql = u"FROM %s" % self._tables[table]
				return sql
		else:
			return self._bookmark_to_SQL(table)
		return u''
		
	def _table_to_search(self, table):
		__table = re.search(ur'((\]|^)(?P<T>FIND\[(?P<table>[A-Z_]+)\]))', table)
		if __table:
			table = __table.group('table')
			if table == u'ALL_TABLE':
				return u'ALL_TABLE'
			if table in self._tables:
				return self._tables[table]
		
	def _bookmark_to_SQL(self, table):
		__table = re.search(ur'([\]|^]?(?P<B>BOOKMARK\[(?P<table>[A-Z_]+)(?P<type>[1-9])\]))', table)
		if __table:
			table = __table.group('table')
			if table in self._tables:
				sql = u"FROM %s WHERE type=\'%s\'" %(self._tables[table], __table.group('type'))
				return sql
		return u''
		
	def _sort_to_SQL(self, sort):
		__sort = re.search(ur'(?P<SORT>SORT\[(?P<cv>[DATE|YEAR|RATE]+)\])', sort)
		if __sort:
			sort = __sort.group('cv')
			if sort == u'DATE':
				return u"ORDER BY date DESC"
			if sort == u'YEAR':
				return u"ORDER BY year DESC"
			if sort == u'RATE':
				return u"ORDER BY rate DESC"
		return u''
		
	def _get_query2(self, line, _type):
		query = u"SELECT * %s %s%s"
		qr = ''

		line = line.decode('utf-8')

		D = self._date_to_SQL(line)
		Y = self._year_to_SQL(line)
		G = self._genre_to_SQL(line)
		S = self._sort_to_SQL(line)
		T = self._table_to_SQL(line)
		F = self._table_to_search(line)
		
		if F:
			return F
		if not T:
			return 'None'

		if D:
			qr = u"WHERE " + D
		if Y:
			qr = u"WHERE " + Y
			if D:
				qr = u"WHERE " + D + u" AND " + Y
		if G:
			qr = u"WHERE " + G
			if D:
				qr = u"WHERE " + D + u" AND " + G
				if Y:
					qr = u"WHERE " + D + u" AND " + Y + u" AND " + G
			elif Y:
				qr = u"WHERE " + Y + u" AND " + G
		if S:
			S = u" " + S

		if len(_type):
			return query % (T, qr, S)
			
	def _open_menu(self):
		text_buffer = []
		try:
			hfile = open(self._filename, 'r+', 1)

			for ln in hfile:
				text_buffer.append(self._remove_comment(ln.decode('utf-8')))
			hfile.close()
		except:
			pass
		return text_buffer

	def _is_new_menu_file(self):
		time = os.path.getmtime(self._filename)
		cache = []
		try:
			hfile = open(self._cache_file, 'r+', 1)

			for ln in hfile:
				cache.append(ln.decode('utf-8'))

			hfile.close()
				
			if int(time) > int(cache[0][0:10]):
				return False
		except:
			return False
		return True
		
	def query_to_SQL(self, query):
		__type_query = self._get_type_attribute(query.decode('base64'))
		if __type_query is not None:
			sql = self._get_query2(query.decode('base64'), __type_query)
				
		return sql
		
	def _load_from_cache(self):
		cache = []
		hfile = open(self._cache_file, 'r+', 1)

		for ln in hfile:
			cache.append(ln)
		hfile.close()

		return json.loads(cache[1])

	def _save_cache(self):
		time = os.path.getmtime(self._filename)
		hfile = open(self._cache_file, 'w+', 1)
		hfile.write(str(time)+u'\n')
		hfile.write(json.dumps(self._menu))
		hfile.close()
