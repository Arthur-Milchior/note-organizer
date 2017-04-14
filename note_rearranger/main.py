# -*- coding: utf-8 -*-

"""
This file is part of the Note Rearranger add-on for Anki

Main Module, hooks add-on methods into Anki

Copyright: Glutanimate 2017
License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl-3.0.en.html
"""

from aqt.qt import *

from aqt.browser import Browser
from aqt.utils import tooltip

from anki.hooks import addHook, wrap

from .forms import rearranger
from .notetable import NoteTable


class RearrangerDialog(QDialog):
    """Main dialog"""
    def __init__(self, browser):
        super(RearrangerDialog, self).__init__(parent=browser)
        self.browser = browser
        self.mw = browser.mw

        # load qt-designer form:
        self.f = rearranger.Ui_Dialog()
        self.f.setupUi(self)
        self.table = NoteTable(self)
        self.f.tableLayout.addWidget(self.table)
        self.f.buttonBox.accepted.connect(self.onAccept)
        self.f.buttonBox.rejected.connect(self.onReject)
        self.fillTable()
        self.table.cellClicked.connect(self.onCellClicked)

        # TODO: handle mw.reset events (especially note deletion)


    def reject(self):
        """Notify browser of close event"""
        self.browser._rearranger = None
        super(RearrangerDialog, self).reject()


    def focusNid(self, nid):
        cell = self.table.findItems(nid, Qt.MatchFixedString)
        if cell:
            self.table.setCurrentItem(cell[0])


    def onCellClicked(self, row, col):
        """Sync row change to Browser"""
        mods = QApplication.keyboardModifiers()
        if mods & (Qt.ShiftModifier | Qt.ControlModifier):
            return # nothing to focus when multiple items are selected
        nid = self.table.item(row, 0).text()
        cids = self.mw.col.db.list(
                "select id from cards where nid = ? order by ord", nid)
        cid = None
        for c in cids:
            if c in self.browser.model.cards:
                cid = c
                break
        if cid:
            self.browser.focusCid(cid)


    def fillTable(self):
        model = self.browser.model
        t = self.table
        data = []
        notes = []
        nids = []

        # sort and eliminate duplicates
        for row, cid in enumerate(model.cards):
            c = self.browser.col.getCard(cid)
            nid = c.note().id
            if nid not in nids:
                notes.append((nid, row))
                nids.append(nid)

        notes.sort()

        # get browser model data for rows
        for idx, (nid, row) in enumerate(notes):
            data.append([str(nid)])
            for col, val in enumerate(model.activeCols):
                index = model.index(row, col)
                # We suppose data are strings
                data[idx].append(model.data(index, Qt.DisplayRole))



        # set table data
        t.setColumnCount(len(model.activeCols) + 1)
        t.setHorizontalHeaderLabels(["Note ID"] + model.activeCols)
        t.setRowCount(len(data))
        for row, columns in enumerate(data):
            for col, value in enumerate(columns):
                t.setItem(row,col,QTableWidgetItem(value))


    def onAccept(self):
        res = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                res.append(item.text())
            else:
                res.append(None)
        print res
        # TODO: Confirmation dialog?
        self.close()


    def onReject(self):
        self.close()

        
def onBrowserRowChanged(self, current, previous):
    """Sync row position to Rearranger"""
    if not self._rearranger:
        return
    nid = str(self.card.nid)
    self._rearranger.focusNid(nid)

def onBrowserClose(self, evt):
    """Close with browser"""
    if self._rearranger:
        self._rearranger.close()

def onRearrange(self):
    """Invoke Rearranger window"""
    if self._rearranger:
        self._rearranger.show()
        return
    if len(self.model.cards) >= 1000:
        tooltip("Loading data", parent=self.mw)
    self._rearranger = RearrangerDialog(self)
    self._rearranger.show()


def setupMenu(self):
    """Setup menu entries and hotkeys"""
    self.menRrng = QMenu(_("&Rearranger"))
    action = self.menuBar().insertMenu(
                self.mw.form.menuTools.menuAction(), self.menRrng)
    menu = self.menRrng
    menu.addSeparator()
    a = menu.addAction('Rearrange Notes...')
    a.setShortcut(QKeySequence("Ctrl+R"))
    a.triggered.connect(self.onRearrange)


# Hooks, etc.:

Browser._rearranger = None
addHook("browser.setupMenus", setupMenu)
Browser.onRearrange = onRearrange
Browser.onRowChanged = wrap(Browser.onRowChanged, onBrowserRowChanged, "after")
Browser.closeEvent = wrap(Browser.closeEvent, onBrowserClose, "before")