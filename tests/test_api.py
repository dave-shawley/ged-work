import io
import unittest

from gedcom import api


class ParseTests(unittest.TestCase):
    def test_that_empty_file_results_in_empty_database(self):
        db = api.parse(io.BytesIO(b''))
        self.assertEqual(db.record_count, 0)

    def test_that_single_root_record_parses_correctly(self):
        string_data = '\n'.join([
            '0 HEAD',
            '1 SOUR SyniumFamilyTree',
            '2 NAME MacFamilyTree',
            '2 VERS 8.3.5',
            '1 CHAR UTF-8',
            '1 GEDC',
            '2 VERS 5.5.1',
            '2 FORM LINEAGE-LINKED',
            '1 PLAC',
            '2 FORM Place,County,State,Country',
        ])
        db = api.parse(io.BytesIO(string_data.encode('utf-8')))
        self.assertEqual(10, db.record_count)
        self.assertEqual(1, len(db.root_records))
        self.assertEqual(string_data + '\n', db.root_records[0].as_string())

    def test_that_multiple_root_records_parse_correctly(self):
        string_data = '\n'.join([
            '0 @I14938282@ INDI',
            '1 NAME Andrew /Bear/',
            '2 GIVN Andrew',
            '2 SURN Bear',
            '1 SEX M',
            '1 BIRT',
            '2 DATE AFT 1773',
            '2 SOUR @S68885317@',
            '1 SOUR @S68885317@',
            '2 PAGE 17',
            '0 @S68885317@ SOUR',
            '1 TITL Three Bears Of Earl Township, Lancaster County, '
            'Pennsylvania, And Other Early Bears',
            '1 AUTH Jane Evans Best',
            '1 PUBL Pennsylvania Mennonite Heritage',
            '1 DATE Oct 1981',
            '1 PLAC Lancaster, Pennsylvania, United States',
            '1 REFN Volume IV, Number 4',
            '1 REPO @R41744368@',
            '0 @R41744368@ REPO',
            '1 NAME Dave Shawley',
            '1 ADDR daveshawley@gmail.com',
        ])
        db = api.parse(io.BytesIO(string_data.encode('utf-8')))
        self.assertEqual(3, len(db.root_records))
        self.assertEqual(21, db.record_count)

    def test_that_pointers_are_registered_in_db(self):
        string_data = '\n'.join([
            '0 @I14938282@ INDI',
            '1 NAME Andrew /Bear/',
            '2 GIVN Andrew',
            '2 SURN Bear',
            '1 SOUR @S68885317@',
            '2 PAGE 17',
            '0 @S68885317@ SOUR',
            '1 TITL Three Bears Of Earl Township, Lancaster County, '
            'Pennsylvania, And Other Early Bears',
            '1 REPO @R41744368@',
            '0 @R41744368@ REPO',
            '1 NAME Dave Shawley',
            '1 ADDR daveshawley@gmail.com',
        ])

        db = api.parse(io.BytesIO(string_data.encode('utf-8')))
        self.assertIs(db.find_pointer('@I14938282@'), db.root_records[0])
        self.assertIs(db.find_pointer('@S68885317@'), db.root_records[1])
        self.assertIs(db.find_pointer('@R41744368@'), db.root_records[2])
