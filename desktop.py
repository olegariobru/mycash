from __future__ import annotations
import os,shutil,sqlite3,sys,uuid
from datetime import date,datetime
from pathlib import Path
from PySide6.QtCore import Qt,QDate,QUrl,QTimer,QPropertyAnimation,QSequentialAnimationGroup,QPauseAnimation,QEasingCurve,QVariantAnimation
from PySide6.QtGui import QDesktopServices,QFontDatabase
from PySide6.QtWidgets import *

BASE=Path(sys.executable).parent if getattr(sys,"frozen",False) else Path(__file__).parent
RESOURCES=Path(getattr(sys,"_MEIPASS",Path(__file__).parent));LOCAL=Path(os.getenv("LOCALAPPDATA",BASE));PREFERRED=LOCAL/"mycash";LEGACY=LOCAL/"ClarezaFinanceira"
def prepare_data():
 try:
  PREFERRED.mkdir(parents=True,exist_ok=True);old=LEGACY/"consultoria.db";new=PREFERRED/"consultoria.db"
  if old.exists() and not new.exists():
   shutil.copy2(old,new)
   if (LEGACY/"anexos").exists():shutil.copytree(LEGACY/"anexos",PREFERRED/"anexos",dirs_exist_ok=True)
  return PREFERRED
 except OSError:
  fallback=BASE/"dados";fallback.mkdir(parents=True,exist_ok=True);return fallback
DATA=prepare_data();FILES=DATA/"anexos";DB=DATA/"consultoria.db";FILES.mkdir(parents=True,exist_ok=True)
def db():c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init_db():
 with db() as c:
  c.executescript("""CREATE TABLE IF NOT EXISTS configuracao(id INTEGER PRIMARY KEY CHECK(id=1),meta REAL NOT NULL);CREATE TABLE IF NOT EXISTS metas_mensais(mes TEXT PRIMARY KEY,meta REAL NOT NULL CHECK(meta>=0));CREATE TABLE IF NOT EXISTS gastos(id INTEGER PRIMARY KEY AUTOINCREMENT,data TEXT NOT NULL,descricao TEXT NOT NULL,categoria TEXT NOT NULL,fornecedor TEXT,valor REAL NOT NULL CHECK(valor>0),observacao TEXT,anexo TEXT,anexo_original TEXT,criado_em TEXT NOT NULL);INSERT OR IGNORE INTO configuracao VALUES(1,19000);""")
  if c.execute("SELECT COUNT(*) FROM metas_mensais").fetchone()[0]==0:
   old=c.execute("SELECT meta FROM configuracao WHERE id=1").fetchone()[0];c.execute("INSERT INTO metas_mensais VALUES(?,?)",(date.today().strftime("%Y-%m"),old))
def number(raw):
 v=raw.strip().replace("R$","").replace(" ","")
 if "," in v:v=v.replace(".","").replace(",",".")
 v=float(v)
 if v<=0:raise ValueError
 return v
def brl(v):return "R$ "+f"{float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
def period_key(raw):return datetime.strptime(raw.strip(),"%m-%Y").strftime("%Y-%m")
STYLE="""QWidget{font-family:'Roboto';font-size:13px;color:#18201e}QMainWindow,QWidget#root{background:#f3f5f3}QFrame#card{background:white;border:1px solid #e1e7e3;border-radius:13px}QLabel#eyebrow{font-family:'Montserrat';color:#2e6f55;font-size:10px;font-weight:700;letter-spacing:1px}QLabel#title{font-family:'Montserrat';font-size:35px;font-weight:700}QLabel#subtitle,QLabel#muted{color:#68736f}QLabel#metric{font-family:'Montserrat';font-size:23px;font-weight:700}QLineEdit,QComboBox,QDateEdit,QTextEdit{background:#fbfcfb;border:1px solid #dce3df;border-radius:7px;padding:8px}QLineEdit:focus,QComboBox:focus,QDateEdit:focus,QTextEdit:focus{border:1px solid #2e6f55}QPushButton{font-family:'Montserrat';border:0;border-radius:7px;padding:9px 13px;background:#eaf0ec;color:#2e6f55;font-weight:600}QPushButton:hover{background:#dcebe3}QPushButton#primary{background:#2e6f55;color:white;padding:11px}QPushButton#primary:hover{background:#245b45}QPushButton#danger{color:#a8453d}QHeaderView::section{font-family:'Montserrat';background:#e9eeeb;border:0;padding:8px;font-weight:600}QTableWidget{background:white;border:0;gridline-color:#edf0ee;selection-background-color:#dcebe3;selection-color:#18201e}QTableWidget::item{padding:5px}"""

