import re
import openpyxl
from openpyxl.styles import Font

def parse_ddl(ddl):
    tables = {}
    current_table = None

    lines = ddl.splitlines()
    for line in lines:
        line = line.strip()
        if line.upper().startswith("CREATE TABLE"):
            table_name = re.findall(r'CREATE TABLE `(\w+)`', line, re.IGNORECASE)[0]
            current_table = table_name
            tables[current_table] = []
        elif line.startswith(");"):
            current_table = None
        elif current_table and line and not line.startswith("PRIMARY KEY") and not line.startswith("KEY") and not line.startswith("CONSTRAINT"):
            column_details = re.findall(r'`(\w+)`\s+(\w+[\(\)\d]*)\s*(NOT NULL|NULL)?\s*(DEFAULT\s+[\w\'\d]+)?\s*(AUTO_INCREMENT)?', line)
            if column_details:
                column_name, column_type, allow_null, default_value, auto_increment = column_details[0]
                logical_name = column_name  # Assuming logical name is same as column name
                domain = column_type  # Assuming domain is same as column type
                allow_null = "NO" if "NOT NULL" in allow_null else "YES"
                default_value = default_value.split("DEFAULT ")[1] if default_value else ""
                comment = "AUTO_INCREMENT" if auto_increment else ""
                tables[current_table].append((logical_name, column_name, domain, column_type, allow_null, default_value, comment))

    return tables

