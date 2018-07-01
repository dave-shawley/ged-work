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
        self.pointer = None
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

        obj.pointer, obj.reference = None, None
        obj.tag, obj.data = None, None

        remaining = line_data.strip()
        if remaining.startswith('@'):
            obj.pointer, space, remaining = remaining.partition(' ')

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

    def as_string(self):
        """Format the record and children as a GEDCOM-ready string."""
        lines = ['{0.record_level} {0.line_data}\n'.format(self)]
        lines.extend(child.as_string() for child in self.children)
        return ''.join(lines)
