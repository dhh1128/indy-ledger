from collections import OrderedDict
from typing import Dict

from ledger.immutable_store.serializers import MappingSerializer


class CompactSerializer(MappingSerializer):

    def __init__(self, fields: OrderedDict=None):
        self.fields = fields
        self.delimiter = "|"

    def stringify(self, name, record, fields=None):
        fields = fields or self.fields
        if record is None or record == {}:
            return ""
        encoder = fields[name][0] or str
        return encoder(record)

    def destringify(self, name, string, fields=None):
        if not string:
            return None
        fields = fields or self.fields
        decoder = fields[name][1] or str
        return decoder(string)

    def serialize(self, data: Dict, fields=None, toBytes=True):
        fields = fields or self.fields
        records = []

        def _addToRecords(name, record):
            records.append(self.stringify(name, record, fields))

        for name in fields:
            if "." in name:
                nameParts = name.split(".")
                record = data.get(nameParts[0], {})
                for part in nameParts[1:]:
                    record = record.get(part, {})
            else:
                record = data.get(name)
            _addToRecords(name, record)

        encoded = self.delimiter.join(records)
        if toBytes:
            encoded = encoded.encode()
        return encoded

    def deserialize(self, data, fields=None):
        fields = fields or self.fields
        if isinstance(data, (bytes, bytearray)):
            data = data.decode()
        data = data.split(self.delimiter)
        result = {}
        for name in fields:
            if "." in name:
                nameParts = name.split(".")
                ref = result
                for part in nameParts[:-1]:
                    if part not in ref:
                        ref[part] = {}
                    ref = ref[part]
                ref[nameParts[-1]] = self.destringify(name, data.pop(0), fields)
            else:
                result[name] = self.destringify(name, data.pop(0), fields)
        return result
