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

将本地（Linux）/opt目录下的文件file01.txt、file02.txt、file03.txt上传到HDFS的/user/root/hdfsdir目录下

指令命令：
```

```

![](assets/HDFS%20Shell常用命令/file-20260325171830038.png)


递归显示HDFS /user/root/hdfsdir目录下的所有内容

![](assets/HDFS%20Shell常用命令/file-20260325172305223.png)

![500](assets/HDFS%20Shell常用命令/file-20260325172508132.png)

查看HDFS /user/root/hdfsdir目录下文件file02.txt中的内容


![](assets/HDFS%20Shell常用命令/file-20260325172406550.png)


合并本地文件系统（Linux）/opt目录下的文件flie01.txt、file02.txt、file03.txt，然后上传到HDFS的 /user/root/hdfsdir目录下，生成文件merge01.txt

![](assets/HDFS%20Shell常用命令/file-20260325172729046.png)

![](assets/HDFS%20Shell常用命令/file-20260325172820226.png)


