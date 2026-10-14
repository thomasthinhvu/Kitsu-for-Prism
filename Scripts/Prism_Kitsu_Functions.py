# -*- coding: utf-8 -*-
from Prism_Kitsu_Tools_Functions import printText
import add_external_folders

import os
import tempfile
import shutil
import webbrowser

from qt_compat import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from Prism_Kitsu_Global_Functions import *
from Prism_Kitsu_Tools_Functions import *
from Prism_Kitsu_Gazu_Functions import *


class Prism_Kitsu_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        self.project_dict = None
        self.tokens = None
        self.publish_type_dict = None

        self.callbacks = []
        self.registerCallbacks()

    @err_catcher(name=__name__)
    def isActive(self):
        return True

    # -------------------------------------------------------------------------
    # HELPER ĐỌC/GHI CONFIG TƯƠNG THÍCH CẢ PRISM 2 VÀ PRISM 1
    # -------------------------------------------------------------------------
    def getPrjConfig(self, key, dft=None):
        val = self.core.getConfig("kitsu", key, config="project")
        if val is None and hasattr(self.core, "prismIni") and self.core.prismIni:
            val = self.core.getConfig("kitsu", key, configPath=self.core.prismIni)
        return dft if val is None else val

    def setPrjConfig(self, key, val):
        self.core.setConfig("kitsu", key, val=val, config="project")

    def getUserConfig(self, key, dft=None):
        val = self.core.getConfig("kitsu", key, config="user")
        if val is None:
            val = self.core.getConfig("kitsu", key)
        return dft if val is None else val

    def setUserConfig(self, key, val):
        self.core.setConfig("kitsu", key, val=val, config="user")

    # -------------------------------------------------------------------------
    # ĐĂNG KÝ CALLBACKS CHUẨN PRISM 2
    # -------------------------------------------------------------------------
    @err_catcher(name=__name__)
    def registerCallbacks(self):
        cb_map = [
            ("onProjectChanged", self.onProjectChanged),
            # User Settings
            ("userSettings_loadUI", self.userSettings_loadUI),
            ("prismSettings_loadUI", self.prismSettings_loadUI),
            ("prismSettings_loadSettings", self.prismSettings_loadSettings),
            ("prismSettings_saveSettings", self.prismSettings_saveSettings),
            # Project Settings (Tách riêng trong Prism 2)
            ("projectSettings_loadUI", self.projectSettings_loadUI),
            ("postProjectSettingsLoad", self.postProjectSettingsLoad),
            ("preProjectSettingsSave", self.preProjectSettingsSave),
            # Project Browser & Context Menus
            ("onProjectBrowserStartup", self.onProjectBrowserStartup),
            ("openPBListContextMenu", self.openPBListContextMenu),
            ("projectBrowser_getAssetMenu", self.projectBrowser_getAssetMenu),
            ("projectBrowser_getShotMenu", self.projectBrowser_getShotMenu),
            ("mediaBrowserContextMenuRequested", self.mediaBrowserContextMenuRequested),
            # Entity Creation Dialogs
            ("onAssetDlgOpen", self.createAsset_open),
            ("onCreateAssetDlgOpen", self.createAsset_open),
            ("onAssetCreated", self.onAssetCreated),
            ("onShotDlgOpen", self.editShot_open),
            ("onShotCreated", self.onShotCreated),
        ]
        for cb_name, cb_fn in cb_map:
            self.callbacks.append(
                self.core.registerCallback(cb_name, cb_fn, plugin=self)
            )

    @err_catcher(name=__name__)
    def onProjectChanged(self, *args):
        self.tokens = None
        self.project_dict = None

    # -------------------------------------------------------------------------
    # GIAO DIỆN USER SETTINGS & PROJECT SETTINGS TRÊN PRISM 2
    # -------------------------------------------------------------------------
    @err_catcher(name=__name__)
    def userSettings_loadUI(self, origin):
        self._buildUserAccountUI(origin)

    @err_catcher(name=__name__)
    def prismSettings_loadUI(self, origin):
        self._buildUserAccountUI(origin)
        if hasattr(origin, "w_prjSettings"):
            self._buildProjectSettingsUI(origin)

    def _buildUserAccountUI(self, origin):
        if hasattr(origin, "gb_ksuAccount"):
            return

        origin.gb_ksuAccount = QGroupBox("Kitsu account")
        lo_ksu = QFormLayout()
        origin.gb_ksuAccount.setLayout(lo_ksu)

        origin.l_ksuUserName = QLabel("Username (Email):")
        origin.e_ksuUserName = QLineEdit()
        origin.l_ksuUserPassword = QLabel("Password:")
        origin.e_ksuUserPassword = QLineEdit()
        origin.e_ksuUserPassword.setEchoMode(QLineEdit.Password)

        lo_ksu.addRow(origin.l_ksuUserName, origin.e_ksuUserName)
        lo_ksu.addRow(origin.l_ksuUserPassword, origin.e_ksuUserPassword)

        # Gắn vào tab General/User của Prism 2 hoặc thêm tab mới
        if hasattr(origin, "w_user") and origin.w_user.layout():
            origin.w_user.layout().addWidget(origin.gb_ksuAccount)
        elif hasattr(origin, "tabWidgetPage1") and origin.tabWidgetPage1.layout():
            origin.tabWidgetPage1.layout().insertWidget(1, origin.gb_ksuAccount)
        elif hasattr(origin, "addTab"):
            w_tab = QWidget()
            lo_tab = QVBoxLayout(w_tab)
            lo_tab.addWidget(origin.gb_ksuAccount)
            lo_tab.addStretch()
            origin.addTab(w_tab, "Kitsu")

    @err_catcher(name=__name__)
    def projectSettings_loadUI(self, origin):
        self._buildProjectSettingsUI(origin)

    def _buildProjectSettingsUI(self, origin):
        if hasattr(origin, "gb_ksuIntegration"):
            return

        origin.gb_ksuIntegration = QGroupBox("Kitsu integration")
        origin.w_Kitsu = QWidget()
        lo_ksuI = QHBoxLayout()
        lo_ksuI.addWidget(origin.w_Kitsu)
        origin.gb_ksuIntegration.setLayout(lo_ksuI)
        origin.gb_ksuIntegration.setCheckable(True)
        origin.gb_ksuIntegration.setChecked(False)

        lo_ksu2 = QVBoxLayout()
        origin.w_Kitsu.setLayout(lo_ksu2)

        origin.formLayout = QFormLayout()
        origin.l_ksuSite = QLabel("Kitsu site:")
        origin.e_ksuSite = QLineEdit()
        origin.l_ksuPrjName = QLabel("Project Name:")
        origin.e_ksuPrjName = QLineEdit()

        origin.formLayout.addRow(origin.l_ksuSite, origin.e_ksuSite)
        origin.formLayout.addRow(origin.l_ksuPrjName, origin.e_ksuPrjName)
        lo_ksu2.addLayout(origin.formLayout)

        origin.horizontalLayout = QHBoxLayout()
        origin.chb_syncUserTasks = QCheckBox("Only sync user assigned tasks")
        origin.chb_syncUserTasks.setChecked(True)
        origin.horizontalLayout.addWidget(origin.chb_syncUserTasks)

        origin.ignorePostSync = QCheckBox("Ignore post sync checks")
        origin.ignorePostSync.setChecked(False)
        origin.horizontalLayout.addWidget(origin.ignorePostSync)

        origin.setFirstFrameOne = QCheckBox(
            "Set first frame to 1 (if only frames is set)"
        )
        origin.setFirstFrameOne.setChecked(False)
        origin.horizontalLayout.addWidget(origin.setFirstFrameOne)
        lo_ksu2.addLayout(origin.horizontalLayout)

        origin.b_checkLogin = QPushButton("Check login")
        origin.b_checkLogin.clicked.connect(
            lambda: self.check_connection(
                {
                    "ksuSite": origin.e_ksuSite.text(),
                    "ksuUsername": (
                        origin.e_ksuUserName.text()
                        if hasattr(origin, "e_ksuUserName")
                        else self.getUserConfig("ksuusername", "")
                    ),
                    "ksuPw": (
                        origin.e_ksuUserPassword.text()
                        if hasattr(origin, "e_ksuUserPassword")
                        else self.getUserConfig("ksuuserpassword", "")
                    ),
                    "ksuProjectName": origin.e_ksuPrjName.text(),
                }
            )
        )
        lo_ksu2.addWidget(origin.b_checkLogin)

        origin.stepMappingLayout = QVBoxLayout()
        origin.l_stepMapping = QLabel("Prism Department and Kitsu Task Mappings")
        origin.l_stepMapping.setMinimumHeight(30)
        origin.stepMappingLayout.addWidget(origin.l_stepMapping)

        origin.tw_steps = QTableWidget()
        origin.tw_steps.setMinimumHeight(250)
        origin.tw_steps.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        origin.tw_steps.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        origin.tw_steps.setColumnCount(2)
        origin.tw_steps.horizontalHeader().setHighlightSections(False)
        origin.tw_steps.horizontalHeader().setStretchLastSection(True)
        origin.tw_steps.verticalHeader().setVisible(False)
        origin.tw_steps.verticalHeader().setHighlightSections(False)
        origin.tw_steps.setHorizontalHeaderLabels(["Prism Department/Step", "Kitsu Task Type"])
        origin.stepMappingLayout.addWidget(origin.tw_steps)
        lo_ksu2.addLayout(origin.stepMappingLayout)

        if hasattr(origin, "w_prjSettings") and origin.w_prjSettings.layout():
            origin.w_prjSettings.layout().insertWidget(5, origin.gb_ksuIntegration)
        elif hasattr(origin, "tw_settings"):
            w_tab = QWidget()
            lo_tab = QVBoxLayout(w_tab)
            lo_tab.addWidget(origin.gb_ksuIntegration)
            lo_tab.addStretch()
            origin.tw_settings.addTab(w_tab, "Kitsu")
        elif hasattr(origin, "addTab"):
            origin.addTab(origin.gb_ksuIntegration, "Kitsu")

        origin.gb_ksuIntegration.toggled.connect(
            lambda x: self.prismSettings_ksuToggled(origin, x)
        )

    @err_catcher(name=__name__)
    def check_connection(self, custom_login):
        self.tokens = None
        self.connectToKitsu(custom_login)

    @err_catcher(name=__name__)
    def prismSettings_loadSettings(self, origin, settings):
        if not hasattr(origin, "e_ksuUserName"):
            return
        if settings and "kitsu" in settings:
            origin.e_ksuUserName.setText(settings["kitsu"].get("ksuusername", ""))
            origin.e_ksuUserPassword.setText(
                settings["kitsu"].get("ksuuserpassword", "")
            )
        else:
            origin.e_ksuUserName.setText(self.getUserConfig("ksuusername", ""))
            origin.e_ksuUserPassword.setText(
                self.getUserConfig("ksuuserpassword", "")
            )

    @err_catcher(name=__name__)
    def postProjectSettingsLoad(self, origin, settings):
        self.prismSettings_loadPrjSettings(origin, settings)

    @err_catcher(name=__name__)
    def prismSettings_loadPrjSettings(self, origin, settings):
        if not hasattr(origin, "gb_ksuIntegration"):
            return

        ksu_cfg = (settings or {}).get("kitsu")
        if ksu_cfg is None:
            ksu_cfg = self.core.getConfig("kitsu", config="project") or {}

        origin.gb_ksuIntegration.setChecked(bool(ksu_cfg.get("active", False)))
        origin.e_ksuSite.setText(str(ksu_cfg.get("site", "")))
        origin.e_ksuPrjName.setText(str(ksu_cfg.get("projectname", "")))
        origin.chb_syncUserTasks.setChecked(bool(ksu_cfg.get("usersync", True)))
        origin.ignorePostSync.setChecked(bool(ksu_cfg.get("ignorepostchecks", False)))
        # Đã sửa lỗi copy-paste nhầm sang ignorePostSync ở bản cũ
        origin.setFirstFrameOne.setChecked(bool(ksu_cfg.get("setfirstframeone", False)))

        origin.tw_steps.setRowCount(0)
        stepMapping = ksu_cfg.get("mapping")
        if isinstance(stepMapping, dict) and len(stepMapping) > 0:
            for prismMap, kitsuMap in stepMapping.items():
                rows = origin.tw_steps.rowCount()
                origin.tw_steps.insertRow(rows)
                origin.tw_steps.setItem(rows, 0, QTableWidgetItem(str(prismMap)))
                origin.tw_steps.setItem(rows, 1, QTableWidgetItem(str(kitsuMap)))
        else:
            self.populateMappingTable(origin)

        self.prismSettings_ksuToggled(origin, origin.gb_ksuIntegration.isChecked())

    @err_catcher(name=__name__)
    def prismSettings_saveSettings(self, origin, settings):
        if not hasattr(origin, "e_ksuUserName"):
            return
        if settings is not None:
            if "kitsu" not in settings:
                settings["kitsu"] = {}
            settings["kitsu"]["ksuusername"] = origin.e_ksuUserName.text()
            settings["kitsu"]["ksuuserpassword"] = origin.e_ksuUserPassword.text()

    @err_catcher(name=__name__)
    def preProjectSettingsSave(self, origin, settings):
        self.prismSettings_savePrjSettings(origin, settings)

    @err_catcher(name=__name__)
    def prismSettings_savePrjSettings(self, origin, settings):
        if not hasattr(origin, "gb_ksuIntegration"):
            return
        if settings is None:
            settings = {}
        if "kitsu" not in settings:
            settings["kitsu"] = {}

        settings["kitsu"]["active"] = origin.gb_ksuIntegration.isChecked()
        settings["kitsu"]["site"] = origin.e_ksuSite.text().strip()
        settings["kitsu"]["projectname"] = origin.e_ksuPrjName.text().strip()
        settings["kitsu"]["usersync"] = origin.chb_syncUserTasks.isChecked()
        settings["kitsu"]["ignorepostchecks"] = origin.ignorePostSync.isChecked()
        settings["kitsu"]["setfirstframeone"] = origin.setFirstFrameOne.isChecked()

        stepMapping = {}
        rows = origin.tw_steps.rowCount()
        for i in range(rows):
            item_p = origin.tw_steps.item(i, 0)
            item_k = origin.tw_steps.item(i, 1)
            prismMap = item_p.text().strip() if item_p else ""
            kitsuMap = item_k.text().strip() if item_k else ""
            if prismMap:
                stepMapping[prismMap] = kitsuMap
        settings["kitsu"]["mapping"] = stepMapping

    @err_catcher(name=__name__)
    def prismSettings_ksuToggled(self, origin, checked):
        if hasattr(origin, "w_Kitsu"):
            origin.w_Kitsu.setVisible(checked)
        if hasattr(origin, "gb_ksuAccount"):
            origin.gb_ksuAccount.setVisible(checked)

    # -------------------------------------------------------------------------
    # MENU KITSU TRÊN PROJECT BROWSER CỦA PRISM 2
    # -------------------------------------------------------------------------
    @err_catcher(name=__name__)
    def onProjectBrowserStartup(self, origin):
        ksuMenu = self.pbBrowser_getMenu(origin)
        if ksuMenu and hasattr(origin, "menubar"):
            origin.menubar.addMenu(ksuMenu)

    @err_catcher(name=__name__)
    def pbBrowser_getMenu(self, origin):
        ksu = self.getPrjConfig("active", dft=False)
        if not ksu:
            return None

        ksuMenu = QMenu("Kitsu", origin)

        actksu = QAction("Open Kitsu Project in Browser", origin)
        actksu.triggered.connect(lambda: self.openKitsu("", "project"))
        ksuMenu.addAction(actksu)

        ksuMenu.addSeparator()

        actASL = QAction("Kitsu assets to local", origin)
        actASL.triggered.connect(lambda: self.ksuAssetsToLocal(origin))
        ksuMenu.addAction(actASL)

        actLAS = QAction("Local assets to Kitsu", origin)
        actLAS.triggered.connect(lambda: self.ksuAssetsToKitsu(origin))
        ksuMenu.addAction(actLAS)

        ksuMenu.addSeparator()

        actSSL = QAction("Kitsu shots to local", origin)
        actSSL.triggered.connect(lambda: self.ksuShotsToLocal(origin))
        ksuMenu.addAction(actSSL)

        actLSS = QAction("Local shots to Kitsu", origin)
        actLSS.triggered.connect(lambda: self.ksuShotsToKitsu(origin))
        ksuMenu.addAction(actLSS)

        return ksuMenu

    @err_catcher(name=__name__)
    def openPBListContextMenu(self, origin, rcmenu, listWidget, item, path, *args):
        """Hỗ trợ menu chuột phải vào Shot / Asset trong EntityWidget của Prism 2."""
        if not self.getPrjConfig("active", dft=False):
            return
        if not hasattr(origin, "getCurrentEntities"):
            return

        entities = origin.getCurrentEntities()
        if not entities or len(entities) != 1:
            return

        entity = entities[0]
        e_type = entity.get("type")
        if e_type == "asset":
            asset_name = os.path.basename(entity.get("asset_path", ""))
            ksuAct = QAction("Open in Kitsu", rcmenu)
            ksuAct.triggered.connect(lambda: self.openKitsu(asset_name, "asset"))
            rcmenu.addAction(ksuAct)
        elif e_type == "shot":
            shot_key = self._getShotKey(entity.get("sequence", ""), entity.get("shot", ""), entity.get("episode"))
            ksuAct = QAction("Open in Kitsu", rcmenu)
            ksuAct.triggered.connect(lambda: self.openKitsu(shot_key, "shot"))
            rcmenu.addAction(ksuAct)

    @err_catcher(name=__name__)
    def projectBrowser_getAssetMenu(self, origin, *args):
        if not self.getPrjConfig("active", dft=False):
            return
        # Tương thích cả chữ ký hàm Prism 1 và Prism 2
        if len(args) >= 2 and isinstance(args[0], QMenu):
            menu, entity = args[0], args[1]
            asset_name = os.path.basename(entity.get("asset_path", "")) if isinstance(entity, dict) else str(entity)
            ksuAct = QAction("Open in Kitsu", menu)
            ksuAct.triggered.connect(lambda: self.openKitsu(asset_name, "asset"))
            menu.addAction(ksuAct)
        elif len(args) >= 1:
            assetname = args[0]
            ksuAct = QAction("Open in Kitsu", origin)
            ksuAct.triggered.connect(lambda: self.openKitsu(assetname, "asset"))
            return ksuAct

    @err_catcher(name=__name__)
    def projectBrowser_getShotMenu(self, origin, *args):
        if not self.getPrjConfig("active", dft=False):
            return
        if len(args) >= 2 and isinstance(args[0], QMenu):
            menu, entity = args[0], args[1]
            if isinstance(entity, dict):
                shot_key = self._getShotKey(entity.get("sequence", ""), entity.get("shot", ""), entity.get("episode"))
            else:
                shot_key = str(entity)
            ksuAct = QAction("Open in Kitsu", menu)
            ksuAct.triggered.connect(lambda: self.openKitsu(shot_key, "shot"))
            menu.addAction(ksuAct)
        elif len(args) >= 1:
            shotname = args[0]
            ksuAct = QAction("Open in Kitsu", origin)
            ksuAct.triggered.connect(lambda: self.openKitsu(shotname, "shot"))
            return ksuAct

    # -------------------------------------------------------------------------
    # HOOK KHI TẠO ASSET / SHOT TRONG PRISM 2
    # -------------------------------------------------------------------------
    @err_catcher(name=__name__)
    def createAsset_open(self, origin, *args):
        if not self.getPrjConfig("active", dft=False):
            return
        if hasattr(origin, "w_options") and origin.w_options.layout():
            origin.chb_createInKitsu = QCheckBox("Create asset in Kitsu")
            origin.w_options.layout().insertWidget(0, origin.chb_createInKitsu)
            origin.chb_createInKitsu.setChecked(True)
        elif hasattr(origin, "layout") and origin.layout():
            origin.chb_createInKitsu = QCheckBox("Create asset in Kitsu")
            origin.layout().addWidget(origin.chb_createInKitsu)
            origin.chb_createInKitsu.setChecked(True)

    @err_catcher(name=__name__)
    def onAssetCreated(self, origin, entity, dlg=None, *args):
        if not self.getPrjConfig("active", dft=False):
            return
        check_dlg = dlg or origin
        if hasattr(check_dlg, "chb_createInKitsu") and not check_dlg.chb_createInKitsu.isChecked():
            return
        if isinstance(entity, dict) and entity.get("asset_path"):
            full_path = os.path.join(self._getAssetBasePath(), entity["asset_path"])
            self.createAssets([full_path])

    @err_catcher(name=__name__)
    def editShot_open(self, origin, entity=None, *args):
        if not self.getPrjConfig("active", dft=False):
            return
        if hasattr(origin, "widget") and origin.widget.layout():
            origin.chb_createInKitsu = QCheckBox("Create shot in Kitsu")
            origin.widget.layout().insertWidget(0, origin.chb_createInKitsu)
            origin.chb_createInKitsu.setChecked(True)

    @err_catcher(name=__name__)
    def onShotCreated(self, origin, entity, *args):
        if not self.getPrjConfig("active", dft=False):
            return
        if hasattr(origin, "chb_createInKitsu") and not origin.chb_createInKitsu.isChecked():
            return
        if isinstance(entity, dict) and entity.get("shot"):
            shot_key = self._getShotKey(entity.get("sequence", ""), entity.get("shot", ""), entity.get("episode"))
            self.createShots([shot_key])

    # -------------------------------------------------------------------------
    # PUBLISH TỪ MEDIA BROWSER CỦA PRISM 2
    # -------------------------------------------------------------------------
    @err_catcher(name=__name__)
    def mediaBrowserContextMenuRequested(self, origin, menu, *args):
        if not self.getPrjConfig("active", dft=False):
            return
        ksuAct = QAction("Publish to Kitsu", menu)
        ksuAct.triggered.connect(lambda: self.ksuPublishPrism2(origin))
        menu.addAction(ksuAct)

    @err_catcher(name=__name__)
    def ksuPublishPrism2(self, media_browser):
        if not self.connectToKitsu():
            return

        entity = media_browser.getCurrentEntity() if hasattr(media_browser, "getCurrentEntity") else None
        if not entity:
            QMessageBox.warning(self.core.messageParent, "Kitsu Publish", "No entity selected.")
            return

        e_type = entity.get("type", "shot")
        if e_type == "asset":
            pType = "Asset"
            objectName = os.path.basename(entity.get("asset_path", ""))
            objectID = getID(self, objectName, "Assetinfo")
        else:
            pType = "Shot"
            objectName = self._getShotKey(entity.get("sequence", ""), entity.get("shot", ""), entity.get("episode"))
            objectID = getID(self, objectName, "Shotinfo")

        if not doEntityExist(objectID):
            QMessageBox.warning(
                self.core.messageParent,
                "Kitsu Publish",
                f"This {pType.lower()} ({objectName}) does not exist on Kitsu.\nPlease sync to Kitsu before publishing.",
            )
            return

        res = getPublishTypeDict(self, pType, doStatus=True)
        if not res or res[0] is None:
            return
        self.publish_type_dict, type_status_dict, set_preview, comment_text = res

        cur_version = media_browser.getCurrentVersion() if hasattr(media_browser, "getCurrentVersion") else {}
        taskName = cur_version.get("identifier", "render") if isinstance(cur_version, dict) else "render"
        versionName = cur_version.get("version", "v0001") if isinstance(cur_version, dict) else "v0001"

        files = media_browser.getCurrentSourceFiles() if hasattr(media_browser, "getCurrentSourceFiles") else []
        if not files and hasattr(media_browser, "lw_version"):
            item = media_browser.lw_version.currentItem()
            if item and item.data(Qt.UserRole):
                data = item.data(Qt.UserRole)
                if isinstance(data, dict) and data.get("path"):
                    files = self.core.media.getFilesFromFolder(data["path"])

        if not files:
            QMessageBox.warning(self.core.messageParent, "Kitsu Publish", "No media files found to publish.")
            return

        ext = os.path.splitext(files[0])[1].lower()
        is_video = ext in [".mp4", ".mov", ".avi", ".webm", ".mkv"]
        temp_folder = None
        videoPaths = []

        if not is_video and len(files) >= 1:
            temp_folder = tempfile.mkdtemp()
            outputpath = os.path.join(temp_folder, f"{objectName}_{taskName}_{versionName}.mp4")
            inputpath = files[0]
            if len(files) > 1:
                pad = getattr(self.core, "framePadding", 4)
                base_no_ext = os.path.splitext(inputpath)[0]
                inputpath = base_no_ext[:-pad] + f"%0{pad}d" + ext
            self.core.media.convertMedia(inputpath, 1001, outputpath)
            if os.path.isfile(outputpath):
                videoPaths.append(outputpath)
            else:
                videoPaths.append(files[0])
        else:
            videoPaths.append(files[0])

        user_email = self.getUserConfig("ksuusername", "")
        for video_URL in videoPaths:
            uploadRevision(
                objectID,
                video_URL,
                self.publish_type_dict,
                type_status_dict,
                user_email,
                set_preview,
                comment=f"{taskName} {versionName} - {comment_text}",
            )

        if temp_folder and os.path.isdir(temp_folder):
            shutil.rmtree(temp_folder, ignore_errors=True)

        QMessageBox.information(
            self.core.messageParent,
            "Kitsu Publish",
            f"'{taskName} {versionName}' was published to {self.publish_type_dict['name']} for {pType.lower()} '{objectName}'",
        )
        self.publish_type_dict = None

    # -------------------------------------------------------------------------
    # KẾT NỐI KITSU SERVER
    # -------------------------------------------------------------------------
    def connectToKitsu(self, custom_login=False):
        if self.tokens is not None and isinstance(self.project_dict, dict):
            return True

        silent = False
        if custom_login is False:
            ksuSite = self.getPrjConfig("site", "")
            ksuProjectName = self.getPrjConfig("projectname", "")
            ksuUsername = self.getUserConfig("ksuusername", "")
            ksuPw = self.getUserConfig("ksuuserpassword", "")
            silent = True
        else:
            ksuSite = custom_login.get("ksuSite", "")
            ksuProjectName = custom_login.get("ksuProjectName", "")
            ksuUsername = custom_login.get("ksuUsername", "")
            ksuPw = custom_login.get("ksuPw", "")

        if not ksuSite or not ksuProjectName:
            QMessageBox.warning(
                self.core.messageParent,
                "Kitsu",
                "Not all required information for the Kitsu integration are configured.\nPlease check Project Settings -> Kitsu.",
            )
            return False

        if not ksuUsername or not ksuPw:
            QMessageBox.warning(
                self.core.messageParent,
                "Kitsu",
                "Not all required information for the Kitsu user login are configured.\nPlease check User Settings -> Kitsu.",
            )
            return False

        self.project_dict = Connect(
            self, ksuSite, ksuUsername, ksuPw, ksuProjectName, silent=silent
        )

        if not isinstance(self.project_dict, dict):
            self.tokens = None
            self.project_dict = None
            return False

        return True

    def openKitsu(self, obj_name, section):
        if not self.connectToKitsu():
            return

        if section == "project":
            obj_id = self.project_dict
        else:
            obj_id = getID(self, obj_name, section + "info")

        if not obj_id:
            QMessageBox.warning(
                self.core.messageParent,
                "Kitsu Sync",
                f"Could not find {section} '{obj_name}' ID in local config. Please sync with Kitsu first.",
            )
            return

        try:
            ksuSite = GetUrl(obj_id, section)
            webbrowser.open(ksuSite)
        except Exception:
            QMessageBox.warning(
                self.core.messageParent,
                "Kitsu Sync",
                f"Could not find {section} in Kitsu.",
            )
            removeID(self, obj_name, section + "info")

    # -------------------------------------------------------------------------
    # HELPER XỬ LÝ ENTITY GIỮA PRISM 1 & PRISM 2
    # -------------------------------------------------------------------------
    def _getAssetBasePath(self):
        if hasattr(self.core, "assetPath"):
            return self.core.assetPath
        return self.core.getAssetPath()

    def _getShotBasePath(self):
        if hasattr(self.core, "shotPath"):
            return self.core.shotPath
        return self.core.getShotPath()

    def _getShotKey(self, seq_name, shot_name, ep_name=None):
        key = f"{seq_name}-{shot_name}" if seq_name else shot_name
        if ep_name:
            key = f"{ep_name}.{key}"
        return key

    def _splitShotKey(self, shot_key):
        ep_name = None
        rest = shot_key
        if "." in shot_key and self.project_dict and self.project_dict.get("production_type") == "tvshow":
            ep_name, rest = shot_key.split(".", 1)
        if "-" in rest:
            seq_name, shot_name = rest.split("-", 1)
        else:
            shot_name, seq_name = self.core.entities.splitShotname(rest)
        return ep_name, seq_name, shot_name

    def _createDepartmentAndTask(self, entity_dict, prism_dept, kitsu_task):
        if not prism_dept:
            return
        if hasattr(self.core.entities, "createDepartment"):
            self.core.entities.createDepartment(
                prism_dept, entity_dict, createCat=False
            )
            if kitsu_task:
                self.core.entities.createCategory(
                    entity_dict, prism_dept, kitsu_task
                )
        elif hasattr(self.core.entities, "createStep"):
            e_type = entity_dict.get("type", "shot")
            target = entity_dict.get("asset_path") if e_type == "asset" else f"{entity_dict.get('sequence')}-{entity_dict.get('shot')}"
            self.core.entities.createStep(prism_dept, e_type, target, createCat=False)
            if kitsu_task:
                self.core.entities.createCategory(e_type, target, prism_dept, kitsu_task)

    def _refreshProjectBrowser(self, origin):
        if hasattr(origin, "tbw_project") and hasattr(origin.tbw_project, "refreshUI"):
            origin.tbw_project.refreshUI()
        elif hasattr(origin, "refreshUI"):
            origin.refreshUI()
        else:
            if hasattr(origin, "refreshAHierarchy"):
                origin.refreshAHierarchy()
            if hasattr(origin, "refreshShots"):
                origin.refreshShots()

    # -------------------------------------------------------------------------
    # ĐỒNG BỘ ASSETS: KITSU <-> PRISM 2
    # -------------------------------------------------------------------------
    @err_catcher(name=__name__)
    def ksuAssetsToLocal(self, origin):
        if not self.connectToKitsu():
            return

        ksuAssets = GetKitsuAssets(self)
        if ksuAssets is False:
            QMessageBox.warning(
                self.core.messageParent,
                "Kitsu Sync",
                "No assets on Kitsu were found",
            )
            return

        isEpisode = self.project_dict.get("production_type") == "tvshow"
        aBasePath = self._getAssetBasePath()

        createdAssets = []
        updatedAssets = []
        configInfo = {}

        for assetData in ksuAssets:
            assetInfo = {}
            assetType = GetAssetType(assetData["entity_type_id"])["name"]
            rel_parts = [assetType]

            if assetData.get("source_id") is not None:
                rel_parts.append(GetEpisodeName(assetData["source_id"]))
            elif isEpisode:
                rel_parts.append("Main Pack")

            rel_parts.append(assetData["name"])
            relAssetPath = "/".join(rel_parts)
            fullAssetPath = os.path.join(aBasePath, *rel_parts)

            assetInfo["objID"] = assetData["id"]
            entity_dict = {"type": "asset", "asset_path": relAssetPath}

            if not os.path.isdir(fullAssetPath):
                try:
                    self.core.entities.createEntity(entity_dict)
                except TypeError:
                    self.core.entities.createEntity("asset", fullAssetPath)
                createdAssets.append(assetData["name"])

            tasks = GetTasksForAsset(assetData)
            for task in tasks:
                kitsuStep = task["task_type_name"]
                prismStep = self.getPrismStepFromKitsuStep(kitsuStep) or kitsuStep
                self._createDepartmentAndTask(entity_dict, prismStep, kitsuStep)

            tmbID, created, updated = DownloadThumbnail(
                self,
                assetData["name"],
                assetData.get("preview_file_id"),
                "Assetinfo",
                entity=entity_dict,
            )
            if tmbID == "":
                removeID(self, assetData["name"], "assetinfo")
            elif tmbID is not False:
                assetInfo["thumbnailID"] = tmbID

            if assetData["name"] not in createdAssets and assetData["name"] not in updatedAssets:
                if created:
                    createdAssets.append(assetData["name"])
                elif updated:
                    updatedAssets.append(assetData["name"])

            desc, created, updated = DownloadDescription(
                self,
                assetData["name"],
                assetData.get("description"),
                "assetinfo",
            )
            if desc is not False:
                assetInfo["description"] = desc
                if hasattr(self.core.entities, "setAssetDescription"):
                    try:
                        self.core.entities.setAssetDescription(assetData["name"], desc or "")
                    except Exception:
                        pass

            if assetData["name"] not in createdAssets and assetData["name"] not in updatedAssets:
                if created:
                    createdAssets.append(assetData["name"])
                elif updated:
                    updatedAssets.append(assetData["name"])

            configInfo[assetData["name"]] = assetInfo

        if len(configInfo) > 0:
            self.core.setConfig(data=configInfo, config="assetinfo")

        ReportUpdateInfo(self, createdAssets, updatedAssets, "assets")

        ignore_post_checks = bool(self.getPrjConfig("ignorepostchecks", dft=False))
        if not ignore_post_checks:
            assets = self.core.entities.getAssetPaths() if hasattr(self.core.entities, "getAssetPaths") else []
            localAssets = []
            for asset_full in assets:
                asset_name = os.path.basename(asset_full)
                if not asset_name.startswith("_"):
                    if getID(self, asset_name, "Assetinfo") is None:
                        localAssets.append(asset_full)

            if len(localAssets) > 0:
                display_names = [os.path.basename(x) for x in localAssets]
                msg = QMessageBox(
                    QMessageBox.Question,
                    "Kitsu Sync",
                    "Some local assets don't exist on Kitsu:\n" + "\n".join(display_names),
                    parent=self.core.messageParent,
                )
                msg.addButton("Add assets to Kitsu", QMessageBox.YesRole)
                msg.addButton("Do nothing", QMessageBox.YesRole)
                msg.addButton("Don't ask again", QMessageBox.YesRole)
                action = msg.exec()

                if action == 0:
                    created_assets, updated_assets = self.createAssets(localAssets)
                    ReportUpdateInfo(self, created_assets, updated_assets, "assets")
                elif action == 2:
                    self.setPrjConfig("ignorepostchecks", True)

        self._refreshProjectBrowser(origin)

    @err_catcher(name=__name__)
    def ksuAssetsToKitsu(self, origin):
        if not self.connectToKitsu():
            return
        assets = self.core.entities.getAssetPaths() if hasattr(self.core.entities, "getAssetPaths") else []
        createdAssets, updatedAssets = self.createAssets(assets)
        self.createAssetTasks(assets)
        ReportUpdateInfo(self, createdAssets, updatedAssets, "assets")

    # -------------------------------------------------------------------------
    # ĐỒNG BỘ SHOTS: KITSU <-> PRISM 2
    # -------------------------------------------------------------------------
    @err_catcher(name=__name__)
    def ksuShotsToLocal(self, origin):
        if not self.connectToKitsu():
            return

        ksuShots = GetKitsuShots(self)
        if ksuShots is False:
            QMessageBox.warning(
                self.core.messageParent,
                "Kitsu Sync",
                "No shots on Kitsu were found",
            )
            return

        createdShots = []
        updatedShots = []
        configInfo = {}

        existing_shots = set()
        if hasattr(self.core.entities, "getShots"):
            res = self.core.entities.getShots()
            shots_list = res[1] if isinstance(res, tuple) and len(res) > 1 else res
            if isinstance(shots_list, list):
                for s in shots_list:
                    if isinstance(s, dict):
                        existing_shots.add(
                            self._getShotKey(s.get("sequence", ""), s.get("shot", ""), s.get("episode"))
                        )

        frame_nudge = 1 if bool(self.getPrjConfig("setfirstframeone", dft=False)) else 1001

        for shotData in ksuShots:
            shotInfo = {}
            seq_name = shotData.get("sequence_name") or "no_sequence"
            shot_short = shotData["name"]
            ep_name = shotData.get("episode_name")

            shotName = self._getShotKey(seq_name, shot_short, ep_name)
            shotInfo["objID"] = shotData["id"]

            entity_dict = {
                "type": "shot",
                "sequence": seq_name,
                "shot": shot_short,
            }
            if ep_name:
                entity_dict["episode"] = ep_name

            # Tính toán Frame Range từ Kitsu
            nb_frames = int(shotData["nb_frames"]) if shotData.get("nb_frames") is not None else None
            frame_in = None
            frame_out = None
            s_data = shotData.get("data") or {}
            if s_data.get("frame_in") is not None:
                frame_in = int(s_data["frame_in"])
            if s_data.get("frame_out") is not None:
                frame_out = int(s_data["frame_out"])

            if frame_in is not None:
                if frame_out is None and nb_frames is not None:
                    frame_out = frame_in + nb_frames - 1
            elif nb_frames is not None:
                frame_in = frame_nudge
                frame_out = nb_frames - 1 + frame_nudge

            frame_range = [frame_in, frame_out] if (frame_in is not None and frame_out is not None) else None

            if shotName not in existing_shots:
                try:
                    if frame_range:
                        self.core.entities.createEntity(entity_dict, frameRange=frame_range)
                    else:
                        self.core.entities.createEntity(entity_dict)
                except TypeError:
                    self.core.entities.createEntity("shot", shotName)
                createdShots.append(shotName)

            tasks = GetTasksForShot(shotData)
            for task in tasks:
                kitsuStep = task["task_type_name"]
                prismStep = self.getPrismStepFromKitsuStep(kitsuStep) or kitsuStep
                self._createDepartmentAndTask(entity_dict, prismStep, kitsuStep)

            if frame_range:
                if hasattr(self.core.entities, "setShotRange"):
                    try:
                        self.core.entities.setShotRange(entity_dict, frame_in, frame_out)
                    except Exception:
                        pass
                shotRange = self.core.getConfig("shotRanges", shotName, config="shotinfo")
                prv_in, prv_out = (int(shotRange[0]), int(shotRange[1])) if (isinstance(shotRange, (list, tuple)) and len(shotRange) == 2) else (None, None)
                if frame_in != prv_in or frame_out != prv_out:
                    self.core.setConfig("shotRanges", shotName, [frame_in, frame_out], config="shotinfo")
                    if shotName not in createdShots and shotName not in updatedShots:
                        updatedShots.append(shotName)

            tmbID, created, updated = DownloadThumbnail(
                self,
                shotName,
                shotData.get("preview_file_id"),
                "Shotinfo",
                entity=entity_dict,
            )
            if tmbID == "":
                removeID(self, shotName, "shotinfo")
            elif tmbID is not False and tmbID is not None:
                shotInfo["thumbnailID"] = tmbID

            if shotName not in createdShots and shotName not in updatedShots:
                if created:
                    createdShots.append(shotName)
                elif updated:
                    updatedShots.append(shotName)

            configInfo[shotName] = shotInfo

        if len(configInfo) > 0:
            self.core.setConfig(data=configInfo, config="shotinfo")

        ReportUpdateInfo(self, createdShots, updatedShots, "shots")
        self._refreshProjectBrowser(origin)

    @err_catcher(name=__name__)
    def ksuShotsToKitsu(self, origin):
        if not self.connectToKitsu():
            return

        shot_names = []
        if hasattr(self.core.entities, "getShots"):
            res = self.core.entities.getShots()
            shots_list = res[1] if isinstance(res, tuple) and len(res) > 1 else res
            if isinstance(shots_list, list):
                for s in shots_list:
                    if isinstance(s, dict) and not s.get("shot", "").startswith("_"):
                        shot_names.append(
                            self._getShotKey(s.get("sequence", ""), s.get("shot", ""), s.get("episode"))
                        )

        created_shots, updated_shots = self.createShots(shot_names)
        self.createShotTasks(shot_names)
        ReportUpdateInfo(self, created_shots, updated_shots, "shots")

    # -------------------------------------------------------------------------
    # TẠO ASSETS / SHOTS / TASKS TRÊN KITSU TỪ PRISM 2
    # -------------------------------------------------------------------------
    @err_catcher(name=__name__)
    def createAssets(self, assets):
        if not self.connectToKitsu():
            return [], []

        created_assets = []
        updated_assets = []
        configInfo = {}
        aBasePath = self._getAssetBasePath()

        for asset_location in assets:
            assetInfo = {}
            rel_path = os.path.relpath(asset_location, aBasePath) if asset_location.startswith(aBasePath) else asset_location
            splits = [p for p in rel_path.replace("\\", "/").split("/") if p]

            asset_name = splits[-1] if splits else os.path.basename(asset_location)
            asset_type_name = splits[0] if len(splits) > 1 else "General"

            asset_description = self.core.getConfig(asset_name, "description", config="assetinfo")
            if len(splits) > 2:
                sub_str = "/".join(splits[1:-1])
                asset_description = f"{sub_str} - {asset_description}" if asset_description else sub_str

            asset_type_dict, _ = createKitsuAssetType(asset_type_name)
            asset_dict, created_asset = createKitsuAsset(
                self.project_dict,
                asset_type_dict,
                asset_name,
                asset_description,
                extra_data={},
                episode=None,
            )

            if created_asset and asset_dict:
                assetInfo["objID"] = asset_dict["id"]
                created_assets.append(asset_name)
                configInfo[asset_name] = assetInfo

        if len(configInfo) > 0:
            self.core.setConfig(data=configInfo, config="assetinfo")

        self.publish_type_dict = None
        return created_assets, updated_assets

    @err_catcher(name=__name__)
    def createAssetTasks(self, assets):
        if not self.connectToKitsu():
            return
        aBasePath = self._getAssetBasePath()
        allTaskTypes = getTaskTypes()

        for asset_location in assets:
            rel_path = os.path.relpath(asset_location, aBasePath) if asset_location.startswith(aBasePath) else asset_location
            asset_name = os.path.basename(rel_path)
            asset_dict = GetAssetByName(self.project_dict, asset_name)
            if not asset_dict:
                continue

            existing_tasks = GetTasksForAsset(asset_dict)
            existing_task_names = [t.get("task_type_name") for t in existing_tasks]

            entity_dict = {"type": "asset", "asset_path": rel_path.replace("\\", "/")}
            depts = (
                self.core.entities.getDepartments(entity_dict)
                if hasattr(self.core.entities, "getDepartments")
                else []
            )
            for dept in depts:
                kitsuStep = self.getKitsuStepFromPrismStep(dept) or dept
                if kitsuStep not in existing_task_names:
                    task_type = next((x for x in allTaskTypes if x["name"] == kitsuStep), None)
                    if task_type:
                        createKitsuTask(asset_dict, task_type)

    @err_catcher(name=__name__)
    def createShots(self, shots):
        if not self.connectToKitsu():
            return [], []

        created_shots = []
        updated_shots = []
        configInfo = {}

        for shot_key in shots:
            shotInfo = {}
            epName, seqName, shotName = self._splitShotKey(shot_key)
            entity_dict = {"type": "shot", "sequence": seqName, "shot": shotName}
            if epName:
                entity_dict["episode"] = epName

            shotRanges = None
            if hasattr(self.core.entities, "getShotRange"):
                try:
                    shotRanges = self.core.entities.getShotRange(entity_dict)
                except Exception:
                    pass
            if not shotRanges:
                shotRanges = self.core.getConfig("shotRanges", shot_key, config="shotinfo")

            episode_dict, _ = createKitsuEpisode(self.project_dict, epName)
            sequence_dict, _ = createKitsuSequence(self.project_dict, seqName, episode_dict)
            shot_dict, created_shot = createKitsuShot(
                self.project_dict, sequence_dict, shotName, shotRanges
            )

            if created_shot and shot_dict:
                shotInfo["objID"] = shot_dict["id"]
                created_shots.append(shot_key)
                configInfo[shot_key] = shotInfo

        if len(configInfo) > 0:
            self.core.setConfig(data=configInfo, config="shotinfo")

        self.publish_type_dict = None
        return created_shots, updated_shots

    @err_catcher(name=__name__)
    def createShotTasks(self, shots):
        if not self.connectToKitsu():
            return
        allTaskTypes = getTaskTypes()

        for shot_key in shots:
            epName, seqName, shotName = self._splitShotKey(shot_key)
            episode_dict = GetEpisodeByName(self.project_dict, epName) if epName else None
            sequence_dict = GetSequenceByName(self.project_dict, seqName, episode_dict)
            if not sequence_dict:
                continue
            shot_dict = GetShotByName(sequence_dict, shotName)
            if not shot_dict:
                continue

            existing_tasks = GetTasksForShot(shot_dict)
            existing_task_names = [t.get("task_type_name") for t in existing_tasks]

            entity_dict = {"type": "shot", "sequence": seqName, "shot": shotName}
            if epName:
                entity_dict["episode"] = epName

            depts = (
                self.core.entities.getDepartments(entity_dict)
                if hasattr(self.core.entities, "getDepartments")
                else []
            )
            for dept in depts:
                kitsuStep = self.getKitsuStepFromPrismStep(dept) or dept
                if kitsuStep not in existing_task_names:
                    task_type = next((x for x in allTaskTypes if x["name"] == kitsuStep), None)
                    if task_type:
                        createKitsuTask(shot_dict, task_type)

    # -------------------------------------------------------------------------
    # STEP / DEPARTMENT MAPPING TABLE
    # -------------------------------------------------------------------------
    def populateMappingTable(self, origin):
        steps = []
        if hasattr(self.core.projects, "getDepartments"):
            try:
                steps = [d.get("abbreviation") or d.get("name") for d in self.core.projects.getDepartments()]
            except Exception:
                pass
        if not steps:
            steps_cfg = self.core.getConfig("globals", "pipeline_steps", config="project") or {}
            steps = list(steps_cfg.keys()) if isinstance(steps_cfg, dict) else []

        for step in steps:
            rows = origin.tw_steps.rowCount()
            origin.tw_steps.insertRow(rows)
            origin.tw_steps.setItem(rows, 0, QTableWidgetItem(str(step)))
            origin.tw_steps.setItem(rows, 1, QTableWidgetItem(str(step)))

    def getKitsuStepFromPrismStep(self, step):
        mapping = self.getPrjConfig("mapping", dft={})
        if isinstance(mapping, dict):
            return mapping.get(step)
        return None

    def getPrismStepFromKitsuStep(self, step):
        mapping = self.getPrjConfig("mapping", dft={})
        if isinstance(mapping, dict):
            for prismStep, kitsuStep in mapping.items():
                if step == kitsuStep:
                    return prismStep
        return None
