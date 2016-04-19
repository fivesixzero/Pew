import unittest, urllib, sys

from pew import Pew, PewApiError, PewConnectionError

import csv

CORP_CSV_ROW = 5	# What CSV row can we use for corp key testing?
CHAR_CSV_ROW = 3	# What CSV row can we use for character key testing?
CHAR_NUM = 0		# What character on that char key are we going to use?

# Grabs our key info from our CSV, returns a pew object and a character ID

def csvPicker(CSV_ROW_IN,CHAR_NUM_IN = None):

	try:
    		apiCSV = open('.eve_apis', 'rb')
	except:
	    	print ''
	    	print 'CSV IMPORT FAILURE! Make sure .eve_apis exists here!'
	    	print ''
	    	print 'CSV format is: keyid,verification,nickname with a key on the first line'
	    	print ''
	    	raise
	    	exit(1)

	apiList = list(csv.reader(apiCSV, delimiter=',', quotechar='\''))
	apiCSV.close()

	API_ID = apiList[CSV_ROW_IN][0]
	API_KEY = apiList[CSV_ROW_IN][1]

	pew = Pew(API_ID,API_KEY)

	chars = pew.acct_characters()
	CHAR = CHAR_NUM
	CHAR_ID = chars.characters[CHAR].characterID
	del chars

	return pew, CHAR_ID

# end CSV setup

class PewTest(unittest.TestCase):

	def setUp(self):
		global CHAR_ID
		global CHAR_ID_CORP
		self.pew, CHAR_ID = csvPicker(CHAR_CSV_ROW,CHAR_NUM)
		self.pewCorp, CHAR_ID_CORP = csvPicker(CORP_CSV_ROW,0)

	def assertHasMember(self, obj, member_name):
		self.assertTrue(member_name in obj.__dict__)

class PewCoreTests(PewTest):

	def test__parse_value_handles_integers(self):

		result = self.pew._parse_value('1')
		self.assertIsInstance(result, int)
		self.assertEqual(result, 1)

	def test__parse_value_handles_strings(self):

		result = self.pew._parse_value('abc')
		self.assertIsInstance(result, str)
		self.assertEqual(result, 'abc')

	def test__parse_xml_handles_values(self):

		result = self.pew._parse_xml('<?xml version="1.0"?><a><b>1</b><c>2</c></a>')
		self.assertEqual(result.b, 1)
		self.assertEqual(result.c, 2)

	def test__parse_xml_handles_attributes(self):

		result = self.pew._parse_xml('<?xml version="1.0"?><a><b x="1"></b><c x="2"></c></a>')

		self.assertEqual(result.b.x, 1)
		self.assertEqual(result.c.x, 2)

	def test__parse_xml_handles_attributes_and_values(self):

		result = self.pew._parse_xml('<?xml version="1.0"?><a><b x="1">abc</b><c x="2">def</c></a>')

		self.assertEqual(result.b.x, 1)
		self.assertEqual(result.b._value, 'abc')
		self.assertEqual(result.c.x, 2)
		self.assertEqual(result.c._value, 'def')

	def test__parse_xml_handles_no_value(self):

		result = self.pew._parse_xml('<?xml version="1.0"?><a><b>1</b><c></c></a>')

		self.assertEqual(result.b, 1)
		self.assertEqual(result.c, None)

	def test__parse_xml_handles_rowsets(self):

		result = self.pew._parse_xml('<?xml version="1.0"?><a><rowset name="test"><row x="1"/><row x="2"/></rowset></a>')

		self.assertEqual(len(result.test), 2)
		self.assertEqual(result.test[0].x, 1)
		self.assertEqual(result.test[1].x, 2)

	def test__build_url_appends_params(self):

		params = {'a': 1, 'b': 2, 'c': 3}
		expected = '%s/%s?%s' % (self.pew.api_url, 'test1/test2.xml.aspx', urllib.urlencode(params))
		self.pew._params = params

		result = self.pew._build_url('test1', 'test2')

		self.assertEqual(result, expected)

	def test__build_url_appends_nothing_with_no_params(self):

		params = {}
		expected = '%s/%s' % (self.pew.api_url, 'test1/test2.xml.aspx')
		self.pew._params = params

		result = self.pew._build_url('test1', 'test2')

		self.assertEqual(result, expected)

	def test__handle_result_returns_result_on_success(self):

		xml = '<?xml version="1.0" encoding="UTF-8"?><pew version="2"><currentTime>123</currentTime><result><a>1</a><b>2</b></result><cachedUntil>123</cachedUntil></pew>'

		result = self.pew._handle_result(xml)

		self.assertEqual(result.a, 1)
		self.assertEqual(result.b, 2)

	def test__handle_result_throws_exception_on_error(self):

		xml = '<?xml version="1.0" encoding="UTF-8"?><pew version="2"><currentTime>123</currentTime><error code="1">Error 1</error><cachedUntil>123</cachedUntil></pew>'

		try:
			self.pew._handle_result(xml)
			self.assertTrue(false)
		except PewApiError as er:
			self.assertEqual(er.code, 1)
			self.assertEqual(er.error, 'Error 1')

	def test__join_joins_intergers(self):

		lst = [1, 2, 3]
		result = self.pew._join(lst)

		self.assertEqual(result, '1,2,3')

	def test__request_bad_url_throws_error(self):

		try:
			self.pew._request('blah', 'blah')
			self.assertTrue(False)
		except PewConnectionError as er:
			self.assertTrue(True)

