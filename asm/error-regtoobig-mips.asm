# buggy code example 1

.text
main:
        addi $68, $t0, 4

loop:   addi $t1, $t1, 4
        j loop  # simply increment $t1 in a loop
