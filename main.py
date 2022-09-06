import sys
import pandas as pd
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import uic
from database import model


login_form, login_window = uic.loadUiType("assets/login.ui")
main_form, main_window = uic.loadUiType("assets/main.ui")
data_form, data_window = uic.loadUiType("assets/data_mahasiswa.ui")


def showError(type, text):
    msg = QMessageBox()
    if (type == "Critical"):
        icon = QMessageBox.Critical
    elif (type == "Information"):
        icon = QMessageBox.Information
    else: 
        icon = QMessageBox.Warning
    msg.setIcon(icon)
    msg.setText(text)
    msg.setWindowTitle(type)
    msg.exec_()

class LoginValidation(login_window, login_form):
    def __init__(self):
        login_window.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("Login Window")
        self.setWindowIcon(QtGui.QIcon('assets/logo.png'))

        self.label.setPixmap(QtGui.QPixmap('assets/absensi.png'))

        model.createDatabase()
        self.login_submit.clicked.connect(self.loginCheck)
    
    def loginCheck(self):
        try:
            # get input
            username = self.login_username.text()
            password = self.login_password.text()
            # get user from database by username
            response, data = model.getUser(username)
            # validating username
            if response == False:
                showError("Critical", data)
            elif response == True:
                if (password == data[2]):
                    self.main = MainProgram(data)
                    self.main.show()
                    self.close()
                else:
                    showError("Critical", "Username atau Password salah.")
            else:
                showError("Information", "Failed while fetching database.")
        except Exception as e:
                ("   Critical", f"Error. {e}")

