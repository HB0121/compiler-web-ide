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

创建命名空间

```
create_namespace 'test'
```

预览所有命名空间
```
list_namespace
```

查看命名空间详情
```
describe_namespace 'test'
```

查看命名空间的表
```
list_namespace_tables 'test'
```

修改命名空间

  alter_namespace 'test', {METHOD => 'set', 'hbase.namespace.quota.maxregion' => '10'}

  alter_namespace 'test', {METHOD => 'set', 'hbase.namespace.quota.maxtables' => '10'}

删除命名空间（被删除的命名空间必须为空，即里面没有建表，否则不能被删除）

```
ndrop_namespace
```

新建表1

```
create 'test:student',{NAME=>'info'},{NAME=>'course',VERSIONS=>5}
```


desc ‘命名空间:表名’：查看制定表的结构
```
desc 'test:student'
```

describe ‘命名空间:表名’：与desc命令相同


list‘命名空间：正则表达式’：查看表名
```
list
```

exists ‘命名空间:表名’：判断制定表是否存在
```
exists 'test:student'
```

新建表2
```
create 'test:pratice','f1',SPLITS=>['10','20','30','40']
```

修改表

修改（添加）列族（列族存在就是修改，不存在就是添加）

```
   alter '命名空间:表名',{语法参数}
```

删除列族

```
   alter '命名空间:表名',{NAME => 'f1', METHOD => 'delete'}

   alter '命名空间:表名', 'delete' => 'f1'
```

修改表属性

```
  alter ‘命名空间:表名’, MAX_FILESIZE => ‘134217728’（设置表属性）

  alter ‘命名空间:表名’, METHOD => ‘table_att_unset’, NAME => ‘MAX_FILESIZE’（删除表属性）
```

```
alter 'test:pratice',{NAME=>'f2'},{NAME=>'f3',VERSIONS=>20}
```

删除原先的列族f1

```
alter 'test:pratice',{NAME=>'f1',METHOD=>'delete'}
```

n为表加上一个属性MAX_FILESIZE=>‘134217728’，查看表

```
alter 'test:pratice',MAX_FILESIZE=>'134217728'
```

删除表

disable '命名空间:表名‘

    重点：表必须首先disabled（禁用），然后才能删除

drop '命名空间:表名'

```
disable 'test:pratice'
```

```
drop 'test:pratice'
```



在命名空间test中完成以下表数据添加任务。

    创建一个表scores，分别有列族course，在表中添加scores数据如下：
```
    create 'test:scores','course'
```

    Tom course:math 97
    
```
put 'test:scores','Tom','course:math','97'
```

    Tom course:art 87

```
put 'test:scores','Tom','course:art','87'
```

    Tom course:english 80

```
put 'test:scores','Tom','course:english','80'
```

    Jim course:chinese 89

```
put 'test:scores','Jim','course:chinese','89'
```

    Jim course:english 80

```
put 'test:scores','Jim','course:english','80'
```


查看表scores中Jim的一行的数据
```
get 'test:scores','Jim'
```

查看Jim course列族的数据
```
get 'test:scores','Jim',{COLUM=>'course'}
```

查看表scores中的course:english列的数据
```
get 'test:scores','Jim',{COLUM=>'course:english'}
```

统计表scores的行数
```
count 'test:scores'
```

全表scores扫描
```
scan 'test:scores'
```


删除scores表Jim的course:chinese的值（重点：如果该数据有多个版本—时间戳，则删除命令只能删除最近一个版本的值，其他版本的值还会保留并显示出来）
```
delete 'test:scores','Jim','course:chinese'
```

删除scores表Tom的course:english的值
```
delete 'test:scores','Tom','course:english'
```
