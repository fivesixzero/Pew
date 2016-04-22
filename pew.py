#---------------------------------------------------------------------------------------
#
# Pew (Python Eve Wrapper) - a lightweight wrapper for the Eve Online API.
#
# Copyright (C) 2012 Chris Smith <crsmithdev@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#---------------------------------------------------------------------------------------
#
# Version 1.2 - April 19th, 2016
#  - Fixed/updated several broken unit tests
#  - Built .eve_apis CSV key loading into unit tests, replaced static data where possible
#  - Fixed a few minor issues found by unit tests
#     - rewrote a bit of _join() to handle all lists properly
#  - Moved api_call_list to misc_call_list
#  - Added misc_call_list and all four planetary calls to unit tests
#
# Version 1.1 - April 18th, 2016
#  - Updated imports to use modern ElementTree
#  - Fixed _join() method, which couldn't handle non-list items
#  - Added all four modern planetary interaction endpoints
#  - Added __init.py__ to allow easy importing
#  - Improved error message output on API failure (URLerror)
#  - Added eve_type_name() for XML API lookup of typeNames via typeIDs
#  - Added api_call_list() for XML API listing of API endpoints
#  - Added acct_api_key_info() for XML API info on the provided API key
#  - Fixed char_account_balance() by updating endpoint name
#  - Improived char_asset_list() to allow optional "flat" mode provided in API
#  - Added CSV API key value input to pew_tests.py to avoid storing key value
#  - Added .eve_apis to .gitignore
#
# Version 1.0 - July 4th, 2012
#  - Initial release
#
# Todos:
#  - Add character / corp / alliance image method (server down at time of writing)
#  - Add (optional?) caching to match timeouts in API doc (maybe in raw_request?)
#  - Figure out a way to properly test the char_contracts_items function
#  - Fix broken endpoints
#     - Corporation Contracts
#     - Corporation Contract Bids
#     - Corporation Contract Items
#  - Add and test any missing endpoints
#     - Character ChatChannels
#     - Character Bookmarks
#     - Character Locations
#     - Character Killmails (vs killLogs, which don't work right)
#     - Corporation Bookmarks
#     - Corporation MemberTrackingExtended
#     - Corporation MemberTrackingLimited
#     - Corporation Locations
#     - Corporation Killmails (vs killLogs, which don't work right)
#
# Completed Todos:
#
#  - Fix problems indicated in newly-fixed unit test [DONE 4/19]
#  - Add unit tests to handle newly added API methods [DONE 4/19]
#  - Add and test any missing endpoints
#     - Character Contracts
#     - Character Contract Bids
#     - Character Contract Items
#  - Fix broken endpoints
#     - Corporation KillLog * BROKEN (httplib.BadStatusLine: HTTP/1.1 000)
#		 - This fails if called within cache timeout! killMails is better.
#     - Corporation FacWarStats * BROKEN (HTTP Error 400: Bad Request)
#		 - This was failing because corp key lacked FW status. Fixed with FW corp.
#
# Requirements:
#  - Python 2.7
#
#---------------------------------------------------------------------------------------

from urllib import urlencode
from urllib2 import urlopen, URLError
import xml.etree.ElementTree as ET

class PewApiObject(object):

	def __init__(self):
		pass

class PewError(Exception):

	def __init__(self, error):
		super(PewError, self).__init__()

		self.error = error

	def __str__(self):
		return repr(self.error)

class PewApiError(PewError):

	def __init__(self, code, error):
		super(PewApiError, self).__init__(error)

		self.code = code

	def __str__(self):
		return repr(self)

	def __repr__(self):
		return '[%s] %s' % (self.code, self.error)

class PewConnectionError(PewError):

	def __init__(self, error):
		super(PewConnectionError, self).__init__(error)