class App(QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle("mycash");self.resize(1120,720);self.setMinimumSize(930,620);self.attachment=None;self.motion_widgets=[];self.animations=[]
  root=QWidget(objectName="root");self.setCentralWidget(root);outer=QVBoxLayout(root);outer.setContentsMargins(30,24,30,28);outer.setSpacing(16)
  head=QHBoxLayout();brand=QVBoxLayout();brand.setSpacing(1);brand.addWidget(self.lbl("mycash","title"));brand.addWidget(self.lbl("Seus gastos e documentos em um só lugar.","subtitle"));head.addLayout(brand);head.addStretch();period=QVBoxLayout();period.addWidget(self.lbl("PERÍODO (MM-AAAA)","eyebrow"));self.month=QLineEdit(date.today().strftime("%m-%Y"));self.month.setInputMask("00-0000;_");self.month.setFixedWidth(140);self.month.editingFinished.connect(self.refresh);period.addWidget(self.month);head.addLayout(period);outer.addLayout(head)
  metrics=QGridLayout();metrics.setSpacing(14);self.goal,self.goal_note=self.make_metric(metrics,0,"META DO MÊS",True);self.total,self.total_note=self.make_metric(metrics,1,"TOTAL GASTO");self.remaining,self.remaining_note=self.make_metric(metrics,2,"DISPONÍVEL");outer.addLayout(metrics)
  content=QHBoxLayout();content.setSpacing(16);content.addWidget(self.form_card(),4);content.addWidget(self.list_card(),7);outer.addLayout(content,1);self.refresh();QTimer.singleShot(40,self.animate_entrance)
 def lbl(self,text,name=""):x=QLabel(text);x.setObjectName(name);return x
 def card(self):return QFrame(objectName="card")
 def make_metric(self,grid,col,title,editable=False):
  card=self.card();layout=QVBoxLayout(card);top=QHBoxLayout();top.addWidget(self.lbl(title,"eyebrow"));top.addStretch()
  if editable:b=QPushButton("Editar");b.clicked.connect(self.edit_goal);top.addWidget(b)
  layout.addLayout(top);value=self.lbl("R$ 0,00","metric");note=self.lbl("","muted");layout.addWidget(value);layout.addWidget(note);grid.addWidget(card,0,col);self.motion_widgets.append(card);return value,note
 def form_card(self):
  card=self.card();layout=QVBoxLayout(card);layout.setContentsMargins(20,18,20,18);layout.addWidget(self.lbl("NOVO REGISTRO","eyebrow"));layout.addWidget(self.lbl("Lançar gasto","metric"));form=QFormLayout();form.setSpacing(9)
  self.desc=QLineEdit();self.desc.setPlaceholderText("Ex.: Mercadorias");form.addRow("Descrição",self.desc);self.value=QLineEdit();self.value.setPlaceholderText("300,00");form.addRow("Valor",self.value);self.when=QDateEdit(QDate.currentDate());self.when.setCalendarPopup(True);self.when.setDisplayFormat("dd/MM/yyyy");form.addRow("Data",self.when);self.category=QComboBox();self.category.addItems(["Mercadorias","Fornecedores","Impostos","Serviços","Transporte","Outros"]);form.addRow("Categoria",self.category);self.supplier=QLineEdit();self.supplier.setPlaceholderText("Opcional");form.addRow("Fornecedor",self.supplier);self.notes=QTextEdit();self.notes.setFixedHeight(60);form.addRow("Observação",self.notes);layout.addLayout(form)
  self.attach=QPushButton("Anexar nota / DANFE — PDF ou imagem");self.attach.clicked.connect(self.choose_file);layout.addWidget(self.attach);save=QPushButton("Salvar lançamento",objectName="primary");save.clicked.connect(self.save);layout.addWidget(save);layout.addStretch();self.motion_widgets.append(card);return card
 def list_card(self):
  card=self.card();layout=QVBoxLayout(card);layout.setContentsMargins(20,18,20,18);head=QHBoxLayout();names=QVBoxLayout();names.addWidget(self.lbl("HISTÓRICO","eyebrow"));names.addWidget(self.lbl("Gastos do mês","metric"));head.addLayout(names);head.addStretch();op=QPushButton("Abrir anexo");op.clicked.connect(self.open_file);delete=QPushButton("Excluir",objectName="danger");delete.clicked.connect(self.delete);head.addWidget(op);head.addWidget(delete);layout.addLayout(head)
  self.table=QTableWidget(0,6);self.table.setHorizontalHeaderLabels(["Data","Descrição","Categoria","Fornecedor","Valor","Documento"]);self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection);self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);self.table.setTextElideMode(Qt.TextElideMode.ElideRight);self.table.setWordWrap(False);self.table.verticalHeader().setVisible(False);header=self.table.horizontalHeader();header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
  for col,mode in enumerate([QHeaderView.ResizeMode.ResizeToContents,QHeaderView.ResizeMode.Stretch,QHeaderView.ResizeMode.ResizeToContents,QHeaderView.ResizeMode.Stretch,QHeaderView.ResizeMode.ResizeToContents,QHeaderView.ResizeMode.ResizeToContents]):header.setSectionResizeMode(col,mode)
  self.table.doubleClicked.connect(self.open_file);layout.addWidget(self.table);self.motion_widgets.append(card);return card
 def animate_entrance(self):
  group=QSequentialAnimationGroup(self)
  for widget in self.motion_widgets:
   effect=QGraphicsOpacityEffect(widget);widget.setGraphicsEffect(effect);effect.setOpacity(0);animation=QPropertyAnimation(effect,b"opacity",self);animation.setDuration(320);animation.setStartValue(0.0);animation.setEndValue(1.0);animation.setEasingCurve(QEasingCurve.Type.OutCubic);group.addAnimation(animation);group.addAnimation(QPauseAnimation(55))
  group.start();self.animations.append(group)
 def animate_money(self,label,target):
  animation=QVariantAnimation(self);animation.setDuration(520);animation.setStartValue(0.0);animation.setEndValue(float(target));animation.setEasingCurve(QEasingCurve.Type.OutCubic);animation.valueChanged.connect(lambda value,l=label:l.setText(brl(value)));animation.start();self.animations.append(animation)
 def current_period(self):
  try:return period_key(self.month.text())
  except ValueError:QMessageBox.warning(self,"Período inválido","Use o formato MM-AAAA.");return None
 def edit_goal(self):
  month=self.current_period()
  if not month:return
  dialog=QDialog(self);dialog.setWindowTitle("Meta mensal");form=QFormLayout(dialog);field=QLineEdit()
  with db() as c:row=c.execute("SELECT meta FROM metas_mensais WHERE mes=?",(month,)).fetchone();field.setText(f"{(row['meta'] if row else 0):.2f}")
  form.addRow("Nova meta",field);save=QPushButton("Atualizar",objectName="primary");form.addRow(save)
  def update():
   try:
    with db() as c:c.execute("INSERT INTO metas_mensais(mes,meta) VALUES(?,?) ON CONFLICT(mes) DO UPDATE SET meta=excluded.meta",(month,number(field.text())))
    dialog.accept();self.refresh()
   except ValueError:QMessageBox.warning(dialog,"Valor inválido","Informe uma meta maior que zero.")
  save.clicked.connect(update);dialog.exec()
 def choose_file(self):
  path,_=QFileDialog.getOpenFileName(self,"Selecionar nota ou comprovante","","Documentos (*.pdf *.png *.jpg *.jpeg *.webp)")
  if not path:return
  if Path(path).stat().st_size>12*1024*1024:QMessageBox.warning(self,"Arquivo grande","O anexo deve ter no máximo 12 MB.");return
  self.attachment=Path(path);self.attach.setText(self.attachment.name)
 def save(self):
  stored=None
  try:
   description=self.desc.text().strip()
   if not description:raise ValueError("Informe a descrição.")
   amount=number(self.value.text());day=self.when.date().toString("yyyy-MM-dd")
   if self.attachment:stored=f"{uuid.uuid4().hex}{self.attachment.suffix.lower()}";shutil.copy2(self.attachment,FILES/stored)
   with db() as c:c.execute("INSERT INTO gastos(data,descricao,categoria,fornecedor,valor,observacao,anexo,anexo_original,criado_em) VALUES(?,?,?,?,?,?,?,?,?)",(day,description,self.category.currentText(),self.supplier.text().strip(),amount,self.notes.toPlainText().strip(),stored,self.attachment.name if self.attachment else None,datetime.now().isoformat(timespec="seconds")))
   self.desc.clear();self.value.clear();self.supplier.clear();self.notes.clear();self.attachment=None;self.attach.setText("Anexar nota / DANFE — PDF ou imagem");self.month.setText(datetime.strptime(day,"%Y-%m-%d").strftime("%m-%Y"));self.refresh();QMessageBox.information(self,"Salvo","Gasto lançado com sucesso.")
  except ValueError as e:
   if stored:(FILES/stored).unlink(missing_ok=True)
   QMessageBox.warning(self,"Dados inválidos",str(e) or "Revise os campos.")
 def selected_id(self):
  row=self.table.currentRow()
  if row<0:QMessageBox.information(self,"Selecione","Selecione um lançamento na lista.");return None
  return int(self.table.item(row,0).data(Qt.ItemDataRole.UserRole))
 def open_file(self):
  item=self.selected_id()
  if not item:return
  with db() as c:row=c.execute("SELECT anexo FROM gastos WHERE id=?",(item,)).fetchone()
  if not row or not row["anexo"]:QMessageBox.information(self,"Sem anexo","Este lançamento não possui documento.");return
  path=FILES/row["anexo"]
  if path.exists():QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
  else:QMessageBox.warning(self,"Não encontrado","O arquivo do anexo não foi encontrado.")
 def delete(self):
  item=self.selected_id()
  if not item or QMessageBox.question(self,"Excluir lançamento","Excluir o lançamento e seu anexo?")!=QMessageBox.StandardButton.Yes:return
  with db() as c:row=c.execute("SELECT anexo FROM gastos WHERE id=?",(item,)).fetchone();c.execute("DELETE FROM gastos WHERE id=?",(item,))
  if row and row["anexo"]:(FILES/row["anexo"]).unlink(missing_ok=True)
  self.refresh()
 def refresh(self):
  month=self.current_period()
  if not month:return
  with db() as c:goal_row=c.execute("SELECT meta FROM metas_mensais WHERE mes=?",(month,)).fetchone();goal=goal_row["meta"] if goal_row else 0;rows=c.execute("SELECT * FROM gastos WHERE substr(data,1,7)=? ORDER BY data DESC,id DESC",(month,)).fetchall()
  total=sum(x["valor"] for x in rows);left=goal-total;self.animate_money(self.goal,goal);self.goal_note.setText(f"{min(total/goal*100 if goal else 0,100):.1f}% utilizado");self.animate_money(self.total,total);self.total_note.setText(f"{len(rows)} lançamento(s)");self.animate_money(self.remaining,abs(left));self.remaining.setStyleSheet("color:#a8453d" if left<0 else "");self.remaining_note.setText("Acima da meta" if left<0 else "Até o limite mensal");self.table.setRowCount(len(rows))
  for r,item in enumerate(rows):
   vals=[datetime.strptime(item["data"],"%Y-%m-%d").strftime("%d/%m/%Y"),item["descricao"],item["categoria"],item["fornecedor"] or "—",brl(item["valor"]),"Sim" if item["anexo"] else "—"]
   for col,val in enumerate(vals):
    cell=QTableWidgetItem(val);cell.setToolTip(val)
    if col in (0,5):cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    elif col==4:cell.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
    else:cell.setTextAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
    self.table.setItem(r,col,cell)
   self.table.item(r,0).setData(Qt.ItemDataRole.UserRole,item["id"])
def center(window):
 screen=window.screen() or QApplication.primaryScreen()
 if screen:frame=window.frameGeometry();frame.moveCenter(screen.availableGeometry().center());window.move(frame.topLeft())
def main():
 init_db();application=QApplication(sys.argv)
 for font in (RESOURCES/"assets"/"fonts").glob("*.ttf"):QFontDatabase.addApplicationFont(str(font))
 application.setStyleSheet(STYLE);window=App();window.setWindowOpacity(0.0);window.show();center(window);fade=QPropertyAnimation(window,b"windowOpacity");fade.setDuration(420);fade.setStartValue(0.0);fade.setEndValue(1.0);fade.setEasingCurve(QEasingCurve.Type.OutCubic);fade.start();window.animations.append(fade)
 if "--self-test" in sys.argv:QTimer.singleShot(1800,application.quit)
 return application.exec()
if __name__=="__main__":
 try:sys.exit(main())
 except Exception as error:
  log=BASE/"mycash-error.log";log.write_text(f"{type(error).__name__}: {error}\n",encoding="utf-8");raise

