import re
import sys
import pexpect
import tempfile
import os
from collections import defaultdict
import base64

TIMEOUT = 45

arrPHPGlobVars = ['$HTTP_GET_VARS', '$_GET', '$_SERVER', '$_POST', '$_FILES', '$_COOKIE', '$_SESSION', '$_REQUEST', '$_ENV', '$HTTP_RAW_POST_DATA', '$argc', '$argv', "mysql_query"]


DEBUG=True

def deobfuscatePHP(FILE):
    """take as input the name of a file and try to deobfuscate it using evalhook.so extension"""
    child = pexpect.spawn(
        'php -d extension=evalhook.so "%s"' % (FILE), timeout=TIMEOUT)


    #this file should be a temporary one
    fdDecoded, decodedName = tempfile.mkstemp()
    decoded=os.fdopen(fdDecoded,"w")
    child.logfile = decoded
    before, after = 0, 0
    rounds = 0
    idx = child.expect_exact(['Do you want to allow execution? [y/N]',
                             pexpect.EOF, pexpect.TIMEOUT])
    if idx == 0:
        child.sendline('y')
        before = after
        after = decoded.tell()
#        #print "Now idx=%d" % after
        rounds += 1
    else:
        if after == 0:
            after = decoded.tell()
    #print "DBG before: %d, after: %d" % (before, after)
    try:
        child.close(force=True)
    except:
        print "ERROR: closing child process failed (%s)" % FILE

    #close handle of temporary file DON'T REMOVE IT
    decoded.close()
    if rounds == 0:
        # deobfuscated==original
        os.remove(decodedName)
        return open(FILE, "r").read(), False
    else:
        # obfuscated: get last piece of code before execution
        #open the same file written before using the name
        fo = open(decodedName,"r")
        output = fo.read()
#       close and remove the temporary file
        fo.close()
        os.remove(decodedName)
        last = output[before:]
        start, end = 0, 0
        step = 0
        for line in last.split('\n'):
            if step == 0:
                start += len(line) + 1
                if line.strip() == 'Script tries to evaluate the following string.':
                    step = 1
            elif step == 1:
                start += len(line) + 1
                if line.strip() == '----':
 #                   #print "start at: %s" % last[start:start+40]
                    step = 2
                    end = start
            elif step == 2:
                if line.strip() == '----':
                    endbuf = end + len(line) + 1
                    step = 3
                else:
                    end += len(line) + 1
            elif step == 3:
                if line.strip() == 'Do you want to allow execution? [y/N]':
                        step = 4
#                        #print "End at: %s" % last[end-40:end]
                        break
                else:
                    # back to step2
                    step = 2
                    # restart from endbuf
                    end = endbuf + len(line) + 1
        if step != 4:
            # probably ended in a TIMEOUT: #print warning and skip (save
            # original file)
	    return open(FILE, "r").read(), True
        else:
            return last[start:end], False




def splitter(orig, prog, noPHP=False):
    """split a file according to the prog regex, and send each part to the deobfuscate"""
    def addVariables (used, t, elem):
        listOfVarsToBeAdded=[]
        added=False
        for possible_var in find_prog.finditer(t):
            if possible_var.group(0) in DICT_VARS:
                for el in DICT_VARS[possible_var.group(0)]:
                    #add only istances of the variables that come before the evaled thing
                    if el["position"]<elem.start() and el not in used:
                        listOfVarsToBeAdded.append(el)
                        used.append(el)
                        added=True
        listOfVarsToBeAdded.sort(key=lambda dic: dic["position"])
        tRet=""
        for el in listOfVarsToBeAdded:
            st = el["raw_data"]
#            res_find_at = regex_find_at.search(st)
#            try:
#                if res_find_at.group(1)!='@':
#                    st=st[:res_find_at.start(1)]+"@"+st[res_find_at.start(1):]
#            except AttributeError:
#                pass
            if st[-1]!=";": st+=";"
            tRet = st+"\n"+tRet
        return used, tRet, added


    def validateEvaluation(totText, eval_match, dic):
        #if any(var in totText for var in arrPHPGlobVars):
        #    return False
        for possible_var in find_prog.finditer(eval_match.group(0)):
            if possible_var.group(0) not in dic:
                return False
            else:
                if not any(element["position"]< eval_match.start() for element in dic[possible_var.group(0)]):
                    return False
        return True

    def decode_hext(orig):
        '''decode any hex encoded character it finds inside the file'''
        def replac(elem):
            return elem.group(1).decode("hex")
        t=re.sub(r'\\[xX]([a-fA-F0-9][a-fA-F0-9])',replac,orig)
        return t
    
    if DEBUG:
        print "Begin to split"
