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

==================================================

Step1. 创建一个HDFS目录/user/root/hdfsdir

```
hdfs dfs -mkdir -p /user/root/hdfsdir
```

![500](assets/HDFS%20Shell常用命令/file-20260325170242687.png)
![500](assets/HDFS%20Shell常用命令/file-20260325170349091.png)


Step2. 在本地（Linux）/opt目录下，使用vim编辑器创建数据文件file01.txt、file02.txt、file03.txt（文件中的内容任意，保证每个文件中有多行文字）

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

Step3. 将本地（Linux）/opt目录下的文件file01.txt、file02.txt、file03.txt上传到HDFS的/user/root/hdfsdir目录下

指令命令：
```
hdfs dfs -put /opt/file01.txt /user/root/hdfsdir
hdfs dfs -put /opt/file02.txt /user/root/hdfsdir
hdfs dfs -put /opt/file03.txt /user/root/hdfsdir

hdfs dfs -ls /user/root/hdfsdir
```

![](assets/HDFS%20Shell常用命令/file-20260325171830038.png)


Step4. 递归显示HDFS /user/root/hdfsdir目录下的所有内容

指令命令：
```
hdfs dfs -R /user/root/hdfsdir
```

![](assets/HDFS%20Shell常用命令/file-20260325172305223.png)

![500](assets/HDFS%20Shell常用命令/file-20260325172508132.png)


Step5. 查看HDFS /user/root/hdfsdir目录下文件file02.txt中的内容

指令命令：
```
hdfs dfs -cat /user/root/hdfsdir/file02.txt
```

![](assets/HDFS%20Shell常用命令/file-20260325172406550.png)


Step6. 合并本地文件系统（Linux）/opt目录下的文件flie01.txt、file02.txt、file03.txt，然后上传到HDFS的 /user/root/hdfsdir目录下，生成文件merge01.txt

指令命令：
```
hdfs dfs -appendToFile /opt/file01.txt /opt/file02.txt /opt/file03.txt /user/root/hdfsdir/merge01.txt
```

![](assets/HDFS%20Shell常用命令/file-20260325172729046.png)

![](assets/HDFS%20Shell常用命令/file-20260325172820226.png)



Step7. 下载HDFS /user/root/hdfsdir目录下的文件merge01.txt到本地文件系统（Linux）的/opt目录下

指令代码：
```
hdfs dfs -get /user/root/hdfsdir/merge01.txt /opt
```

![](assets/HDFS%20Shell常用命令/file-20260325173056311.png)

Step8. 删除HDFS中的 /user/root/hdfsdir目录（包括目录下的文件）

指令代码：
```
hdfs dfs -rm -r /user/root/hdfsdir
```

![](assets/HDFS%20Shell常用命令/file-20260325173152382.png)

![](assets/HDFS%20Shell常用命令/file-20260325173226420.png)