class MainProgram(main_window, main_form):
    def __init__(self, session):
        main_window.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("e-Presensi | Universitas Jenderal Achmad Yani Yogyakarta")
        self.setWindowIcon(QtGui.QIcon('assets/logo.png'))

        # initialize session
        self.username, self.password, self.level = session[1], session[2], session[3]

        # set current date in select_date
        self.currentDate = QDate.currentDate()
        self.select_date.setDate(self.currentDate)
        self.select_date.setCalendarPopup(True)
        self.date = self.currentDate.toString(Qt.ISODate)

        # get all log from database
        logs = model.viewLog()
        for log in logs:
            self.editLog(log[0], log[1])

        # insert current log
        self.editLog(self.date, f"User {self.username} telah login.", db=True)
        
        # get all data from database
        self.refreshTable()
        self.select_date.editingFinished.connect(self.refreshTable)

        # menu absensi
        self.search_nim.editingFinished.connect(self.profileMahasiswa)
        self.menu_submit.clicked.connect(self.prosesAbsen)
        self.mahasiswaButton_add.clicked.connect(self.tambahMahasiswa)
        self.mahasiswaButton_remove.clicked.connect(self.hapusMahasiswa)
        self.userButton_add.clicked.connect(self.tambahUser)
        self.userButton_remove.clicked.connect(self.hapusUser)
        self.settingButton_confirm.clicked.connect(self.ubahAdmin)
        self.log_clear.clicked.connect(self.hapusLog)
        self.export_button.clicked.connect(self.exportData)
        self.show_dataMahasiswa.clicked.connect(self.show_mahasiswa)
        self.settingButton_logout.clicked.connect(self.logout)
    
    def refreshTable(self):
        try:
            self.table_data.setRowCount(0)
            selected_date = self.select_date.date()
            absens = model.getAbsensi(selected_date.toString(Qt.ISODate))
            if len(absens) < 0 :
                pass
            else:
                for absen in absens:
                    mahasiswa = model.getMahasiswa(absen[0])
                    row = self.table_data.rowCount()
                    self.table_data.insertRow(row)
                    self.table_data.setItem(row, 0, QtWidgets.QTableWidgetItem(str(mahasiswa[1][0])))
                    self.table_data.setItem(row, 1, QtWidgets.QTableWidgetItem(mahasiswa[1][1]))
                    self.table_data.setItem(row, 2, QtWidgets.QTableWidgetItem(mahasiswa[1][2]))
                    self.table_data.setItem(row, 3, QtWidgets.QTableWidgetItem(mahasiswa[1][3]))
                    self.table_data.setItem(row, 4, QtWidgets.QTableWidgetItem(absen[1]))
                    self.table_data.setItem(row, 5, QtWidgets.QTableWidgetItem(absen[2]))
        except Exception as e:
             showError("Critical", f"Error. {e}")

    def profileMahasiswa(self):
        try:
            nim = self.search_nim.text()
            response, data = model.getMahasiswa(nim)
            if response == False:
                showError("Critical", data)
            elif response == True:
                self.labelMenu_name.setText(":" + data[1])
                self.labelMenu_nim.setText(":" + str(data[0]))
                self.labelMenu_prodi.setText(":" + data[2])
                self.labelMenu_fakultas.setText(":" + data[3])
                self.nama, self.nim, self.prodi, self.fakultas = data[1], data[0], data[2], data[3]
            else:
                showError("Information", "Failed to get data.")
        except Exception as e:
             showError("Critical", f"Error. {e}")
    
    def prosesAbsen(self):
        try:
            status = self.select_status.currentText()
            model.absenDB(self.nim, status, self.date)
            showError("Information", f"Mahasiswa {self.nama} telah berhasil melakukan presensi")
            self.editLog(self.date, f"Mahasiswa {self.nama} telah melakukan presensi dengan keterangan: {status}")
            self.select_date.setDate(self.currentDate)
            self.refreshTable()
        except Exception as e:
             showError("Critical", f"Error. {e}")
    
    def tambahMahasiswa(self):
        try:
            nama = self.mahasiswaInput_name.text()
            nim = self.mahasiswaInput_nim.text()
            prodi = self.mahasiswaInput_prodi.text()
            fakultas = self.mahasiswaInput_fakultas.text()
            model.addMahasiswa(nim, nama, prodi, fakultas)
            showError("Information", "Data Mahasiswa berhasil ditambahkan.")
            self.editLog(self.date, f"User {self.username} telah menambahkan Mahasiswa dengan NIM: {nim}", db=True)
        except Exception as e:
            showError("Critical", f"Error. {e}")
    
    def hapusMahasiswa(self):
        try:
            nim = self.mahasiswaInput_rnim.text()
            model.removeMahasiswa(nim)
            showError("Information", "Data Mahasiswa berhasil dihapus.")
            self.editLog(self.date, f"User {self.username} telah menghapus Mahasiswa dengan NIM: {nim}")
        except Exception as e:
             showError("Critical", f"Error. {e}")
    
    def tambahUser(self):
        try:
            username = self.userInput_username.text()
            password = self.userInput_password.text()
            if self.level == 0:
                model.addUser(username, password)
                showError("Information", "User telah berhasil ditambahkan.")
                self.editLog(self.date, f"User {self.username} telah berhasil menambahkan User: {username}")
            else:
                showError("Critical", f"Gagal menambahkan user. Tidak memiliki akses untuk menambah user.")
        except Exception as e:
             showError("Critical", f"Error. {e}")

    def hapusUser(self):
        try:
            username = self.userInput_rusername.text()
            if self.level == 0:
                model.removeUser(username)
                showError("Information", "User telah berhasil dihapus.")
                self.editLog(self.date, f"User {self.username} telah berhasil menghapus User: {username}")
            else:
                showError("Critical", "Gagal menghapus user. Tidak memiliki akses untuk menghapus user.")
        except Exception as e:
             showError("Critical", f"Error. {e}")

    def ubahAdmin(self):
        try:
            adminpw = self.settingInput_adminpw.text()
            newpw = self.settingInput_newpw.text()
            if self.password == adminpw:
                model.changeAdmin(self.username, newpw)
                showError("Information", "Berhasil mengubah password.")
                self.editLog(self.date, f"User {self.username} berhasil mengubah password.")
            else:
                showError("Critical", "Gagal mengubah password. Password tidak sama")
        except Exception as e:
             showError("Critical", f"Error. {e}")
    
    def hapusLog(self):
        try:
            if self.log_withdb.isChecked():
                model.clearLog()
                self.log_listview.clear()
                showError("Information", "Log berhasil dihapus.")
            else:
                self.log_listview.clear()
                showError("Information", "Log berhasil dihapus.")
        except Exception as e:
             showError("Critical", f"Error. {e}")
    
    def editLog(self, tanggal, text, db = False):
        try:
            if db == True:
                model.insertLog(tanggal, text)
            self.log_label.setText(f"[{tanggal}] {text}")
            self.log_label.show()
            self.log_listview.addItem(f"[{tanggal}] {text}")
        except Exception as e:
             showError("Critical", f"Error. {e}")
    
    def exportData(self):
        try:
            df = pd.DataFrame(columns=["NIM", "Nama", "Program Studi", "Fakultas", "Status", "Tanggal"])
            rowCount = self.table_data.rowCount()
            for row in range(rowCount):
                nim = self.table_data.item(row, 0).text()
                nama = self.table_data.item(row, 1).text()
                prodi = self.table_data.item(row, 2).text()
                fakultas = self.table_data.item(row, 3).text()
                status = self.table_data.item(row, 4).text()
                tanggal = self.table_data.item(row, 5).text()
                df = df.append({"NIM": nim, "Nama": nama, "Program Studi": prodi, "Fakultas": fakultas, "Status": status, "Tanggal": tanggal}, ignore_index=True)
            path = QtWidgets.QFileDialog.getSaveFileName(self, "Save as", "", "CSV Files (*.csv)")
            df.to_csv(path[0], index=False)
            showError("Information", "Export Successfully.")
            self.editLog(self.date, f"User {self.username} telah berhasil melakukan export.", db=True)
        except Exception as e:
            showError("Critical", "Export Failed." + e)
    
    def show_mahasiswa(self):
        self.dataMahsiswa = DataMahasiswa()
        self.dataMahsiswa.show()
    
    def logout(self):
        showError("Information", "Logout Successfully.")
        self.editLog(self.date, f"User {self.username} telah berhasil logout.", db=True)
        self.login = LoginValidation()
        self.login.show()
        self.close()