#        print "*" * 160
#        print orig
#        print "*" * 160
    #for m in re.finditer(var_nums, text):
    #    t = {"position": m.start(), "source": m.group(1), "element": m.group(2), "raw_data" : m.group(0)}
    #    if t not in DICT_VARS[m.group(1)]: DICT_VARS[m.group(1)].append( t)
    #    DICT_OF_RAW_DATA[m.group(1)].append(m.group(0))
        #print "var_nums aggiunge"
        #print DICT_VARS[m.group(1)]

    text = decode_hext(orig)
    result = False
    err=False
    usedTot=[]
    #creation of the temporary file where to store informations
    fdPreg, tfname = tempfile.mkstemp()
    tf = os.fdopen(fdPreg, "r")
    tf.close()
    off=0
    found=True
    while found:
        found=False
        elem = prog.search(text, off)
    #for elem in re.finditer(prog, text):
#        if not any(var in elem.group(0) for var in arrPHPGlobVars):
        
        if elem:
            found=True
            off = elem.start()+2
            DICT_VARS = defaultdict(list)
            DICT_OF_RAW_DATA = defaultdict(list)
            used=[]
            #inserted, DICT_VARS, DICT_OF_RAW_DATA = createDicOfVars(DICT_VARS, DICT_RAW_DATA, text)
            #for key in DICT_VARS:
            #    for element in DICT_VARS[key]:
            #        while inserted:
            #            inserted, DICT_VARS, DICT_OF_RAW_DATA = createDicOfVars(DICT_VARS, DICT_RAW_DATA, DICT_VARS[key]["element"])
            listOfText=[{"offset":0,"text": text}]
            for textVars in listOfText:
                for m in var_vars.finditer(textVars["text"]):
                # if not any(var in m.group(0) for var in arrPHPGlobVars):
                    t = {"position": m.start()+textVars["offset"], "end": m.end()+textVars["offset"], "source": m.group(1), "element": m.group(2), "raw_data" : m.group(0)}
                    if t not in DICT_VARS[m.group(1)]:
                        DICT_VARS[m.group(1)].append( t)
                        listOfText.append({"offset": m.start(2), "text": m.group(2)})
                    DICT_OF_RAW_DATA[m.group(1)].append(m.group(0))
            eval_t = elem.group(0)
            if DEBUG:
                print text
                print "-"*160
                print "Matching: %s at %d (pos %d)" %(eval_t, elem.start(),elem.pos)
                print "-"*160

            t = eval_t[:]
            #look if inside the eval thing there is a variable
            #if it's inside we put all the instances of the variable inside the file
            used, textOfVars, edited = addVariables ([], t, elem)
            while edited:
                used, textOfVars, edited = addVariables(used, textOfVars, elem)            
            used.sort(key=lambda dic: dic["position"])
            #for i in used:
            #    print used
            for ins in reversed(used):
                st= ins["raw_data"]
                if any(var in st for var in arrPHPGlobVars):
                    continue
                res_find_at = regex_find_at.search(st)
                try:
                    if res_find_at.group(1)!='@':
                        st=st[:res_find_at.start(1)]+"@"+st[res_find_at.start(1):]
                except AttributeError:
                    pass

                if st[-1]!=";": st+=";"
                t = st+"\n"+t
            t = "<?php\n" + t + "\n?>"
            if DEBUG:
#                print "dict_vars:"
#                for ev in DICT_VARS["$eval"]:
#                    print ev["position"]
#                print "\n"+str(len(used))+"\n"
#                print "\n"*10
#                print t
#                for el in DICT_VARS:
#                    print DICT_VARS[el]
                print "\n"*10
                print "Evaluation is"
                print t
            if validateEvaluation(t, elem, DICT_VARS): 
        #       this should be a temporary file
                tf = open(tfname, "w")    
                tf.write(t)
                tf.close()
                    # close the handle DON'T REMOVE IT
                sub, err = deobfuscatePHP(tfname)
                #this is a workaround for wrong treatment of array->string from evalhook
                if sub == "Array\r\n":
                    sub=""
                if sub:
                    if sub[0] == '\r' or sub[0] == '\n':
                        sub = sub[2:]
                    if sub != t:
                        if DEBUG:
                            print "Done! start from: " + str(elem.start()) + " to: " + str(elem.end())
                            print eval_t
                            print "will change in"
                            print repr(sub)
                            print "Size of changement: Before " + str(sys.getsizeof(eval_t)), "After: " + str(sys.getsizeof(sub))
                        result = True
                        text = text.replace(eval_t, sub, 1)
                        usedTot+=used
                    else:
                        if DEBUG:
                            print "REFUSED because equals"
                        pass
                else:
                    if DEBUG:
                        print "NO GOOD!"
                    pass
                #print text
            else:
                if DEBUG:
                    print t
                    print "not passed the test"
                pass
            #if DEBUG:
            #    print "\n"*10
            #    print "Complete text is"
            #    print text
        if DEBUG:
            raw_input("press any key to continue    ")
    os.remove(tfname)
    return text, result, err, usedTot


