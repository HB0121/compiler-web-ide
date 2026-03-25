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

