.data

    #foo: .asciiz "bar"
# nothing

.text
main:
    li $t1, 0
    li $t2, 1
    li $t3, 20
    li $t4, -4
    li $s1, -1
    li $s2, 2147483648
    li $s3, 4294967296
    li $s4, 4294967297

    move $a0, $t3
    jal print_int

    #add $a0, $t1, $t3
    #jal print_int

    # exit
    li $v0, 10
    syscall

print_int:
    nop
    li $v0, 1
    syscall
    jr $ra