def general_deobfuscate(filename):
    """starting point for deobfuscation: take a file name, send to splitter and to the same operations until there is something to evaluate"""
    result = True
    count = 0
    fd=open(filename)
    text=fd.read()
    fd.close()
    toBeRemoved=[]
    while result:
        if DEBUG:
            print "testing regex1"
        text, result1, err1, used = splitter(text, regex_preg_replace1)
        if result1:
            count+=1
            toBeRemoved+=used
        if DEBUG:
            print "testing regex2"
        text, result1b, err1b, used = splitter(text, regex_preg_replace2)
        if result1b:
            count+=1
            toBeRemoved+=used
        if DEBUG:
            print "testing eval1"
        text, result2, err2, used = splitter(text, regex_eval1)
        if result2:
            count+=1
            toBeRemoved+=used
        if DEBUG:
            print "testing eval2"
        text, result2b, err2b, used = splitter(text, regex_eval2)
        if result2b:
            count+=1
            toBeRemoved+=used
        result = result1 | result2 | result1b | result2b
        err = err1 | err2 | err1b | err2b
    #return a string with the file content, not the filename
    for elem in toBeRemoved:
        text = text.replace(elem["raw_data"], '')
    return text, count, err

#var_string = re.compile(r'(\$[\w-]+)[ \t\n]*\=[ \t\n]*([^\=]*?;)', re.DOTALL)
#var_string1 = re.compile(r"(\$[\w-]+)[ \r\t\n]*\=([^\=]?[ \r\t\n]*?'.*?')", re.DOTALL)
#var_string2 = re.compile(r'(\$[\w-]+)[ \r\t\n]*\=([^\=]?[ \r\t\n]*?".*?")', re.DOTALL)
#var_nums = re.compile(r"(\$[\w-]+)[ \r\t\n]*\=[ \r\t\n]?(\d+?;)", re.DOTALL)
#var_ops = re.compile (r"(\$[\w-]+)[ \r\t\n]*\=[ \t\r\n]?([\w]+.*?;)", re.DOTALL)
regex_find_at = re.compile(r'\=[ \t]*(.)')
var_vars = re.compile (r"(\$[\w-]+)[ \r\t\n]*[\+\-\*\.]?\=([^\=].*?;)", re.DOTALL)
find_prog = re.compile(r'\$[\w-]+')
regex_preg_replace1 = re.compile(r'[@]?preg_replace[^;,]*e.*?;',re.DOTALL)
regex_preg_replace2 = re.compile(r'[@]?preg_replace[^;,]*e.*?[\t \r\n]*\?>', re.DOTALL)
regex_eval1 = re.compile(r'[@]?eval[ \t\r\n]*\(.*?;', re.DOTALL)
regex_eval2 = re.compile(r'[@]?eval[ \t\r\n]*\([^;]*?[\t \r\n]*\?>', re.DOTALL)
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "error in number of parameters"
        sys.exit(1)
    #listOfFiles = open(sys.argv[1]).readlines()
    listOfFiles = [sys.argv[1]]
    for el in listOfFiles:
        el = el.rstrip()
        try:
            f = open(el)
        except IOError as err:
            print "PANIC!"
            print err
        else:
            seg = f.read()
#            print "Before:", el, "size: ", str(sys.getsizeof(seg))
#            print "-" * 80 + "\n" + "Before:\n"
            f.close()
#            print seg
            text, times_evaled, error = general_deobfuscate(el)
            t = text
            siz = sys.getsizeof(t)
            if error:
                print "Careful! Timeout problem during evaluation!"
            print "After :", el, "size: ", str(siz)
            print "It has been decoded " + str(times_evaled) + " times"
            print "This is the file \n\n"
            print t
            print "\n\n"
