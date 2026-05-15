@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
declare i32 @printf(i8*, ...)

define i32 @main() {
entry:
  %a = alloca i32
  %b = alloca i32
  %c = alloca i32
  %d = alloca i32
  %x = alloca i32
  %y = alloca i32
  %z = alloca i32
  store i32 10, i32* %a
  store i32 5, i32* %b
  %v1 = load i32, i32* %a
  %v2 = load i32, i32* %b
  %t1 = add i32 %v1, %v2
  store i32 %t1, i32* %c
  %v3 = load i32, i32* %a
  %v4 = load i32, i32* %b
  %t2 = add i32 %v3, %v4
  store i32 %t2, i32* %d
  %v5 = load i32, i32* %c
  %v6 = load i32, i32* %d
  %t3 = mul i32 %v5, %v6
  store i32 %t3, i32* %x
  %v7 = load i32, i32* %x
  %cmp1 = icmp sgt i32 %v7, 20
  br i1 %cmp1, label %L11, label %L16
L11:
  %v8 = load i32, i32* %a
  %v9 = load i32, i32* %b
  %t4 = add i32 %v8, %v9
  store i32 %t4, i32* %y
  %v10 = load i32, i32* %y
  %v11 = load i32, i32* %d
  %t5 = mul i32 %v10, %v11
  store i32 %t5, i32* %z
  br label %L20
L16:
  %v12 = load i32, i32* %a
  %v13 = load i32, i32* %b
  %t6 = sub i32 %v12, %v13
  store i32 %t6, i32* %y
  %v14 = load i32, i32* %y
  %v15 = load i32, i32* %d
  %t7 = add i32 %v14, %v15
  store i32 %t7, i32* %z
  br label %L20
L20:
  %v16 = load i32, i32* %z
  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.fmt_int, i32 0, i32 0), i32 %v16)
  %t8 = add i32 0, 0
  ret i32 0
}
