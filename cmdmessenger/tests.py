#!/usr/bin/env python

import serial

from . import messenger
from . import params

cmds = [
    {'name': 'kCommError'},  # 0
    {'name': 'kComment'},  # 1
    {  # 2
        'name': 'kAcknowledge',
        'params': [str],
    },
    {  # 3
        # sent either from or to arduino, kAcknowledge expected in <1 sec
        'name': 'kAreYouReady',  # to arduino [OnArduinoReady]
        #'params': {  # params to arduino are different than those from
        #    'from': [str],  # TODO support this?
        #},
        'params': [str],
    },
    {  # 4
        'name': 'kError',  # from arduino
        'params': [str],
    },
    {'name': 'kAskUsIfReady'},  # 5, to arduino [OnAskIfReady]
    {  # 6
        # this seems to be used as a reply from the arduino on:
        #   kAskIfReady, with 1 bool param
        #       or
        #   OnUnknownCommand, with 2 params: [str, int16]
        # TODO support vargs?
        'name': 'kYouAreReady',
        #'params': {
        #    'from': [bool],
        #}
        'params': [bool],
    },
    {  # 7
        'name': 'kValuePing',  # to arduino [OnValuePing]
        'params': ['i16', str],  # 2nd param must be pre-packed
    },
    {  # 8
        'name': 'kValuePong',
        'params': [str],  # param must unpacked
    },
    {  # 9
        'name': 'kMultiValuePing',  # to arduino [OnMultiValuePing]
        'params': ['i16', 'i32', 'd'],
    },
    {  # 10
        # response (echo) of kMultiValuePing
        'name': 'kMultiValuePong',
        'params': ['i16', 'i32', 'd'],
    },
    {'name': 'kRequestReset'},  # 11, to arduino [OnRequestReset]
    {  # 12
        'name': 'kRequestResetAcknowledge',
        'params': [str],
    },
    {  # 13
        'name': 'kRequestSeries',  # to arduino [OnRequestSeries]
        'params': ['i16', 'f'],
    },
    {  # 14
        'name': 'kReceiveSeries',
        'params': ['f'],
    },
    {  # 15
        'name': 'kDoneReceiveSeries',
        'params': [str],
    },
    {  # 16
        # send a series of numbers (each using kSendSeries)
        # when number sent == the value of params[0]
        #   kAckSendSeries will be sent
        'name': 'kPrepareSendSeries',  # to arduino [OnPrepareSendSeries]
        'params': ['i16'],  # seriesLength
    },
    {  # 17
        'name': 'kSendSeries',  # to arduino [OnSendSeries]
        'params': ['f'],
    },
    {  # 18
        'name': 'kAckSendSeries',
        'params': [str],
    },
]

pptypes = [
    'kBool',  # 0
    'kInt16',  # 1
    'kInt32',  # 2
    'kFloat',  # 3
    'kFloatSci',  # 4
    'kDouble',  # 5
    'kDoubleSci',  # 6
    'kChar',  # 7
    'kString',  # 8
    'kBBool',  # 9
    'kBInt16',  # 10
    'kBInt32',  # 11
    'kBFloat',  # 12
    'kBDouble',  # 13
    #'kBChar',  # 14
    #'kEscString',  # 15
]

# TODO bug in cmdMessenger, cannot send ',' '/' or ';' to arduino
# TODO char cannot be ',' or ';', same with BChar
# TODO string sending is also screwed up by ',' and ';'
# TODO scientific notation with -exponents are truncated
ppvalues = {
    'kBool': [True, False],
    'kInt16': [0, 128, 256, 32767, -32767],
    'kInt32': [0, 256, -256, 32767, -32767, 2147483647, -2147483647],
    #'kFloat': [0., -1., 1., -1E-3, 1E-3, -1E6, 1E6],
    'kFloat': [0., -1., 1., -0.01, 0.01, -10000, 10000],
    'kFloatSci': [0., -1., 1., -1E-1, 1E-1, -1E2, 1E2],
    'kDouble': [0., -1., 1., -1E-1, 1E-1, -1E2, 1E2],
    'kDoubleSci': [0., -1., 1., -1E-1, 1E-1, -1E2, 1E2],
    #'kChar': [chr(0), chr(128), chr(255), ',', ';', '\n', '\r', '\\'],
    'kChar': [chr(0), chr(128), chr(255), '/', '\n', '\r'],
    #'kString': ['hi', 'hello', 'how are things', '\x00\\\r\n,;'],
    'kString': ['hi', 'hello', 'how are things'],
}
ppvalues['kBBool'] = ppvalues['kBool']
ppvalues['kBInt16'] = ppvalues['kInt16']
ppvalues['kBInt32'] = ppvalues['kInt32']
ppvalues['kBFloat'] = ppvalues['kFloat']
ppvalues['kBDouble'] = ppvalues['kDouble']