class Pew(object):

	_API_TYPE = 'api'
	_CORP_TYPE = 'corp'
	_CHAR_TYPE = 'char'
	_ACCT_TYPE = 'account'
	_MAPS_TYPE = 'map'
	_EVE_TYPE = 'eve'

	def __init__(self, api_id = None, api_key = None):

		self.api_id = api_id
		self.api_key = api_key
		self.api_url = 'https://api.eveonline.com'
		self.emd_url = 'http://eve-marketdata.com/api'
		self.emd_charname = 'demo' # maybe dynamically get this in the future?
		self.ecent_url = 'http://api.eve-central.com/api'
		self._params = {}

	# Request methods.

	def _char_request(self, api_type, method_name, character_id):

		self._params['characterId'] = character_id

		return self._auth_request(api_type, method_name)

	def _auth_request(self, api_type, method_name):

		self._params['keyId'] = self.api_id
		self._params['vCode'] = self.api_key

		return self._request(api_type, method_name)

	def _emd_request(self, api_type, method_name):

		self._params['char_name'] = self.emd_charname

		return self._request(api_type, method_name)

	def _request(self, api_type, method_name):

		url = self._build_url(api_type, method_name)
		self._params.clear()

		result = self._raw_request(url)

		return self._handle_result(result)

	def _raw_request(self, url):

		try:
			response = urlopen(url)
			result = response.read()

			return result

		except URLError as er:
			raise PewConnectionError(str('url: ' + str(url) + ' || error: ' + str(er)))

	def _build_url(self, api_type, method_name):

		if api_type == 'emd':
			url = '%s/%s.xml' % (self.emd_url , method_name)
		elif api_type == 'ecent':
			url = '%s/%s' % (self.ecent_url , method_name)
		else:
			url = '%s/%s/%s.xml.aspx' % (self.api_url, api_type, method_name)

		if len(self._params) > 0:
			url = '%s?%s' % (url, urlencode(self._params))

		return url

	# Result handling methods.

	def _parse_xml(self, xml):

		tree = ET.fromstring(xml)

		return self._r_parse_xml(tree)[0]

	def _r_parse_xml(self, node):

		has_value = node.text is not None and len(node.text.strip()) > 0

		if node.tag == 'rowset':
			return [self._r_parse_xml(child)[0] for child in node], node.get('name')

		if len(node) > 0 or len(node.items()) > 0:

			obj = PewApiObject()

			for attr, value in node.items():
				setattr(obj, attr, self._parse_value(value))

			for child in node:
				child_obj, child_tag = self._r_parse_xml(child)
				setattr(obj, child_tag, child_obj)

			if has_value:
				setattr(obj, '_value', node.text)

			return obj, node.tag

		elif has_value:
			return self._parse_value(node.text), node.tag

		return None, node.tag

	def _parse_value(self, value):
		try:
			return int(value)
		except ValueError:
			return value

	def _handle_result(self, xml):

		result = self._parse_xml(xml)

		if hasattr(result, 'error'):
			raise PewApiError(int(result.error.code), result.error._value)

		return result.result

	# Misc. methods.

	def _join(self, lst):

		if type(lst) is list:
			return ','.join([str(i) for i in lst])
		else:
			return str(lst) # we want to return original in string form if its not a list

	# eve-marketdata.com API methods -- EXPERIMENTAL

	def emd_item_prices(self, buysell, type_ids, marketgroup_ids = None, region_ids = None, solarsystem_ids = None, station_ids = None):
		self._params['buysell'] = buysell
		self._params['type_ids'] = self._join(type_ids)
		if marketgroup_ids is not None:
			self._params['marketgroup_ids'] = self._join(marketgroup_ids)
		if region_ids is not None:
			self._params['region_ids'] = self._join(region_ids)
		if solarsystem_ids is not None:
			self._params['solarsystem_ids'] = self._join(solarsystem_ids)
		if station_ids is not None:
			self._params['station_ids'] = self._join(station_ids)
		return self._emd_request('emd', 'item_prices2')

	# usage: emd = emd_item_orders('b' os 's' or 'a', region_ids list or None, solarsystem_ids or None, station_ids or None)
	def emd_item_orders(self, buysell, minmax, type_ids, marketgroup_ids = None, region_ids = None, solarsystem_ids = None, station_ids = None):
		self._params['buysell'] = buysell
		self._params['minmax'] = minmax
		self._params['type_ids'] = self._join(type_ids)
		if marketgroup_ids is not None:
			self._params['marketgroup_ids'] = self._join(marketgroup_ids)
		if region_ids is not None:
			self._params['region_ids'] = self._join(region_ids)
		if solarsystem_ids is not None:
			self._params['solarsystem_ids'] = self._join(solarsystem_ids)
		if station_ids is not None:
			self._params['station_ids'] = self._join(station_ids)
		return self._emd_request('emd', 'item_orders2')

	# Account API methods.

	def acct_characters(self):
		return self._auth_request(self._ACCT_TYPE, 'characters')

	def acct_status(self):
		return self._auth_request(self._ACCT_TYPE, 'accountStatus')

	def acct_api_key_info(self):
		return self._auth_request(self._ACCT_TYPE, 'APIKeyInfo')

	# Character API Methods

	def char_account_balance(self, character_id):
		return self._char_request(self._CHAR_TYPE,'AccountBalance', character_id)

	def char_asset_list(self, character_id, flat=0):
		self._params['flat'] = self._join(flat)
		return self._char_request(self._CHAR_TYPE,'assetList', character_id)

	def char_calendar_event_attendees(self, character_id, event_ids):
		self._params['eventIds'] = self._join(event_ids)
		return self._char_request(self._CHAR_TYPE,'calendarEventAttendees', character_id)

	def char_character_sheet(self, character_id):
		return self._char_request(self._CHAR_TYPE,'characterSheet', character_id)

	def char_contact_list(self, character_id):
		return self._char_request(self._CHAR_TYPE,'contactList', character_id)

	def char_contact_notifications(self, character_id):
		return self._char_request(self._CHAR_TYPE,'contactNotifications', character_id)

	def char_contracts(self, character_id, contract_id = None):
		self._params['contractID'] = self._join(contract_id)
		return self._char_request(self._CHAR_TYPE,'contracts', character_id)

	def char_contract_bids(self, character_id):
		return self._char_request(self._CHAR_TYPE,'contractBids', character_id)

	def char_contract_items(self, character_id, contract_id):
		self._params['contractID'] = self._join(contract_id)
		return self._char_request(self._CHAR_TYPE,'contractItems', character_id)

	def char_factional_warfare_statistics(self, character_id):
		return self._char_request(self._CHAR_TYPE,'facWarStats', character_id)

	def char_industry_jobs(self, character_id):
		return self._char_request(self._CHAR_TYPE,'industryJobs', character_id)

	def char_industry_job_history(self, character_id):
		return self._char_request(self._CHAR_TYPE,'industryJobHistory', character_id)

	def char_kill_log(self, character_id):
		return self._char_request(self._CHAR_TYPE,'killLog', character_id)

	def char_mailing_lists(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'mailinglists', character_id)

	def char_mail_bodies(self, character_id, mail_ids):
		self._params['ids'] = self._join(mail_ids)
		return self._char_request(self._CHAR_TYPE, 'mailbodies', character_id)

	def char_mail_messages(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'mailmessages', character_id)

	def char_market_orders(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'marketorders', character_id)

	def char_medals(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'medals', character_id)

	def char_notification_texts(self, character_id, notification_ids):
		self._params['ids'] = self._join(notification_ids)
		return self._char_request(self._CHAR_TYPE, 'notificationtexts', character_id)

	def char_notifications(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'notifications', character_id)

	def char_npc_standings(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'standings', character_id)

	def char_planetary_colonies(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'planetaryColonies', character_id)

	def char_planetary_links(self, character_id, planet_id):
		self._params['planetID'] = planet_id
		return self._char_request(self._CHAR_TYPE, 'planetaryLinks', character_id)

	def char_planetary_pins(self, character_id, planet_id):
		self._params['planetID'] = planet_id
		return self._char_request(self._CHAR_TYPE, 'planetaryPins', character_id)

	def char_planetary_routes(self, character_id, planet_id):
		self._params['planetID'] = planet_id
		return self._char_request(self._CHAR_TYPE, 'PlanetaryRoutes', character_id)

	def char_research(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'research', character_id)

	def char_skill_in_training(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'skillintraining', character_id)

	def char_skill_queue(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'skillqueue', character_id)

	def char_upcoming_calendar_events(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'upcomingcalendarevents', character_id)

	def char_wallet_journal(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'walletjournal', character_id)

	def char_wallet_transactions(self, character_id):
		return self._char_request(self._CHAR_TYPE, 'wallettransactions', character_id)

	# Corporation API methods.

	def corp_account_balance(self, character_id):
		return self._char_request(self._CORP_TYPE, 'accountBalance', character_id)

	def corp_asset_list(self, character_id):
		return self._char_request(self._CORP_TYPE,'assetList', character_id)

	def corp_contact_list(self, character_id):
		return self._char_request(self._CORP_TYPE,'contactList', character_id)

	def corp_container_log(self, character_id):
		return self._char_request(self._CORP_TYPE, 'containerlog', character_id)

	#def corp_contracts(self, character_id, contract_id = None):
	#	self._params['contractID'] = self._join(contract_id)
	#	return self._char_request(self._CORP_TYPE,'contracts', character_id)

	#def corp_contract_bids(self, character_id):
	#	return self._char_request(self._CORP_TYPE,'contractBids', character_id)

	#def corp_contract_items(self, character_id, contract_id):
	#	self._params['contractID'] = self._join(contract_id)
	#	return self._char_request(self._CORP_TYPE,'contractItems', character_id)

	def corp_corporation_sheet(self, character_id):
		return self._char_request(self._CORP_TYPE, 'corporationsheet', character_id)

	def corp_factional_warfare_statistics(self, character_id):
		return self._char_request(self._CORP_TYPE,'facWarStats', character_id)

	def corp_industry_jobs(self, character_id):
		return self._char_request(self._CORP_TYPE,'industryJobs', character_id)

	def corp_kill_log(self, character_id):
		return self._char_request(self._CORP_TYPE,'killLog', character_id)

	def corp_market_orders(self, character_id):
		return self._char_request(self._CORP_TYPE, 'marketorders', character_id)

	def corp_medals(self, character_id):
		return self._char_request(self._CORP_TYPE, 'medals', character_id)

	def corp_member_medals(self, character_id):
		return self._char_request(self._CORP_TYPE, 'membermedals', character_id)

	def corp_member_security(self, character_id):
		return self._char_request(self._CORP_TYPE, 'membersecurity', character_id)

	def corp_member_security_log(self, character_id):
		return self._char_request(self._CORP_TYPE, 'membersecuritylog', character_id)

	def corp_member_tracking(self, character_id):
		return self._char_request(self._CORP_TYPE, 'membertracking', character_id)

	def corp_npc_standings(self, character_id):
		return self._char_request(self._CORP_TYPE, 'standings', character_id)

	def corp_outpost_list(self, character_id):
		return self._char_request(self._CORP_TYPE, 'outpostlist', character_id)

	def corp_outpost_service_detail(self, character_id):
		return self._char_request(self._CORP_TYPE, 'outpostservicedetail', character_id)

	def corp_pos_detail(self, item_id):
		self._params['itemID'] = item_id
		return self._auth_request(self._CORP_TYPE, 'starbasedetail', item_id)

	def corp_pos_list(self, character_id):
		return self._char_request(self._CORP_TYPE, 'starbaselist', character_id)

	def corp_shareholders(self, character_id):
		return self._char_request(self._CORP_TYPE, 'shareholders', character_id)

	def corp_titles(self, character_id):
		return self._char_request(self._CORP_TYPE, 'titles', character_id)

	def corp_wallet_journal(self, character_id):
		return self._char_request(self._CORP_TYPE, 'walletjournal', character_id)

	def corp_wallet_transactions(self, character_id):
		return self._char_request(self._CORP_TYPE, 'wallettransactions', character_id)

	# Eve API methods.

	def eve_alliance_list(self):
		return self._request(self._EVE_TYPE, 'alliancelist')

	def eve_certificate_tree(self):
		return self._request(self._EVE_TYPE, 'certificatetree')

	def eve_character_id(self, character_names):
		self._params['names'] = ''.join(character_names)
		return self._request(self._EVE_TYPE, 'characterid')

	def eve_character_info(self, character_id):
		return self._char_request(self._EVE_TYPE, 'characterinfo', character_id)

	def eve_character_name(self, character_ids):
		self._params['ids'] = self._join(character_ids)
		return self._request(self._EVE_TYPE, 'charactername')

	def eve_conquerable_station_list(self):
		return self._request(self._EVE_TYPE, 'conquerablestationlist')

	def eve_error_list(self):
		return self._request(self._EVE_TYPE, 'errorlist')

	def eve_factional_warfare_statistics(self):
		return self._request(self._EVE_TYPE, 'facwarstats')

	def eve_factional_warfare_top_statistics(self):
		return self._request(self._EVE_TYPE, 'facwartopstats')

	def eve_reference_types(self):
		return self._request(self._EVE_TYPE, 'reftypes')

	def eve_skill_tree(self):
		return self._request(self._EVE_TYPE, 'skilltree')

	def eve_type_name(self, ids):
		self._params['ids'] = self._join(ids)
		return self._request(self._EVE_TYPE, 'typeName')

	# Maps API methods.

	def maps_factional_warfare_systems(self):
		return self._request(self._MAPS_TYPE, 'facwarsystems')

	def maps_jumps(self):
		return self._request(self._MAPS_TYPE, 'jumps')

	def maps_kills(self):
		return self._request(self._MAPS_TYPE, 'kills')

	def maps_sovereignty(self):
		return self._request(self._MAPS_TYPE, 'sovereignty')

	# Misc API methods.

	def misc_server_status(self):
		return self._request('server', 'serverstatus')

	def misc_call_list(self):
		return self._auth_request(self._API_TYPE, 'CallList')
