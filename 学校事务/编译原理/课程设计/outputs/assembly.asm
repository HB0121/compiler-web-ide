; MASM 16-bit DOS assembly
; Assemble with MASM/LINK:
; masm program.asm;
; link program.obj;
.MODEL SMALL
.STACK 100h
.DATA
.CODE

main PROC
    push bp
    mov bp, sp
    mov ax, @data
    mov ds, ax
    sub sp, 24
    mov ax, 2
    mov WORD PTR [bp-2], ax
    mov ax, 3
    mov WORD PTR [bp-4], ax
    mov ax, WORD PTR [bp-2]
    add ax, WORD PTR [bp-4]
    mov WORD PTR [bp-6], ax
    mov ax, WORD PTR [bp-6]
    mov WORD PTR [bp-8], ax
    mov ax, WORD PTR [bp-2]
    add ax, WORD PTR [bp-4]
    mov WORD PTR [bp-10], ax
    mov ax, WORD PTR [bp-10]
    mov WORD PTR [bp-12], ax
    mov ax, WORD PTR [bp-8]
    mov bx, WORD PTR [bp-12]
    imul bx
    mov WORD PTR [bp-14], ax
    mov ax, WORD PTR [bp-14]
    mov WORD PTR [bp-16], ax
    mov ax, WORD PTR [bp-16]
    cmp ax, 20
    jg L11
    jmp L14
L11:
    mov ax, WORD PTR [bp-16]
    sub ax, 1
    mov WORD PTR [bp-18], ax
    mov ax, WORD PTR [bp-18]
    mov WORD PTR [bp-20], ax
    jmp L16
L14:
    mov ax, WORD PTR [bp-16]
    add ax, 1
    mov WORD PTR [bp-22], ax
    mov ax, WORD PTR [bp-22]
    mov WORD PTR [bp-20], ax
L16:
    mov ax, WORD PTR [bp-20]
    ; builtin write(): value is already evaluated
    mov WORD PTR [bp-24], ax
    mov ax, 0
    mov ah, 4Ch
    int 21h
main ENDP

END main
