### Ackermann.s function:
###
###              - n+1				if m==0
###             /
### Ack(m,n) := -- Ack(m-1, 1)			if m>0, n==0
###             \
###              - Ack(m-1, Ack(m, n-1))	if m>0, n>0
###

        /^_RdR_LLCACA$
     /R=/^RPL+$
`FAq=/R=\^RPL+$
        \^P_1CA$
    

`B-"Insert m: ":P-I-"Insert n: ":P-I-"Ackermann(":PL;R',:P' :P;") == ":P-CA-;~n:P
