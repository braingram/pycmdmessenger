#!/usr/bin/env python

import serial

from . import messenger

cmds = [
    {'name': 'kCommError'},
    {'name': 'kComment'},
    {
        'name': 'kAcknowledge',
        'params': [str],
    },
    {
        # sent either from or to arduino, kAcknowledge expected in <1 sec
        'name': 'kAreYouReady',  # to arduino [OnArduinoReady]
        #'params': {  # params to arduino are different than those from
        #    'from': [str],  # TODO support this?
        #},
        'params': [str],
    },
    {
        'name': 'kError',  # from arduino
        'params': [str],
    },
    {'name': 'kAskUsIfReady'},  # to arduino [OnAskIfReady]
    {
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
    {
        'name': 'kValuePing',  # to arduino [OnValuePing]
        'params': ['i16', str],  # 2nd param must be pre-packed
    },
    {
        'name': 'kValuePong',
        'params': [str],  # param must unpacked
    },
    {
        'name': 'kMultiValuePing',  # to arduino [OnMultiValuePing]
        'params': ['i16', 'i32', 'd'],
    },
    {
        # response (echo) of kMultiValuePing
        'name': 'kMultiValuePong',
        'params': ['i16', 'i32', 'd'],
    },
    {'name': 'kRequestReset'},  # to arduino [OnRequestReset]
    {
        'name': 'kRequestResetAcknowledge',
        'params': [str],
    },
    {
        'name': 'kRequestSeries',  # to arduino [OnRequestSeries]
        'params': ['i16', 'f'],
    },
    {
        'name': 'kReceiveSeries',
        'params': ['f'],
    },
    {
        'name': 'kDoneReceiveSeries',
        'params': [str],
    },
    {
        # send a series of numbers (each using kSendSeries)
        # when number sent == the value of params[0]
        #   kAckSendSeries will be sent
        'name': 'kPrepareSendSeries',  # to arduino [OnPrepareSendSeries]
        'params': ['i16'],  # seriesLength
    },
    {
        'name': 'kSendSeries',  # to arduino [OnSendSeries]
        'params': ['f'],
    },
    {
        'name': 'kAckSendSeries',
        'params': [str],
    },
]

pptypes = [
    'kBool', 'kInt16', 'kInt32', 'kFloat', 'kFloatSci', 'kDouble',
    'kDoubleSci', 'kChar', 'kString', 'kBBool', 'kBInt16', 'kBInt32',
    'kBFloat', 'kBDouble', 'kBChar', 'kEscString']


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
        self.last_line = None
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
        l = self.messenger.read_line()
        self.last_line = l
        self.messenger.process_line(l)

    def expect(self, cmd_id, args=None):
        self.update()
        if not isinstance(cmd_id, int):
            cmd_id = self.messenger.cmds[cmd_id]['id']
        if self.last_message['id'] != cmd_id:
            return False, "id: %s != %s" % (self.last_message['id'], cmd_id)
        if args is None:
            return True, ""
        if len(args) != len(self.last_message['args']):
            return False, \
                "len(args): %s != %s" % \
                (len(self.last_message['args']), len(args))
        for (i, (ea, a)) in enumerate(zip(args, self.last_message['args'])):
            if ea != a:
                return False, "arg[%s]: %s != %s" % (i, a, ea)
        return True, ""

    def __call__(self, cmd_id, args=None):
        success, msg = self.expect(cmd_id, args)
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


def value_tests(m):
    # ->kValuePing <-kValuePong for all types
    pass


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
