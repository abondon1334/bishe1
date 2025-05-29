from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QComboBox, QMessageBox)
from models.database import DatabaseManager
from datetime import datetime
from utils.styles import GLOBAL_STYLESHEET, COLORS, add_shadow_effect
from utils.conflict_detector import ConflictDetector

class TeacherExamAdjustmentDialog(QDialog):
    def __init__(self, parent=None, exam_arrangement=None):
        super().__init__(parent)
        self.exam_arrangement = exam_arrangement
        self.teacher_name = parent.teacher_name  # 获取当前教师名称
        self.conflict_detector = ConflictDetector()  # 添加冲突检测器
        
        # 查询考试安排ID
        self.arrangement_id = self.get_arrangement_id()
        if not self.arrangement_id:
            QMessageBox.warning(self, '错误', '无法获取考试安排ID')
            self.reject()
            return
        
        # 权限检查
        if not self.check_permission():
            QMessageBox.warning(self, '权限错误', '您只能调整自己的考试安排')
            self.reject()
            return
        
        self.setWindowTitle('申请调整考试安排')
        self.init_ui()

    def get_arrangement_id(self):
        """
        根据考试安排信息查询对应的arrangement_id
        """
        db_manager = DatabaseManager()
        try:
            query = '''
                SELECT ea.arrangement_id 
                FROM exam_arrangements ea
                JOIN courses c ON ea.课程号 = c.id
                WHERE c.课程名称 = ? AND c.学院班级 = ? AND ea.考试日期 = ? AND ea.考试时间 = ?
            '''
            
            print(f"执行查询: {query}")
            print(f"查询参数: {self.exam_arrangement['课程名称']}, {self.exam_arrangement['学院班级']}, {self.exam_arrangement['考试日期']}, {self.exam_arrangement['考试时间']}")
            
            try:
                db_manager.cursor.execute(query, (
                    self.exam_arrangement['课程名称'],
                    self.exam_arrangement['学院班级'],
                    self.exam_arrangement['考试日期'],
                    self.exam_arrangement['考试时间']
                ))
                result = db_manager.cursor.fetchone()
                print(f"查询结果: {result}")
                return result[0] if result else None
            except Exception as query_error:
                print(f"SQL查询执行失败: {str(query_error)}")
                # 尝试备选查询
                alternative_query = '''
                    SELECT ea.arrangement_id 
                    FROM exam_arrangements ea
                    JOIN courses c ON ea.course_id = c.id
                    WHERE c.课程名称 = ? AND c.学院班级 = ? AND ea.考试日期 = ? AND ea.考试时间 = ?
                '''
                print(f"尝试备选查询: {alternative_query}")
                try:
                    db_manager.cursor.execute(alternative_query, (
                        self.exam_arrangement['课程名称'],
                        self.exam_arrangement['学院班级'],
                        self.exam_arrangement['考试日期'],
                        self.exam_arrangement['考试时间']
                    ))
                    result = db_manager.cursor.fetchone()
                    print(f"备选查询结果: {result}")
                    return result[0] if result else None
                except Exception as alt_error:
                    print(f"备选SQL查询也失败: {str(alt_error)}")
                    # 最后尝试最宽松的查询
                    last_query = '''
                        SELECT ea.arrangement_id 
                        FROM exam_arrangements ea
                        WHERE ea.考试日期 = ? AND ea.考试时间 = ?
                        LIMIT 1
                    '''
                    print(f"尝试最后查询: {last_query}")
                    db_manager.cursor.execute(last_query, (
                        self.exam_arrangement['考试日期'],
                        self.exam_arrangement['考试时间']
                    ))
                    result = db_manager.cursor.fetchone()
                    print(f"最后查询结果: {result}")
                    return result[0] if result else None
                    
        except Exception as e:
            error_message = f'获取考试安排ID失败：{str(e)}'
            QMessageBox.warning(self, '错误', error_message)
            import traceback
            traceback_info = traceback.format_exc()
            print(f"详细错误信息: {traceback_info}")
            # 显示数据库结构信息
            try:
                db_manager.cursor.execute("PRAGMA table_info(exam_arrangements)")
                ea_cols = db_manager.cursor.fetchall()
                print("考试安排表结构:", ea_cols)
                
                db_manager.cursor.execute("PRAGMA table_info(courses)")
                c_cols = db_manager.cursor.fetchall()
                print("课程表结构:", c_cols)
            except Exception as schema_e:
                print(f"获取表结构失败: {str(schema_e)}")
            return None
        finally:
            db_manager.close()

    def check_permission(self):
        """
        检查教师是否有权限调整该考试安排
        """
        # 检查考试安排的教师是否与当前教师一致
        db_manager = DatabaseManager()
        try:
            query = '''
                SELECT c.教师 
                FROM exam_arrangements ea
                JOIN courses c ON ea.课程号 = c.id
                WHERE ea.arrangement_id = ?
            '''
            
            print(f"执行权限检查查询: {query}")
            print(f"查询参数: {self.arrangement_id}")
            
            try:
                db_manager.cursor.execute(query, (self.arrangement_id,))
                result = db_manager.cursor.fetchone()
                print(f"权限检查结果: {result}")
                
                if result and result[0] == self.teacher_name:
                    return True
                return False
            except Exception as query_error:
                print(f"权限检查SQL查询执行失败: {str(query_error)}")
                # 尝试备选查询
                alternative_query = '''
                    SELECT c.教师 
                    FROM exam_arrangements ea
                    JOIN courses c ON ea.course_id = c.id
                    WHERE ea.arrangement_id = ?
                '''
                print(f"尝试备选权限查询: {alternative_query}")
                try:
                    db_manager.cursor.execute(alternative_query, (self.arrangement_id,))
                    result = db_manager.cursor.fetchone()
                    print(f"备选权限查询结果: {result}")
                    
                    if result and result[0] == self.teacher_name:
                        return True
                    return False
                except Exception as alt_error:
                    print(f"备选权限SQL查询也失败: {str(alt_error)}")
                    # 由于权限检查非常重要，如果都失败则默认拒绝
                    return False
        except Exception as e:
            error_message = f'权限检查失败：{str(e)}'
            QMessageBox.warning(self, '错误', error_message)
            import traceback
            traceback_info = traceback.format_exc()
            print(f"详细错误信息: {traceback_info}")
            return False
        finally:
            db_manager.close()

    def init_ui(self):
        self.setStyleSheet(GLOBAL_STYLESHEET + f"""
            QLineEdit, QTextEdit, QComboBox {{
                padding: 8px;
                border: 2px solid {COLORS['primary']};
                border-radius: 10px;
                background-color: white;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border-color: {COLORS['secondary']};
                box-shadow: 0 0 10px rgba(52, 152, 219, 0.3);
            }}
        """)

        # 为对话框添加阴影
        add_shadow_effect(self)

        layout = QVBoxLayout()

        # 原考试安排信息
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"课程：{self.exam_arrangement['课程名称']}"))
        info_layout.addWidget(QLabel(f"班级：{self.exam_arrangement['学院班级']}"))
        info_layout.addWidget(QLabel(f"原考试日期：{self.exam_arrangement['考试日期']}"))
        info_layout.addWidget(QLabel(f"原考试时间：{self.exam_arrangement['考试时间']}"))
        info_layout.addWidget(QLabel(f"原教室：{self.exam_arrangement['教室名称']}"))

        # 新教室选择
        room_layout = QHBoxLayout()
        room_label = QLabel('新教室：')
        self.room_combo = QComboBox()
        self.load_rooms()
        room_layout.addWidget(room_label)
        room_layout.addWidget(self.room_combo)

        # 新日期和时间输入
        date_layout = QHBoxLayout()
        date_label = QLabel('新考试日期：')
        self.date_input = QLineEdit()
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_input)

        time_layout = QHBoxLayout()
        time_label = QLabel('新考试时间：')
        self.time_input = QLineEdit()
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_input)

        # 申请理由
        reason_layout = QHBoxLayout()
        reason_label = QLabel('申请理由：')
        self.reason_text = QTextEdit()
        reason_layout.addWidget(reason_label)
        reason_layout.addWidget(self.reason_text)

        # 提交按钮
        submit_btn = QPushButton('提交申请')
        submit_btn.clicked.connect(self.submit_request)

        # 组装布局
        layout.addLayout(info_layout)
        layout.addLayout(room_layout)
        layout.addLayout(date_layout)
        layout.addLayout(time_layout)
        layout.addLayout(reason_layout)
        layout.addWidget(submit_btn)

        self.setLayout(layout)

    def load_rooms(self):
        db_manager = DatabaseManager()
        db_manager.cursor.execute('SELECT 教室编号, 教室名称 FROM exam_rooms')
        rooms = db_manager.cursor.fetchall()
        for room_id, room_name in rooms:
            self.room_combo.addItem(f"{room_id} - {room_name}")
        db_manager.close()

    def submit_request(self):
        db_manager = DatabaseManager()
        try:
            # 再次检查权限
            if not self.check_permission():
                QMessageBox.warning(self, '权限错误', '您没有权限修改此考试安排')
                return

            # 获取选择的教室
            room_text = self.room_combo.currentText()
            new_room_id = room_text.split(' - ')[0]
            new_date = self.date_input.text()
            new_time = self.time_input.text()

            # 验证输入
            if not new_date or not new_time:
                QMessageBox.warning(self, '错误', '请填写完整的日期和时间')
                return

            # 进行冲突检测
            has_conflict, conflicts = self.conflict_detector.check_all_conflicts(
                new_room_id, 
                self.teacher_name, 
                self.exam_arrangement['学院班级'],
                new_date, 
                new_time,
                exclude_arrangement_id=self.arrangement_id
            )
            
            if has_conflict:
                # 显示冲突信息
                conflict_message = self.conflict_detector.format_conflict_message(conflicts)
                reply = QMessageBox.question(
                    self, '检测到冲突', 
                    f"检测到以下冲突：\n\n{conflict_message}\n\n是否仍要提交申请？",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return

            # 直接更新考试安排（删除审核流程）
            update_query = '''
                UPDATE exam_arrangements 
                SET 考试日期 = ?, 考试时间 = ?, 教室编号 = ?
                WHERE arrangement_id = ?
            '''
            
            db_manager.cursor.execute(update_query, (new_date, new_time, new_room_id, self.arrangement_id))
            db_manager.conn.commit()
            
            QMessageBox.information(self, '成功', '考试安排已成功调整')
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, '错误', f'调整考试安排失败：{str(e)}')
            import traceback
            traceback.print_exc()
        finally:
            db_manager.close() 