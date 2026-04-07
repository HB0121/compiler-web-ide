HBase的启动方式：

在主节点执行
```
/usr/local/sbin/ntp_update
```
启动时间同步服务👆


执行命令
```
service mysqld start
```
启动MySQL服务👆


执行命令
```
zk_cluster start
```
启动ZooKeeper集群👆


执行命令
```
/usr/local/sbin/hadoop_cluster start
```
启动Hadoop集群👆


执行命令
```
/usr/local/hbase-1.3.6/bin/start-hbase.sh
```
启动HBase👆


通过命令 
```
hbase shell
```
进入hbase命令窗口👆

使用以下指令查看各节点服务是否正常开启
```
jsp
```

通过浏览器查看HBase: [http://master:16010/](http://master:16010/)

    通过浏览器查看HBase的命名空间和数据：

        [http://master:50070/dfshealth.jsp](http://master:50070/dfshealth.jsp)

==注意：在HBase命令窗口中输入命令，如果输入出错，直接使用删除键【delete】是无法删除输入字符的，必须使用【ctrl+delete】组合键才能删除。==

HBase的关闭方式：HBase使用完成后必须关闭，释放相关资源。

```
exit
```
退出命令窗口👆

在主节点执行命令
```
/usr/local/hbase-1.3.6/bin/stop-hbase.sh
```
关闭HBase👆

执行命令
```
/usr/local/sbin/hadoop_cluster stop
```
关闭Hadoop集群👆

执行命令
```
zk_cluster stop
```
关闭ZooKeeper集群👆