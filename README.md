# ft_printall
Another tester for 42 project : ft_printf

need python3 to run.

then either : "chmod +x test.py && ./test.py"

or : "python3 test.py"

options :

-d : display details for failed tests

-a : display details for all tests

-c : dont delete generated *.c files

-e : add '$' at end of output lines

-t <csdiuxX%p> : run tests for selected types only

-l : test only for leaks (can use "-l val" or "-l san", san is default")

WIP : -d / -a can reverse printing order if there was a crash during testing. still work tho.
