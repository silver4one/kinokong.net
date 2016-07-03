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
import os, time
import sqlite3

def to_lower(string):
	return string.lower()
	
class AbstractBase(object):
	def __init__(self, filename, max_item_count=1000, max_file_size_kb=-1):
		self._filename = filename
		if not self._filename.endswith('.sqlite'):
			self._filename += '.sqlite'
			pass
		#self._table_name = None
		self._file = None
		self._cursor = None
		self._max_item_count = max_item_count
		self._max_file_size_kb = max_file_size_kb

		self._table_created = False
		self._needs_commit = False
		pass

	def set_max_item_count(self, max_item_count):
		self._max_item_count = max_item_count
		pass

	def set_max_file_size_kb(self, max_file_size_kb):
		self._max_file_size_kb = max_file_size_kb
		pass

	def __del__(self):
		self.close()
		pass

	def open(self):
		if self._file is None:
			#self._optimize_file_size()
			path = os.path.dirname(self._filename)
			try:
				if not os.path.exists(path):
					os.makedirs(path)
					pass
			except:
				pass

			self._file = sqlite3.connect(self._filename, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES, timeout=1)
			self._file.create_function("lower", 1, to_lower)
			self._file.isolation_level = None
			self._cursor = self._file.cursor()
			
			for tries in range(10):
				try:
					self._cursor.execute('PRAGMA journal_mode=MEMORY')
				except:
					time.sleep(10)
			#self._cursor.execute('PRAGMA synchronous=OFF')
		pass

	def _execute(self, needs_commit, query, values=[]):
		if not self._needs_commit and needs_commit:
			self._needs_commit = True
			self._cursor.execute('BEGIN')
			pass

		for tries in range(5):
			try:
				return self._cursor.execute(query, values)
			except:
				time.sleep(2)
				pass
		else:
			return self._cursor.execute(query, values)

	def close(self, commit=True):
		if self._file is not None:
			if commit:
				#self._cursor.execute('COMMIT TRANSACTION')
				for tries in range(10):
					try:
						self._file.commit()
					except:
						time.sleep(10)

			self._cursor.close()
			self._cursor = None
			self._file.close()
			self._file = None
			pass
		pass

	def _optimize_file_size(self):
		# do nothing - only we have given a size
		if self._max_file_size_kb <= 0:
			return

		# do nothing - only if this folder exists
		path = os.path.dirname(self._filename)
		if not os.path.exists(path):
			return

		if not os.path.exists(self._filename):
			return

		file_size_kb = os.path.getsize(self._filename) / 1024
		if file_size_kb >= self._max_file_size_kb:
			os.remove(self._filename)
			pass
		pass

	def create_table(self, table_name):
		pass

	def sync(self):
		if self._file is not None and self._needs_commit:
			self._needs_commit = False
			for tries in range(2):
				try:
					return self._file.commit()
				except:
					time.sleep(5)
						
			#return self._file.commit()
		pass

	def _set(self, item_id, item):
		pass

	def _optimize_item_count(self):
		pass

	def clear(self, table_name):
		self._open()
		query = 'DELETE FROM %s' % table_name
		self._execute(True, query)
		self.create_table(table_name)
		pass

	def _is_empty(self):
		return False

	def _is_empty_id(self, item_id):
		return False

	def remove(self, table_name, item_id):
		self._open()
		query = 'DELETE FROM %s WHERE key = ?' % table_name
		self._execute(True, query, [item_id])
		pass

	pass