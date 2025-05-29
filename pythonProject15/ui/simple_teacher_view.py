import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QMessageBox, 
                             QApplication)
from PyQt5.QtCore import Qt
from models.database import DatabaseManager

class SimpleTeacherView(QWidget):
    def __init__(self, teacher_name):
        super().__init__()
        self.teacher_name = teacher_name
        self.db_manager = DatabaseManager()
        self.setWindowTitle(f'考试安排查看 - {self.teacher_name}')
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # 标题标签
        title_label = QLabel(f'欢迎 {self.teacher_name} 老师')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet('font-size: 18px; font-weight: bold;')
        main_layout.addWidget(title_label)
        
        # 功能按钮
        button_layout = QHBoxLayout()
        refresh_button = QPushButton('刷新')
        refresh_button.clicked.connect(self.refresh_exam_arrangements)
        button_layout.addWidget(refresh_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 表格
        self.exam_table = QTableWidget()
        self.exam_table.setColumnCount(5)
        self.exam_table.setHorizontalHeaderLabels(['课程名称', '考试日期', '考试时间', '教室名称', '考试人数'])
        main_layout.addWidget(self.exam_table)
        
        self.setLayout(main_layout)
        
        # 加载数据
        self.refresh_exam_arrangements()
        
    def refresh_exam_arrangements(self):
        try:
            # 查询考试安排 - 修正JOIN条件
            query = '''
                SELECT 
                    c.课程名称, 
                    ea.考试日期, 
                    ea.考试时间, 
                    er.教室名称,
                    ea.考试人数
                FROM exam_arrangements ea
                JOIN courses c ON ea.课程号 = c.id
                JOIN exam_rooms er ON ea.教室编号 = er.教室编号
                WHERE c.教师 = ?
            '''
            
            # 打印查询语句和参数进行调试
            print(f"执行查询: {query}")
            print(f"查询参数: {self.teacher_name}")
            
            try:
                self.db_manager.cursor.execute(query, (self.teacher_name,))
                arrangements = self.db_manager.cursor.fetchall()
                print(f"查询结果行数: {len(arrangements)}")
            except Exception as query_error:
                print(f"SQL查询执行失败: {str(query_error)}")
                # 尝试修改JOIN条件
                alternative_query = '''
                    SELECT 
                        c.课程名称, 
                        ea.考试日期, 
                        ea.考试时间, 
                        er.教室名称,
                        ea.考试人数
                    FROM exam_arrangements ea
                    JOIN courses c ON ea.course_id = c.id
                    JOIN exam_rooms er ON ea.教室编号 = er.教室编号
                    WHERE c.教师 = ?
                '''
                print(f"尝试备选查询: {alternative_query}")
                try:
                    self.db_manager.cursor.execute(alternative_query, (self.teacher_name,))
                    arrangements = self.db_manager.cursor.fetchall()
                    print(f"备选查询结果行数: {len(arrangements)}")
                except Exception as alt_error:
                    print(f"备选SQL查询也失败: {str(alt_error)}")
                    # 再次尝试另一种JOIN条件
                    second_alt_query = '''
                        SELECT 
                            c.课程名称, 
                            ea.考试日期, 
                            ea.考试时间, 
                            er.教室名称,
                            ea.考试人数
                        FROM exam_arrangements ea
                        JOIN courses c ON ea.arrangement_id = c.id
                        JOIN exam_rooms er ON ea.教室编号 = er.教室编号
                        WHERE c.教师 = ?
                    '''
                    print(f"尝试第二备选查询: {second_alt_query}")
                    try:
                        self.db_manager.cursor.execute(second_alt_query, (self.teacher_name,))
                        arrangements = self.db_manager.cursor.fetchall()
                        print(f"第二备选查询结果行数: {len(arrangements)}")
                    except Exception as second_alt_error:
                        print(f"第二备选SQL查询也失败: {str(second_alt_error)}")
                        # 最后一次尝试
                        last_attempt_query = '''
                            SELECT 
                                c.课程名称, 
                                ea.考试日期, 
                                ea.考试时间, 
                                er.教室名称,
                                ea.考试人数
                            FROM exam_arrangements ea
                            JOIN courses c ON 1=1
                            JOIN exam_rooms er ON ea.教室编号 = er.教室编号
                            WHERE c.教师 = ?
                            LIMIT 10
                        '''
                        print(f"尝试最后查询: {last_attempt_query}")
                        self.db_manager.cursor.execute(last_attempt_query, (self.teacher_name,))
                        arrangements = self.db_manager.cursor.fetchall()
                        print(f"最后查询结果行数: {len(arrangements)}")

            # 清空表格
            self.exam_table.setRowCount(0)

            # 填充表格
            for row_data in arrangements:
                row_position = self.exam_table.rowCount()
                self.exam_table.insertRow(row_position)
                for col, value in enumerate(row_data):
                    self.exam_table.setItem(row_position, col, QTableWidgetItem(str(value)))
            
            # 显示统计信息
            if not arrangements:
                QMessageBox.information(self, '提示', '没有找到您的考试安排')

        except Exception as e:
            error_message = f'加载考试安排失败：{str(e)}'
            QMessageBox.warning(self, '错误', error_message)
            import traceback
            traceback_info = traceback.format_exc()
            print(f"详细错误信息: {traceback_info}")
            # 显示更多数据库信息
            try:
                # 检查课程表结构
                self.db_manager.cursor.execute("PRAGMA table_info(courses)")
                courses_cols = self.db_manager.cursor.fetchall()
                print("课程表结构:", courses_cols)
                
                # 检查考试安排表结构
                self.db_manager.cursor.execute("PRAGMA table_info(exam_arrangements)")
                ea_cols = self.db_manager.cursor.fetchall()
                print("考试安排表结构:", ea_cols)
                
                # 检查教室表结构
                self.db_manager.cursor.execute("PRAGMA table_info(exam_rooms)")
                er_cols = self.db_manager.cursor.fetchall()
                print("教室表结构:", er_cols)
            except Exception as schema_e:
                print(f"获取表结构失败: {str(schema_e)}")


def main():
    app = QApplication(sys.argv)
    view = SimpleTeacherView('张三')  # 测试用
    view.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 