class PewAccountTests(PewTest):

	def test_acct_characters(self):

		result = self.pew.acct_characters()
		self.assertHasMember(result, 'characters')

	def test_acct_status(self):

		result = self.pew.acct_status()
		self.assertHasMember(result, 'paidUntil')

class PewCharacterTests(PewTest):

	def test_char_account_balance(self):

		result = self.pew.char_account_balance(CHAR_ID)
		self.assertHasMember(result, 'accounts')

	def test_char_asset_list(self):

		result = self.pew.char_asset_list(CHAR_ID)
		self.assertHasMember(result, 'assets')

	def test_char_calendar_event_attendees(self):

		result = self.pew.char_calendar_event_attendees(CHAR_ID, ['123'])
		self.assertHasMember(result, 'eventAttendees')

	def test_char_character_sheet(self):

		result = self.pew.char_character_sheet(CHAR_ID)
		self.assertHasMember(result, 'characterID')

	def test_char_contact_list(self):

		result = self.pew.char_contact_list(CHAR_ID)
		self.assertHasMember(result, 'contactList')

	def test_char_contact_notifications(self):

		result = self.pew.char_contact_notifications(CHAR_ID)
		self.assertHasMember(result, 'contactNotifications')

	def test_char_factional_warfare_statistics(self):
		pass

	def test_char_industry_jobs(self):

		result = self.pew.char_industry_jobs(CHAR_ID)
		self.assertHasMember(result, 'jobs')

	def test_char_kill_log(self):
		pass

	def test_char_mailing_list(self):

		result = self.pew.char_mailing_lists(CHAR_ID)
		self.assertHasMember(result, 'mailingLists')

	def test_char_mail_bodies(self):

		result = self.pew.char_mail_bodies(CHAR_ID, '123')
		self.assertHasMember(result, 'messages')

	def test_char_mail_messages(self):

		result = self.pew.char_mail_messages(CHAR_ID)
		self.assertHasMember(result, 'messages')

	def test_char_market_orders(self):

		result = self.pew.char_market_orders(CHAR_ID)
		self.assertHasMember(result, 'orders')

	def test_char_medals(self):

		result = self.pew.char_medals(CHAR_ID)
		self.assertHasMember(result, 'currentCorporation')

	def test_char_notification_texts(self):

		result = self.pew.char_notification_texts(CHAR_ID, '123')
		self.assertHasMember(result, 'notifications')

	def test_char_notifications(self):

		result = self.pew.char_notifications(CHAR_ID)
		self.assertHasMember(result, 'notifications')

	def test_char_npc_standings(self):

		result = self.pew.char_npc_standings(CHAR_ID)
		self.assertHasMember(result, 'characterNPCStandings')

	def test_char_planetary_colonies(self):

		result = self.pew.char_planetary_colonies(CHAR_ID)
		self.assertHasMember(result, 'colonies')

	def test_char_planetary_links(self):

		result = self.pew.char_planetary_links(CHAR_ID, '123')
		self.assertHasMember(result, 'links')

	def test_char_planetary_pins(self):

		result = self.pew.char_planetary_pins(CHAR_ID, '123')
		self.assertHasMember(result, 'pins')

	def test_char_planetary_routes(self):

		result = self.pew.char_planetary_routes(CHAR_ID, '123')
		self.assertHasMember(result, 'routes')

	def test_char_research(self):

		result = self.pew.char_research(CHAR_ID)
		self.assertHasMember(result, 'research')

	def test_char_skill_in_training(self):

		result = self.pew.char_skill_in_training(CHAR_ID)
		self.assertHasMember(result, 'skillInTraining')

	def test_char_skill_queue(self):

		result = self.pew.char_skill_queue(CHAR_ID)
		self.assertHasMember(result, 'skillqueue')

	def test_char_upcoming_calendar_events(self):

		result = self.pew.char_upcoming_calendar_events(CHAR_ID)
		self.assertHasMember(result, 'upcomingEvents')

	def test_char_wallet_journal(self):

		result = self.pew.char_wallet_journal(CHAR_ID)
		self.assertHasMember(result, 'transactions')

	def test_char_wallet_transactions(self):

		result = self.pew.char_wallet_transactions(CHAR_ID)
		self.assertHasMember(result, 'transactions')

