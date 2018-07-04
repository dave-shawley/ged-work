import io
import random
import unittest.mock
import uuid

from gedcom import api, models


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

    def test_that_pointer_cannot_be_modified(self):
        record = models.Record.from_line('0 PARENT')
        with self.assertRaises(AttributeError):
            record.pointer = '@P1@'

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


class TreeRelatedTests(unittest.TestCase):
    def test_that_add_child_sets_record_level(self):
        root = models.Record.from_line('0 PARENT')
        child = models.Record.from_line('2 CHILD')
        self.assertEqual(2, child.record_level)
        root.add_child(child)
        self.assertEqual(1, child.record_level)

    def test_that_add_child_modifies_parents_list_of_children(self):
        root = models.Record.from_line('0 PARENT')
        child = models.Record.from_line('1 CHILD')
        root.add_child(child)
        self.assertListEqual([child], root.children)

    def test_that_add_child_returns_child(self):
        root = models.Record.from_line('0 PARENT')
        child = models.Record.from_line('1 CHILD')
        result = root.add_child(child)
        self.assertIs(result, child)

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

    def test_find_first_child(self):
        root = models.Record.from_line('0 PARENT')
        first_child = root.add_child(models.Record.from_line('1 FIRST CHILD'))

        self.assertIs(root.find_first_child('FIRST'), first_child)
        self.assertIsNone(root.find_first_child('SECOND'))

    def test_gen_children_by_tag(self):
        line_data = [
            '1 CHILD FIRST\n',
            '1 CHILD SECOND\n',
            '1 CHILD THIRD\n',
        ]
        root = models.Record.from_line('0 PARENT')
        for line in line_data:
            root.add_child(models.Record.from_line(line))
        root.add_child(models.Record.from_line('1 NOTCHILD\n'))

        gen = root.gen_children_by_tag('CHILD')
        for expected in line_data:
            self.assertEqual(next(gen).as_string(), expected)
        with self.assertRaises(StopIteration):
            next(gen)

    def test_find_descendants(self):
        lines = [
            '0 @P@ PARENT',
            '1 @P1@ CHILD',
            '1 @P2@ CHILD',
            '2 @P21@ CHILD',
            '2 @P22@ CHILD',
            '1 @P3@ CHILD',
            '1 @P4@ CHILD',
            '2 @P41@ CHILD',
            '3 @P411@ CHILD',
            '2 @P42@ CHILD',
        ]
        buf = io.BytesIO('\n'.join(lines).encode('utf-8'))
        db = api.parse(buf)
        self.assertEqual(1, len(db.root_records))

        root = db.root_records[0]
        self.assertListEqual(root.find_descendants('NOTTHERE'), [])
        self.assertListEqual(
            [record.pointer for record in root.find_descendants('CHILD')],
            [
                '@P1@',
                '@P2@',
                '@P3@',
                '@P4@',
                '@P21@',
                '@P22@',
                '@P41@',
                '@P42@',
                '@P411@',
            ],
        )

    def test_find_records(self):
        lines = [
            '0 @P@ PARENT',
            '1 @P1@ CHILD',
            '1 @P2@ CHILD',
            '2 @P21@ CHILD',
            '2 @P22@ CHILD',
            '0 @Q@ PARENT',
            '1 @Q1@ CHILD',
            '1 @Q2@ CHILD',
            '2 @Q21@ CHILD',
            '3 @Q211@ CHILD',
            '2 @Q22@ CHILD',
        ]
        buf = io.BytesIO('\n'.join(lines).encode('utf-8'))
        db = api.parse(buf)

        self.assertListEqual(
            [record.pointer for record in db.find_records('CHILD')],
            [
                '@P1@',
                '@P2@',
                '@P21@',
                '@P22@',
                '@Q1@',
                '@Q2@',
                '@Q21@',
                '@Q22@',
                '@Q211@',
            ],
        )

        self.assertListEqual(
            [record.pointer for record in db.find_records('PARENT')],
            ['@P@', '@Q@'],
        )


class DatabaseTests(unittest.TestCase):
    def test_that_write_processes_all_records(self):
        lines = [
            '0 @F59501820@ FAM',
            '1 HUSB @I49205438@',
            '1 WIFE @I72999056@',
            '1 CHIL @I17651300@',
            '2 PEDI birth',
            '1 CHIL @I30378916@',
            '2 PEDI birth',
            '1 CHIL @I29261188@',
            '2 PEDI birth',
            '1 CHIL @I30782740@',
            '2 PEDI birth',
            '1 CHIL @I32365563@',
            '2 PEDI birth',
            '1 CHIL @I22387942@',
            '2 PEDI birth',
            '1 CHIL @I33483194@',
            '2 PEDI birth',
            '1 CHIL @I14938282@',
            '2 PEDI birth',
            '1 CHIL @I79238897@',
            '2 PEDI birth',
        ]
        buf = io.BytesIO('\n'.join(lines).encode('utf-8'))

        record_from_line = models.Record.from_line
        as_string = unittest.mock.Mock(side_effect=models.Record.as_string)
        file_object = io.BytesIO()

        def patched_from_line(*args, **kwargs):
            obj = record_from_line(*args, **kwargs)
            obj.as_string = lambda: as_string(obj)
            return obj

        with unittest.mock.patch('gedcom.api.models.Record') as record_cls:
            record_cls.from_line.side_effect = patched_from_line
            db = api.parse(buf)
            db.write(file_object)

        self.assertEqual(record_cls.from_line.call_count, len(lines))
        self.assertEqual(as_string.call_count, len(lines))
        self.assertEqual(buf.getvalue(), '\n'.join(lines).encode('utf-8'))
