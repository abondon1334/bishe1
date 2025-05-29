from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, 
                             QVBoxLayout, QHBoxLayout, QPushButton, 
                             QMessageBox, QLabel)
from PyQt5.QtCore import Qt
from models.database import DatabaseManager

class ExamAdjustmentReviewWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 标题
        title_label = QLabel('考场调整申请审核')
        title_label.setStyleSheet('font-size: 18px; font-weight: bold;')
        layout.addWidget(title_label)

        # 申请列表表格
        self.request_table = QTableWidget()
        self.request_table.setColumnCount(11)
        self.request_table.setHorizontalHeaderLabels([
            '申请ID', '课程名称', '学院班级', '申请人', 
            '原日期', '原时间', '原教室', 
            '新日期', '新时间', '新教室', '申请理由'
        ])
        self.request_table.horizontalHeader().setStretchLastSection(True)

        # 审核按钮区
        button_layout = QHBoxLayout()
        approve_btn = QPushButton('同意申请')
        reject_btn = QPushButton('拒绝申请')
        approve_btn.clicked.connect(self.approve_request)
        reject_btn.clicked.connect(self.reject_request)
        button_layout.addWidget(approve_btn)
        button_layout.addWidget(reject_btn)

        layout.addWidget(self.request_table)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        
        # 加载申请
        self.load_requests()

    def load_requests(self):
        try:
            # 修正JOIN条件
            query = '''
                SELECT 
                    r.request_id, 
                    c.课程名称, 
                    c.学院班级, 
                    r.申请人, 
                    r.原考试日期, 
                    r.原考试时间, 
                    r.原教室, 
                    r.新考试日期, 
                    r.新考试时间, 
                    r.新教室, 
                    r.申请理由
                FROM exam_adjustment_requests r
                JOIN exam_arrangements ea ON r.arrangement_id = ea.arrangement_id
                JOIN courses c ON ea.课程号 = c.id
                WHERE r.状态 = '待审核'
            '''
            
            print(f"执行查询: {query}")
            
            try:
                self.db_manager.cursor.execute(query)
                requests = self.db_manager.cursor.fetchall()
                print(f"查询结果行数: {len(requests)}")
            except Exception as query_error:
                print(f"SQL查询执行失败: {str(query_error)}")
                # 尝试修改JOIN条件
                alternative_query = '''
                    SELECT 
                        r.request_id, 
                        c.课程名称, 
                        c.学院班级, 
                        r.申请人, 
                        r.原考试日期, 
                        r.原考试时间, 
                        r.原教室, 
                        r.新考试日期, 
                        r.新考试时间, 
                        r.新教室, 
                        r.申请理由
                    FROM exam_adjustment_requests r
                    JOIN exam_arrangements ea ON r.arrangement_id = ea.arrangement_id
                    JOIN courses c ON ea.course_id = c.id
                    WHERE r.状态 = '待审核'
                '''
                print(f"尝试备选查询: {alternative_query}")
                try:
                    self.db_manager.cursor.execute(alternative_query)
                    requests = self.db_manager.cursor.fetchall()
                    print(f"备选查询结果行数: {len(requests)}")
                except Exception as alt_error:
                    print(f"备选SQL查询也失败: {str(alt_error)}")
                    # 使用最简单的查询
                    simple_query = '''
                        SELECT 
                            request_id, 
                            '未知' as 课程名称, 
                            '未知' as 学院班级, 
                            申请人, 
                            原考试日期, 
                            原考试时间, 
                            原教室, 
                            新考试日期, 
                            新考试时间, 
                            新教室, 
                            申请理由
                        FROM exam_adjustment_requests
                        WHERE 状态 = '待审核'
                    '''
                    print(f"尝试简单查询: {simple_query}")
                    self.db_manager.cursor.execute(simple_query)
                    requests = self.db_manager.cursor.fetchall()
                    print(f"简单查询结果行数: {len(requests)}")

            # 清空表格
            self.request_table.setRowCount(0)

            # 填充表格
            for row, request in enumerate(requests):
                self.request_table.insertRow(row)
                for col, value in enumerate(request):
                    self.request_table.setItem(row, col, QTableWidgetItem(str(value)))

            # 显示结果统计 - 不再弹出消息框
            # if not requests:
            #     QMessageBox.information(self, '提示', '没有待审核的申请')

        except Exception as e:
            error_message = f'加载申请失败：{str(e)}'
            QMessageBox.warning(self, '错误', error_message)
            import traceback
            traceback_info = traceback.format_exc()
            print(f"详细错误信息: {traceback_info}")
            # 显示数据库结构信息
            try:
                # 检查相关表结构
                self.db_manager.cursor.execute("PRAGMA table_info(exam_adjustment_requests)")
                r_cols = self.db_manager.cursor.fetchall()
                print("申请表结构:", r_cols)
                
                self.db_manager.cursor.execute("PRAGMA table_info(exam_arrangements)")
                ea_cols = self.db_manager.cursor.fetchall()
                print("考试安排表结构:", ea_cols)
                
                self.db_manager.cursor.execute("PRAGMA table_info(courses)")
                c_cols = self.db_manager.cursor.fetchall()
                print("课程表结构:", c_cols)
            except Exception as schema_e:
                print(f"获取表结构失败: {str(schema_e)}")

    def check_exam_conflict(self, new_date, new_time, new_room):
        """
        检查新的考试安排是否与现有安排冲突
        """
        try:
            query = '''
                SELECT COUNT(*) FROM exam_arrangements 
                WHERE 考试日期 = ? AND 考试时间 = ? AND 教室编号 = ?
            '''
            self.db_manager.cursor.execute(query, (new_date, new_time, new_room))
            conflict_count = self.db_manager.cursor.fetchone()[0]
            return conflict_count > 0
        except Exception as e:
            QMessageBox.warning(self, '错误', f'检查冲突失败：{str(e)}')
            return True

    def approve_request(self):
        # 获取选中的申请
        current_row = self.request_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请选择要审核的申请')
            return

        # 获取申请详情
        request_id = self.request_table.item(current_row, 0).text()
        new_date = self.request_table.item(current_row, 7).text()
        new_time = self.request_table.item(current_row, 8).text()
        new_room = self.request_table.item(current_row, 9).text()

        # 检查是否有冲突
        if self.check_exam_conflict(new_date, new_time, new_room):
            QMessageBox.warning(self, '冲突', '新的考试安排与现有安排冲突，无法通过')
            return

        try:
            # 更新考试安排
            update_arrangement_query = '''
                UPDATE exam_arrangements 
                SET 考试日期 = ?, 考试时间 = ?, 教室编号 = ?
                WHERE arrangement_id = (
                    SELECT arrangement_id FROM exam_adjustment_requests 
                    WHERE request_id = ?
                )
            '''
            self.db_manager.cursor.execute(update_arrangement_query, 
                                           (new_date, new_time, new_room, request_id))

            # 更新申请状态
            update_request_query = '''
                UPDATE exam_adjustment_requests 
                SET 状态 = '已同意', 审核人 = ?, 审核备注 = ?
                WHERE request_id = ?
            '''
            self.db_manager.cursor.execute(update_request_query, 
                                           ('管理员', '审核通过', request_id))

            self.db_manager.conn.commit()
            QMessageBox.information(self, '成功', '考场调整申请已通过')
            
            # 重新加载申请列表
            self.load_requests()

        except Exception as e:
            self.db_manager.conn.rollback()
            QMessageBox.warning(self, '错误', f'审核失败：{str(e)}')

    def reject_request(self):
        # 获取选中的申请
        current_row = self.request_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请选择要审核的申请')
            return

        # 获取申请ID
        request_id = self.request_table.item(current_row, 0).text()

        try:
            # 更新申请状态为已拒绝
            update_query = '''
                UPDATE exam_adjustment_requests 
                SET 状态 = '已拒绝', 审核人 = ?, 审核备注 = ?
                WHERE request_id = ?
            '''
            self.db_manager.cursor.execute(update_query, 
                                           ('管理员', '审核未通过', request_id))

            self.db_manager.conn.commit()
            QMessageBox.information(self, '成功', '考场调整申请已拒绝')
            
            # 重新加载申请列表
            self.load_requests()

        except Exception as e:
            self.db_manager.conn.rollback()
            QMessageBox.warning(self, '错误', f'操作失败：{str(e)}') 