class DataMahasiswa(data_window, data_form):
    def __init__(self):
        data_window.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("Data Mahasiswa | Universitas Jenderal Achmad Yani Yogyakarta")
        self.setWindowIcon(QtGui.QIcon('assets/logo.png'))
        self.filterBy_dataMahasiswa.hide()
        self.show_tableMahasiswa()
        self.filter_dataMahasiswa.currentIndexChanged['QString'].connect(self.enableWidget)
        self.filterBy_dataMahasiswa.editingFinished.connect(self.show_tableMahasiswa)
    
    def enableWidget(self, currentIndex):
        if currentIndex != "All":
            self.filterBy_dataMahasiswa.show()
        else:
            self.filterBy_dataMahasiswa.hide()
            self.show_tableMahasiswa()
     
    def show_tableMahasiswa(self):
        try:
            filter = self.filter_dataMahasiswa.currentText()
            value = self.filterBy_dataMahasiswa.text()
            self.table_dataMahasiswa.setRowCount(0)
            datas = model.showMahasiswa(filter, value)
            for mahasiswa in datas:
                row = self.table_dataMahasiswa.rowCount()
                self.table_dataMahasiswa.insertRow(row)
                self.table_dataMahasiswa.setItem(row, 0, QtWidgets.QTableWidgetItem(str(mahasiswa[0])))
                self.table_dataMahasiswa.setItem(row, 1, QtWidgets.QTableWidgetItem(mahasiswa[1]))
                self.table_dataMahasiswa.setItem(row, 2, QtWidgets.QTableWidgetItem(mahasiswa[2]))
                self.table_dataMahasiswa.setItem(row, 3, QtWidgets.QTableWidgetItem(mahasiswa[3]))
        except Exception as e:
             showError("Critical", f"Error. {e}")




if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    login_app = LoginValidation()
    login_app.show()
    sys.exit(app.exec_())

        
        