class PewEveTests(PewTest):

	def test_eve_alliance_list(self):

		result = self.pew.eve_alliance_list()
		self.assertHasMember(result, 'alliances')

	def test_eve_certificate_tree(self):

		result = self.pew.eve_certificate_tree()
		self.assertHasMember(result, 'categories')

	def test_eve_character_id(self):

		result = self.pew.eve_character_id('test')
		self.assertHasMember(result, 'characters')

	def test_eve_character_info(self):

		result = self.pew.eve_character_info(CHAR_ID)
		self.assertHasMember(result, 'characterID')

	def test_eve_character_name(self):

		result = self.pew.eve_character_name(CHAR_ID)
		self.assertHasMember(result, 'characters')

	def test_eve_conquerable_station_list(self):

		result = self.pew.eve_conquerable_station_list()
		self.assertHasMember(result, 'outposts')

	def test_eve_error_list(self):

		result = self.pew.eve_error_list()
		self.assertHasMember(result, 'errors')

	def test_eve_factional_warfare_statistics(self):

		result = self.pew.eve_factional_warfare_statistics()
		self.assertHasMember(result, 'totals')

	def test_eve_factional_warfare_top_statistics(self):

		result = self.pew.eve_factional_warfare_top_statistics()
		self.assertHasMember(result, 'characters')

	def test_eve_reference_types(self):

		result = self.pew.eve_reference_types()
		self.assertHasMember(result, 'refTypes')

	def test_eve_skill_tree(self):

		result = self.pew.eve_skill_tree()
		self.assertHasMember(result, 'skillGroups')

class PewMapsTests(PewTest):

	def test_maps_factional_warfare_systems(self):

		result = self.pew.maps_factional_warfare_systems()
		self.assertHasMember(result, 'solarSystems')

	def test_maps_jumps(self):

		result = self.pew.maps_jumps()
		self.assertHasMember(result, 'solarSystems')

	def test_maps_kills(self):

		result = self.pew.maps_kills()
		self.assertHasMember(result, 'solarSystems')

	def test_maps_sovereignty(self):

		result = self.pew.maps_sovereignty()
		self.assertHasMember(result, 'solarSystems')

