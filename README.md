mu-language
===========

The MU esoteric language.
MU is a funge esolang.
An example of code is the following _Hello, world!_ program:
```text
                                      ,-^',----:P'w-----:P'r-----:P'd-----:P-,
                                     /                                        \
                                    /                                          \
`BH----'o'l-'l--'e---'H-:P:P:P:P:P-*                                            @-~n:
                                    \                                          /
                                     \                                        /
                                      ,-^--:P' -----:P'o-----:P'l-----:P'!---,

```

Other _Hello, world!_ programs:

```text
                         -
                        / \
           `BH-'F++-:P-*   \
                            *---*
                                |           *------------* 
                                *           |             \
                               / \          ~              \
                              '   '         n               \
                             l     e        :                \
                            '       :       E                 \
                           l         P                         \
                          /           \                         *
                         *:P:P---------.--------' :P-------*    |
                                        \                  |    |
                                         \                 |    |
        E:n~P:P:P:P:---*                  \                |    |
                      P                    \               |    |
                     :                      \              |    *
                    P                        '             |   /
                   :                          ,            |  /
                  /                            '           | / 
                 |                              o          |/
                  \                              \         *
                   *----w'o'r'l'd'-_"'-P:P:-------*

```

```text
                                          P
                 \           P           :
                  P          :          w
                   :                   '
                    ,        '        /
                     '       |       /
                      \      |      /
                       \     |     /
                        \    |    /
                         \   |   /
                          \  |  /
                           5 6 7
                            BBB
      P:n~P:!'-----P:o'---4HB`B0'H:P-----'o:P
                            BBB
                           3 2 1
                          /  |  \
                         /   |   ' 
                        /    '    e
                       '     l     :
                      l      :      P
                     :       P       \
                    P        |        \
                   /         |         \
                  /          |          \
                 /           |           \
                /            |            '
               /             '             r
              '              l              :
             d               :               P
            :                P                \
           P                 |                 \

```

```text
             -         -         -         -         -         -         -          
            ! \       / \       / \       / \       / \       / \       / \          
           '   '     l   '     o   '         '     o   '     l   '     H   \        
          H     d   '     r   '     w   '     ,   '     l   '     e   '     \    
         B       \ /       \ /       \ /       \ /       \ /       \ /       \   
        `         -         -         -         -         -         -         \
                                                                               *
                                                                               |
                                                                               *
        E         -         -         -         -         -         -         /          
         :       / \       / \       / \       / \       / \       / \       / 	          
          n     :   P     :   P     :   P     :   P     :   P     :   P     :            
           ~   P     :   P     :   P     :   P     :   P     :   P     :   P          
            \ /       \ /       \ /       \ /       \ /       \ /       \ /           
             -         -         -         -         -         -         -    
```

```text
          ,---,
         /     \
`Oy-----*-------@---"world":P   `H'uro-", ":P
        |\     /|
        | ,---, |           `FY-"Hello":P
        \-------/

        ,[5]xw,
       /       \
      / ,--CY-, u
     /  |     |  \ 
`BH-*---*-----@---@---'!:P~n:E
     \   \   /   /
      \   ,w,   /
       \       /
        ,-y---,

```

This is an implementation of the Conway's game of life:
The library:
```text
`H0rfqLL^RMC*Lx+

`H"Lcrtf"rfqC*;x(q^^0)

`H1rfqc^dmRdmLv^MM     
                         /--------------\                                                 /---------------\
                       /?/vLLd^MvRR^x+-i\------\                                        /?/-vLLd^MvRR^x+-i\------\
`H2rfq^PPPvR^M-----x+->/--vLLd^dRMvRR^x_--<\PLi\i/-v0L---------RRRRd^MvLLLL^-M------x+->/--v-LLd^dRMvRR^x_--<\PLi\i/
                                           \P0LP-/                                                           \P0LP-/


`H3rfqc^18x&0_d2&mm0_02&mm0_12&mm0d_2&mm012&mm10_2&mm102&mm112&mmPP[16]xM6&m6&m6&m6&m6&m6&m6&m6&mv7xC+^M

`H4rfq0&++d^PPMxLLP1RMxR

`H5rfq0&++d^PPMxLLP0RMxR

`H6rfq0&++d^PPMxLLdmvR^M+xRvL^M

                                                  /P(qz^MM)^MM5&v\
                                               /_=/P-------------\-\
                                          /P__=/P---------------i\-\-\
`H7rfqc0di/z2x(q^zMM)^^MM3&mvvLL^^MM6&mvv=/P___=\P(qz^MM)^MM4&vi/-i\i\\  
          |                                     \P--------------/     | 
          \-----\i-----------/i\i------------------P\                 |
                \-v&"tnrpL"^-/ |    />d_x_vRmdL^d+PP\>_x_vRRmdLL^d+z--/
                               \-0PP/

`f*q_dRxdLx(^x+)^PPM ### multiply

`f+q^x+  ### sum

`H"Lstep"rFq7&z^zC*dRxP++xM
                                          
`H"Lprnt"rFq~n:P-~n:Pzx(^dmx(^^' :P;P)~n:PM)

                  /----------------------------\
                  |                   /^1v-\   |
`H"Lread"rFq^00v0i\i/a? d~nx_?\Pd'0x_=/^0vi\PP+/
                    |         \PPd^L+Ldmvx_->\^PMRRvi/\
                    |                        \^--RRv-/|
                    \-----------------------------0Pxl/

`X-"Lread"&-D-~n:P-"Lprnt"&-i/-"Lprnt"&-"ENTER to continue, [q] to quit...":Pad'qx_= "Lstep"&-\

```

The main:
```text
`BR-"Lread"&-D-~n:P-"Lprnt"&-[2]x(^"Lstep"&"Lprnt"&)-~n:
```

The input:
```text
00000
00100
01110
00100
00000
```


This is a quine:
```text
`Fqq:'[:P;']:P'C:P'q:P~n:P

`BQ[158879760829061318991975427000950345381773628394447915895288766801]Cq
```
