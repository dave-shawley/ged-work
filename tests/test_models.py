import random
import unittest.mock
import uuid

from gedcom import models


class RecordTests(unittest.TestCase):
    @staticmethod
    def get_line_data():
        return str(uuid.uuid4())

    def test_that_either_record_level_or_parent_is_required(self):
        with self.assertRaises(RuntimeError):
            models.Record(self.get_line_data())

        r = models.Record(
            self.get_line_data(), record_level=random.randint(0, 10))
        models.Record(self.get_line_data(), parent=r)

    def test_that_record_level_is_set_from_parent(self):
        parent = models.Record(self.get_line_data(), record_level=0)
        record = models.Record(self.get_line_data(), parent=parent)
        self.assertIs(record.parent, parent)
        self.assertEqual(record.record_level, parent.record_level + 1)

    def test_that_record_level_is_retained_as_is(self):
        record_level = random.randint(10, 20)
        record = models.Record(self.get_line_data(), record_level=record_level)
        self.assertEqual(record.record_level, record_level)

    def test_that_parent_overrides_record_level(self):
        parent = models.Record(self.get_line_data(), record_level=0)
        record = models.Record(
            self.get_line_data(),
            parent=parent,
            record_level=random.randint(10, 20))
        self.assertEqual(record.record_level, parent.record_level + 1)

    def test_that_creating_record_adds_new_child(self):
        parent = models.Record(self.get_line_data(), record_level=0)
        record = models.Record(self.get_line_data(), parent=parent)
        self.assertIs(parent.children[0], record)

    def test_that_tag_is_parsed_from_line_data(self):
        tag, _, data = str(uuid.uuid4()).upper().partition('-')
        line_data = '{} {}'.format(tag, data)
        record = models.Record(line_data, record_level=0)
        self.assertEqual(record.tag, tag)
        self.assertEqual(record.data, data)
        self.assertEqual(record.line_data, line_data)