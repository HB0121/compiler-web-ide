1、查看存储系统信息（DataNode信息）

```
hdfs dfsadmin -report
```

2、查看HDFS集群基本信息

```
hdfs fsck /
```

3、查看HDFS常用命令

```
hdfs dfs
```

4、创建目录

```
hdfs dfs -mkdir [-p] <path> ...
```

```
hdfs dfs -mkdir -p /user/root/hdfsdir
```

-p:实现多级创建目录(建立/user/root/txtdir 目录)

使用指令：
查看HDFS根目录（“/”）的目录结构
```
hdfs dfs -ls /
```

![500](assets/HDFS%20Shell常用命令/file-20260325170242687.png)
![500](assets/HDFS%20Shell常用命令/file-20260325170349091.png)

在Linux文件中创建文件

```
vim /opt/file01.txt
```

```
vim /opt/file02.txt
```

```
vim /opt/file03.txt
```

- 按键盘上的 **`i`** 键进入“插入模式”（Insert Mode）。
- - 按 **`Esc`** 键退出插入模式。
- 输入 **`:wq`** 并回车，保存并退出。

查看结果：
```
ls -l /opt/file0*.txt

cat /opt/file01.txt
```

![](assets/HDFS%20Shell常用命令/file-20260325171436754.png)
