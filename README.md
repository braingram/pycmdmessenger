Python module for intefacing with the ardunio cmdmessenger library

cmdmessenger messages:

    cmdid, p1, ... pn;

WARNING!!
There appears to be several critical bugs in cmdmessanger with param sending.
These include:
- poor char handling (sending ',' or ';' returns '\x00')
- poor scientific notation handling (1E-3 return 0)
- poor float/double handling (0.001 returns 0)
- poor string handling
It's safest to use:
- params as bytes (byte_float, etc...)
- escaped strings (escaped_string)

fs ',' and sep ';' can be changed (also escape character '\')
params can be text or binary (escaped byte string)
lines may (optionally) be followed by lf & cr
commands might request acknowledge (default id 1)
    should ack be handled by the external program?


types:
    bool
    int16
    int32
    float (can be scientific notation)
    floatsci
    double
    doublesci
    char
    string
    bbool (as bytes)
    bint16
    bint32
    bfloat
    bdouble
    bchar


Basic parsing:
    check_line : can I check if a new line is available
    read_line : wait for line sep
    process_line :


User CmdMessengerTest.ino to test
    kAreYouReady (OnArduinoReady)
        3; -> 2,Arduino ready;
    kAskUsIfReady (OnAskUsIfReady)
        5; -> 3,Asking PC if ready; -> 2; [ack] -> 6,[ack];
    kValuePing (OnValuePing)
    kMultiValuePing (OnMultiValuePing)
    etc ...
