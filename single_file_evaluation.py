#!/usr/bin/env python
'''
testing script for launching deobfuscation of the file. In addition, it removes unicode null characters, empty php tags and additional blanklines caused by the deobfuscation.
It prints a json objects
@author: Maurizio Abba
'''

import library.transformer as transformer
import sys
import json
import library.HTMLremover as HTMLremover

if len(sys.argv)!=2:
    print "Usage: %s php_file" % sys.argv[0]
    sys.exit(1)

try:
    f = open(sys.argv[1])
except IOError as err:
    print "PANIC! file %s does not exist" %(sys.argv[1])
    sys.exit(1)

#print os.geteuid()

before_size=sys.getsizeof(f.read())
f.close()
text, times_evaled, error = transformer.general_deobfuscate(sys.argv[1])
t = HTMLremover.remove_unicode_null(text)
t = HTMLremover.remove_empty_php_tags(t)
t = HTMLremover.remove_blanklines(t)
after_size=sys.getsizeof(t)
#print "Before: %s" %(str(before_size)) 
#print "After: %s" %(str(after_size)) 
#s="Error: "
#if error:
#    s+="YES"
#else:
#    s+="NO"
#print s
#print "Times_evaled: %s" %(str(times_evaled))
#print "File:\n"
#print t
#f=open("/tmp/testDecoding","w")
#f.write(t)
print json.dumps ({
    "beforeSize":before_size,
    "afterSize":after_size,
    "error":error,
    "timesEvaled":times_evaled,
    "file_content":unicode(t, errors="replace")})
