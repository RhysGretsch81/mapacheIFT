.data 

msg: .asciiz "\nEnter a number: "
answer: .asciiz "\nFactorial is: "

.text
main:
    li $v0, 4
    la $a0, msg
    syscall  # print msg

    li $v0, 5
    syscall # read input string
    move $a0, $v0

    jal calculate_factorial
    move $a1, $v0

    li $v0, 4
    la $a0, answer
    syscall

    move $a0, $a1
    li $v0, 1
    syscall

    # exit
    li $v0, 10
    syscall

calculate_factorial:
    addi $sp, $sp, -4
    sw $ra, 0($sp)
    li $v0, 1

multiply:
    beq $a0, $0, return
    mult $v0, $a0
    mflo $v0
    addi $a0, $a0, -1
    j multiply

return:
    lw $ra, 0($sp)
    addi $sp, $sp, 4
    jr $ra
