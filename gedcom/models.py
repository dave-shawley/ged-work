import weakref


class Record(object):
    """
    A GEDCOM record.

    :keyword int record_level: depth of the GEDCOM record.  This is
        zero at the root and increases by one for each additional
        level.
    :keyword Record parent: parent of this record

    When creating a new record, either the `parent` or the `record_level`
    is required.  If both are provided, then the `record_level` is ignored
    in deferrence to `parent.record_level`.  If neither are specified, then
    a :class:`RuntimeError` will be raised.

    .. attribute:: children

       Possibly empty list of child records.

    .. attribute:: parent

       Parent record or :data:`None`.

    .. attribute:: record_level

       Depth of this record.

    .. attribute:: tag

       Parsed GEDCOM tag.

    .. attribute:: data

       Portion of the GEDCOM record following the tag.

    """

    def __init__(self, *, record_level=None, parent=None):
        if record_level is None and parent is None:
            raise RuntimeError('either parent or record_level is required')

        self.children = []
        self.parent = None
        self.record_level = record_level
        self._pointer = None
        self.tag = None
        self.reference = None
        self.data = None

        if parent is not None:
            parent.add_child(self)

    @property
    def line_data(self):
        """Content of the GEDCOM line following the record level."""
        parts = []
        if self.pointer:
            parts.append(self.pointer)
        parts.append(self.tag)
        if self.data:
            parts.append(self.data)
        if self.reference:
            parts.append(self.reference)
        return ' '.join(parts)

    @property
    def node_count(self):
        """The number of nodes rooted at this record."""
        return 1 + sum(child.node_count for child in self.children)

    @property
    def pointer(self):
        """Possibly empty GEDCOM pointer ID of this record."""
        return self._pointer

    @classmethod
    def from_line(cls, raw_line, parent=None):
        """
        Create a record from a GEDCOM line.

        :param str raw_line: raw GEDCOM line with or without line terminator
        :param Record parent: optional parent of the new node
        :returns: a parsed record
        :rtype: Record

        """
        record_level, space, line_data = raw_line.strip().partition(' ')
        obj = cls(record_level=int(record_level), parent=parent)

        remaining = line_data.strip()
        if remaining.startswith('@'):
            obj._pointer, space, remaining = remaining.partition(' ')

        obj.tag, space, remaining = remaining.partition(' ')

        remaining, space, maybe_ref = remaining.rpartition(' ')
        if maybe_ref.startswith('@') and maybe_ref.endswith('@'):
            obj.reference = maybe_ref
        elif maybe_ref:
            remaining = ' '.join([remaining, maybe_ref])

        obj.data = remaining.strip()

        return obj

    def add_child(self, newborn):
        """
        Make `newborn` a new child of `self`.

        :param Record newborn: record to re-parent.
        :returns: `newborn`
        :rtype: Record

        This method sets the parent of `newborn` to `self`, appends `newborn`
        to :attr:`children`, and sets :attr:`.record_level` to the parent's
        record level plus one.

        """
        newborn.parent = self
        self.children.append(newborn)
        newborn.record_level = self.record_level + 1
        return newborn

    def find_first_child(self, tag):
        """
        Find the first child tagged as `tag`.

        :param str tag: GEDCOM tag to search for
        :return: a :class:`.Record` instance or :data:`None`
        :rtype: Record

        """
        for child in self.children:
            if child.tag == tag:
                return child

    def gen_children_by_tag(self, tag):
        """
        Generate children tagged by `tag` in order.

        :param str tag: GEDCOM tag to search for
        :return: a generator that generates :class:`.Record` instances
            in order

        """
        for child in self.children:
            if child.tag == tag:
                yield child

    def find_descendants(self, tag):
        """
        Find all descendants tagged with `tag`.

        :param str tag: GEDCOM tag to search for
        :return: a possibly empty :class:`list` of :class:`.Record` instances
        :rtype: list

        """
        matched = []
        queue = self.children[:]
        while queue:
            child = queue.pop(0)
            if child.tag == tag:
                matched.append(child)
            queue.extend(child.children)
        return matched

    def as_string(self):
        """Format the record and children as a GEDCOM-ready string."""
        lines = ['{0.record_level} {0.line_data}\n'.format(self)]
        lines.extend(child.as_string() for child in self.children)
        return ''.join(lines)


class Database(object):
    """
    Represents a database of parsed GEDCOM records.

    You should not create instances of this class yourself.  Call
    :func:`gedcom.api.parse` to create an instance instead.

    """

    def __init__(self):
        super().__init__()
        self.root_records = []
        self._pointers = weakref.WeakValueDictionary()

    def add_root_record(self, record):
        """
        Add a new root record.

        :param Record record: the record to add.

        """
        self.root_records.append(record)

    @property
    def record_count(self):
        """Total number of records in the database."""
        return sum(r.node_count for r in self.root_records)

    def find_pointer(self, pointer):
        """
        Find a node by it's GEDCOM pointer.

        :param str pointer: GEDCOM pointer to look up
        :return: the :class:`.Record` or :data:`None`
        :rtype: Record

        """
        return self._pointers.get(pointer, None)

    def register_record(self, record):
        """
        Register `record` in appropriate lookup maps.

        :param Record record: the record to process

        """
        if record.pointer:
            self._pointers[record.pointer] = record

    def find_records(self, tag):
        """
        Returns all records tagged with `tag`.

        :param str tag: GEDCOM tag to search for
        :return: a possibly empty :class:`list` of :class:`.Record` instances

        """
        matched = []
        for record in self.root_records:
            if record.tag == tag:
                matched.append(record)
            matched.extend(record.find_descendants(tag))
        return matched
