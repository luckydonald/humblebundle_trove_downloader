# log in to humble bundle and copy from the website inspector in safari, the the cookies section in the storage tab there.
# highlight the cookie, press cmd+C, paste the full thing here into a string:
COOKIE_STRINGS = [
    "_simpleauth_sess	eyJ1c2VyX2lkIjo1MzE4MDc4MTU4fwMDk2LCJpsZCI6IjJZcnVuZ32352JhdXRoX3RpbWUiOjE1NzAfRKVMzB9|32485324|8d0cd113dasda2dc9624364eaf8595	www.humblebundle.com	/	4/6/2020, 5:52:11 PM	160 B	✓	✓	",
]

COOKIES = {}
COOKIE_JAR = {}

for cookie_name in COOKIE_STRINGS:
    COOKIES[cookie_name] = {}
    COOKIES[cookie_name]['name'], COOKIES[cookie_name]['value'], COOKIES[cookie_name]['domain'], COOKIES[cookie_name]['path'], COOKIES[cookie_name]['expires'], COOKIES[cookie_name]['size'], COOKIES[cookie_name]['secure'], COOKIES[cookie_name]['http_only'], COOKIES[cookie_name]['same_site'] = COOKIE_STRINGS[cookie_name].split("\t")
    COOKIES[cookie_name] = {k: v if k not in ('secure', 'http_only', 'same_site') else v == '✓' for k, v in COOKIES[cookie_name].items()}
    COOKIE_JAR[COOKIES[cookie_name]['name']] = COOKIES[cookie_name]['value']
# end for

print('COOKIE_JAR = ' + repr(COOKIE_JAR))
