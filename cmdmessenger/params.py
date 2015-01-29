#!/usr/bin/env python
"""

'to': to arduino (python -> arduino)
'from': from arduino (arduino -> python)

types [length]:
    bool [1]
    int16 [?]
    int32 [?]
    float (can be scientific notation) [?]
    floatsci [?]
    double [?]
    doublesci [?]
    char [1]
    string [?]

    bbool (as bytes) [1]
    bint16 [2]
    bint32 [4]
    bfloat [4]
    bdouble [4]
    bchar [1]
"""

import struct


def tosci(v):
    s = "%.2E" % v
    if 'E' not in s:
        return s
    if s[-2] == '0' and s[-3] in '+-':
        return s[:-2] + s[-1]
    return s

bool_to_string = lambda v: str(int(v))
bool_from_string = lambda s: bool(int(s))
bool_to_bytes = lambda v: struct.pack('<?', v)
bool_from_bytes = lambda s: struct.unpack('<?', s)[0]

#int16_to_string = lambda v: str(int(v) & 0xFFFF)
int16_to_string = lambda v: str(int(v))
int16_from_string = lambda s: int(s)
#int16_to_bytes = lambda v: struct.pack('<h', v & 0xFFFF)
int16_to_bytes = lambda v: struct.pack('<h', v)
int16_from_bytes = lambda s: struct.unpack('<h', s)[0]

#int32_to_string = lambda v: str(int(v) & 0xFFFFFFFF)
int32_to_string = lambda v: str(int(v))
int32_from_string = lambda s: int(s)
#int32_to_bytes = lambda v: struct.pack('<i', v & 0xFFFFFFFF)
int32_to_bytes = lambda v: struct.pack('<i', v)
int32_from_bytes = lambda s: struct.unpack('<i', s)[0]

float_to_string = lambda v: str(float(v))  # TODO precision?
float_from_string = lambda s: float(s)
float_to_bytes = lambda v: struct.pack('<f', v)
float_from_bytes = lambda s: struct.unpack('<f', s)[0]

floatsci_to_string = lambda v: tosci(v)
floatsci_from_string = lambda s: float(s)
#floatsci_to_bytes =
#floatsci_from_bytes =

doublesci_to_string = lambda v: tosci(v)
doublesci_from_string = lambda s: float(s)
#doublesci_to_bytes =
#doublesci_from_bytes =

double_to_string = lambda v: str(float(v))
double_from_string = lambda s: float(s)
double_to_bytes = lambda v: struct.pack('<f', v)
double_from_bytes = lambda s: struct.unpack('<f', s)[0]

char_to_string = lambda v: v[0]
char_from_string = lambda s: s[0]
#char_to_bytes = lambda v: v[0]
#char_from_bytes = lambda s: s[0]

string_to_string = lambda v: v
string_from_string = lambda s: s
#string_to_bytes = lambda v: v
#string_from_bytes = lambda s: s


types = {
    'bool':  {'to': bool_to_string, 'from': bool_from_string, 'n': 1},
    'int16': {'to': int16_to_string, 'from': int16_from_string},
    'int32': {'to': int32_to_string, 'from': int32_from_string},
    'float': {'to': float_to_string, 'from': float_from_string},
    'double': {'to': double_to_string, 'from': double_from_string},
    'char': {'to': char_to_string, 'from': char_from_string},
    'string': {'to': string_to_string, 'from': string_from_string},
    'escaped_string': {
        'to': string_to_string, 'from': string_from_string,
        'escaped': True},
    'float_sci': {
        'to': floatsci_to_string, 'from': floatsci_from_string},
    'double_sci': {
        'to': doublesci_to_string, 'from': doublesci_from_string},
    # bytes
    'byte_bool': {
        'to': bool_to_bytes, 'from': bool_from_bytes, 'n': 1,
        'escape': True},
    'byte_int16': {
        'to': int16_to_bytes, 'from': int16_from_bytes,
        'escape': True},
    'byte_int32': {
        'to': int32_to_bytes, 'from': int32_from_bytes,
        'escape': True},
    'byte_float': {
        'to': float_to_bytes, 'from': float_from_bytes,
        'escape': True},
    'byte_double': {
        'to': double_to_bytes, 'from': double_from_bytes,
        'escape': True},
}

# add shortcuts
types['b'] = types['bool']
types['i'] = types['int16']
types['i16'] = types['int16']
types['i32'] = types['int32']
types['f'] = types['float']
types['d'] = types['double']
types['c'] = types['char']
types['s'] = types['string']
types['es'] = types['escaped_string']
types['fs'] = types['float_sci']
types['ds'] = types['double_sci']

types['floatsci'] = types['float_sci']
types['doublesci'] = types['double_sci']

types['bbool'] = types['byte_bool']
types['bint16'] = types['byte_int16']
types['bint32'] = types['byte_int32']
types['bfloat'] = types['byte_float']
types['bdouble'] = types['byte_double']

types['bb'] = types['byte_bool']
types['bi'] = types['byte_int16']
types['bi16'] = types['byte_int16']
types['bi32'] = types['byte_int32']
types['bf'] = types['byte_float']
types['bd'] = types['byte_double']

types[bool] = types['bool']
types[int] = types['int16']
types[float] = types['float']
types[str] = types['string']
