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
import re, random

from BeautifulSoup  import BeautifulSoup
import Utils

URI = u'http://www.kinopoisk.ru/index.php?level=7&from=forma&result=adv&m_act[from]=forma&m_act[what]=content&m_act[find]=%s&m_act[year]=%s'
URI4 = u'http://www.kinopoisk.ru/index.php?level=7&from=forma&result=adv&m_act[from]=forma&m_act[what]=content&m_act[find]=%s&m_act[from_year]=%s&m_act[to_year]=%s'


URI_ID = u'http://www.kinopoisk.ru/film/%s/'


class Kinopoisk(object):
	MAXGENPRIMEINDEX = 20
	MINGENPRIMTINDEX = 5

	HASH_COUNT = 84
	SUPERGROUPS = 6
	SUPER_SIZE = HASH_COUNT / SUPERGROUPS

	def __init__(self, cookie_file):
		self.cookies = cookie_file

	def __gen_prime(self, index):
		D = {}
		q = 2
		gen_index = 0
		while True:
			if q not in D:
				gen_index += 1
				if gen_index == index:
					return q
				D[q * q] = [q]
			else:
				for p in D[q]:
					D.setdefault(p + q, []).append(p)
				del D[q]
			q += 1
		
	def __canonize(self, source):
		stop_symbols = u'.,!?:;-\n\r)'
		stop_words = (u'я', u'восемь', u'это', u'как', u'так', u'и', u'в', u'над', u'к', u'до', u'не', u'на', u'но', u'за', u'то', u'с',
			u'ли', u'а', u'во', u'от', u'со', u'для', u'о', u'же', u'ну', u'вы', u'бы', u'что', u'кто', u'он', u'она', u'3D', u'3d')
		return ([x for x in [y.strip(stop_symbols).decode('UTF-8') for y in source.lower().split()] if x and (x not in stop_words)])

	def __gen_hash(self):
		prime = self.__gen_prime(random.randint(Kinopoisk.MINGENPRIMTINDEX, Kinopoisk.MAXGENPRIMEINDEX))
		base = random.randint(prime, 2*prime)
		return (base, prime)

	def __prepare_hashes(self, count):
		return [self.__gen_hash() for i in xrange(count)]

	def __calc_hash(self, shingle, func):
		s = ''.join(shingle)
		base, prime = func
		value = 0
		for i in xrange(len(s)):
			value += ord(s[i])*pow(base, i) % prime
		return value

	def __calc_shingles(self, text, size, hashes):
		matrix = []
		for i in xrange(len(text) - (size - 1)):
			shignle = [x for x in text[i:i + size]]
			matrix.append([self.__calc_hash(shignle, func) for func in hashes])
		transposed = map(list, zip(*matrix))
		return [min(transposed[i]) for i in xrange(Kinopoisk.HASH_COUNT)]
	
	def __compare_shingles(self, shingles1, shingles2):
		same = 0.0
		for h1, h2 in zip(shingles1, shingles2):
			if h1 == h2:
				same += 1.0
		return same / Kinopoisk.HASH_COUNT

	def __cmpString(self, str1, str2):
		str1 = re.compile(ur"[+| ]", re.IGNORECASE).sub(" " , str1)
		str2 = re.compile(ur"[+| ]", re.IGNORECASE).sub(" " , str2)
		HASH_COUNT = 84
		text1 = self.__canonize(str1)
		text2 = self.__canonize(str2)
		hashes = self.__prepare_hashes(HASH_COUNT)
		shingles1 = self.__calc_shingles(text1, 1, hashes)
		shingles2 = self.__calc_shingles(text2, 1, hashes)
		return self.__compare_shingles(shingles1, shingles2)*100

	def __clearString(self, string):
		return re.compile(ur"&[#]?[a-zA-Z0-9]+;", re.IGNORECASE).sub(u" ", string)

	def __remSymbol(self, string):
		string = re.sub(ur'ё', u'е', string)
		string = re.compile(ur"[,.:-=-'?!«»]+", re.IGNORECASE).sub(u" " , string)
		string = re.sub('\s+', ' ', string)
		return string.strip()

	def get_country_id(self, country):
		gn = country.strip()
		_search_country = ''
		if u'россия' == gn.lower():
			_search_country += '&m_act[country]=2'
		if u'сша' == gn.lower():
			_search_country += '&m_act[country]=1'
		if u'ссср' == gn.lower():
			_search_country += '&m_act[country]=13'
		if u'австралия' == gn.lower():
			_search_country += '&m_act[country]=25'
		if u'австрия' == gn.lower():
			_search_country += '&m_act[country]=57'
		if u'азербайджан' == gn.lower():
			_search_country += '&m_act[country]=136'
		if u'албания' == gn.lower():
			_search_country += '&m_act[country]=120'
		if u'алжир' == gn.lower():
			_search_country += '&m_act[country]=20'
		if u'американские виргинские острова' == gn.lower():
			_search_country += '&m_act[country]=1026'
		if u'американское самоа' == gn.lower():
			_search_country += '&m_act[country]=1062'
		if u'ангола' == gn.lower():
			_search_country += '&m_act[country]=139'
		if u'андорра' == gn.lower():
			_search_country += '&m_act[country]=159'
		if u'антарктида' == gn.lower():
			_search_country += '&m_act[country]=1044'
		if u'антигуа и барбуда' == gn.lower():
			_search_country += '&m_act[country]=1030'
		if u'антильские острова' == gn.lower():
			_search_country += '&m_act[country]=1009'
		if u'аргентина' == gn.lower():
			_search_country += '&m_act[country]=24'
		if u'армения' == gn.lower():
			_search_country += '&m_act[country]=89'
		if u'аруба' == gn.lower():
			_search_country += '&m_act[country]=175'
		if u'афганистан' == gn.lower():
			_search_country += '&m_act[country]=113'
		if u'багамы' == gn.lower():
			_search_country += '&m_act[country]=124'
		if u'бангладеш' == gn.lower():
			_search_country += '&m_act[country]=75'
		if u'барбадос' == gn.lower():
			_search_country += '&m_act[country]=105'
		if u'бахрейн' == gn.lower():
			_search_country += '&m_act[country]=164'
		if u'беларусь' == gn.lower():
			_search_country += '&m_act[country]=69'
		if u'белиз' == gn.lower():
			_search_country += '&m_act[country]=173'
		if u'бельгия' == gn.lower():
			_search_country += '&m_act[country]=41'
		if u'бенин' == gn.lower():
			_search_country += '&m_act[country]=140'
		if u'берег слоновой кости' == gn.lower():
			_search_country += '&m_act[country]=109'
		if u'бермуды' == gn.lower():
			_search_country += '&m_act[country]=1004'
		if u'бирма' == gn.lower():
			_search_country += '&m_act[country]=148'
		if u'болгария' == gn.lower():
			_search_country += '&m_act[country]=63'
		if u'боливия' == gn.lower():
			_search_country += '&m_act[country]=118'
		if u'босния' == gn.lower():
			_search_country += '&m_act[country]=178'
		if u'босния-герцеговина' == gn.lower():
			_search_country += '&m_act[country]=39'
		if u'ботсвана' == gn.lower():
			_search_country += '&m_act[country]=145'
		if u'бразилия' == gn.lower():
			_search_country += '&m_act[country]=10'
		if u'бруней-даруссалам' == gn.lower():
			_search_country += '&m_act[country]=1066'
		if u'буркина-фасо' == gn.lower():
			_search_country += '&m_act[country]=92'
		if u'бурунди' == gn.lower():
			_search_country += '&m_act[country]=162'
		if u'бутан' == gn.lower():
			_search_country += '&m_act[country]=114'
		if u'вануату' == gn.lower():
			_search_country += '&m_act[country]=1059'
		if u'великобритания' == gn.lower():
			_search_country += '&m_act[country]=11'
		if u'венгрия' == gn.lower():
			_search_country += '&m_act[country]=49'
		if u'венесуэла' == gn.lower():
			_search_country += '&m_act[country]=72'
		if u'внешние малые острова сша' == gn.lower():
			_search_country += '&m_act[country]=1064'
		if u'восточная сахара' == gn.lower():
			_search_country += '&m_act[country]=1043'
		if u'вьетнам' == gn.lower():
			_search_country += '&m_act[country]=52'
		if u'вьетнам северный' == gn.lower():
			_search_country += '&m_act[country]=170'
		if u'габон' == gn.lower():
			_search_country += '&m_act[country]=127'
		if u'гаити' == gn.lower():
			_search_country += '&m_act[country]=99'
		if u'гайана' == gn.lower():
			_search_country += '&m_act[country]=165'
		if u'гамбия' == gn.lower():
			_search_country += '&m_act[country]=1040'
		if u'гана' == gn.lower():
			_search_country += '&m_act[country]=144'
		if u'гваделупа' == gn.lower():
			_search_country += '&m_act[country]=142'
		if u'гватемала' == gn.lower():
			_search_country += '&m_act[country]=135'
		if u'гвинея' == gn.lower():
			_search_country += '&m_act[country]=129'
		if u'гвинея-бисау' == gn.lower():
			_search_country += '&m_act[country]=116'
		if u'германия' == gn.lower():
			_search_country += '&m_act[country]=3'
		if u'германия (гдр)' == gn.lower():
			_search_country += '&m_act[country]=60'
		if u'германия (фрг)' == gn.lower():
			_search_country += '&m_act[country]=18'
		if u'гибралтар' == gn.lower():
			_search_country += '&m_act[country]=1022'
		if u'гондурас' == gn.lower():
			_search_country += '&m_act[country]=112'
		if u'гонконг' == gn.lower():
			_search_country += '&m_act[country]=28'
		if u'гренада' == gn.lower():
			_search_country += '&m_act[country]=1060'
		if u'гренландия' == gn.lower():
			_search_country += '&m_act[country]=117'
		if u'греция' == gn.lower():
			_search_country += '&m_act[country]=55'
		if u'грузия' == gn.lower():
			_search_country += '&m_act[country]=61'
		if u'гуам' == gn.lower():
			_search_country += '&m_act[country]=1045'
		if u'дания' == gn.lower():
			_search_country += '&m_act[country]=4'
		if u'демократическая республика конго' == gn.lower():
			_search_country += '&m_act[country]=1037'
		if u'джибути' == gn.lower():
			_search_country += '&m_act[country]=1028'
		if u'доминика' == gn.lower():
			_search_country += '&m_act[country]=1031'
		if u'доминикана' == gn.lower():
			_search_country += '&m_act[country]=128'
		if u'египет' == gn.lower():
			_search_country += '&m_act[country]=101'
		if u'заир' == gn.lower():
			_search_country += '&m_act[country]=155'
		if u'замбия' == gn.lower():
			_search_country += '&m_act[country]=133'
		if u'зимбабве' == gn.lower():
			_search_country += '&m_act[country]=104'
		if u'израиль' == gn.lower():
			_search_country += '&m_act[country]=42'
		if u'индия' == gn.lower():
			_search_country += '&m_act[country]=29'
		if u'индонезия' == gn.lower():
			_search_country += '&m_act[country]=73'
		if u'иордания' == gn.lower():
			_search_country += '&m_act[country]=154'
		if u'ирак' == gn.lower():
			_search_country += '&m_act[country]=90'
		if u'иран' == gn.lower():
			_search_country += '&m_act[country]=48'
		if u'ирландия' == gn.lower():
			_search_country += '&m_act[country]=38'
		if u'исландия' == gn.lower():
			_search_country += '&m_act[country]=37'
		if u'испания' == gn.lower():
			_search_country += '&m_act[country]=15'
		if u'италия' == gn.lower():
			_search_country += '&m_act[country]=14'
		if u'йемен' == gn.lower():
			_search_country += '&m_act[country]=169'
		if u'кабо-верде' == gn.lower():
			_search_country += '&m_act[country]=146'
		if u'казахстан' == gn.lower():
			_search_country += '&m_act[country]=122'
		if u'каймановы острова' == gn.lower():
			_search_country += '&m_act[country]=1051'
		if u'камбоджа' == gn.lower():
			_search_country += '&m_act[country]=84'
		if u'камерун' == gn.lower():
			_search_country += '&m_act[country]=95'
		if u'канада' == gn.lower():
			_search_country += '&m_act[country]=6'
		if u'катар' == gn.lower():
			_search_country += '&m_act[country]=1002'
		if u'кения' == gn.lower():
			_search_country += '&m_act[country]=100'
		if u'кипр' == gn.lower():
			_search_country += '&m_act[country]=64'
		if u'кирибати' == gn.lower():
			_search_country += '&m_act[country]=1024'
		if u'китай' == gn.lower():
			_search_country += '&m_act[country]=31'
		if u'колумбия' == gn.lower():
			_search_country += '&m_act[country]=56'
		if u'коморы' == gn.lower():
			_search_country += '&m_act[country]=1058'
		if u'конго' == gn.lower():
			_search_country += '&m_act[country]=134'
		if u'конго (дрк)' == gn.lower():
			_search_country += '&m_act[country]=1014'
		if u'корея' == gn.lower():
			_search_country += '&m_act[country]=156'
		if u'корея северная' == gn.lower():
			_search_country += '&m_act[country]=137'
		if u'корея южная' == gn.lower():
			_search_country += '&m_act[country]=26'
		if u'косово' == gn.lower():
			_search_country += '&m_act[country]=1013'
		if u'коста-рика' == gn.lower():
			_search_country += '&m_act[country]=131'
		if u'куба' == gn.lower():
			_search_country += '&m_act[country]=76'
		if u'кувейт' == gn.lower():
			_search_country += '&m_act[country]=147'
		if u'кыргызстан' == gn.lower():
			_search_country += '&m_act[country]=86'
		if u'лаос' == gn.lower():
			_search_country += '&m_act[country]=149'
		if u'латвия' == gn.lower():
			_search_country += '&m_act[country]=54'
		if u'лесото' == gn.lower():
			_search_country += '&m_act[country]=1015'
		if u'либерия' == gn.lower():
			_search_country += '&m_act[country]=176'
		if u'ливан' == gn.lower():
			_search_country += '&m_act[country]=97'
		if u'ливия' == gn.lower():
			_search_country += '&m_act[country]=126'
		if u'литва' == gn.lower():
			_search_country += '&m_act[country]=123'
		if u'лихтенштейн' == gn.lower():
			_search_country += '&m_act[country]=125'
		if u'люксембург' == gn.lower():
			_search_country += '&m_act[country]=59'
		if u'маврикий' == gn.lower():
			_search_country += '&m_act[country]=115'
		if u'мавритания' == gn.lower():
			_search_country += '&m_act[country]=67'
		if u'мадагаскар' == gn.lower():
			_search_country += '&m_act[country]=150'
		if u'макао' == gn.lower():
			_search_country += '&m_act[country]=153'
		if u'македония' == gn.lower():
			_search_country += '&m_act[country]=80'
		if u'малави' == gn.lower():
			_search_country += '&m_act[country]=1025'
		if u'малайзия' == gn.lower():
			_search_country += '&m_act[country]=83'
		if u'мали' == gn.lower():
			_search_country += '&m_act[country]=151'
		if u'мальдивы' == gn.lower():
			_search_country += '&m_act[country]=1050'
		if u'мальта' == gn.lower():
			_search_country += '&m_act[country]=111'
		if u'марокко' == gn.lower():
			_search_country += '&m_act[country]=43'
		if u'мартиника' == gn.lower():
			_search_country += '&m_act[country]=102'
		if u'маршалловы острова' == gn.lower():
			_search_country += '&m_act[country]=1067'
		if u'масаи' == gn.lower():
			_search_country += '&m_act[country]=1042'
		if u'мексика' == gn.lower():
			_search_country += '&m_act[country]=17'
		if u'мелкие отдаленные острова сша' == gn.lower():
			_search_country += '&m_act[country]=1041'
		if u'мозамбик' == gn.lower():
			_search_country += '&m_act[country]=81'
		if u'молдова' == gn.lower():
			_search_country += '&m_act[country]=58'
		if u'монако' == gn.lower():
			_search_country += '&m_act[country]=22'
		if u'монголия' == gn.lower():
			_search_country += '&m_act[country]=132'
		if u'монтсеррат' == gn.lower():
			_search_country += '&m_act[country]=1065'
		if u'мьянма' == gn.lower():
			_search_country += '&m_act[country]=1034'
		if u'намибия' == gn.lower():
			_search_country += '&m_act[country]=91'
		if u'непал' == gn.lower():
			_search_country += '&m_act[country]=106'
		if u'нигер' == gn.lower():
			_search_country += '&m_act[country]=157'
		if u'нигерия' == gn.lower():
			_search_country += '&m_act[country]=110'
		if u'нидерланды' == gn.lower():
			_search_country += '&m_act[country]=12'
		if u'никарагуа' == gn.lower():
			_search_country += '&m_act[country]=138'
		if u'новая зеландия' == gn.lower():
			_search_country += '&m_act[country]=35'
		if u'новая каледония' == gn.lower():
			_search_country += '&m_act[country]=1006'
		if u'норвегия' == gn.lower():
			_search_country += '&m_act[country]=33'
		if u'оаэ' == gn.lower():
			_search_country += '&m_act[country]=119'
		if u'оккупированная палестинская территория' == gn.lower():
			_search_country += '&m_act[country]=1019'
		if u'оман' == gn.lower():
			_search_country += '&m_act[country]=1003'
		if u'остров мэн' == gn.lower():
			_search_country += '&m_act[country]=1052'
		if u'остров святой елены' == gn.lower():
			_search_country += '&m_act[country]=1047'
		if u'острова кука' == gn.lower():
			_search_country += '&m_act[country]=1063'
		if u'острова теркс и кайкос' == gn.lower():
			_search_country += '&m_act[country]=1007'
		if u'пакистан' == gn.lower():
			_search_country += '&m_act[country]=74'
		if u'палау' == gn.lower():
			_search_country += '&m_act[country]=1057'
		if u'палестина' == gn.lower():
			_search_country += '&m_act[country]=78'
		if u'панама' == gn.lower():
			_search_country += '&m_act[country]=107'
		if u'папуа - новая гвинея' == gn.lower():
			_search_country += '&m_act[country]=163'
		if u'парагвай' == gn.lower():
			_search_country += '&m_act[country]=143'
		if u'перу' == gn.lower():
			_search_country += '&m_act[country]=23'
		if u'польша' == gn.lower():
			_search_country += '&m_act[country]=32'
		if u'португалия' == gn.lower():
			_search_country += '&m_act[country]=36'
		if u'пуэрто рико' == gn.lower():
			_search_country += '&m_act[country]=82'
		if u'реюньон' == gn.lower():
			_search_country += '&m_act[country]=1036'
		if u'российская империя' == gn.lower():
			_search_country += '&m_act[country]=1033'
		if u'руанда' == gn.lower():
			_search_country += '&m_act[country]=103'
		if u'румыния' == gn.lower():
			_search_country += '&m_act[country]=46'
		if u'сальвадор' == gn.lower():
			_search_country += '&m_act[country]=121'
		if u'самоа' == gn.lower():
			_search_country += '&m_act[country]=1039'
		if u'сан-марино' == gn.lower():
			_search_country += '&m_act[country]=1011'
		if u'саудовская аравия' == gn.lower():
			_search_country += '&m_act[country]=158'
		if u'свазиленд' == gn.lower():
			_search_country += '&m_act[country]=1029'
		if u'сейшельские острова' == gn.lower():
			_search_country += '&m_act[country]=1010'
		if u'сенегал' == gn.lower():
			_search_country += '&m_act[country]=65'
		if u'сент-винсент и гренадины' == gn.lower():
			_search_country += '&m_act[country]=1055'
		if u'сент-люсия ' == gn.lower():
			_search_country += '&m_act[country]=1049'
		if u'сербия' == gn.lower():
			_search_country += '&m_act[country]=177'
		if u'сербия и черногория' == gn.lower():
			_search_country += '&m_act[country]=174'
		if u'сиам' == gn.lower():
			_search_country += '&m_act[country]=1021'
		if u'сингапур' == gn.lower():
			_search_country += '&m_act[country]=45'
		if u'сирия' == gn.lower():
			_search_country += '&m_act[country]=98'
		if u'словакия' == gn.lower():
			_search_country += '&m_act[country]=94'
		if u'словения' == gn.lower():
			_search_country += '&m_act[country]=40'
		if u'сомали' == gn.lower():
			_search_country += '&m_act[country]=160'
		if u'судан' == gn.lower():
			_search_country += '&m_act[country]=167'
		if u'суринам' == gn.lower():
			_search_country += '&m_act[country]=171'
		if u'сьерра-леоне' == gn.lower():
			_search_country += '&m_act[country]=1023'
		if u'таджикистан' == gn.lower():
			_search_country += '&m_act[country]=70'
		if u'таиланд' == gn.lower():
			_search_country += '&m_act[country]=44'
		if u'тайвань' == gn.lower():
			_search_country += '&m_act[country]=27'
		if u'танзания' == gn.lower():
			_search_country += '&m_act[country]=130'
		if u'тимор-лесте' == gn.lower():
			_search_country += '&m_act[country]=1068'
		if u'того' == gn.lower():
			_search_country += '&m_act[country]=161'
		if u'тонга' == gn.lower():
			_search_country += '&m_act[country]=1012'
		if u'тринидад и тобаго' == gn.lower():
			_search_country += '&m_act[country]=88'
		if u'тувалу' == gn.lower():
			_search_country += '&m_act[country]=1053'
		if u'тунис' == gn.lower():
			_search_country += '&m_act[country]=50'
		if u'туркменистан' == gn.lower():
			_search_country += '&m_act[country]=152'
		if u'турция' == gn.lower():
			_search_country += '&m_act[country]=68'
		if u'уганда' == gn.lower():
			_search_country += '&m_act[country]=172'
		if u'узбекистан' == gn.lower():
			_search_country += '&m_act[country]=71'
		if u'украина' == gn.lower():
			_search_country += '&m_act[country]=62'
		if u'уругвай' == gn.lower():
			_search_country += '&m_act[country]=79'
		if u'фарерские острова' == gn.lower():
			_search_country += '&m_act[country]=1008'
		if u'федеративные штаты микронезии' == gn.lower():
			_search_country += '&m_act[country]=1038'
		if u'фиджи' == gn.lower():
			_search_country += '&m_act[country]=166'
		if u'филиппины' == gn.lower():
			_search_country += '&m_act[country]=47'
		if u'финляндия' == gn.lower():
			_search_country += '&m_act[country]=7'
		if u'франция' == gn.lower():
			_search_country += '&m_act[country]=8'
		if u'французская гвиана' == gn.lower():
			_search_country += '&m_act[country]=1032'
		if u'французская полинезия' == gn.lower():
			_search_country += '&m_act[country]=1046'
		if u'хорватия' == gn.lower():
			_search_country += '&m_act[country]=85'
		if u'цар' == gn.lower():
			_search_country += '&m_act[country]=141'
		if u'чад' == gn.lower():
			_search_country += '&m_act[country]=77'
		if u'черногория' == gn.lower():
			_search_country += '&m_act[country]=1020'
		if u'чехия' == gn.lower():
			_search_country += '&m_act[country]=34'
		if u'чехословакия' == gn.lower():
			_search_country += '&m_act[country]=16'
		if u'чили' == gn.lower():
			_search_country += '&m_act[country]=51'
		if u'швейцария' == gn.lower():
			_search_country += '&m_act[country]=21'
		if u'швеция' == gn.lower():
			_search_country += '&m_act[country]=5'
		if u'шри-ланка' == gn.lower():
			_search_country += '&m_act[country]=108'
		if u'эквадор' == gn.lower():
			_search_country += '&m_act[country]=96'
		if u'экваториальная гвинея' == gn.lower():
			_search_country += '&m_act[country]=1061'
		if u'эритрея' == gn.lower():
			_search_country += '&m_act[country]=87'
		if u'эстония' == gn.lower():
			_search_country += '&m_act[country]=53'
		if u'эфиопия' == gn.lower():
			_search_country += '&m_act[country]=168'
		if u'юар' == gn.lower():
			_search_country += '&m_act[country]=30'
		if u'югославия' == gn.lower():
			_search_country += '&m_act[country]=19'
		if u'югославия (фр)' == gn.lower():
			_search_country += '&m_act[country]=66'
		if u'ямайка' == gn.lower():
			_search_country += '&m_act[country]=93'
		if u'япония' == gn.lower():
			_search_country += '&m_act[country]=9'

		return _search_country
		
	def get_search_kinopoisk(self, in_name, year='', step=0):
		name = in_name.strip()
		name = name.replace(" ", "+")
		kpid 	= u''
		rating 	= u''
		min		= u''

		if step == 0:
			search_uri = URI %(name, '')
		elif step == 1:
			search_uri = URI %(name+'+'+year, '')
		elif step == 2:
			search_uri = URI %(name, year)

	#	if act_year is None:
	#		search_uri = URI %(name+'+'+year, '')
	#	else:
	#		search_uri = URI %(name, act_year)

		html = Utils.get_HTML(search_uri, self.cookies)

		soup = BeautifulSoup(html, fromEncoding=u"windows-1251")
		search_results = soup.find(u"div", {u"class" : u"search_results"})
		if search_results == None:
			return  u'', u'', u''
		flymenu = search_results.find(u"p", {u"class" : u"name"})
		text = flymenu.a.text

		try:
			for p in range(9):
				if __debug__:
					print('%i -> text:%s == name:%s [%s]'  %(p, self.__clearString(text), name.replace("+", " "), self.__cmpString(self.__remSymbol(self.__clearString(text)), name)))
				if self.__cmpString(self.__remSymbol(self.__clearString(text)), name) > 60.0:
					rating = search_results.find("div", {"class" : "rating  "})
					if not rating:
						rating = search_results.find("div", {"class" : "rating  ratingGreenBG"})
						if not rating:
							rating = search_results.find("div", {"class" : "rating ratingRedBG "})
					try:
						rating = rating.text
					except:
						rating = u''
						pass

					kpid = re.search(ur'film\/([0-9]+)\/', flymenu.a['href']).group(1)
					try:
						info = search_results.find("div", {"class" : "info"})
						span = info.findAll("span")
						for sp in span:
							if re.search(ur'(,[ ]+)?([0-9]+)[ ]+[мин|ìèí]+$', sp.text):
								min = re.search(ur'(,[ ]+)?(?P<time>[0-9]+)[ ]+[мин|ìèí]+$', sp.text).group('time')
					except:
						pass

				elif p == 0:
					if re.search(ur'(\(.*\))$', in_name):
						name = name.replace(re.search(ur'(\(.*\))$', in_name).group(1), "")
						name.strip()

					if re.search(ur'^(.*?)[/]+', in_name):
						name = re.search(ur'^(.*?)[/]+', in_name).group(1)
						name.strip()

					if re.search(ur'(\(.*\))$', text):
						text = text.replace(re.search(ur'(\(.*\))$', text).group(1), "")
						text.strip()
					continue
				elif p == 1:
					if re.search(ur'/ (.*)$', in_name):
						name = re.search(ur'/ (.*)$', in_name).group(1)
					continue
				elif p == 2:
					if re.search(ur'([0-9]+([ ]+|[ ]?)[Сс]езон)', name):
						name = name.replace(re.search(ur'([0-9]+([ ]+|[ ]?)[Сс]езон)', name).group(1), '')
					if re.search(ur'([Сс]езон([ ]+|[ ]?)[0-9]+)', name):
						name = name.replace(re.search(ur'([Сс]езон([ ]+|[ ]?)[0-9]+)', name).group(1), '')
					if re.search(ur'(([Сc]езон|[Сc]ерия).*$)', name):
						name = name.replace(re.search(ur'(([Сc]езон|[Сc]ерия).*$)', name).group(1), '')
					continue
				elif p == 3:
					try:
						text =  flymenu.a.text.decode('utf-8').encode('cp1252').decode('cp1251')
					except:
						pass
					continue
				elif p == 4:
					if re.search(ur'^(.*?)[/]+', in_name):
						name = re.search(ur'^(.*?)[/]+', in_name).group(1)
						name.strip()
					continue
				elif p == 5:
					if re.search(ur'(^[Сс]мотреть|[Оо]нлайн)?(?P<name>.*)', in_name):
						name = re.search(ur'(^[Сс]мотреть|[Оо]нлайн)?.(?P<name>.*)', in_name).group('name')
						name.strip()
					continue
				elif p == 6:
					if re.search(ur':', in_name):
						name = name.split(':')[1]
						name.strip()
					if re.search(ur'-', in_name):
						name = name.split('-')[1]
						name.strip()
					continue
				elif p == 7 and step == 0:
					kp = self.get_search_kinopoisk(in_name, year, 1)
					if kp[1] != u'':
						return kp

				elif p == 8 and step == 1:
					kp = self.get_search_kinopoisk(in_name, year, 2)
					if kp[1] != u'':
						return kp
				break
		except:
			return  u'', u'', u''

		return rating, kpid, min

	def get_kinopoisk(self, kpid):
		year = ''
		genre = ''
		st = ''
		treiler = ''
		rating = ''
		html = Utils.get_HTML(URI_ID %kpid, self.cookies)
		soup = BeautifulSoup(html, fromEncoding=u"windows-1251")
		info = soup.find(u"table", {u"class" : u"info"})

		scriptTags = soup.findAll('script')
		for script in scriptTags:
			tagContent = script.text
			if tagContent.count('getTrailersDomain') > 0:
				http = re.search(ur'getTrailersDomain[() ]+\{[A-z ]+\'(?P<domain>[A-z.-\/:]+)\'[;}]+', tagContent).group('domain')
			if tagContent.count('GetTrailerPreview') > 0:
				uri = re.search(ur'trailerFile[\'\": ]+(?P<tr>[A-z.\/:0-9-]+)[\"\',\n]+', tagContent).group('tr')
		try:
			treiler = 'http://%s/%s' %(http,uri)
		except:
			pass
		
		brand_words = soup.find(u"div", {u"class" : u"brand_words"})
		plot = self.__clearString(brand_words.text)
		
		try:
			rating = soup.find("span", {"class" : "rating_ball"}).text
		except:
			rating = ''
			
		for tr in info.findAll("tr"):
			try:
				key = self.__clearString(tr.find("td", {"class":"type"}).text)
			except:
				continue
			try:
				if info.a != None:
					if key == u"год":
						year = self.__clearString(tr.a.text)

					if key == u"жанр":
						genre = tr.find("span", {"itemprop":"genre"})
						strGenre = ''
						for ge in genre.findAll("a"):
							strGenre = strGenre + " " + ge.text
						genre = strGenre.strip()
					elif key == u"страна":
						st = self.__clearString(tr.a.text)
			except:
				pass

		return year, genre, st, plot, treiler, rating

	def get_search_kinopoisk2(self, in_name, year='', genre='', contry='', type=0):
		name = in_name.strip()
		name = name.replace(" ", "+")
		kpid 	= u''
		rating 	= u''
		min		= u''

		from_year = str(int(year)-1)
		to_year = str(int(year)+1)
		try:
			contry = re.search(ur'([А-я]+)', contry).group(1)
		except:
			contry = ''
		search_uri = URI4 %(name, from_year, to_year) + self.get_country_id(contry)
		if type == 0:
			search_uri += '&m_act[content_find]=film'
		elif type == 1:
			search_uri += '&m_act[content_find]=serial'
			
		html = Utils.get_HTML(search_uri, self.cookies)
		soup = BeautifulSoup(html, fromEncoding=u"windows-1251")
		search_results = soup.find(u"div", {u"class" : u"search_results"})
		if search_results == None:
			try:
				link = soup.find(u"link", {u"rel" : u"canonical"})
				if re.search(ur'film\/([0-9]+)\/', link['href']):
					return self.get_kinopoisk2(html, link['href']) + (u'',)
				else:
					if contry != '':
						return self.get_search_kinopoisk2(in_name, year, genre='', contry='')
					elif type != 2:
						return self.get_search_kinopoisk2(in_name, year, genre='', contry='', type=2)
						
					return u'', u'', u'', u''
			except:
				return u'', u'', u'', u''
		else:
			flymenu = search_results.find(u"p", {u"class" : u"name"})
			text = flymenu.a.text

			try:
				for p in range(9):
					if __debug__:
						print('%i -> text:%s == name:%s [%s]'  %(p, self.__clearString(text), name.replace("+", " "), self.__cmpString(self.__remSymbol(self.__clearString(text)), name)))
					if self.__cmpString(self.__remSymbol(self.__clearString(text)), self.__remSymbol(name)) > 60.0:
						rating = search_results.find("div", {"class" : "rating  "})
						if not rating:
							rating = search_results.find("div", {"class" : "rating  ratingGreenBG"})
							if not rating:
								rating = search_results.find("div", {"class" : "rating ratingRedBG "})
						try:
							rating = rating.text
						except:
							rating = u''
							pass

						kpid = re.search(ur'film\/([0-9]+)\/', flymenu.a['href']).group(1)
						try:
							info = search_results.find("div", {"class" : "info"})
							span = info.findAll("span")
							for sp in span:
								if re.search(ur'(,[ ]+)?([0-9]+)[ ]+[мин|ìèí]+$', sp.text):
									min = re.search(ur'(,[ ]+)?(?P<time>[0-9]+)[ ]+[мин|ìèí]+$', sp.text).group('time')
						except:
							pass

					elif p == 1:
						if re.search(ur'(\(.*\))$', in_name):
							name = name.replace(re.search(ur'(\(.*\))$', in_name).group(1), "")
							name.strip()

						if re.search(ur'^(.*?)[/]+', in_name):
							name = re.search(ur'^(.*?)[/]+', in_name).group(1)
							name.strip()

						if re.search(ur'(\(.*\))$', text):
							text = text.replace(re.search(ur'(\(.*\))$', text).group(1), "")
							text.strip()
						continue
					elif p == 2:
						if re.search(ur'/ (.*)$', in_name):
							name = re.search(ur'/ (.*)$', in_name).group(1)
						continue
					elif p == 3:
						if re.search(ur'([0-9]+([ ]+|[ ]?)[Сс]езон)', name):
							name = name.replace(re.search(ur'([0-9]+([ ]+|[ ]?)[Сс]езон)', name).group(1), '')
						if re.search(ur'([Сс]езон([ ]+|[ ]?)[0-9]+)', name):
							name = name.replace(re.search(ur'([Сс]езон([ ]+|[ ]?)[0-9]+)', name).group(1), '')
						if re.search(ur'(([Сc]езон|[Сc]ерия).*$)', name):
							name = name.replace(re.search(ur'(([Сc]езон|[Сc]ерия).*$)', name).group(1), '')
						continue
					elif p == 1:
						try:
							text =  flymenu.a.text.decode('utf-8').encode('cp1252').decode('cp1251')
						except:
							pass
						continue
					elif p == 4:
						if re.search(ur'^(.*?)[/]+', in_name):
							name = re.search(ur'^(.*?)[/]+', in_name).group(1)
							name.strip()
						continue
					elif p == 5:
						if re.search(ur'(^[Сс]мотреть|[Оо]нлайн)?(?P<name>.*)', in_name):
							name = re.search(ur'(^[Сс]мотреть|[Оо]нлайн)?.(?P<name>.*)', in_name).group('name')
							name.strip()
						continue
					elif p == 6:
						if re.search(ur':', in_name):
							try:
								name = name.split(':')[1]
							except:
								pass
							name.strip()
							continue
						if re.search(ur'-', in_name):
							try:
								name = name.split('-')[1]
							except:
								pass
							name.strip()
						continue
					elif p == 7:
						if contry != '':
							return self.get_search_kinopoisk2(in_name, year, genre='', contry='', type=type)
					break
			except:
				return  u'', u'', u'', u''

			return rating, kpid, min, self.__clearString(name.replace("+", " "))
		return  u'', u'', u'',  u''
		
	def get_kinopoisk2(self, html, hr):
		#year = ''
		#genre = ''
		min = ''
		rating = ''
		kpid = re.search(ur'film\/([0-9]+)\/', hr).group(1)
		soup = BeautifulSoup(html, fromEncoding=u"windows-1251")

		#brand_words = soup.find(u"div", {u"class" : u"brand_words"})
		#plot = self.__clearString(brand_words.text)

		try:
			rating = soup.find("span", {"class" : "rating_ball"}).text
		except:
			rating = ''

		try:
			min = soup.find("td", {"class" : "time"}).text
			min = re.search(ur'([0-9]+)', min).group(1)
		except:
			min = ''

		return rating, kpid, min