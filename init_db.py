from app import app, db, Lianxifangshi, Yewuchangjing, Monijuese, Xunlianjuese, Yingxiaodafa, Shilihuashu, ConversationHistory

def init_db():
    """初始化数据库和表"""
    with app.app_context():
        try:
            # 创建所有表
            db.create_all()
            
            # 检查是否需要初始化数据
            if Lianxifangshi.query.first() is None:
                # 添加默认数据
                items = ['一对一练习', '团队练习', '自主练习']
                for item in items:
                    db.session.add(Lianxifangshi(name=item))
                
                items = ['终端销售', '线上咨询', '电话营销']
                for item in items:
                    db.session.add(Yewuchangjing(name=item))
                    
                items = ['门店店员', '直销人员', '客服代表']
                for item in items:
                    db.session.add(Monijuese(name=item))
                    
                items = ['销售新人', '资深销售', '销售主管']
                for item in items:
                    db.session.add(Xunlianjuese(name=item))
                    
                items = ['产品介绍', '需求挖掘', '异议处理', '成交促进']
                for item in items:
                    db.session.add(Yingxiaodafa(name=item))
                    
                items = ['您好，请问有什么可以帮您?', '这个产品的优势是...', '我理解您的顾虑...']
                for item in items:
                    db.session.add(Shilihuashu(name=item))
                    
                db.session.commit()
                print("数据库初始化完成")
                
            # 检查并更新现有会话记录的api_type字段
            try:
                # 为没有api_type字段的现有记录设置默认值
                # conversations = ConversationHistory.query.filter(ConversationHistory.api_type.is_(None)).all()
                # for conv in conversations:
                #     conv.api_type = 'dify'
                # db.session.commit()
                # print(f"更新了 {len(conversations)} 条会话记录的API类型")
                print("跳过会话记录API类型更新")
            except Exception as e:
                print(f"更新会话记录API类型时出错: {str(e)}")
                
        except Exception as e:
            db.session.rollback()
            print(f"数据库初始化失败: {str(e)}")
            raise

if __name__ == '__main__':
    init_db() 