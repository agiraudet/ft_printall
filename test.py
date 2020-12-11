#!/bin/python3

import subprocess
import os
import sys

lib_path = ""
inc_path = ""
rul_path = ""

allTypes = "csdiuxX%p"
genSet = ""
rules = {}
ruleNb = 0

flags = {
	'T' : False,  #generate only part of tests
	'D' : False,  #details failed test
	'A' : False,  #details every test
	'C' : False,  #dont delete *.c
	'E' : False,  #add $ at the end of lines
	'B' : False,  #dont delete binary files (usefull for checking for leaks)
	'L' : False   #check for leaks
}

leakTester = "san"

GRN = '\033[32m'
RED = '\033[31m'
YLW = '\033[33m'
CYN = '\033[36m'
NOC = '\033[0m'
BLU = '\033[34m'
LGT = '\033[3m' + BLU
BLD = '\033[1m'

def parseArgs():
	global flags
	global rul_path
	global genSet
	global leakTester

	t = False
	l = False
	for arg in sys.argv:
		if arg == sys.argv[0]:
			continue
		elif t is True:
			for letter in arg:
				if letter not in allTypes:
					print("Wrong paramter : " + arg)
					exit()
				genSet = arg
			else:
				rul_path = arg
			t = False
		elif l is True:
			if arg == "val" or arg == "san":
				leakTester = arg
			else:
				print("-l argument should be:")
				print("\"val\" (valgrind) or \"san\" (fsanitize)")
				exit()
			l = False
		elif arg == '-b':
			flags['B'] = True
		elif arg == '-l':
			flags['L'] = True
			l = True
		elif arg == '-d':
			flags['D'] = True
		elif arg == '-a' :
			flags['A'] = True
		elif arg == '-c':
			flags['C'] = True
		elif arg == '-e':
			flags['E'] = True
		elif arg == '-t':
			flags['T'] = True
			t = True
		else:
			print("Wrong parameter : " + arg)
			exit()
	if genSet == "":
		genSet = allTypes

def parseConfig():
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

def cleanCharArg(i):
	if int(i) < 0:
		i = i[1:]
	if int (i) > 127:
		i = "127"
	return i

def genArgs(cnv, nbWC, mini=False):
	ints = ["0","1","42","-21"]
	maxInt = "2147483647"
	args = []
	if cnv in "cdiuxX%":
		if cnv in "diuxX" and mini is False:
			ints.append(maxInt)
		elif cnv is "%":
			nbWC -= 1
		if nbWC == 0:
			for i in ints:
				if cnv is "c":
					i = cleanCharArg(i)
				args.append(i)
		elif nbWC == 1:
			for i1 in ints:
				for i2 in ints:
					if cnv is "c":
						i2 = cleanCharArg(i2)
					a = "{}, {}".format(i1, i2)
					if a not in args:
						args.append(a)
		elif nbWC == 2:
			for i1 in ints:
				for i2 in ints:
					for i3 in ints:
						if cnv is "c":
							i3 = cleanCharArg(i3)
						a = "{}, {}, {}".format(i1, i2, i3)
						if a not in args:
							args.append(a)
	ptrs = ["i", "c", "0"]
	if cnv in "ps":
		if cnv == "s":
			ptrs = ["\"Hello World!\"", "0"]
		if nbWC == 0:
			for p in ptrs:
				args.append(p)
		elif nbWC == 1:
			for i in ints:
				for p in ptrs:
					a = "{}, {}".format(i, p)
					if a not in args:
						args.append(a)
		elif nbWC == 2:
			for i1 in ints:
				for i2 in ints:
					for p in ptrs:
						a = "{}, {}, {}".format(i1, i2, p)
						if a not in args:
							args.append(a)
	return (args)

def genRules():
		global rules

		prefix=["%","%15","%-15","%0","%-----5","%015","%-015","%0-15","%.","%.3","%.20","%.0","%15.6","%15.20","%15.0","%15.","%*","%-*","%0*","%0-*","%-0*","%.*","%-.*","%0.*","%0-.*","%-0.*","%*.*","%0*.*","%-*.*","%0-*.*","%-0*.*"]
		for cnv in genSet:
			rules[cnv] = []
			for pfx in prefix:
				args = genArgs(cnv, pfx.count('*'))
				for av in args:
					rules[cnv].append("\"{}{}\", {}".format(pfx, cnv, av))
		if cnv == "c":
			for i in range(-1, 127):
				rules["c"].append("\"%c\", {}".format(i))

def makeRule(fct, rule, nb):
	if rule[-1] == '\n':
		rule = rule[:-1]
	return "\tif (atoi(argv[1]) == "+str(nb)+")\n\t\treturn ("+fct+"("+rule+"));\n"

def buildLeaks(path):
	miniRules = {}
	miniSet = "csduxX"
	miniPrefix = ["%", "%15", "%0", "%*", "%*.*", "%.15", "%.*"]
	for cnv in miniSet:
		miniRules[cnv] = []
		for pfx in miniPrefix:
			args = genArgs(cnv, pfx.count('*'), mini=True)
			for av in args:
				miniRules[cnv].append("\"{}{}\", {}".format(pfx, cnv, av))
	with open(path, 'w') as file:
		file.write("#include \"{}\"\n".format(inc_path))
		file.write("#include <stdio.h>")
		file.write("\nint main(int argc, char **argv)\n{\n")
		for r in miniRules:
			for v in miniRules[r]:
				file.write("\tft_printf("+ v +"); printf(\"\\n\");\n")
		file.write("printf(\"@\");\n")
		#file.write("char *c = malloc(sizeof(char));\n")
		file.write("}\n");
	if leakTester == "san":
		subprocess.run(["gcc", "-g", "-fsanitize=address", path, "-o", path[:-2], "-L", lib_path, "-lftprintf"])
	else:
		subprocess.run(["gcc", "-g", path, "-o", path[:-2], "-L", lib_path, "-lftprintf"])
	if not flags.get('C'):
		os.remove(path)