class PewMiscTests(PewTest):

	def test_misc_server_status(self):

		result = self.pew.misc_server_status()
		self.assertHasMember(result, 'serverOpen')

	def test_misc_call_list(self):

		result = self.pew.misc_call_list()
		self.assertHasMember(result, 'callGroups')

class PewCorpTests(PewTest):

	def test_corp_account_balance(self):

		result = self.pewCorp.corp_account_balance(CHAR_ID_CORP)
		self.assertHasMember(result, 'accounts')

	def test_corp_asset_list(self):

		result = self.pewCorp.corp_asset_list(CHAR_ID_CORP)
		self.assertHasMember(result, 'assets')

	def test_corp_contact_list(self):

		result = self.pewCorp.corp_contact_list(CHAR_ID_CORP)
		self.assertHasMember(result, 'contactList')

	def test_corp_factional_warfare_statistics(self):

		result = self.pewCorp.corp_factional_warfare_statistics(CHAR_ID_CORP)
		self.assertHasMember(result, 'factionID')

	def test_corp_industry_jobs(self):

		result = self.pewCorp.corp_industry_jobs(CHAR_ID_CORP)
		self.assertHasMember(result, 'jobs')

	def test_corp_kill_log(self):

		result = self.pewCorp.corp_kill_log(CHAR_ID_CORP)
		self.assertHasMember(result, 'kills')

	def test_corp_market_orders(self):

		result = self.pewCorp.corp_market_orders(CHAR_ID_CORP)
		self.assertHasMember(result, 'orders')

	def test_corp_medals(self):

		result = self.pewCorp.corp_medals(CHAR_ID_CORP)
		self.assertHasMember(result, 'currentCorporation')

	def test_corp_npc_standings(self):

		result = self.pewCorp.corp_npc_standings(CHAR_ID_CORP)
		self.assertHasMember(result, 'characterNPCStandings')

	def test_corp_wallet_journal(self):

		result = self.pewCorp.corp_wallet_journal(CHAR_ID_CORP)
		self.assertHasMember(result, 'transactions')

	def test_corp_wallet_transactions(self):

		result = self.pewCorp.corp_wallet_transactions(CHAR_ID_CORP)
		self.assertHasMember(result, 'transactions')

if __name__ == "__main__":

	loader = unittest.TestLoader()
	runner = unittest.TextTestRunner(verbosity=2)
	suite = None
	tests = None

	if len(sys.argv) < 2:
		tests = 'all'
	else:
		tests = str(sys.argv[1]).lower()

	if tests == 'core':
		suite = loader.loadTestsFromTestCase(PewCoreTests)
	if tests == 'char':
		suite = loader.loadTestsFromTestCase(PewCharacterTests)
	if tests == 'corp':
		suite = loader.loadTestsFromTestCase(PewCorpTests)
	if tests == 'eve':
		suite = loader.loadTestsFromTestCase(PewEveTests)
	if tests == 'maps':
		suite = loader.loadTestsFromTestCase(PewMapsTests)
	if tests == 'misc':
		suite = loader.loadTestsFromTestCase(PewMiscTests)
	if tests == 'account':
		suite = loader.loadTestsFromTestCase(PewAccountTests)
	elif tests == 'all':
		suite = unittest.TestSuite()

		suite.addTests(loader.loadTestsFromTestCase(PewCoreTests))
		suite.addTests(loader.loadTestsFromTestCase(PewAccountTests))
		suite.addTests(loader.loadTestsFromTestCase(PewCharacterTests))
		suite.addTests(loader.loadTestsFromTestCase(PewCorpTests))
		suite.addTests(loader.loadTestsFromTestCase(PewEveTests))
		suite.addTests(loader.loadTestsFromTestCase(PewMapsTests))
		suite.addTests(loader.loadTestsFromTestCase(PewMiscTests))

	runner.run(suite)
