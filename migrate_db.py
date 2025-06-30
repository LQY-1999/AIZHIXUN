#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加api_type字段
"""

import sqlite3
import os

def migrate_database():
    """迁移数据库，添加api_type字段"""
    db_path = 'agent_config.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查api_type字段是否存在
        cursor.execute("PRAGMA table_info(conversation_history)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'api_type' not in columns:
            print("正在添加api_type字段...")
            cursor.execute("ALTER TABLE conversation_history ADD COLUMN api_type TEXT DEFAULT 'dify'")
            print("api_type字段添加成功")
        else:
            print("api_type字段已存在")
        
        # 更新现有记录的api_type字段
        cursor.execute("UPDATE conversation_history SET api_type = 'dify' WHERE api_type IS NULL")
        updated_count = cursor.rowcount
        print(f"更新了 {updated_count} 条记录的api_type字段")
        
        # 提交更改
        conn.commit()
        print("数据库迁移完成")
        
    except Exception as e:
        print(f"数据库迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database() 