def buildCfiles(path, fct):
	global ruleNb

	print(LGT + "generating {}".format(path) + NOC)
	with open(path, 'w') as file:
		file.write("#include <stdio.h>\n")
		file.write("#include \"{}\"\n".format(inc_path))
		file.write("\nint main(int argc, char **argv)\n{\n")
		file.write("\tint\ti = 42;\n\tchar\t*c = \"Fly you fools\";\n\n")
		nb = 0
		for r in rules:
			for v in rules[r]:
				if r == 'p':
					file.write(makeRulePTR(fct, v, nb))
				else:
					file.write(makeRule(fct, v, nb))
				nb += 1
		file.write("\n\t(void)i;\n\t(void)c;\n}\n")
	print(LGT + "compiling {}".format(path) + NOC)
	subprocess.run(["gcc", "-w", path, "-o", path[:-2], "-L", lib_path, "-lftprintf"])
	if flags.get('C') is False:
		os.remove(path)
	ruleNb = nb

def makeRulePTR(fct, rule, nb):
	if rule[-1] == '\n':
		rule = rule[:-1]
	if "ft" in fct:
		return "\tif (atoi(argv[1]) == "+str(nb)+")\n\t\t{ fprintf(stderr,"+rule+"); return(ft_printf("+rule+")); }\n"
	else:
		return "\tif (atoi(argv[1]) == "+str(nb)+")\n\t\t{ ft_printf("+rule+"); return(fprintf(stderr,"+rule+")); }\n"

def printRes(ok, ko):
	print("  \u02EAOK : " + GRN + str(ok) + NOC)
	print("  \u02EAKO : " + RED + str(ko) + NOC)
	print("  \u02EAtests done: " + YLW + str(ok + ko) + '\n' + NOC)

def runTest(progA, progB):
	totalok = 0
	totalko = 0
	rNb = 0

	for r in rules:
		ok = 0
		ko = 0
		print(BLD + "testing " + CYN + "%" + r + NOC)
		for v in rules[r]:
			rNb += 1
			resFT = subprocess.run(['uptime'], capture_output=True, text=True)
			resPF = resFT
			try:
				resFT = subprocess.run(["./" + progA, str(rNb)], capture_output=True, text=True)
			except:
				resFT.returncode = 0
				resFT.stdout = RED + "CRASH" + NOC
			try:
				resPF = subprocess.run(["./" + progB, str(rNb)], capture_output=True, text=True)
			except:
				resPF.returncode = 0
				resPF.stdout = RED + "CRASH" + NOC
			if r == 'p':
				resPF.stdout = resFT.stderr
			if resFT.returncode == resPF.returncode and resFT.stdout == resPF.stdout:
				ok += 1
				if flags.get('A'):
					print(GRN + "OK" + NOC)
					print("both: " + v)
					print("   \u02EAreturn: " + YLW + str(resPF.returncode) + NOC)
					if flags.get('E'):
						resPF.stdout += '$'
					print("   \u02EAoutput: " + YLW + resPF.stdout + NOC)
			else:
				print(RED + "KO" + NOC + " > " + v)
				ko += 1
				if flags.get('A') or flags.get('D'):
					print("printf:")
					print("  \u02EAreturn: " + YLW + str(resPF.returncode) + NOC)
					if flags.get('E'):
						resPF.stdout += '$'
					print("  \u02EAoutput: " + YLW + resPF.stdout + NOC)
					print("ft_printf:")
					print("  \u02EAreturn: " + YLW + str(resFT.returncode) + NOC)
					if flags.get('E'):
						resFT.stdout += '$'
					print("  \u02EAoutput: " + YLW + resFT.stdout + NOC + '\n')
		printRes(ok, ko)
		totalok += ok
		totalko += ko
	print(BLD + CYN + "TOTAL" + NOC)
	printRes(totalok, totalko)
	if not flags.get('B'):
		os.remove(progA)
		os.remove(progB)

def runLeakTest(path):
	if leakTester == "san":
		lk = subprocess.run(["./" + path], capture_output=True, text=True)
		out = lk.stderr
	else:
		try:
			lk = subprocess.run(["valgrind", "./" + path], capture_output=True, text=True)
			out = lk.stderr
		except:
			out = "could not run valgrind."
	if not flags.get('B'):
		os.remove(path)
	if not out:
		print( GRN + "NO LEAKS DETECTED" + NOC)
	elif leakTester == "san":
		if flags.get('L'):
			print(out)
		else:
			print(RED + "LEAKS DETECTED" + NOC)
			print(LGT + "run {} -l for details".format(sys.argv[0]) + NOC)
	else:
		print(out)

parseArgs()
parseConfig()
genRules()
if not flags.get('L'):
	buildCfiles("ft.c", "ft_printf")
	buildCfiles("pf.c", "printf")
	print()
	runTest("ft", "pf")
buildLeaks("leaks.c")
runLeakTest("leaks")