def generate_excel(tables, filename):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Table Definitions"

    header_font = Font(bold=True)

    headers = ["Logical Name", "Physical Name", "Domain", "Type", "Allow Null", "Default Value", "Comment"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = header_font

    for table, columns in tables.items():
        ws.append([f"Table: {table}"] + [""] * (len(headers) - 1))
        for column in columns:
            ws.append(column)
        ws.append([""] * len(headers))  # Add an empty row for separation

    wb.save(filename)

# Example DDL script
ddl_script = """
CREATE TABLE `db_engine` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) DEFAULT NULL,
  `created_by` varchar(40) COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_by` varchar(40) COLLATE utf8mb4_bin DEFAULT NULL,
  `use_flag` tinyint(1) NOT NULL DEFAULT 1,
  `engine_id` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `engine_type` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `license` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `os_template_name` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `version` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UK_3nre4blvus7ukwmxlbm4pee97` (`engine_id`)
);

CREATE TABLE `db_default_config` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) DEFAULT NULL,
  `created_by` varchar(40) COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_by` varchar(40) COLLATE utf8mb4_bin DEFAULT NULL,
  `use_flag` tinyint(1) NOT NULL DEFAULT 1,
  `default_value` varchar(2000) COLLATE utf8mb4_bin NOT NULL,
  `is_restart` bit(1) DEFAULT NULL,
  `max_value` double DEFAULT NULL,
  `min_value` double DEFAULT NULL,
  `option_values` varchar(2000) COLLATE utf8mb4_bin DEFAULT NULL,
  `permitted_range_text` varchar(2000) COLLATE utf8mb4_bin DEFAULT NULL,
  `variable_name` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `variable_type` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `db_engine_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UK_rk9wu82grjk5rk0w2ex7t4gmo` (`variable_name`),
  KEY `FKnthonog1or4903ryy61hid45p` (`db_engine_id`),
  CONSTRAINT `FKnthonog1or4903ryy61hid45p` FOREIGN KEY (`db_engine_id`) REFERENCES `db_engine` (`id`)
);

CREATE TABLE `db_service` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) DEFAULT NULL,
  `created_by` varchar(40) COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_by` varchar(40) COLLATE utf8mb4_bin DEFAULT NULL,
  `use_flag` tinyint(1) NOT NULL DEFAULT 1,
  `company_code` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `cpu` int(11) NOT NULL,
  `data_center` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `database_name` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL,
  `db_user` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL,
  `disk_vol` int(11) NOT NULL,
  `ha_type` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `mem` int(11) NOT NULL,
  `node_count` int(11) NOT NULL,
  `product_id` bigint(20) DEFAULT NULL,
  `service_name` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `status` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `engine_id` bigint(20) DEFAULT NULL,
  `contract_id` bigint(20) DEFAULT NULL,
  `port` int(11) NOT NULL,
  `disk_type` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `dpm_resource_group_id` bigint(20) DEFAULT NULL,
  `parent_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `FKmif2p277mxfjvi0s4ccd2hwve` (`engine_id`),
  CONSTRAINT `FKmif2p277mxfjvi0s4ccd2hwve` FOREIGN KEY (`engine_id`) REFERENCES `db_engine` (`id`)
);

CREATE TABLE `db_config` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) DEFAULT NULL,
  `created_by` varchar(40) COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_by` varchar(40) COLLATE utf8mb4_bin DEFAULT NULL,
  `use_flag` tinyint(1) NOT NULL DEFAULT 1,
  `customized_value` varchar(2000) COLLATE utf8mb4_bin DEFAULT NULL,
  `service_id` bigint(20) DEFAULT NULL,
  `db_default_config_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `FKf62m71vmsw8kv17k1iowrnen8` (`service_id`),
  KEY `FKrqjerft1j4x5srhtqig9fwu9m` (`db_default_config_id`),
  CONSTRAINT `FKf62m71vmsw8kv17k1iowrnen8` FOREIGN KEY (`service_id`) REFERENCES `db_service` (`id`),
  CONSTRAINT `FKrqjerft1j4x5srhtqig9fwu9m` FOREIGN KEY (`db_default_config_id`) REFERENCES `db_default_config` (`id`)
);

CREATE TABLE `db_server` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) DEFAULT NULL,
  `created_by` varchar(40) COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_by` varchar(40) COLLATE utf8mb4_bin DEFAULT NULL,
  `use_flag` tinyint(1) NOT NULL DEFAULT 1,
  `count_number` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL,
  `management_ip` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL,
  `replication_ip` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL,
  `resource_id` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `service_ip` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL,
  `type` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `vip` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL,
  `service_id` bigint(20) DEFAULT NULL,
  `master_flag` tinyint(1) DEFAULT NULL COMMENT 'replication 삭제요청/삭제요청 취소시에만 유효',
  `backup_ip` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL,
  `dpm_resource_id` bigint(20) DEFAULT NULL,
  `bck_disk_vol` bigint(20) DEFAULT NULL,
  `cluster` varchar(100) COLLATE utf8mb4_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UK_m6xcjfxcnk4lppj838v1idnkr` (`resource_id`),
  KEY `FKf879bihbvj4rqpl7iagip4x6g` (`service_id`),
  CONSTRAINT `FKf879bihbvj4rqpl7iagip4x6g` FOREIGN KEY (`service_id`) REFERENCES `db_service` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=929 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;


-- dbaas_be.db_backup_schedule definition

CREATE TABLE `db_backup_schedule` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `backup_time` datetime NOT NULL,
  `backup_status` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `obj_bucket_name` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `obj_endpoint` varchar(255) COLLATE utf8mb4_bin NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `server_id` bigint(20) NOT NULL,
  `service_id` bigint(20) DEFAULT NULL,
  `created_by` varchar(40) COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_by` varchar(40) COLLATE utf8mb4_bin DEFAULT NULL,
  `use_flag` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `FKsm50m2xqgetuom6aie1rgu185` (`server_id`),
  KEY `FKq2fgy4eeq2ae34cv1caui1ckh` (`service_id`),
  CONSTRAINT `FKq2fgy4eeq2ae34cv1caui1ckh` FOREIGN KEY (`service_id`) REFERENCES `db_service` (`id`),
  CONSTRAINT `FKsm50m2xqgetuom6aie1rgu185` FOREIGN KEY (`server_id`) REFERENCES `db_server` (`id`)
);

CREATE TABLE `backup_history` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `created_by` varchar(40) DEFAULT NULL,
  `updated_by` varchar(40) DEFAULT NULL,
  `use_flag` tinyint(1) NOT NULL DEFAULT 1,
  `status` varchar(10) NOT NULL,
  `type` varchar(10) NOT NULL,
  `db_server_id` bigint(20) DEFAULT NULL,
  `service_id` bigint(20) DEFAULT NULL,
  `backup_schedule_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `FK_backup_history_db_server` (`db_server_id`),
  KEY `FK_backup_history_db_service` (`service_id`),
  KEY `backup_history_db_backup_schedule_FK` (`backup_schedule_id`),
  CONSTRAINT `FK_backup_history_db_server` FOREIGN KEY (`db_server_id`) REFERENCES `db_server` (`id`),
  CONSTRAINT `FK_backup_history_db_service` FOREIGN KEY (`service_id`) REFERENCES `db_service` (`id`),
  CONSTRAINT `backup_history_db_backup_schedule_FK` FOREIGN KEY (`backup_schedule_id`) REFERENCES `db_backup_schedule` (`id`)
);
"""

# Parse the DDL script
tables = parse_ddl(ddl_script)

# Generate the Excel file
generate_excel(tables, "table_definitions.xlsx")

print("Excel file 'table_definitions.xlsx' has been created.")