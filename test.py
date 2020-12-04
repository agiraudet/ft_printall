#!/bin/python3

import subprocess
import os
import sys

lib_path = ""
inc_path = ""
rules_path = "rules"

DFLAG = False
RFLAG = False
TFLAG = False
CFLAG = False
GFLAG = False

GREEN = '\033[32m'
RED = '\033[31m'
YELLOW = '\033[33m'
ENDL = '\033[0m'

def setArgs():
    global rules_path
    global RFLAG
    global DFLAG
    global TFLAG
    global CFLAG
    global GFLAG
    readrule = False
    makerule = False
    for arg in sys.argv:
        if readrule:
            readrule = False
            rules_path = arg
            if os.path.isfile(rules_path) is False:
                printf("Incorrect usage of -r option: file does not exist")
        if makerule:
            makerule = False
            with open("rules.tmp", 'w') as tmp:
                tmp.write(arg)
        if arg == "-d":
            DFLAG = True
        if arg == "-r":
            RFLAG = True
            if TFLAG:
                print("options -r and -t cant be used together")
                exit()
            readrule = True
        if arg == "-t":
            TFLAG = True
            if RFLAG:
                print("options -r and -t cant be used together")
                exit()
            makerule = True
            rules_path = "rules.tmp"
        if arg == "-c":
            CFLAG = True
        if arg == "-g":
            GFLAG = True

def readConfig():
    global lib_path
    global inc_path
    if os.path.isfile("config") is False:
        with open("config", 'w') as conf:
            conf.write("#dont use \"\" when defining paths\n#path to your ft_printf\nLIB_PATH=..\n\n#path to your *.h file (only one can be used)\nINC_PATH=../includes/ft_printf.h\n")
        print("created config file, please fill it and run again.")
        exit()
    with open("config", 'r') as conf:
        for line in conf:
            if "LIB_PATH" in line:
                lib_path = line[line.index('=')+1:].rstrip('\n')
            elif "INC_PATH" in line:
                inc_path = line[line.index('=')+1:].rstrip('\n')
    if os.path.isfile(lib_path + "/libftprintf.a") is False:
        subprocess.run(['make','-C',lib_path])
    if os.path.isfile(lib_path + "/libftprintf.a") is False:
        print("file libftprintf.a not found at " + lib_path)
        exit()
    if os.path.isfile(inc_path) is False:
        print("no .h file at " + inc_path)
        exit()

def makeRule(fct, rule, nb):
    return "\tif (atoi(argv[1]) == "+str(nb)+")\n\t\treturn ("+fct+"("+rule[:-1]+"));\n"

def buildC(path, fct):
    with open(path, 'w') as file:
        file.write("#include <stdlib.h>\n")
        if fct == "ft_printf":
            compil = ["gcc", "-g", path, "-o", path[:-2], "-L", lib_path, "-lftprintf"]
            file.write("#include \""+inc_path+"\"\n")
        else:
            compil = ["gcc", path, "-o", path[:-2]]
            file.write("#include <stdio.h>\n")
        file.write("\nint main(int argc, char** argv)\n{\n")
        with open(rules_path, 'r') as rules:
            nb = 0
            for rule in rules:
                file.write(makeRule(fct, rule, nb))
                nb += 1
        file.write("}\n")
    subprocess.run(compil)
    if CFLAG is False:
        os.remove(path)
    return nb

def getRule(linenb):
    line = ""
    with open(rules_path, 'r') as file:
        for l in range(linenb):
            line = file.readline()
    return line[:-1]

def test(rule_nb):
    ok = 0
    ko = 0
    for r in range(rule_nb):
        resFT = subprocess.run(['./ft', str(r)], capture_output=True, text=True)
        resPF = subprocess.run(['./pf', str(r)], capture_output=True, text=True)
        if resFT.returncode == resPF.returncode and resFT.stdout == resPF.stdout:
            print(GREEN + "OK (" + getRule(r + 1) + ")" + ENDL)
            ok += 1
        else:
            print(RED + "KO" + ENDL + " > " + RED + getRule(r + 1) + ENDL)
            if DFLAG:
                print("printf:")
                print("  \u02EAreturn: " + YELLOW + str(resPF.returncode) + ENDL)
                print("  \u02EAoutput: " + YELLOW + resPF.stdout + "$" + ENDL)
                print("ft_printf:")
                print("  \u02EAreturn: " + YELLOW + str(resFT.returncode) + ENDL)
                print("  \u02EAoutput: " + YELLOW + resFT.stdout + "$" + ENDL + '\n')
            ko += 1
    print("\n" + str(rule_nb) + " TESTS:\n" + "  OK " + GREEN + str(ok) + ENDL + "\n  KO " + RED + str(ko) + ENDL)
    if not GFLAG:
        os.remove('ft')
    os.remove('pf')

readConfig()
setArgs()
buildC("ft.c", "ft_printf")
x = buildC("pf.c", "printf")
test(x)
if TFLAG:
    os.remove("rules.tmp")
