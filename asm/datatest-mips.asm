     .data
foo: .asciiz "hello_world."
bar: .asciiz "goodbye_world."
x:   .word 7
y:   .word 8
z:   .half 3
w:   .word 7
     .text
foo: 
    add $t0 $t0 $t0
