#'!/usr/bin/env python
"""
use stream.inWaiting to check if bytes are available

    A command is a python -> arduino
    A callback is arduino -> python

    Commands are defined by dictionaries with:
        name: [string] namespace name, only used for commands
        id: [int] message id, only used for commands
        params: [list of types, see params.py] if not present, no params
        function: [callable] only used for callbacks

"""

from . import params


class InvalidCommand(Exception):
    pass


def validate_command(cmd):
    if isinstance(cmd, (list, tuple)):
        return [validate_command(c) for c in cmd]
    if 'params' in cmd:
        for p in cmd['params']:
            if p not in params.types:
                raise InvalidCommand("Command %s unknown param %s" % (cmd, p))
    return True


def split_line(l, fs=',', ls=';', esc='/'):
    sline = l.strip()
    start = 0
    if sline[-1] == ls:
        end = len(sline) - 1
    else:
        end = len(sline)
    if end <= start:
        raise Exception("Invalid line %s" % l)
    tokens = []
    while start < end:
        sub_line = sline[start:end]
        if fs not in sub_line:
            tokens.append(sub_line)
            break
        i = sub_line.index(fs)
        if i == 0:
            raise Exception("Invalid line %s" % l)
        while sub_line[i - 1] == esc:  # this fs is escaped
            if len(sub_line) > 1 and sub_line[i - 2] == esc:
                # this is an escaped escape ("0\\,1") so the fs is valid
                break
            sub_sub_line = sub_line[i+1:end]
            if fs not in sub_sub_line:  # this escaped fs was in the last token
                i = end
                break
            i += sub_sub_line.index(fs) + 1
        tokens.append(sub_line[:i])
        start += i + 1
        if len(tokens) > 5:
            raise Exception
    return tokens


def escape(s, fs=',', ls=';', esc='/'):
    if isinstance(s, (tuple, list)):
        return [escape(i, fs, ls, esc) for i in s]
    # TODO optimize this
    cs = [fs, ls, esc, '\x00']
    ns = ""
    for c in s:
        if c in cs:
            ns += esc
        ns += c
    return ns


def unescape(s, esc='/'):
    if isinstance(s, (tuple, list)):
        return [unescape(i, esc) for i in s]
    # TODO optimize this
    ns = ""
    i = 0
    while i < len(s):
        if s[i] == esc:
            i += 1
            if i < len(s):
                ns += s[i]
        else:
            ns += s[i]
        i += 1
    return ns
    #return s.replace(esc, '')


class Messenger(object):
    def __init__(self, stream, cmds, fs=',', ls=';', esc='/'):
        """cmds should be a list"""
        self.stream = stream
        self.fs = fs
        self.ls = ls
        self.esc = esc
        # TODO validate commands
        validate_command(cmds)
        self.cmds = {}
        self.callbacks = {}
        for (i, c) in enumerate(cmds):
            # resolve command name
            if not isinstance(c, dict):
                c = {'name': c}
            else:
                c = c.copy()
            # resolve command id
            c['id'] = i
            # resolve command params
            if 'params' in c:
                ps = []
                for rp in c['params']:
                    ps.append(params.types[rp])
                c['params'] = ps
            self.callbacks[i] = []
            self.cmds[i] = c
            if 'name' in c:
                self.cmds[c['name']] = c

    # stream parsing
    def trigger(self, cmd_id, *args):
        if len(self.callbacks.get(cmd_id, [])) == 0:
            self.unknown()
        else:
            [c(*args) for c in self.callbacks[cmd_id]]

    def next_value(self, until=None, escape=False, n=None):
        if until is None:
            until = self.fs
        print("\t\t%s:%s" % (until, escape))
        s = ""
        while True:
            c = self.stream.read(1)
            if escape and c == self.esc:
                c = self.stream.read(1)
            s += c
            if c in until and n is None:
                break
            if n is not None and len(s) == n:
                break
        print("\tnext_value: %s" % s)
        return s

        if until is None:
            until = self.fs
        c = self.stream.read(1)
        while c[-1] not in until:
            c += self.stream.read(1)
            if escape and c[-1] == self.esc:
                c = self.stream.read(1)
        print("\tnext_value: %s" % c)
        return c

    def next_command(self):
        s = self.next_value(self.fs + self.ls)
        cmd_id = int(s[:-1])
        if s[-1] == self.ls:
            self.trigger(cmd_id)
        cmd = self.cmds[cmd_id]
        ptypes = cmd['params']
        args = []
        print("\tfound %s[%s]: %s" % (cmd_id, cmd.get('name', '?'), ptypes))
        while len(args) < len(ptypes):
            ptype = ptypes[len(args)]
            print("\t\t\t%s" % ptype)
            n = ptype.get('n', None)
            esc = ptype.get('escape', False)
            if n is None:
                s = self.next_value(self.fs + self.ls, esc)
            else:
                s = self.next_value('', esc, n + 1)
            args.append(ptype['from'](s[:-1]))
        print(args, s)
        if s[-1] != self.ls:
            print('\tflushing until ls')
            self.next_value(self.ls)
        self.trigger(cmd_id, *args)

    def process_line(self, l):
        print("\tprocess[%s]: %s" % (len(l), l.strip()))
        #tokens = unescape(
        #    split_line(l, self.fs, self.ls, self.esc),
        #    self.esc)
        tokens = split_line(l, self.fs, self.ls, self.esc)
        cmd_id = int(tokens[0])
        types = self.cmds[cmd_id].get('params', [])
        args = [t['from'](a) for (t, a) in zip(types, tokens[1:])]
        if len(self.callbacks.get(cmd_id, [])) == 0:
            self.unknown(*args)
        else:
            [c(*args) for c in self.callbacks[cmd_id]]

    def read_line(self):
        l = self.stream.read(1)  # TODO optimize this
        esc = l[-1] == self.esc
        while l[-1] != self.ls or esc:
            l += self.stream.read(1)
            if esc:
                esc = False
            else:
                esc = l[-1] == self.esc
        return l

    def send(self, cmd_id, *args):
        #msg = self.fs.join(
        #    (str(cmd_id), ) +
        #    tuple(escape(args, self.fs, self.ls, self.esc))) + self.ls
        msg = self.fs.join((str(cmd_id), ) + args) + self.ls
        print("\tsend[%s]: %s" % (len(msg), msg.strip()))
        self.stream.write(msg)
        # TODO LFCF?

    # callbacks
    def attach(self, func, index):
        self.callbacks[index].append(func)
        return id(func)

    def detach(self, callback_id):
        if not isinstance(callback_id, int):
            callback_id = id(callback_id)
        for cmd_id in self.callbacks:
            if callback_id in self.callbacks[cmd_id]:
                self.callbacks[cmd_id].remove(callback_id)

    def unknown(self, *args):
        pass  # called when an unknown command is received

    # commands
    def call(self, index, *args):
        # can be cmd_id or name
        cmd = self.cmds[index]
        types = cmd.get('params', [])
        self.send(cmd['id'], *[t['to'](a) for (t, a) in zip(types, args)])
