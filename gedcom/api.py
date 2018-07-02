from gedcom import models


def parse(file_object):
    """
    Parse a GEDCOM file into a database instance.

    :param file_object: an object instance that looks and acts like
        a :class:`file` instance
    :returns: a database instance
    :rtype: gedcom.models.Database

    """
    db = models.Database()
    parse_stack = []

    for line_number, line_data in enumerate(file_object):
        record = models.Record.from_line(line_data.decode('utf-8'))
        db.register_record(record)

        if record.record_level == 0:
            if parse_stack:
                db.add_root_record(parse_stack[0])
                parse_stack.clear()
        elif record.record_level > parse_stack[-1].record_level:
            parse_stack[-1].add_child(record)
        elif record.record_level == parse_stack[-1].record_level:
            parse_stack[-1].parent.add_child(record)
        else:
            while parse_stack[-1].record_level >= record.record_level:
                parse_stack.pop()
            parse_stack[-1].add_child(record)
        parse_stack.append(record)

    if parse_stack:
        db.add_root_record(parse_stack[0])

    return db