def setup(port='/dev/ttyUSB0'):
    s = serial.Serial(port, 115200)
    return messenger.Messenger(s, cmds)


def wrap(f, cmd_id):
    def wrapped(*args):
        f(cmd_id, *args)
    return wrapped


class Expect(object):
    def __init__(self, messenger):
        self.messenger = messenger
        self.last_message = None
        self.messages = []
        self.callbacks = []
        self.attach_callbacks()

    def attach_callbacks(self):
        for c in self.messenger.cmds:
            cmd_id = self.messenger.cmds[c]['id']
            self.callbacks.append(
                self.messenger.attach(wrap(self.log, cmd_id), cmd_id))
            #self.callbacks.append(self.messenger.attach(
            #    lambda f=self.log, cmd_id=cmd_id, *args: f(cmd_id, *args),
            #    cmd_id))

    def log(self, cmd_id, *args):
        msg = {'id': cmd_id, 'args': args}
        self.last_message = msg
        self.messages.append(msg)

    def update(self):
        self.messenger.next_command()
        #l = self.messenger.read_line()
        #self.last_line = l
        #self.messenger.process_line(l)

    def expect(self, cmd_id, *args):
        self.update()
        if not isinstance(cmd_id, int):
            cmd_id = self.messenger.cmds[cmd_id]['id']
        if self.last_message['id'] != cmd_id:
            return False, "id: %s != %s" % (self.last_message['id'], cmd_id)
        if len(args) == 0:
            return True, ""
        if len(args) != len(self.last_message['args']):
            return False, \
                "len(args): %s != %s" % \
                (len(self.last_message['args']), len(args))
        for (i, (ea, a)) in enumerate(zip(args, self.last_message['args'])):
            if ea != a:
                return False, "arg[%s]: %s != %s" % (i, a, ea)
        return True, ""

    def __call__(self, cmd_id, *args):
        success, msg = self.expect(cmd_id, *args)
        if not success:
            raise Exception(msg)
        return success, msg

    def detach_callbacks(self):
        for c in self.callbacks:
            self.messenger.detach(c)
        self.callbacks = []

    def __del__(self):
        self.detach_callbacks()


def flush(m):
    pass


def acknowledge_tests(m):
    expect = Expect(m)
    # send 'kAreYouReady', expect back 'kAcknowledge'
    m.call('kAreYouReady')
    expect('kAcknowledge')
    print("kAreYouReady test passed")
    # send 'kAskUsIfReady', expect back 'kAreYouReady', send back
    m.call('kAskUsIfReady')
    expect('kAreYouReady')
    #   'kAcknowledge', expect back 'kYouAreReady'
    m.call('kAcknowledge')
    expect('kYouAreReady')
    print("kAskUsIfReady test passed")
    expect.detach_callbacks()


def eq(a, b):
    if isinstance(a, float):
        if a - b < 1E-8:
            return True
        return False
    return a == b


def escape(s, chars, esc):
    r = ""
    for c in s:
        if c in chars:
            r += esc
        r += c
    return r


def unescape(s, esc='/'):
    r = ""
    e = False
    for c in s:
        if not e and c == esc:
            e = True
        else:
            r += c
            e = False
    return r


def value_tests(m):
    expect = Expect(m)
    for (ti, pptype) in enumerate(pptypes):
        for v in ppvalues[pptype]:
            # encode value
            t = pptype.lower()[1:]  # remove leading k
            ptype = params.types[t]
            ev = ptype['to'](v)
            if ptype.get('escape', False):
                ev = escape(ev, m.ls + m.fs + '\x00', m.esc)
            m.call('kValuePing', ti, ev)
            #expect('kValuePong', ev)
            expect('kValuePong')
            # decode value
            if ptype.get('escape', False):
                rv = unescape(expect.last_message['args'][0], m.esc)
            else:
                rv = expect.last_message['args'][0]
            dv = ptype['from'](rv)
            if not eq(dv, v):
                raise Exception("%s: decoded value %s != %s" % (pptype, dv, v))
        print("kValuePing[%s] test passed" % (pptype))
    expect.detach_callbacks()


def multiple_arguments_tests(m):
    # ->kMultiValuePing <-kMultiValuePong
    pass


def transfer_speed_tests(m):
    # send series of N [10000] floats, benchmark transfer speed
    pass


def run(m):
    for test in (
            acknowledge_tests, value_tests, multiple_arguments_tests,
            transfer_speed_tests):
        flush(m)
        test(m)
        print("%s passed" % test.__name__)


def test():
    m = setup()
    run(m)
