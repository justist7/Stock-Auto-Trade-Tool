import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import pandas as pd
from my_invest import *
import json

csv_test = pd.read_csv('pdno.csv')
pdno_dict = dict()

for index, row in csv_test.iterrows():
    pdno_dict[row['종목코드']] = row['종목명']

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.comp_odno_sets = self.load_data('comp_odno_sets')
        self.auto_infos = self.load_data('auto_infos')

    def load_data(self, data_name):
        try:
            with open(data_name+ '.json', 'r', encoding='UTF-8') as f:
                result = json.load(f)
        except:
            result = []
        return result

    def save_data(self, data, data_name):
        with open(data_name + '.json', 'w', encoding='UTF-8') as f:
            json.dump(data, f)
        return

    def initUI(self):
        menubar = self.menuBar()

        # 메뉴바에 '창1' 메뉴 아이템을 생성하고 triggered 시그널을 show_label 메서드에 연결
        menu_action1 = menubar.addAction('자동 주문 조회')
        menu_action1.triggered.connect(self.show_label)

        # 메뉴바에 '창2' 메뉴 아이템을 생성하고 triggered 시그널을 auto_order 메서드에 연결
        menu_action2 = menubar.addAction('자동 주문 실행')
        menu_action2.triggered.connect(self.auto_order)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.vbox = QVBoxLayout(self.central_widget)
        # 계좌 정보 불러오기
        self.accounts = sendAccounts()

        #자동주문 계좌번호 초기화
        #self.auto_odnos = []

        self.setGeometry(100, 100, 2000, 1000)
        self.setWindowTitle('주식 거래 데이터 정렬')
        self.show()

    def clear_layout(self, layout):
        '''
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget():
                if isinstance(item.widget(), QComboBox):
                    item.widget().clear()
                else:
                    item.widget().hide()  # 위젯을 직접 숨기도록 수정
            elif item.layout():
                self.clear_layout(item.layout()) #레이아웃일경우 재귀함수로 내부 위젯/레이아웃 검색하여 숨김
        '''
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.clear_layout(item.layout())

    def expanding_policy(self, layout):
        for i in range(layout.count()):a
            item = layout.itemAt(i)
            if item.widget():
                item.widget().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            elif item.layout():
                self.expanding_policy(item.layout())

    def show_label(self):
        self.clear_layout(self.vbox)
        self.view_accounts = list(self.accounts.keys())
        self.view_states = [0,1]

        # 계좌, 체결/미체결 체크박스
        hbox_checkboxes = QHBoxLayout()

        self.account_label = QLabel('계좌: ', self)
        hbox_checkboxes.addWidget(self.account_label)
        self.account_checkboxes = []
        for acntName in list(self.accounts.keys()):
            checkbox = QCheckBox(acntName, self)
            self.account_checkboxes.append(checkbox)
            checkbox.setChecked(True)
            hbox_checkboxes.addWidget(checkbox)
            self.view_accounts.append(acntName)
            checkbox.stateChanged.connect(lambda: self.view_accounts.append(acntName) if not acntName in self.view_accounts else self.view_accounts.remove(acntName))
            checkbox.stateChanged.connect(self.view_show_label)

        self.state_label = QLabel('체결 여부: ', self)
        hbox_checkboxes.addWidget(self.state_label)
        self.state_checkboxes = []
        for stateName in ['체결','미체결','취소']:
            checkbox = QCheckBox(stateName, self)
            self.state_checkboxes.append(checkbox)
            if stateName != '취소':
                checkbox.setChecked(True)
            hbox_checkboxes.addWidget(checkbox)
            self.view_states.append(stateName)
            checkbox.stateChanged.connect(lambda: self.view_states.append(stateName) if not stateName in self.view_states else self.view_states.remove(stateName))
            checkbox.stateChanged.connect(self.view_show_label)

        #hbox_checkboxes.setAlignment(Qt.Alignment)
        self.vbox.addLayout(hbox_checkboxes)
        
        #real <-> test
        #self.view_show_label()
        self.test_show_label()

    def test_show_label(self):
        self.selected_view_data = [
            ['테스트계좌', '서울식품', '004410', '1', '180', '1', '0', '1', '1', '1', '1', '미체결'],
            ['가나다', '땡땡전자', '123456', '101010', '1', '1', '1', '1', '1', '1', '1', '체결'],
            ['abc', '똥똥증권', '515151', '234234', '1', '1', '1', '1', '1', '1', '1', '체결'],
            ]

        # 표
        self.table = QTableWidget(self)
        self.table.setRowCount(len(self.selected_view_data))
        if len(self.selected_view_data) != 0:
            self.table.setColumnCount(len(self.selected_view_data[0]) + 1)  # 열 하나 추가 (삭제 버튼용)
        self.table.setHorizontalHeaderLabels(['계좌', '종목명', '종목번호', '매도 주문번호', '매도 호가', '매도 수량', '매도 체결수량', '매수 주문번호', '매수 호가', '매수 수량', '매수 체결수량', '체결 완료여부', '주문 취소'])

        # 표에 데이터 채우기
        for i, row in enumerate(self.selected_view_data):
            for j, item in enumerate(row):
                table_item = QTableWidgetItem(item)
                if j != len(row):  # 삭제 버튼 열이 아닌 경우에만 셀을 읽기 전용으로 설정
                    table_item.setFlags(table_item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(i, j, table_item)

            # 삭제 버튼 추가
            cancel_button = QPushButton('취소'+str(i), self)
            cancel_button.clicked.connect(lambda state, row=i: self.test_cancel_auto_order(row))
            self.table.setCellWidget(i, len(row), cancel_button)

        # 표의 각 항목에 클릭 이벤트 추가
        self.table.horizontalHeader().sectionClicked.connect(self.sort_table)

        # 레이아웃 구성
        self.vbox.addWidget(self.table)

        self.expanding_policy(self.vbox)
        
        #self.show()

    def test_cancel_auto_order(self, view_row_index):
        # 데이터에서 행 제거
        if 0 <= view_row_index < len(self.selected_view_data):
            reply = QMessageBox.question(
                self,
                '자동 주문 취소 확인',
                '정말 취소하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                print('view_row_index:', view_row_index)
                print('self.selected_view_data[view_row_index]:')
                print(self.selected_view_data[view_row_index])

    def view_show_label(self):
        # 데이터
        self.all_order = getAllOrders()
        #[0'계좌', 1'종목명', 2'종목번호', 3'매도 주문번호', 4'매도 호가', 5'매도 수량', 6'매도 체결수량', 7'매수 주문번호', 8'매수 호가', 9'매수 수량', 10'매수 체결수량', 11'주문 상태']
        self.view_data = [['' for _ in range(13)] for _ in range(len(self.comp_odno_sets))]
        self.selected_view_data =[]

        for index, odnos in enumerate(self.comp_odno_sets):
            sell_comp_odno, buy_comp_odno = odnos
            print('line 127')
            print(self.view_data[index])
            
            if sell_comp_odno != '':
                sell_data = self.all_order[sell_comp_odno]
                print('sell_data')
                print(sell_data)

                self.view_data[index][0] = sell_data['acntName']
                self.view_data[index][1] = sell_data['prdt_name']
                self.view_data[index][2] = sell_data['pdno']

                self.view_data[index][3] = sell_comp_odno
                self.view_data[index][4] = sell_data['ord_unpr']
                self.view_data[index][5] = sell_data['ord_qty']
                self.view_data[index][6] = sell_data['tot_ccld_qty']

                if sell_data['order_ccld']:
                    self.view_data[index][11] = '매도 체결'
                if sell_data['cncl_yn'] == 'y' or sell_data['cncl_yn'] == 'Y':
                    self.view_data[index][11] = '매도 취소'

            if buy_comp_odno != '':
                buy_data = self.all_order[buy_comp_odno]
                print('buy_data')
                print(buy_data)

                if buy_comp_odno == '':
                    self.view_data[index][0] = buy_data['acntName']
                    self.view_data[index][1] = buy_data['prdt_name']
                    self.view_data[index][2] = buy_data['pdno']
                    
                self.view_data[index][7] = buy_comp_odno
                self.view_data[index][8] = buy_data['ord_unpr']
                self.view_data[index][9] = buy_data['ord_qty']
                self.view_data[index][10] = buy_data['tot_ccld_qty']

                if buy_data['order_ccld']:
                    self.view_data[index][11] = '매수 체결'
                if buy_data['cncl_yn'] == 'y' or buy_data['cncl_yn'] == 'Y':
                    self.view_data[index][11] = '매도 취소'

        for data in self.view_data:
            if data[0] in self.view_accounts:
                if ('체결' in data[11] and '체결' in self.view_states) or ('체결' not in data[11] and '미체결' in self.view_states):
                    self.selected_view_data.append(data)

        #테스트용 데이타
        '''
        self.selected_view_data = [
            ]
        '''

        # 표
        self.table = QTableWidget(self)
        self.table.setRowCount(len(self.selected_view_data))
        if len(self.selected_view_data) != 0:
            self.table.setColumnCount(len(self.selected_view_data[0]) + 1)  # 열 하나 추가 (삭제 버튼용)
        self.table.setHorizontalHeaderLabels(['계좌', '종목명', '종목번호', '매도 주문번호', '매도 호가', '매도 수량', '매도 체결수량', '매수 주문번호', '매수 호가', '매수 수량', '매수 체결수량', '체결 완료여부', '주문 취소'])

        # 표에 데이터 채우기
        for i, row in enumerate(self.selected_view_data):
            for j, item in enumerate(row):
                table_item = QTableWidgetItem(item)
                if j != len(row):  # 삭제 버튼 열이 아닌 경우에만 셀을 읽기 전용으로 설정
                    table_item.setFlags(table_item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(i, j, table_item)

            # 삭제 버튼 추가
            cancel_button = QPushButton('취소'+str(i), self)
            cancel_button.clicked.connect(lambda state, row=i: self.cancel_auto_order(row))
            self.table.setCellWidget(i, len(row), cancel_button)

        # 표의 각 항목에 클릭 이벤트 추가
        self.table.horizontalHeader().sectionClicked.connect(self.sort_table)

        # 레이아웃 구성
        self.vbox.addWidget(self.table)

        self.expanding_policy(self.vbox)
        
        #self.show()

    def pdno2name(self, pdno):
        if pdno in pdno_dict.keys():
            self.product_number.setText(pdno_dict[pdno])
        else:
            self.product_number.setText('')

    def auto_order(self):
        self.clear_layout(self.vbox)

        # 종목번호 입력란
        self.product_number_label = QLabel('종목번호:', self)
        self.product_number_edit = QLineEdit(self)
        self.product_number = QLabel('', self)
        self.vbox.addWidget(self.product_number_label)
        self.vbox.addWidget(self.product_number_edit)
        self.vbox.addWidget(self.product_number)
        
        self.product_number_edit.textChanged.connect(lambda: self.pdno2name(self.product_number_edit.text()))

        # 수평 레이아웃을 사용하여 '매도 호가', '매도량' 입력란 나란히 표시
        hbox_sell = QHBoxLayout()
        self.sell_checkbox = QCheckBox('매도', self)
        self.sell_checkbox.setChecked(True)
        self.sell_account_label = QLabel('계좌:', self)
        self.sell_account_combobox = QComboBox(self)
        self.sell_account_combobox.addItems(['']+list(self.accounts.keys()))
        self.sell_price_label = QLabel('호가:', self)
        self.sell_price_edit = QLineEdit(self)
        self.sell_quantity_label = QLabel('매도 수량:', self)
        self.sell_quantity_edit = QLineEdit(self)
        hbox_sell.addWidget(self.sell_checkbox)
        hbox_sell.addWidget(self.sell_account_label)
        hbox_sell.addWidget(self.sell_account_combobox)
        hbox_sell.addWidget(self.sell_price_label)
        hbox_sell.addWidget(self.sell_price_edit)
        hbox_sell.addWidget(self.sell_quantity_label)
        hbox_sell.addWidget(self.sell_quantity_edit)
        self.vbox.addLayout(hbox_sell)

        # 수평 레이아웃을 사용하여 '매수 호가', '매수량' 입력란 나란히 표시
        hbox_buy = QHBoxLayout()
        self.buy_checkbox = QCheckBox('매수', self)
        self.buy_checkbox.setChecked(True)
        self.buy_account_label = QLabel('계좌:', self)
        self.buy_account_combobox = QComboBox(self)
        self.buy_account_combobox.addItems(['']+list(self.accounts.keys()))
        self.buy_price_label = QLabel('호가:', self)
        self.buy_price_edit = QLineEdit(self)
        self.buy_quantity_label = QLabel('매수 수량:', self)
        self.buy_quantity_edit = QLineEdit(self)
        hbox_buy.addWidget(self.buy_checkbox)
        hbox_buy.addWidget(self.buy_account_label)
        hbox_buy.addWidget(self.buy_account_combobox)
        hbox_buy.addWidget(self.buy_price_label)
        hbox_buy.addWidget(self.buy_price_edit)
        hbox_buy.addWidget(self.buy_quantity_label)
        hbox_buy.addWidget(self.buy_quantity_edit)
        self.vbox.addLayout(hbox_buy)

        #편차 입력란
        hbox_deviation = QHBoxLayout()
        self.deviation_label = QLabel('편차:', self)
        self.deviation_edit = QLineEdit(self)
        hbox_deviation.addWidget(self.deviation_label)
        hbox_deviation.addWidget(self.deviation_edit)
        self.vbox.addLayout(hbox_deviation)

        # 확인 버튼
        self.confirm_button = QPushButton('확인', self)
        self.vbox.addWidget(self.confirm_button)

        # 확인 버튼에 클릭 이벤트 연결
        self.confirm_button.clicked.connect(self.set_deviation)
        self.confirm_button.clicked.connect(self.show_confirmation_dialog)

        #self.setLayout(self.vbox)

        # 체크/콤보박스 상태 변화에 따른 이벤트 연결
        self.buy_checkbox.stateChanged.connect(self.toggle_buy_widgets)
        self.sell_checkbox.stateChanged.connect(self.toggle_sell_widgets)
        self.target_sell_account =''
        self.target_buy_account =''
        self.sell_account_combobox.currentIndexChanged.connect(lambda: setattr(self, 'target_sell_account', self.sell_account_combobox.currentText()))
        self.buy_account_combobox.currentIndexChanged.connect(lambda: setattr(self, 'target_buy_account', self.buy_account_combobox.currentText()))

        self.sell_account_combobox.currentIndexChanged.connect(lambda: print(self.target_sell_account))
        self.buy_account_combobox.currentIndexChanged.connect(lambda: print(self.target_buy_account))

        # 초기에는 매수, 매도 입력란 활성화
        self.toggle_buy_widgets(2)
        self.toggle_sell_widgets(2)

        self.expanding_policy(self.vbox)

    def set_deviation(self):
        if self.check_type(self.sell_price_edit.text(), 'int') and self.check_type(self.buy_price_edit.text(), 'int'):
            deviation = (int(self.sell_price_edit.text()) - int(self.buy_price_edit.text()))/2
            self.deviation_edit.setText(str(deviation))

    def check_type(self, string, typo):
        if string=='':
            return False

        ints = ['0','1','2','3','4','5','6','7','8','9']

        if typo=='int':
            for c in string:
                if c not in ints:
                    return False
            if string=='0':
                return True
            if string[0]=='0':
                return False
        if typo=='iscd':
            if string not in pdno_dict.keys():
                return False
        return True

    def show_confirmation_dialog(self):
        # 확인창 생성
        product_number = self.product_number_edit.text()
        sell_price = self.sell_price_edit.text() if self.sell_checkbox.isChecked() else ''
        sell_quantity = self.sell_quantity_edit.text() if self.sell_checkbox.isChecked() else ''
        sell_account = self.target_sell_account if self.sell_checkbox.isChecked() else ''
        buy_price = self.buy_price_edit.text() if self.buy_checkbox.isChecked() else ''
        buy_quantity = self.buy_quantity_edit.text() if self.buy_checkbox.isChecked() else ''
        buy_account = self.target_buy_account if self.buy_checkbox.isChecked() else ''
        deviation = self.deviation_edit.text()

        product_number_text = '종목번호: ' + product_number
        sell_text = '매도계좌: ' + sell_account + '매도호가: ' + sell_price + '원   매도수량: ' + sell_quantity + '주'
        buy_text = '매수계좌: ' + buy_account + '매수호가: ' + buy_price + '원   매수수량: ' + buy_quantity + '주'
        auto_info = dict()
        auto_info['product_number'] = product_number
        auto_info['sell_acntName'] =''
        auto_info['sell_quantity'] = ''
        auto_info['buy_acntName'] = ''
        auto_info['buy_quantity'] = ''
        auto_info['std_price'] = ''
        auto_info['deviation'] = deviation

        if not self.sell_checkbox.isChecked() and not self.buy_checkbox.isChecked():
            reply = QMessageBox.warning(self, '오류', '매도 또는 매수를 선택해야 주문이 가능합니다.')
            return

        reply_text = product_number_text

        if not self.check_type(product_number, 'iscd'):
            reply = QMessageBox.warning(self, '입력 값 오류', '종목 번호 입력 값을 다시 확인해주세요.')
            return

        reply_text += '\n종목명: ' + pdno_dict[product_number]

        if not self.check_type(deviation, 'int') and (not self.sell_checkbox.isChecked() or not self.buy_checkbox.isChecked()):
            reply = QMessageBox.warning(self, '입력 값 오류', '편차 값을 다시 확인해주세요.')
            return

        print('line 345')
        print(self.target_sell_account)
        print(self.target_buy_account)

        if self.sell_checkbox.isChecked():
            if not self.check_type(sell_price, 'int') or not self.check_type(sell_quantity, 'int') or sell_quantity=='0' or self.target_sell_account == '':
                reply = QMessageBox.warning(self, '입력 값 오류', '입력 값을 다시 확인해주세요.')
                return
            auto_info['sell_acntName'] =self.target_sell_account
            auto_info['sell_quantity'] = sell_quantity
            auto_info['std_price'] = str(float(sell_price)-float(deviation))
            reply_text += '\n' + sell_text
        else:
            reply_text += '\n매도 없음'

        if self.buy_checkbox.isChecked():
            if not self.check_type(buy_price, 'int') or not self.check_type(buy_quantity, 'int') or buy_quantity=='0' or self.target_buy_account == '':
                reply = QMessageBox.warning(self, '입력 값 오류', '입력 값을 다시 확인해주세요.')
                return
            auto_info['buy_acntName'] =self.target_buy_account
            auto_info['buy_quantity'] = buy_quantity
            auto_info['std_price'] = str(float(buy_price)+float(deviation))
            reply_text += '\n' + buy_text
        else:
            reply_text += '\n매수 없음'

        reply_text += '\n 편차: ' + deviation
        reply_text += '\n\n자동 주문하시겠습니까?'

        reply = QMessageBox.question(self, '주문 확인', reply_text, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        # 사용자가 'Yes'를 선택한 경우
        if reply == QMessageBox.Yes:
            # 종목번호 및 결과 표시
            print('show_confirmation_dialogue result:')
            print(auto_info)
            self.comp_odno_sets.append(initAutoTrade(auto_info))
            self.auto_infos.append(auto_info)

            #self.result_label.setText(f'자동 주문 완료되었습니다.')
            

    def toggle_buy_widgets(self, state):
        # 매수 체크박스 상태에 따라 매수 입력란 활성화 또는 비활성화
        enabled = state == 2  # 2는 체크된 상태를 나타냄
        self.buy_price_label.setEnabled(enabled)
        self.buy_price_edit.setEnabled(enabled)
        self.buy_quantity_label.setEnabled(enabled)
        self.buy_quantity_edit.setEnabled(enabled)

    def toggle_sell_widgets(self, state):
        # 매도 체크박스 상태에 따라 매도 입력란 활성화 또는 비활성화
        enabled = state == 2  # 2는 체크된 상태를 나타냄
        self.sell_price_label.setEnabled(enabled)
        self.sell_price_edit.setEnabled(enabled)
        self.sell_quantity_label.setEnabled(enabled)
        self.sell_quantity_edit.setEnabled(enabled)

    def show_order_info(self):
        product_number = self.product_number_edit.text()
        sell_price = self.sell_price_edit.text() if self.sell_checkbox.isChecked() else ''
        sell_quantity = self.sell_quantity_edit.text() if self.sell_checkbox.isChecked() else ''
        buy_price = self.buy_price_edit.text() if self.buy_checkbox.isChecked() else ''
        buy_quantity = self.buy_quantity_edit.text() if self.buy_checkbox.isChecked() else ''

        print(f'종목번호: {product_number}')
        print(f'매도 호가: {sell_price}')
        print(f'매도량: {sell_quantity}')
        print(f'매수 호가: {buy_price}')
        print(f'매수량: {buy_quantity}')

    def cancel_auto_order(self, view_row_index):
        # 데이터에서 행 제거
        if 0 <= view_row_index < len(self.selected_view_data):
            reply = QMessageBox.question(
                self,
                '자동 주문 취소 확인',
                '정말 취소하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                real_row_index = view_row_index
                
                data = getAllOrders()
                order_states = autoTradeStates(self.comp_odno_sets, data)
                order_state = order_states[real_row_index]
                comp_odno_set = self.comp_odno_sets.pop(real_row_index)
                self.auto_infos.pop(real_row_index)
                for index, state in enumerate(order_state):
                    if state == False:
                        comp_odno = comp_odno_set[index]
                        comp_key = comp_odno
                        order = data[comp_key]
                        acntName = order['acntName']
                        KRX_FWDG_ORD_ORGNO = order['ord_gno_brno']
                        ORGN_ODNO = order['odno']
                        postCancelOrder(acntName, KRX_FWDG_ORD_ORGNO, ORGN_ODNO)
                
                self.comp
                print('view_row_index:', view_row_index)
                print('real_row_index:', real_row_index)

                #self.selected_view_data.pop(row_index)
                #print(row_index)

                #240312 test
                '''
                # 현재 정렬 정보 저장
                logical_index = self.table.horizontalHeader().sortIndicatorSection()
                order = self.table.horizontalHeader().sortIndicatorOrder()

                # 테이블 위젯 초기화 및 데이터로 다시 테이블 생성
                #self.show_label()

                # 정렬 복원
                if logical_index != -1:
                    self.table.sortItems(logical_index, order)
                    # 정렬 방향 복원
                    self.table.horizontalHeader().setSortIndicator(logical_index, order)
                '''

    def sort_table(self, logical_index):
        order = self.table.horizontalHeader().sortIndicatorOrder()
        if order == Qt.AscendingOrder:
            self.table.sortItems(logical_index, Qt.DescendingOrder)
        else:
            self.table.sortItems(logical_index, Qt.AscendingOrder)

        self.table.horizontalHeader().setSortIndicator(logical_index, order)

        # 모든 열에 대해 정렬 방향 표시 제거
        for i in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(i)
            if header_item and self.table.cellWidget(0, i) is None:
                # 기존에 아이콘이 있을 때만 제거
                if header_item.icon():
                    header_item.setIcon(QIcon())

        # 현재 정렬된 열에 대해 정렬 방향 표시 추가
        current_header_item = self.table.horizontalHeaderItem(logical_index)
        if current_header_item:
            current_header_item.setIcon(QIcon('arrow_down.png' if order == Qt.AscendingOrder else 'arrow_up.png'))

        print('order:', order)
        print('logical_index', logical_index)

    def closeEvent(self, event):
        self.save_data(self.comp_odno_sets, 'comp_odno_sets')
        self.save_data(self.auto_infos, 'auto_infos')
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
