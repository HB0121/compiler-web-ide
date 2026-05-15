@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
declare i32 @printf(i8*, ...)

define i32 @main() {
entry:
  %i = alloca i32
  %odd = alloca i32
  store i32 0, i32* %i
  store i32 0, i32* %odd
  br label %L3
L3:
  %v1 = load i32, i32* %i
  %cmp1 = icmp slt i32 %v1, 5
  br i1 %cmp1, label %L5, label %L13
L5:
  %v2 = load i32, i32* %i
  %t1 = srem i32 %v2, 2
  %cmp2 = icmp ne i32 %t1, 0
  br i1 %cmp2, label %L8, label %L10
L8:
  %v3 = load i32, i32* %odd
  %t2 = add i32 %v3, 1
  store i32 %t2, i32* %odd
  br label %L10
L10:
  %v4 = load i32, i32* %i
  %t3 = add i32 %v4, 1
  store i32 %t3, i32* %i
  br label %L3
L13:
  %v5 = load i32, i32* %odd
  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.fmt_int, i32 0, i32 0), i32 %v5)
  %t4 = add i32 0, 0
  ret i32 0
}
