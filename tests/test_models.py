import random
import unittest.mock
import uuid

from gedcom import models


class RecordTests(unittest.TestCase):
    def test_that_either_record_level_or_parent_is_required(self):
        with self.assertRaises(RuntimeError):
            models.Record()

        r = models.Record(record_level=random.randint(0, 10))
        models.Record(parent=r)

    def test_that_record_level_is_set_from_parent(self):
        parent = models.Record(record_level=0)
        record = models.Record(parent=parent)
        self.assertIs(record.parent, parent)
        self.assertEqual(record.record_level, parent.record_level + 1)

    def test_that_record_level_is_retained_as_is(self):
        record_level = random.randint(10, 20)
        record = models.Record(record_level=record_level)
        self.assertEqual(record.record_level, record_level)

    def test_that_parent_overrides_record_level(self):
        parent = models.Record(record_level=0)
        record = models.Record(
            record_level=random.randint(10, 20), parent=parent)
        self.assertEqual(record.record_level, parent.record_level + 1)

    def test_that_creating_record_adds_new_child(self):
        parent = models.Record(record_level=0)
        record = models.Record(parent=parent)
        self.assertIs(parent.children[0], record)

    def test_that_tag_is_parsed_from_line_data(self):
        # 0 NAME Joe /SCHMOE/
        tag, _, data = str(uuid.uuid4()).upper().partition('-')
        line_data = '{} {}'.format(tag, data)

        record = models.Record.from_line('0 {}'.format(line_data))
        self.assertEqual(record.record_level, 0)
        self.assertIsNone(record.pointer)
        self.assertEqual(record.tag, tag)
        self.assertEqual(record.data, data)
        self.assertEqual(record.line_data, line_data)
        self.assertEqual('{} {} {}\n'.format(record.record_level, tag, data),
                         record.as_string())
        self.assertEqual(1, record.node_count)

    def test_that_pointer_is_parsed_if_present(self):
        # 0 @I14938282@ INDI ...
        tokens = str(uuid.uuid4()).upper().split('-')
        line_data = '@{}@ {}'.format(tokens[0], tokens[1])

        record = models.Record.from_line('0 {}'.format(line_data))
        self.assertEqual(record.record_level, 0)
        self.assertEqual(record.pointer, '@{}@'.format(tokens[0]))
        self.assertEqual(record.tag, tokens[1])
        self.assertEqual(record.data, '')
        self.assertEqual(record.line_data, line_data)
        self.assertEqual(
            '{} @{}@ {}\n'.format(record.record_level, tokens[0], tokens[1]),
            record.as_string())
        self.assertEqual(1, record.node_count)

    def test_that_reference_is_parsed_if_present(self):
        # 2 SOUR ... @S68885317@
        tokens = str(uuid.uuid4()).upper().split('-')
        line_data = '{} {} @{}@'.format(tokens[0], tokens[1], tokens[2])

        record = models.Record.from_line('0 {}'.format(line_data))
        self.assertEqual(record.record_level, 0)
        self.assertIsNone(record.pointer)
        self.assertEqual(record.tag, tokens[0])
        self.assertEqual(record.reference, '@{}@'.format(tokens[2]))
        self.assertEqual(record.data, tokens[1])
        self.assertEqual(record.line_data, line_data)
        self.assertEqual(
            '{} {} {} @{}@\n'.format(record.record_level, tokens[0], tokens[1],
                                     tokens[2]), record.as_string())
        self.assertEqual(1, record.node_count)

    def test_that_children_are_formatted_recursively(self):
        indi = models.Record.from_line('0 @I14938282@ INDI')
        name = indi.add_child(models.Record.from_line('1 NAME Andrew /Bear/'))
        name.add_child(models.Record.from_line('2 GIVN Andrew'))
        name.add_child(models.Record.from_line('2 SURN Bear'))
        self.assertEqual(
            '0 @I14938282@ INDI\n'
            '1 NAME Andrew /Bear/\n'
            '2 GIVN Andrew\n'
            '2 SURN Bear\n',
            indi.as_string(),
        )
        self.assertEqual(4, indi.node_count)
        self.assertEqual(3, name.node_count)
