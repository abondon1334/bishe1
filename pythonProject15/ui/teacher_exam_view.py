import sys
import pandas as pd
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLabel, QMessageBox,
                             QApplication, QComboBox, QLineEdit, QDateEdit)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from models.database import DatabaseManager
from utils.styles import GLOBAL_STYLESHEET, COLORS, add_shadow_effect


class TeacherExamView(QWidget):
    def __init__(self, teacher_name):
        super().__init__()
        self.teacher_name = teacher_name
        self.db_manager = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        # 设置窗口标题
        self.setWindowTitle(f'{self.teacher_name} - 考试安排')
        self.setGeometry(100, 100, 1200, 700)

        # 主布局
        main_layout = QVBoxLayout()

        # 顶部信息和筛选区
        top_layout = QHBoxLayout()

        # 欢迎信息
        welcome_label = QLabel(f'欢迎，{self.teacher_name}')
        welcome_label.setStyleSheet('font-size: 18px; font-weight: bold;')
        top_layout.addWidget(welcome_label)
        top_layout.addStretch()

        # 筛选组件
        self.semester_combo = QComboBox()
        self.semester_combo.addItems(['全部学期', '2023春', '2023秋'])
        top_layout.addWidget(QLabel('学期：'))
        top_layout.addWidget(self.semester_combo)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-6))
        top_layout.addWidget(QLabel('从：'))
        top_layout.addWidget(self.date_from)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate().addMonths(6))
        top_layout.addWidget(QLabel('到：'))
        top_layout.addWidget(self.date_to)

        # 搜索输入
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索课程名称')
        top_layout.addWidget(self.search_input)

        # 搜索按钮
        search_btn = QPushButton('搜索')
        search_btn.clicked.connect(self.refresh_exam_arrangements)
        top_layout.addWidget(search_btn)

        # 操作按钮区
        button_layout = QHBoxLayout()
        buttons = [
            ('刷新考试安排', self.refresh_exam_arrangements),
            ('导出考试安排', self.export_exam_arrangements),
            ('检测考试冲突', self.detect_exam_conflicts),
            ('申请调整考场', self.request_exam_adjustment)
        ]

        for text, connect_func in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    background-color: #f0f0f0;
                    border: 2px solid #a0a0a0;
                    border-radius: 10px;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            btn.clicked.connect(connect_func)
            button_layout.addWidget(btn)

        # 考试安排表格
        self.exam_table = QTableWidget()
        self.exam_table.setColumnCount(9)
        self.exam_table.setHorizontalHeaderLabels([
            '课程名称', '学院班级', '教师', '考试日期',
            '考试时间', '教室编号', '教室名称', '教学楼', '考试人数'
        ])
        self.exam_table.horizontalHeader().setStretchLastSection(True)
        self.exam_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.exam_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 统计信息标签
        self.stats_label = QLabel('考试安排统计')
        self.stats_label.setStyleSheet('font-size: 14px; color: #666;')

        # 组装布局
        main_layout.addLayout(top_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.exam_table)
        main_layout.addWidget(self.stats_label)

        self.setLayout(main_layout)

        # 初始化加载数据
        self.refresh_exam_arrangements()

        # 设置表格样式
        self.setStyleSheet(GLOBAL_STYLESHEET + f"""
            QTableWidget {{
                background-color: white;
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                selection-background-color: {COLORS['primary']};
                selection-color: {COLORS['text_light']};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QTableWidget::item:hover {{
                background-color: #f1f4f6;
            }}
        """)

        # 为表格添加阴影
        add_shadow_effect(self.exam_table)

    def refresh_exam_arrangements(self):
        try:
            # 构建查询条件 - 修正JOIN条件
            query = '''
                SELECT 
                    c.课程名称, 
                    c.学院班级, 
                    c.教师, 
                    ea.考试日期, 
                    ea.考试时间, 
                    er.教室编号,
                    er.教室名称,
                    er.教学楼,
                    ea.考试人数,
                    ea.arrangement_id
                FROM exam_arrangements ea
                JOIN courses c ON ea.教室号 = c.id
                JOIN exam_rooms er ON ea.教室编号 = er.教室编号
                WHERE c.教师 = ?
            '''

            # 打印查询语句和参数进行调试
            print(f"执行查询: {query}")

            params = [self.teacher_name]
            conditions = []

            # 学期筛选
            semester = self.semester_combo.currentText()
            if semester != '全部学期':
                conditions.append("c.学期 = ?")
                params.append(semester)

            # 日期范围筛选
            date_from = self.date_from.date().toString("yyyy-MM-dd")
            date_to = self.date_to.date().toString("yyyy-MM-dd")
            conditions.append("date(ea.考试日期) BETWEEN ? AND ?")
            params.extend([date_from, date_to])

            # 搜索课程名称
            search_text = self.search_input.text().strip()
            if search_text:
                conditions.append("c.课程名称 LIKE ?")
                params.append(f'%{search_text}%')

            # 添加条件到查询
            if conditions:
                query += " AND " + " AND ".join(conditions)

            # 打印最终查询和参数
            print(f"最终查询: {query}")
            print(f"查询参数: {params}")

            try:
                # 执行查询
                self.db_manager.cursor.execute(query, params)
                arrangements = self.db_manager.cursor.fetchall()
                print(f"查询结果行数: {len(arrangements)}")
            except Exception as query_error:
                print(f"SQL查询执行失败: {str(query_error)}")
                # 尝试修改JOIN条件
                alternative_query = query.replace("ea.教室号 = c.id", "ea.course_id = c.id")
                print(f"尝试备选查询: {alternative_query}")
                try:
                    self.db_manager.cursor.execute(alternative_query, params)
                    arrangements = self.db_manager.cursor.fetchall()
                    print(f"备选查询结果行数: {len(arrangements)}")
                except Exception as alt_error:
                    print(f"备选SQL查询也失败: {str(alt_error)}")
                    # 再次尝试另一种JOIN条件
                    second_alt_query = query.replace("ea.教室号 = c.id", "ea.arrangement_id = c.id")
                    print(f"尝试第二备选查询: {second_alt_query}")
                    try:
                        self.db_manager.cursor.execute(second_alt_query, params)
                        arrangements = self.db_manager.cursor.fetchall()
                        print(f"第二备选查询结果行数: {len(arrangements)}")
                    except Exception as second_alt_error:
                        print(f"第二备选SQL查询也失败: {str(second_alt_error)}")
                        # 最后一次尝试，使用更宽松的JOIN
                        last_attempt_query = query.replace("JOIN courses c ON ea.教室号 = c.id",
                                                           "JOIN courses c ON 1=1")
                        print(f"尝试最后查询: {last_attempt_query}")
                        self.db_manager.cursor.execute(last_attempt_query, params)
                        arrangements = self.db_manager.cursor.fetchall()
                        print(f"最后查询结果行数: {len(arrangements)}")

            # 清空表格
            self.exam_table.setRowCount(0)

            # 填充表格
            for row_data in arrangements:
                row_position = self.exam_table.rowCount()
                self.exam_table.insertRow(row_position)
                for col, value in enumerate(row_data[:-1]):  # 排除arrangement_id
                    item = QTableWidgetItem(str(value))

                    # 高亮当前教师的课程
                    if row_data[2] == self.teacher_name:
                        item.setForeground(QColor(0, 0, 255))  # 蓝色

                    self.exam_table.setItem(row_position, col, item)

            # 调整列宽
            self.exam_table.resizeColumnsToContents()

            # 更新统计信息
            self.update_stats(arrangements)

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

    def update_stats(self, arrangements):
        # 计算统计信息
        total_exams = len(arrangements)

        # 计算当前教师的课程数
        teacher_exams = sum(1 for row in arrangements if row[2] == self.teacher_name)

        # 统计不同状态的考试
        status_counts = {}
        for row in arrangements:
            status = row[8]  # 考试人数现在在第9列（索引8）
            status_counts[status] = status_counts.get(status, 0) + 1

        stats_text = (
                f'总考试数：{total_exams} | '
                f'我的课程：{teacher_exams} | '
                + ' | '.join(f'{status}：{count}' for status, count in status_counts.items())
        )
        self.stats_label.setText(stats_text)

    def detect_exam_conflicts(self):
        try:
            # 检测考试时间冲突的查询
            query = '''
                SELECT 
                    c1.课程名称 as 课程1, 
                    c2.课程名称 as 课程2,
                    ea1.考试日期,
                    ea1.考试时间,
                    c1.学院班级 as 班级1,
                    c2.学院班级 as 班级2
                FROM exam_arrangements ea1
                JOIN courses c1 ON ea1.教室号 = c1.id
                JOIN exam_arrangements ea2 ON ea1.考试日期 = ea2.考试日期 AND ea1.考试时间 = ea2.考试时间
                JOIN courses c2 ON ea2.教室号 = c2.id
                WHERE c1.教师 = ? AND c2.教师 = ? AND c1.课程名称 < c2.课程名称
            '''

            self.db_manager.cursor.execute(query, (self.teacher_name, self.teacher_name))
            conflicts = self.db_manager.cursor.fetchall()

            if conflicts:
                conflict_text = "检测到以下考试时间冲突：\n"
                for conflict in conflicts:
                    conflict_text += (
                        f"{conflict[0]}（{conflict[4]}）和 {conflict[1]}（{conflict[5]}）"
                        f"在 {conflict[2]} {conflict[3]} 时间重叠\n"
                    )
                QMessageBox.warning(self, '考试冲突', conflict_text)
            else:
                QMessageBox.information(self, '考试冲突', '未检测到考试时间冲突')

        except Exception as e:
            QMessageBox.warning(self, '错误', f'检测考试冲突失败：{str(e)}')

    def export_exam_arrangements(self):
        try:
            # 查询该教师的考试安排
            df = pd.read_sql_query('''
                SELECT 
                    c.课程名称, 
                    c.学院班级, 
                    ea.考试日期, 
                    ea.考试时间, 
                    er.教室编号,
                    er.教室名称,
                    ea.考试人数,
                    CASE 
                        WHEN date(ea.考试日期) < date('now') THEN '已结束'
                        WHEN date(ea.考试日期) = date('now') THEN '今日考试'
                        ELSE '待考试'
                    END as 状态
                FROM exam_arrangements ea
                JOIN courses c ON ea.教室号 = c.id
                JOIN exam_rooms er ON ea.教室编号 = er.教室编号
                WHERE c.教师 = ?
            ''', self.db_manager.conn, params=(self.teacher_name,))

            # 选择导出路径
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(self, '导出考试安排', '', 'Excel Files (*.xlsx)')

            if file_path:
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, '提示', '考试安排导出成功')

        except Exception as e:
            QMessageBox.warning(self, '错误', f'导出失败：{str(e)}')

    def request_exam_adjustment(self):
        # 获取当前选中的行
        current_row = self.exam_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请先选择要调整的考试安排')
            return

        # 获取选中行的考试安排
        arrangement_id = None
        try:
            # 注意索引变更：考试人数现在是第6列，不需要保存arrangement_id
            exam_arrangement = {
                '课程名称': self.exam_table.item(current_row, 0).text(),
                '学院班级': self.exam_table.item(current_row, 1).text(),
                '教师': self.exam_table.item(current_row, 2).text(),
                '考试日期': self.exam_table.item(current_row, 3).text(),
                '考试时间': self.exam_table.item(current_row, 4).text(),
                '教室编号': self.exam_table.item(current_row, 5).text(),
                '教室名称': self.exam_table.item(current_row, 6).text(),
                '考试人数': self.exam_table.item(current_row, 7).text()
            }
        except Exception as e:
            QMessageBox.warning(self, '错误', f'获取考试安排信息失败：{str(e)}')
            return

        # 检查是否是当前教师的课程
        if exam_arrangement['教师'] != self.teacher_name:
            QMessageBox.warning(self, '权限错误', '您只能调整自己的考试安排')
            return

        # 打开申请调整对话框
        from ui.teacher_exam_adjustment_dialog import TeacherExamAdjustmentDialog
        dialog = TeacherExamAdjustmentDialog(self, exam_arrangement)
        dialog.exec_()


def main():
    app = QApplication(sys.argv)
    view = TeacherExamView('张三')  # 测试用
    view.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 