-- 智慧园区设备运维管理平台 PostgreSQL 建表脚本
-- 说明：
-- 1. 本脚本根据《智慧园区设备运维管理平台需求说明书》的数据库字典生成。
-- 2. 所有业务表统一包含通用字段：is_enable、level_mark_id、level_mark_value、date_created、modify_date、created_by_id、created_by_name、modify_by_id、modify_by_name。
-- 3. is_enable 逻辑删除标记：0 表示正常，-1 表示已删除。
-- 4. 主键 id 采用 bigint 类型，实际项目可接入框架雪花 ID 或 Flex ID 生成策略。

create table if not exists ops_area (
    id bigint primary key,
    parent_id bigint,
    area_name varchar(100) not null,
    area_code varchar(50) not null,
    description varchar(255),
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_area is '区域表';
comment on column ops_area.id is '区域 ID';
comment on column ops_area.parent_id is '父级区域';
comment on column ops_area.area_name is '区域名称';
comment on column ops_area.area_code is '区域编码';
comment on column ops_area.description is '说明';
comment on column ops_area.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_area.level_mark_id is '组织架构 ID';
comment on column ops_area.level_mark_value is '组织架构值';
comment on column ops_area.date_created is '创建时间';
comment on column ops_area.modify_date is '修改时间';
comment on column ops_area.created_by_id is '创建人 ID';
comment on column ops_area.created_by_name is '创建人名称';
comment on column ops_area.modify_by_id is '修改人 ID';
comment on column ops_area.modify_by_name is '修改人名称';
create unique index if not exists uk_ops_area_code on ops_area(area_code) where is_enable = 0;
create index if not exists idx_ops_area_parent_id on ops_area(parent_id);

create table if not exists ops_device_category (
    id bigint primary key,
    category_name varchar(100) not null,
    category_code varchar(50) not null,
    parent_id bigint,
    description varchar(255),
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_device_category is '设备分类表';
comment on column ops_device_category.id is '分类 ID';
comment on column ops_device_category.category_name is '分类名称';
comment on column ops_device_category.category_code is '分类编码';
comment on column ops_device_category.parent_id is '父级分类';
comment on column ops_device_category.description is '说明';
comment on column ops_device_category.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_device_category.level_mark_id is '组织架构 ID';
comment on column ops_device_category.level_mark_value is '组织架构值';
comment on column ops_device_category.date_created is '创建时间';
comment on column ops_device_category.modify_date is '修改时间';
comment on column ops_device_category.created_by_id is '创建人 ID';
comment on column ops_device_category.created_by_name is '创建人名称';
comment on column ops_device_category.modify_by_id is '修改人 ID';
comment on column ops_device_category.modify_by_name is '修改人名称';
create unique index if not exists uk_ops_device_category_code on ops_device_category(category_code) where is_enable = 0;
create index if not exists idx_ops_device_category_parent_id on ops_device_category(parent_id);

create table if not exists ops_device (
    id bigint primary key,
    device_code varchar(50) not null,
    device_name varchar(100) not null,
    category_id bigint not null,
    category_name varchar(100),
    brand varchar(100),
    model varchar(100),
    area_id bigint not null,
    area_name varchar(100),
    location varchar(255) not null,
    manager_id bigint,
    manager_name varchar(50),
    supplier_id bigint,
    supplier_name varchar(100),
    purchase_date date,
    warranty_end_date date,
    status varchar(20) not null,
    remark varchar(500),
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_device is '设备表';
comment on column ops_device.id is '设备 ID';
comment on column ops_device.device_code is '设备编号';
comment on column ops_device.device_name is '设备名称';
comment on column ops_device.category_id is '设备分类 ID';
comment on column ops_device.category_name is '设备分类名称';
comment on column ops_device.brand is '品牌';
comment on column ops_device.model is '型号';
comment on column ops_device.area_id is '所在区域 ID';
comment on column ops_device.area_name is '所在区域名称';
comment on column ops_device.location is '安装位置';
comment on column ops_device.manager_id is '负责人 ID';
comment on column ops_device.manager_name is '负责人名称';
comment on column ops_device.supplier_id is '供应商 ID';
comment on column ops_device.supplier_name is '供应商名称';
comment on column ops_device.purchase_date is '购买日期';
comment on column ops_device.warranty_end_date is '保修截止日期';
comment on column ops_device.status is '设备状态：running、fault、maintenance、scrapped';
comment on column ops_device.remark is '备注';
comment on column ops_device.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_device.level_mark_id is '组织架构 ID';
comment on column ops_device.level_mark_value is '组织架构值';
comment on column ops_device.date_created is '创建时间';
comment on column ops_device.modify_date is '修改时间';
comment on column ops_device.created_by_id is '创建人 ID';
comment on column ops_device.created_by_name is '创建人名称';
comment on column ops_device.modify_by_id is '修改人 ID';
comment on column ops_device.modify_by_name is '修改人名称';
create unique index if not exists uk_ops_device_code on ops_device(device_code) where is_enable = 0;
create index if not exists idx_ops_device_category_id on ops_device(category_id);
create index if not exists idx_ops_device_area_id on ops_device(area_id);
create index if not exists idx_ops_device_supplier_id on ops_device(supplier_id);
create index if not exists idx_ops_device_status on ops_device(status);

create table if not exists ops_work_order (
    id bigint primary key,
    order_no varchar(50) not null,
    title varchar(100) not null,
    device_id bigint not null,
    device_name varchar(100),
    source_type varchar(30) not null,
    source_id bigint,
    source_desc varchar(255),
    reporter_id bigint not null,
    reporter_name varchar(50) not null,
    reporter_phone varchar(20),
    assignee_id bigint,
    assignee_name varchar(50),
    priority varchar(20) not null,
    status varchar(30) not null,
    description text not null,
    cause text,
    solution text,
    result text,
    report_time timestamp not null,
    expected_finish_time timestamp,
    finish_time timestamp,
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_work_order is '工单表';
comment on column ops_work_order.id is '工单 ID';
comment on column ops_work_order.order_no is '工单编号';
comment on column ops_work_order.title is '工单标题';
comment on column ops_work_order.device_id is '关联设备 ID';
comment on column ops_work_order.device_name is '关联设备名称';
comment on column ops_work_order.source_type is '工单来源：manual、inspection_item';
comment on column ops_work_order.source_id is '来源业务 ID，手动创建时为空，检查项异常转工单时为巡检检查项 ID';
comment on column ops_work_order.source_desc is '来源说明';
comment on column ops_work_order.reporter_id is '报修人 ID';
comment on column ops_work_order.reporter_name is '报修人';
comment on column ops_work_order.reporter_phone is '报修联系电话';
comment on column ops_work_order.assignee_id is '处理人 ID';
comment on column ops_work_order.assignee_name is '处理人';
comment on column ops_work_order.priority is '工单优先级：low、medium、high、urgent';
comment on column ops_work_order.status is '工单状态：pending、assigned、processing、reviewing、completed、closed、rejected';
comment on column ops_work_order.description is '故障描述';
comment on column ops_work_order.cause is '故障原因';
comment on column ops_work_order.solution is '处理措施';
comment on column ops_work_order.result is '处理结果';
comment on column ops_work_order.report_time is '报修时间';
comment on column ops_work_order.expected_finish_time is '期望完成时间';
comment on column ops_work_order.finish_time is '完成时间';
comment on column ops_work_order.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_work_order.level_mark_id is '组织架构 ID';
comment on column ops_work_order.level_mark_value is '组织架构值';
comment on column ops_work_order.date_created is '创建时间';
comment on column ops_work_order.modify_date is '修改时间';
comment on column ops_work_order.created_by_id is '创建人 ID';
comment on column ops_work_order.created_by_name is '创建人名称';
comment on column ops_work_order.modify_by_id is '修改人 ID';
comment on column ops_work_order.modify_by_name is '修改人名称';
create unique index if not exists uk_ops_work_order_no on ops_work_order(order_no) where is_enable = 0;
create index if not exists idx_ops_work_order_device_id on ops_work_order(device_id);
create index if not exists idx_ops_work_order_status on ops_work_order(status);
create index if not exists idx_ops_work_order_assignee_id on ops_work_order(assignee_id);
create index if not exists idx_ops_work_order_report_time on ops_work_order(report_time);
create index if not exists idx_ops_work_order_source on ops_work_order(source_type, source_id);

create table if not exists ops_work_order_timeline (
    id bigint primary key,
    work_order_id bigint not null,
    operator_id bigint not null,
    operator_name varchar(50) not null,
    action varchar(50) not null,
    content varchar(500) not null,
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_work_order_timeline is '工单流转记录表';
comment on column ops_work_order_timeline.id is '记录 ID';
comment on column ops_work_order_timeline.work_order_id is '工单 ID';
comment on column ops_work_order_timeline.operator_id is '操作人 ID';
comment on column ops_work_order_timeline.operator_name is '操作人名称';
comment on column ops_work_order_timeline.action is '操作类型';
comment on column ops_work_order_timeline.content is '操作内容';
comment on column ops_work_order_timeline.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_work_order_timeline.level_mark_id is '组织架构 ID';
comment on column ops_work_order_timeline.level_mark_value is '组织架构值';
comment on column ops_work_order_timeline.date_created is '创建时间';
comment on column ops_work_order_timeline.modify_date is '修改时间';
comment on column ops_work_order_timeline.created_by_id is '创建人 ID';
comment on column ops_work_order_timeline.created_by_name is '创建人名称';
comment on column ops_work_order_timeline.modify_by_id is '修改人 ID';
comment on column ops_work_order_timeline.modify_by_name is '修改人名称';
create index if not exists idx_ops_work_order_timeline_order_id on ops_work_order_timeline(work_order_id);

create table if not exists ops_inspection_plan (
    id bigint primary key,
    plan_name varchar(100) not null,
    area_id bigint not null,
    area_name varchar(100),
    category_id bigint,
    category_name varchar(100),
    cycle_type varchar(20) not null,
    owner_id bigint not null,
    owner_name varchar(50) not null,
    next_execute_time timestamp,
    status varchar(20) not null,
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_inspection_plan is '巡检计划表';
comment on column ops_inspection_plan.id is '计划 ID';
comment on column ops_inspection_plan.plan_name is '计划名称';
comment on column ops_inspection_plan.area_id is '巡检区域';
comment on column ops_inspection_plan.area_name is '巡检区域名称';
comment on column ops_inspection_plan.category_id is '设备分类';
comment on column ops_inspection_plan.category_name is '设备分类名称';
comment on column ops_inspection_plan.cycle_type is '巡检周期：daily、weekly、monthly';
comment on column ops_inspection_plan.owner_id is '负责人 ID';
comment on column ops_inspection_plan.owner_name is '负责人';
comment on column ops_inspection_plan.next_execute_time is '下次执行时间';
comment on column ops_inspection_plan.status is '启停状态：enabled、disabled';
comment on column ops_inspection_plan.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_inspection_plan.level_mark_id is '组织架构 ID';
comment on column ops_inspection_plan.level_mark_value is '组织架构值';
comment on column ops_inspection_plan.date_created is '创建时间';
comment on column ops_inspection_plan.modify_date is '修改时间';
comment on column ops_inspection_plan.created_by_id is '创建人 ID';
comment on column ops_inspection_plan.created_by_name is '创建人名称';
comment on column ops_inspection_plan.modify_by_id is '修改人 ID';
comment on column ops_inspection_plan.modify_by_name is '修改人名称';
create index if not exists idx_ops_inspection_plan_area_id on ops_inspection_plan(area_id);
create index if not exists idx_ops_inspection_plan_category_id on ops_inspection_plan(category_id);
create index if not exists idx_ops_inspection_plan_status on ops_inspection_plan(status);

create table if not exists ops_inspection_plan_item (
    id bigint primary key,
    category_id bigint not null,
    category_name varchar(100),
    item_name varchar(100) not null,
    standard varchar(255) not null,
    item_type varchar(30) not null,
    required smallint not null default 1,
    sort_order int not null default 0,
    enabled smallint not null default 1,
    remark varchar(255),
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_inspection_plan_item is '设备分类检查项模板表';
comment on column ops_inspection_plan_item.id is '模板检查项 ID';
comment on column ops_inspection_plan_item.category_id is '设备分类 ID';
comment on column ops_inspection_plan_item.category_name is '设备分类名称';
comment on column ops_inspection_plan_item.item_name is '检查项名称';
comment on column ops_inspection_plan_item.standard is '标准要求';
comment on column ops_inspection_plan_item.item_type is '检查项类型：text、number、select、photo';
comment on column ops_inspection_plan_item.required is '是否必填，1 是，0 否';
comment on column ops_inspection_plan_item.sort_order is '排序号';
comment on column ops_inspection_plan_item.enabled is '是否启用，1 是，0 否';
comment on column ops_inspection_plan_item.remark is '备注';
comment on column ops_inspection_plan_item.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_inspection_plan_item.level_mark_id is '组织架构 ID';
comment on column ops_inspection_plan_item.level_mark_value is '组织架构值';
comment on column ops_inspection_plan_item.date_created is '创建时间';
comment on column ops_inspection_plan_item.modify_date is '修改时间';
comment on column ops_inspection_plan_item.created_by_id is '创建人 ID';
comment on column ops_inspection_plan_item.created_by_name is '创建人名称';
comment on column ops_inspection_plan_item.modify_by_id is '修改人 ID';
comment on column ops_inspection_plan_item.modify_by_name is '修改人名称';
create index if not exists idx_ops_inspection_plan_item_category_id on ops_inspection_plan_item(category_id);

create table if not exists ops_inspection_task (
    id bigint primary key,
    plan_id bigint not null,
    task_no varchar(50) not null,
    inspector_id bigint not null,
    inspector_name varchar(50) not null,
    status varchar(20) not null,
    result varchar(20),
    description varchar(500),
    related_order_id bigint,
    execute_time timestamp,
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_inspection_task is '巡检任务表';
comment on column ops_inspection_task.id is '任务 ID';
comment on column ops_inspection_task.plan_id is '计划 ID';
comment on column ops_inspection_task.task_no is '任务编号';
comment on column ops_inspection_task.inspector_id is '巡检人 ID';
comment on column ops_inspection_task.inspector_name is '巡检人';
comment on column ops_inspection_task.status is '巡检任务状态：pending、processing、completed';
comment on column ops_inspection_task.result is '巡检结果：normal、abnormal、recheck';
comment on column ops_inspection_task.description is '巡检说明';
comment on column ops_inspection_task.related_order_id is '关联工单 ID';
comment on column ops_inspection_task.execute_time is '执行时间';
comment on column ops_inspection_task.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_inspection_task.level_mark_id is '组织架构 ID';
comment on column ops_inspection_task.level_mark_value is '组织架构值';
comment on column ops_inspection_task.date_created is '创建时间';
comment on column ops_inspection_task.modify_date is '修改时间';
comment on column ops_inspection_task.created_by_id is '创建人 ID';
comment on column ops_inspection_task.created_by_name is '创建人名称';
comment on column ops_inspection_task.modify_by_id is '修改人 ID';
comment on column ops_inspection_task.modify_by_name is '修改人名称';
create unique index if not exists uk_ops_inspection_task_no on ops_inspection_task(task_no) where is_enable = 0;
create index if not exists idx_ops_inspection_task_plan_id on ops_inspection_task(plan_id);
create index if not exists idx_ops_inspection_task_status on ops_inspection_task(status);

create table if not exists ops_inspection_item (
    id bigint primary key,
    task_id bigint not null,
    template_item_id bigint,
    item_name varchar(100) not null,
    standard varchar(255) not null,
    result varchar(20),
    abnormal_desc varchar(500),
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_inspection_item is '巡检检查项表';
comment on column ops_inspection_item.id is '检查项 ID';
comment on column ops_inspection_item.task_id is '巡检任务 ID';
comment on column ops_inspection_item.template_item_id is '来源模板检查项 ID';
comment on column ops_inspection_item.item_name is '检查项';
comment on column ops_inspection_item.standard is '标准要求';
comment on column ops_inspection_item.result is '巡检结果：normal、abnormal、recheck';
comment on column ops_inspection_item.abnormal_desc is '异常说明';
comment on column ops_inspection_item.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_inspection_item.level_mark_id is '组织架构 ID';
comment on column ops_inspection_item.level_mark_value is '组织架构值';
comment on column ops_inspection_item.date_created is '创建时间';
comment on column ops_inspection_item.modify_date is '修改时间';
comment on column ops_inspection_item.created_by_id is '创建人 ID';
comment on column ops_inspection_item.created_by_name is '创建人名称';
comment on column ops_inspection_item.modify_by_id is '修改人 ID';
comment on column ops_inspection_item.modify_by_name is '修改人名称';
create index if not exists idx_ops_inspection_item_task_id on ops_inspection_item(task_id);
create index if not exists idx_ops_inspection_item_template_item_id on ops_inspection_item(template_item_id);

create table if not exists ops_spare_part (
    id bigint primary key,
    part_code varchar(50) not null,
    part_name varchar(100) not null,
    part_type varchar(50) not null,
    model varchar(100),
    stock_quantity int not null default 0,
    safety_stock int not null default 0,
    unit varchar(20) not null,
    location varchar(100),
    supplier_id bigint,
    supplier_name varchar(100),
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_spare_part is '备件表';
comment on column ops_spare_part.id is '备件 ID';
comment on column ops_spare_part.part_code is '备件编号';
comment on column ops_spare_part.part_name is '备件名称';
comment on column ops_spare_part.part_type is '备件类型';
comment on column ops_spare_part.model is '规格型号';
comment on column ops_spare_part.stock_quantity is '当前库存';
comment on column ops_spare_part.safety_stock is '安全库存';
comment on column ops_spare_part.unit is '单位';
comment on column ops_spare_part.location is '存放位置';
comment on column ops_spare_part.supplier_id is '供应商 ID';
comment on column ops_spare_part.supplier_name is '供应商名称';
comment on column ops_spare_part.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_spare_part.level_mark_id is '组织架构 ID';
comment on column ops_spare_part.level_mark_value is '组织架构值';
comment on column ops_spare_part.date_created is '创建时间';
comment on column ops_spare_part.modify_date is '修改时间';
comment on column ops_spare_part.created_by_id is '创建人 ID';
comment on column ops_spare_part.created_by_name is '创建人名称';
comment on column ops_spare_part.modify_by_id is '修改人 ID';
comment on column ops_spare_part.modify_by_name is '修改人名称';
create unique index if not exists uk_ops_spare_part_code on ops_spare_part(part_code) where is_enable = 0;
create index if not exists idx_ops_spare_part_supplier_id on ops_spare_part(supplier_id);
create index if not exists idx_ops_spare_part_type on ops_spare_part(part_type);

create table if not exists ops_inventory_record (
    id bigint primary key,
    record_no varchar(50) not null,
    part_id bigint not null,
    part_name varchar(100),
    record_type varchar(20) not null,
    quantity int not null,
    related_order_id bigint,
    operator_id bigint not null,
    operator_name varchar(50) not null,
    remark varchar(255),
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_inventory_record is '库存流水表';
comment on column ops_inventory_record.id is '流水 ID';
comment on column ops_inventory_record.record_no is '流水编号';
comment on column ops_inventory_record.part_id is '备件 ID';
comment on column ops_inventory_record.part_name is '备件名称';
comment on column ops_inventory_record.record_type is '库存流水类型：inbound、outbound、adjust';
comment on column ops_inventory_record.quantity is '数量';
comment on column ops_inventory_record.related_order_id is '关联工单 ID';
comment on column ops_inventory_record.operator_id is '操作人 ID';
comment on column ops_inventory_record.operator_name is '操作人名称';
comment on column ops_inventory_record.remark is '备注';
comment on column ops_inventory_record.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_inventory_record.level_mark_id is '组织架构 ID';
comment on column ops_inventory_record.level_mark_value is '组织架构值';
comment on column ops_inventory_record.date_created is '创建时间';
comment on column ops_inventory_record.modify_date is '修改时间';
comment on column ops_inventory_record.created_by_id is '创建人 ID';
comment on column ops_inventory_record.created_by_name is '创建人名称';
comment on column ops_inventory_record.modify_by_id is '修改人 ID';
comment on column ops_inventory_record.modify_by_name is '修改人名称';
create unique index if not exists uk_ops_inventory_record_no on ops_inventory_record(record_no) where is_enable = 0;
create index if not exists idx_ops_inventory_record_part_id on ops_inventory_record(part_id);
create index if not exists idx_ops_inventory_record_related_order_id on ops_inventory_record(related_order_id);
create index if not exists idx_ops_inventory_record_type on ops_inventory_record(record_type);

create table if not exists ops_supplier (
    id bigint primary key,
    supplier_name varchar(100) not null,
    supplier_type varchar(50) not null,
    contact_name varchar(50) not null,
    contact_phone varchar(20) not null,
    email varchar(100),
    address varchar(255),
    service_scope varchar(500),
    status varchar(20) not null,
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_supplier is '供应商表';
comment on column ops_supplier.id is '供应商 ID';
comment on column ops_supplier.supplier_name is '供应商名称';
comment on column ops_supplier.supplier_type is '供应商类型：device、maintenance、part';
comment on column ops_supplier.contact_name is '联系人';
comment on column ops_supplier.contact_phone is '联系电话';
comment on column ops_supplier.email is '邮箱';
comment on column ops_supplier.address is '地址';
comment on column ops_supplier.service_scope is '服务范围';
comment on column ops_supplier.status is '启停状态：enabled、disabled';
comment on column ops_supplier.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_supplier.level_mark_id is '组织架构 ID';
comment on column ops_supplier.level_mark_value is '组织架构值';
comment on column ops_supplier.date_created is '创建时间';
comment on column ops_supplier.modify_date is '修改时间';
comment on column ops_supplier.created_by_id is '创建人 ID';
comment on column ops_supplier.created_by_name is '创建人名称';
comment on column ops_supplier.modify_by_id is '修改人 ID';
comment on column ops_supplier.modify_by_name is '修改人名称';
create index if not exists idx_ops_supplier_type on ops_supplier(supplier_type);
create index if not exists idx_ops_supplier_status on ops_supplier(status);

create table if not exists ops_knowledge_article (
    id bigint primary key,
    title varchar(100) not null,
    category varchar(50) not null,
    device_category_id bigint,
    device_category_name varchar(100),
    content text not null,
    tags varchar(255),
    maintainer_id bigint,
    maintainer_name varchar(50),
    status varchar(20) not null,
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_knowledge_article is '知识库文章表';
comment on column ops_knowledge_article.id is '文章 ID';
comment on column ops_knowledge_article.title is '标题';
comment on column ops_knowledge_article.category is '分类';
comment on column ops_knowledge_article.device_category_id is '关联设备分类';
comment on column ops_knowledge_article.device_category_name is '关联设备分类名称';
comment on column ops_knowledge_article.content is '内容';
comment on column ops_knowledge_article.tags is '标签';
comment on column ops_knowledge_article.maintainer_id is '文章维护人 ID';
comment on column ops_knowledge_article.maintainer_name is '文章维护人';
comment on column ops_knowledge_article.status is '文章状态：draft、published';
comment on column ops_knowledge_article.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_knowledge_article.level_mark_id is '组织架构 ID';
comment on column ops_knowledge_article.level_mark_value is '组织架构值';
comment on column ops_knowledge_article.date_created is '创建时间';
comment on column ops_knowledge_article.modify_date is '修改时间';
comment on column ops_knowledge_article.created_by_id is '创建人 ID';
comment on column ops_knowledge_article.created_by_name is '创建人名称';
comment on column ops_knowledge_article.modify_by_id is '修改人 ID';
comment on column ops_knowledge_article.modify_by_name is '修改人名称';
create index if not exists idx_ops_knowledge_article_category on ops_knowledge_article(category);
create index if not exists idx_ops_knowledge_article_device_category_id on ops_knowledge_article(device_category_id);
create index if not exists idx_ops_knowledge_article_status on ops_knowledge_article(status);

create table if not exists ops_attachment (
    id bigint primary key,
    biz_type varchar(50) not null,
    biz_id bigint not null,
    file_name varchar(255) not null,
    file_type varchar(50) not null,
    file_ext varchar(20),
    file_size bigint not null,
    file_url varchar(500) not null,
    thumbnail_url varchar(500),
    upload_scene varchar(50),
    description varchar(255),
    uploader_id bigint,
    uploader_name varchar(50),
    is_enable int not null default 0,
    level_mark_id bigint,
    level_mark_value varchar(255),
    date_created timestamp not null default now(),
    modify_date timestamp not null default now(),
    created_by_id bigint,
    created_by_name varchar(50),
    modify_by_id bigint,
    modify_by_name varchar(50)
);

comment on table ops_attachment is '附件表';
comment on column ops_attachment.id is '附件 ID';
comment on column ops_attachment.biz_type is '业务类型：work_order、inspection_task、inspection_item、knowledge_article';
comment on column ops_attachment.biz_id is '业务数据 ID';
comment on column ops_attachment.file_name is '原始文件名';
comment on column ops_attachment.file_type is '文件类型：image、document、video、other';
comment on column ops_attachment.file_ext is '文件扩展名';
comment on column ops_attachment.file_size is '文件大小，单位 byte';
comment on column ops_attachment.file_url is '文件访问地址';
comment on column ops_attachment.thumbnail_url is '缩略图地址';
comment on column ops_attachment.upload_scene is '上传场景：report、process、result、inspection、article';
comment on column ops_attachment.description is '附件说明';
comment on column ops_attachment.uploader_id is '上传人 ID';
comment on column ops_attachment.uploader_name is '上传人名称';
comment on column ops_attachment.is_enable is '逻辑删除标记，0 表示正常，-1 表示已删除';
comment on column ops_attachment.level_mark_id is '组织架构 ID';
comment on column ops_attachment.level_mark_value is '组织架构值';
comment on column ops_attachment.date_created is '创建时间';
comment on column ops_attachment.modify_date is '修改时间';
comment on column ops_attachment.created_by_id is '创建人 ID';
comment on column ops_attachment.created_by_name is '创建人名称';
comment on column ops_attachment.modify_by_id is '修改人 ID';
comment on column ops_attachment.modify_by_name is '修改人名称';
create index if not exists idx_ops_attachment_biz on ops_attachment(biz_type, biz_id);
create index if not exists idx_ops_attachment_file_type on ops_attachment(file_type);
