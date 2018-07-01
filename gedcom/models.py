class Record(object):
    """
    A GEDCOM record.

    :param str line_data: content from the GEDCOM file line following
        the record level.
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

    def __init__(self, line_data, *, record_level=None, parent=None):
        if record_level is None and parent is None:
            raise RuntimeError('either parent or record_level is required')

        self.children = []
        self.parent = None
        self.record_level = record_level
        self.tag = None
        self.data = None

        self.line_data = line_data
        if parent is not None:
            parent.add_child(self)

    @property
    def line_data(self):
        """Content of the GEDCOM line following the record level."""
        return '{} {}'.format(self.tag, self.data)

    @line_data.setter
    def line_data(self, line_data):
        self.tag, space, self.data = line_data.partition(' ')

    def add_child(self, newborn):
        """
        Make `newborn` a new child of `self`.

        :param Record newborn: record to re-parent.

        This method sets the parent of `newborn` to `self`, appends `newborn`
        to :attr:`children`, and sets :attr:`.record_level` to the parent's
        record level plus one.

        """
        newborn.parent = self
        self.children.append(newborn)
        newborn.record_level = self.record_level + 1
