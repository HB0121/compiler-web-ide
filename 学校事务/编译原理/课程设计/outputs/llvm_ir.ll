@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
declare i32 @printf(i8*, ...)

define i32 @main() {
entry:
  %value = alloca i32
  store i32 5, i32* %value
  %v1 = load i32, i32* %value
  %t4 = add i32 0, 0
  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.fmt_int, i32 0, i32 0), i32 %t4)
  %t5 = add i32 0, 0
  ret i32 0
}
